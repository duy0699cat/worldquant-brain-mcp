# Reference data (not committed)

This directory holds locally-generated reference artifacts produced by
`wq-ingest-reference` from a documentation PDF you supply yourself
(`wq-ops.md`, `wq-ops.chunks.json`).

These files are intentionally **git-ignored** and not distributed, because the
source documentation is WorldQuant's proprietary material. Generate your own:

```powershell
wq-ingest-reference --input your-docs.pdf
```
