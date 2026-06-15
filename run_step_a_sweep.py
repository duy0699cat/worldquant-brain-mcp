"""
Step A sweep — [REDACTED] wrapper discipline probes.
Seeds A1, A3, A4, A6 (tweaked). Sequential, bounded at 180s each.
"""
from __future__ import annotations

import json
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient
from worldquant_mcp.models import SimulationSettings

SEEDS = {
    "A1": "[REDACTED]",
    "A3": "[REDACTED]",
    "A4": "[REDACTED]",
    "A6": "[REDACTED]",
}

SETTINGS = SimulationSettings(
    instrument_type="EQUITY",
    region="USA",
    universe="TOP3000",
    delay=1,
    decay=6,
    neutralization="SUBINDUSTRY",
    truncation=0.08,
)

config = WorldQuantConfig.from_env()
client = WorldQuantClient(config)
auth = client.authenticate()
print(f"Auth OK: {bool(auth)}\n")

results = {}
for name, expr in SEEDS.items():
    print(f"--- {name} ---")
    print(f"Expression: {expr}")
    try:
        sub = client.submit_simulation(expression=expr, settings=SETTINGS)
        sc = sub.get("status_code")
        url = sub.get("progress_url")
        print(f"Submitted: status_code={sc}, url={url}")
        if not url:
            print(f"  ERROR: No progress_url. Skipping.")
            results[name] = {"error": "no_progress_url", "expression": expr}
            continue
        result = client.wait_for_simulation(url, timeout_seconds=180)
        sim_status = result.get("status")
        print(f"  Simulation status: {sim_status}")
        alpha = result.get("alpha")
        if isinstance(alpha, dict):
            alpha_id = alpha.get("id", "?")
            metrics = alpha.get("is", {})
            checks = alpha.get("checks", [])
            sharpe = metrics.get("sharpe")
            fitness = metrics.get("fitness")
            returns = metrics.get("returns")
            turnover = metrics.get("turnover")
            sub_u = metrics.get("subUniverseSharpe", "N/A")
            blocking = [c for c in checks if c.get("result") == "FAIL"]
            pending = [c.get("name") for c in checks if c.get("result") == "PENDING"]
            print(f"  Alpha ID: {alpha_id}")
            print(f"  Sharpe:   {sharpe}")
            print(f"  Fitness:  {fitness}")
            print(f"  Returns:  {returns}")
            print(f"  Turnover: {turnover}")
            print(f"  Sub-U Sh: {sub_u}")
            print(f"  Blocking: {blocking}")
            print(f"  Pending:  {pending}")
            results[name] = {
                "expression": expr,
                "alphaId": alpha_id,
                "sharpe": sharpe,
                "fitness": fitness,
                "returns": returns,
                "turnover": turnover,
                "subUniverseSharpe": sub_u,
                "blocking": blocking,
                "pending": pending,
                "simulationStatus": sim_status,
            }
        else:
            print(f"  No alpha produced. Raw: {str(result)[:400]}")
            results[name] = {"error": "no_alpha", "status": sim_status, "expression": expr}
    except Exception as exc:
        print(f"  EXCEPTION: {exc}")
        results[name] = {"error": str(exc), "expression": expr}
    print()

print("=== FINAL SUMMARY ===")
for name, r in results.items():
    if "alphaId" in r:
        print(f"{name}: {r['alphaId']}  Sharpe={r['sharpe']}  Fitness={r['fitness']}  SubUSh={r['subUniverseSharpe']}")
    else:
        print(f"{name}: ERROR — {r.get('error')}")
print()
print(json.dumps(results, indent=2))
