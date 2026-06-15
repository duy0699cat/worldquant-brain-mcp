"""State-changing submission helpers."""

from __future__ import annotations

from typing import Any

from ..client import WorldQuantClient


def validate_alpha_submission(client: WorldQuantClient, alpha_id: str) -> dict[str, Any]:
    alpha = client.get_alpha(alpha_id)
    in_sample = alpha.get("is") or {}
    checks = in_sample.get("checks") or []
    failed_checks = [check for check in checks if check.get("result") == "FAIL"]
    pending_checks = [check for check in checks if check.get("result") == "PENDING"]
    # Only FAILED checks block submission. PENDING checks (e.g. SELF_CORRELATION)
    # are OS-stage computations that Brain runs after submission — they do NOT
    # block IS→OS promotion. QP2NPG6X and d5QNpnwv both shipped with PENDING checks.
    submittable = not failed_checks

    return {
        "alpha_id": alpha_id,
        "submittable": submittable,
        "status": alpha.get("status"),
        "stage": alpha.get("stage"),
        "grade": alpha.get("grade"),
        "metrics": {
            "sharpe": in_sample.get("sharpe"),
            "fitness": in_sample.get("fitness"),
            "returns": in_sample.get("returns"),
            "turnover": in_sample.get("turnover"),
            "drawdown": in_sample.get("drawdown"),
            "margin": in_sample.get("margin"),
        },
        "blockingChecks": failed_checks,
        "pendingChecks": pending_checks,
        "checkCount": len(checks),
    }


def submit_alpha(client: WorldQuantClient, alpha_id: str, *, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        raise ValueError("submit_alpha is state-changing; pass confirm=True to proceed.")
    validation = validate_alpha_submission(client, alpha_id)
    if not validation["submittable"]:
        raise ValueError(
            "alpha is not ready for submission; resolve failed IS checks first: "
            f"{validation}"
        )
    return {
        "alpha_id": alpha_id,
        "validation": validation,
        "response": client.submit_alpha(alpha_id),
    }
