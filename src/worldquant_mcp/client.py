"""Thin WorldQuant Brain API client used by MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import time
from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import WorldQuantConfig
from .models import SimulationSettings


class WorldQuantAPIError(RuntimeError):
    """Raised when the WorldQuant API returns an unexpected response."""


class WorldQuantClient:
    def __init__(self, config: WorldQuantConfig):
        self.config = config
        self.http = httpx.Client(
            base_url=config.base_url,
            auth=(config.email, config.password),
            follow_redirects=True,
            timeout=config.request_timeout,
        )
        self.auth_payload: dict[str, Any] | None = None

    def authenticate(self, *, force: bool = False) -> dict[str, Any]:
        if self.auth_payload is not None and not force:
            return self.auth_payload

        response = self.http.post("/authentication")
        self._raise_for_status(response, "authenticate")
        payload = response.json()

        token = payload.get("token")
        if isinstance(token, str) and token:
            self.http.headers["X-WQB-Session-Token"] = token

        self.auth_payload = payload
        return payload

    def get_account_info(self) -> dict[str, Any]:
        return self._get_json("/users/self")

    def list_operators(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/operators")
        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("results", data.get("items", []))

    def list_data_fields(
        self,
        *,
        region: str = "USA",
        delay: int = 1,
        universe: str = "TOP3000",
        instrument_type: str = "EQUITY",
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any] | list[Any]:
        params: dict[str, Any] = {
            "region": region,
            "delay": delay,
            "universe": universe,
            "instrumentType": instrument_type,
            "limit": limit,
            "offset": offset,
        }
        if search:
            params["search"] = search
        return self._get_json("/data-fields", params=params)

    def list_recent_alphas(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        region: str | None = None,
        order: str = "-dateCreated",
    ) -> dict[str, Any] | list[Any]:
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "hidden": "false",
            "order": order,
        }
        if status:
            params["status"] = status
        if region:
            params["settings.region"] = region
        return self._get_json("/users/self/alphas", params=params)

    def get_alpha(self, alpha_id: str) -> dict[str, Any]:
        return self._get_json(f"/alphas/{alpha_id}")

    def get_alpha_check(self, alpha_id: str) -> dict[str, Any] | list[Any]:
        return self._get_json(f"/alphas/{alpha_id}/check")

    def submit_simulation(
        self,
        expression: str,
        settings: SimulationSettings | None = None,
        *,
        simulation_type: str = "REGULAR",
    ) -> dict[str, Any]:
        settings = settings or SimulationSettings()
        payload = {
            "type": simulation_type,
            "settings": settings.to_api_payload(),
            "regular": expression,
        }
        response = self._request("POST", "/simulations", json=payload)
        progress_url = response.headers.get("Location") or response.headers.get("location")
        return {
            "status_code": response.status_code,
            "progress_url": progress_url,
            "payload": payload,
        }

    def get_simulation_status(self, simulation_id_or_url: str) -> dict[str, Any]:
        path = self._normalize_location(simulation_id_or_url)
        response = self._request("GET", path)
        if not response.text.strip():
            return {
                "status": "INITIALIZING",
                "path": path,
            }
        return response.json()

    def wait_for_simulation(
        self,
        simulation_id_or_url: str,
        *,
        timeout_seconds: int | None = None,
        on_update: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        timeout_limit = timeout_seconds or self.config.max_poll_seconds
        started_at = datetime.now().astimezone()
        started_monotonic = time.monotonic()
        deadline = started_monotonic + timeout_limit
        path = self._normalize_location(simulation_id_or_url)
        poll_count = 0

        while time.monotonic() < deadline:
            poll_count += 1
            payload = self.get_simulation_status(path)
            update = self._build_simulation_tracking(
                path=path,
                payload=payload,
                started_at=started_at,
                started_monotonic=started_monotonic,
                timeout_seconds=timeout_limit,
                poll_count=poll_count,
            )
            if on_update:
                on_update(update)

            alpha = payload.get("alpha") if isinstance(payload, dict) else None
            if alpha:
                alpha_id = alpha.split("/")[-1] if isinstance(alpha, str) else alpha.get("id")
                details = self.get_alpha(alpha_id) if alpha_id else None
                complete_update = self._build_simulation_tracking(
                    path=path,
                    payload=payload,
                    started_at=started_at,
                    started_monotonic=started_monotonic,
                    timeout_seconds=timeout_limit,
                    poll_count=poll_count,
                    final_status="COMPLETE",
                    progress_override=1.0,
                )
                if on_update:
                    on_update(complete_update)
                return {
                    "status": "COMPLETE",
                    "simulation": payload,
                    "alpha_id": alpha_id,
                    "alpha": details,
                    "tracking": complete_update,
                }
            if isinstance(payload, dict) and payload.get("status") in {"FAILED", "ERROR"}:
                failed_update = self._build_simulation_tracking(
                    path=path,
                    payload=payload,
                    started_at=started_at,
                    started_monotonic=started_monotonic,
                    timeout_seconds=timeout_limit,
                    poll_count=poll_count,
                    final_status=str(payload.get("status")),
                )
                if on_update:
                    on_update(failed_update)
                return {
                    "status": payload.get("status"),
                    "simulation": payload,
                    "tracking": failed_update,
                }
            time.sleep(self.config.poll_interval_seconds)

        payload = self.get_simulation_status(path)
        timeout_update = self._build_simulation_tracking(
            path=path,
            payload=payload,
            started_at=started_at,
            started_monotonic=started_monotonic,
            timeout_seconds=timeout_limit,
            poll_count=poll_count,
            final_status="TIMEOUT",
        )
        if on_update:
            on_update(timeout_update)
        return {
            "status": "TIMEOUT",
            "simulation": payload,
            "tracking": timeout_update,
        }

    def submit_alpha(self, alpha_id: str) -> dict[str, Any]:
        response = self._request("POST", f"/alphas/{alpha_id}/submit")
        return self._coerce_json(response)

    def get_submission_status(self, alpha_id: str) -> dict[str, Any] | list[Any]:
        return self._get_json(f"/alphas/{alpha_id}/submit")

    def close(self) -> None:
        self.http.close()

    def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        response = self._request("GET", path, params=params)
        return response.json()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.authenticate()

        last_response: httpx.Response | None = None
        max_attempts = max(1, self.config.rate_limit_max_retries + 1)
        for attempt in range(max_attempts):
            response = self.http.request(method, path, **kwargs)
            last_response = response

            if response.status_code == 401 and attempt == 0:
                self.authenticate(force=True)
                continue

            if response.status_code == 429 and attempt < max_attempts - 1:
                sleep_seconds = self._rate_limit_sleep_seconds(response, attempt)
                time.sleep(sleep_seconds)
                continue

            self._raise_for_status(response, f"{method} {path}")
            return response

        assert last_response is not None
        self._raise_for_status(last_response, f"{method} {path}")
        return last_response

    def _normalize_location(self, simulation_id_or_url: str) -> str:
        if simulation_id_or_url.startswith("http://") or simulation_id_or_url.startswith("https://"):
            parsed = urlparse(simulation_id_or_url)
            return parsed.path
        if simulation_id_or_url.startswith("/"):
            return simulation_id_or_url
        return f"/simulations/{simulation_id_or_url}"

    def _raise_for_status(self, response: httpx.Response, action: str) -> None:
        if response.status_code < 400:
            return
        detail = self._coerce_json(response)
        raise WorldQuantAPIError(f"{action} failed with {response.status_code}: {detail}")

    def _build_simulation_tracking(
        self,
        *,
        path: str,
        payload: dict[str, Any] | list[Any],
        started_at: datetime,
        started_monotonic: float,
        timeout_seconds: int | float,
        poll_count: int,
        final_status: str | None = None,
        progress_override: float | None = None,
    ) -> dict[str, Any]:
        elapsed_seconds = max(0.0, time.monotonic() - started_monotonic)
        progress = progress_override
        raw_status: str | None = None
        if isinstance(payload, dict):
            raw_status = payload.get("status") if isinstance(payload.get("status"), str) else None
            if progress is None:
                progress = self._coerce_progress_fraction(payload.get("progress"))

        status = final_status or raw_status or ("RUNNING" if progress is not None else "INITIALIZING")
        tracking = {
            "path": path,
            "status": status,
            "start_time": started_at.strftime("%H:%M:%S"),
            "started_at": started_at.isoformat(timespec="seconds"),
            "elapsed": self._format_elapsed(elapsed_seconds),
            "elapsed_seconds": round(elapsed_seconds, 1),
            "poll_count": poll_count,
            "timeout_seconds": timeout_seconds,
            "remaining_seconds": round(max(float(timeout_seconds) - elapsed_seconds, 0.0), 1),
        }
        if raw_status:
            tracking["raw_status"] = raw_status
        if progress is not None:
            tracking["progress"] = round(progress, 4)
            tracking["progress_percent"] = round(progress * 100.0, 1)
        return tracking

    def _coerce_progress_fraction(self, value: Any) -> float | None:
        if not isinstance(value, (int, float)):
            return None
        progress = float(value)
        if progress < 0:
            return 0.0
        if progress <= 1:
            return progress
        if progress <= 100:
            return progress / 100.0
        return 1.0

    def _format_elapsed(self, elapsed_seconds: float) -> str:
        total_seconds = max(0, int(round(elapsed_seconds)))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h{minutes}m{seconds}s"
        if minutes:
            return f"{minutes}m{seconds}s"
        return f"{seconds}s"

    def _rate_limit_sleep_seconds(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), self.config.rate_limit_max_wait_seconds)
            except ValueError:
                pass

        detail = self._coerce_json(response)
        if isinstance(detail, dict) and detail.get("detail") == "CONCURRENT_SIMULATION_LIMIT_EXCEEDED":
            # Brain can hold concurrency locks for a while; back off harder here.
            return min(15.0 * (attempt + 1), self.config.rate_limit_max_wait_seconds)

        return min(float(2 ** (attempt + 1)), self.config.rate_limit_max_wait_seconds)

    def _coerce_json(self, response: httpx.Response) -> dict[str, Any] | list[Any] | str:
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        return response.text.strip()
