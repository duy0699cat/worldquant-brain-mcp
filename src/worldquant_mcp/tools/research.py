"""Research and simulation tool helpers."""

from __future__ import annotations

from typing import Any

from ..client import WorldQuantClient
from ..models import SimulationSettings


def get_account_info(client: WorldQuantClient) -> dict[str, Any]:
    account = client.get_account_info()
    return {
        "id": account.get("id"),
        "email": account.get("email"),
        "fullName": account.get("fullName"),
        "approved": account.get("approved"),
        "geniusLevel": account.get("geniusLevel"),
        "settings": account.get("settings"),
        "auxiliary": account.get("auxiliary"),
    }


def list_operators(client: WorldQuantClient) -> dict[str, Any]:
    operators = client.list_operators()
    return {
        "count": len(operators),
        "operators": operators,
    }


def list_data_fields(
    client: WorldQuantClient,
    *,
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
    instrument_type: str = "EQUITY",
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    data = client.list_data_fields(
        region=region,
        delay=delay,
        universe=universe,
        instrument_type=instrument_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "request": {
            "region": region,
            "delay": delay,
            "universe": universe,
            "instrumentType": instrument_type,
            "search": search,
            "limit": limit,
            "offset": offset,
        },
        "data": data,
    }


def list_recent_alphas(
    client: WorldQuantClient,
    *,
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    data = client.list_recent_alphas(limit=limit, offset=offset, status=status, region=region)
    return {
        "request": {
            "limit": limit,
            "offset": offset,
            "status": status,
            "region": region,
        },
        "data": data,
    }


def get_alpha_details(client: WorldQuantClient, alpha_id: str) -> dict[str, Any]:
    alpha = client.get_alpha(alpha_id)
    checks = client.get_alpha_check(alpha_id)
    return {
        "alpha": alpha,
        "checks": checks,
    }


def get_submission_status(client: WorldQuantClient, alpha_id: str) -> dict[str, Any]:
    return {
        "alpha_id": alpha_id,
        "submission": client.get_submission_status(alpha_id),
    }


def submit_simulation(
    client: WorldQuantClient,
    expression: str,
    *,
    region: str = "USA",
    universe: str = "TOP3000",
    delay: int = 1,
    decay: int = 5,
    neutralization: str = "SUBINDUSTRY",
    truncation: float = 0.08,
    instrument_type: str = "EQUITY",
) -> dict[str, Any]:
    settings = SimulationSettings(
        instrument_type=instrument_type,
        region=region,
        universe=universe,
        delay=delay,
        decay=decay,
        neutralization=neutralization,
        truncation=truncation,
    )
    return client.submit_simulation(expression=expression, settings=settings)


def wait_for_simulation(
    client: WorldQuantClient,
    simulation_id_or_url: str,
    *,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    return client.wait_for_simulation(simulation_id_or_url, timeout_seconds=timeout_seconds)


def get_simulation_status(client: WorldQuantClient, simulation_id_or_url: str) -> dict[str, Any]:
    return client.get_simulation_status(simulation_id_or_url)
