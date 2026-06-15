"""Extracts a PDF into cleaned markdown and chunked JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from .clean import clean_page_text, extract_operator_names, split_into_chunks


def build_markdown(
    pages: Iterable[tuple[int, str]], source_name: str, extraction_method: str
) -> tuple[str, list[dict[str, object]]]:
    markdown_pages: list[str] = [f"# {source_name}", f"_Extraction method: {extraction_method}_"]
    chunk_records: list[dict[str, object]] = []

    for page_index, raw_text in pages:
        cleaned = clean_page_text(raw_text)
        if not cleaned.strip():
            continue

        markdown_pages.append(f"\n<!-- page: {page_index} -->\n")
        markdown_pages.append(cleaned)

        for chunk_index, chunk_text in enumerate(split_into_chunks(cleaned), start=1):
            chunk_records.append(
                {
                    "id": f"{source_name.lower()}-p{page_index}-c{chunk_index}",
                    "source": source_name,
                    "page": page_index,
                    "chunk": chunk_index,
                    "text": chunk_text,
                    "operators": extract_operator_names(chunk_text),
                }
            )

    return "\n\n".join(markdown_pages).strip() + "\n", chunk_records


def extract_text_pages(input_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(input_path))
    pages: list[tuple[int, str]] = []

    for page_index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        if raw_text.strip():
            pages.append((page_index, raw_text))

    return pages


def _load_ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except ImportError:
        from rapidocr import RapidOCR  # type: ignore

    return RapidOCR()


def _ocr_result_to_text(result: object) -> str:
    if hasattr(result, "txts"):
        return "\n".join(getattr(result, "txts"))

    if isinstance(result, tuple):
        return _ocr_result_to_text(result[0])

    if isinstance(result, list):
        lines: list[str] = []
        for item in result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                candidate = item[1]
                if isinstance(candidate, str):
                    lines.append(candidate)
                elif isinstance(candidate, (list, tuple)) and candidate:
                    lines.append(str(candidate[0]))
            elif isinstance(item, dict) and "text" in item:
                lines.append(str(item["text"]))
        return "\n".join(line for line in lines if line.strip())

    return str(result).strip()


def extract_ocr_pages(input_path: Path, *, scale: float = 2.0) -> list[tuple[int, str]]:
    import numpy
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(input_path))
    engine = _load_ocr_engine()
    pages: list[tuple[int, str]] = []

    for page_index in range(len(document)):
        page = document.get_page(page_index)
        image = page.render(scale=scale).to_pil()
        raw_result = engine(numpy.array(image))
        page_text = _ocr_result_to_text(raw_result)
        if page_text.strip():
            pages.append((page_index + 1, page_text))
        page.close()

    document.close()
    return pages


def parse_args() -> argparse.Namespace:
    default_data_dir = Path(__file__).resolve().parent / "data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the source PDF")
    parser.add_argument(
        "--markdown-output",
        default=str(default_data_dir / "wq-ops.md"),
        help="Path for cleaned markdown output",
    )
    parser.add_argument(
        "--chunks-output",
        default=str(default_data_dir / "wq-ops.chunks.json"),
        help="Path for chunked JSON output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    markdown_output = Path(args.markdown_output).expanduser().resolve()
    chunks_output = Path(args.chunks_output).expanduser().resolve()

    source_name = input_path.stem
    pages = extract_text_pages(input_path)
    extraction_method = "text-layer"

    if not pages:
        pages = extract_ocr_pages(input_path)
        extraction_method = "ocr"

    markdown, chunks = build_markdown(pages, source_name, extraction_method)

    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    chunks_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown, encoding="utf-8")
    chunks_output.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    print(f"Wrote {markdown_output}")
    print(f"Wrote {chunks_output}")
    print(f"Extracted {len(chunks)} chunks")


if __name__ == "__main__":
    main()