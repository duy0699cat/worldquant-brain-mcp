"""Configuration loading for the WorldQuant MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class WorldQuantConfig:
    email: str
    password: str
    base_url: str = "https://api.worldquantbrain.com"
    request_timeout: float = 30.0
    poll_interval_seconds: float = 10.0
    max_poll_seconds: int = 180
    rate_limit_max_retries: int = 6
    rate_limit_max_wait_seconds: float = 90.0
    reference_markdown_path: Path = Path("src/worldquant_mcp/reference/data/wq-ops.md")
    reference_chunks_path: Path = Path("src/worldquant_mcp/reference/data/wq-ops.chunks.json")
    research_journal_path: Path = Path("docs/quant-journey.md")
    experiment_memory_path: Path = Path("src/worldquant_mcp/data/experiment_memory.json")

    @classmethod
    def from_env(cls, dotenv_path: str | os.PathLike[str] | None = None) -> "WorldQuantConfig":
        load_dotenv(dotenv_path=dotenv_path or ".env", override=False)

        email = os.getenv("WQ_BRAIN_EMAIL") or os.getenv("worldquant_signin_email")
        password = os.getenv("WQ_BRAIN_PASSWORD") or os.getenv("worldquant_signin_password")

        if not email or not password:
            raise ValueError(
                "Missing WorldQuant credentials. Set WQ_BRAIN_EMAIL/WQ_BRAIN_PASSWORD "
                "or worldquant_signin_email/worldquant_signin_password."
            )

        base_url = os.getenv("WQ_BRAIN_BASE_URL", "https://api.worldquantbrain.com").rstrip("/")
        timeout = float(os.getenv("WQ_BRAIN_REQUEST_TIMEOUT", "30"))
        poll_interval = float(os.getenv("WQ_BRAIN_POLL_INTERVAL", "10"))
        max_poll = int(os.getenv("WQ_BRAIN_MAX_POLL_SECONDS", "180"))
        rate_limit_max_retries = int(os.getenv("WQ_BRAIN_RATE_LIMIT_MAX_RETRIES", "6"))
        rate_limit_max_wait = float(os.getenv("WQ_BRAIN_RATE_LIMIT_MAX_WAIT_SECONDS", "90"))

        return cls(
            email=email,
            password=password,
            base_url=base_url,
            request_timeout=timeout,
            poll_interval_seconds=poll_interval,
            max_poll_seconds=max_poll,
            rate_limit_max_retries=rate_limit_max_retries,
            rate_limit_max_wait_seconds=rate_limit_max_wait,
        )
