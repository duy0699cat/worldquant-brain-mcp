"""B1 peer-relative dislocation sweep — sequential bounded simulations."""
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient
from worldquant_mcp.models import SimulationSettings

config = WorldQuantConfig.from_env()
client = WorldQuantClient(config)
client.authenticate()
print("Auth OK")

settings = SimulationSettings()  # USA/TOP3000/delay=1/decay=5/SUBINDUSTRY/truncation=0.08

SEEDS = [
    ("B1-1", "[REDACTED]"),
    ("B1-2", "[REDACTED]"),
    ("B1-3", "[REDACTED]"),
    ("B1-4r", "[REDACTED]"),
    ("B1-5", "[REDACTED]"),
]

results = []
fail_counts = {}

for name, expr in SEEDS:
    print("\n--- " + name + " ---")
    print("Expression: " + expr)
    r = client.submit_simulation(expr, settings)
    url = r.get("progress_url")
    print("Progress URL: " + str(url))
    result = client.wait_for_simulation(url, timeout_seconds=180)
    status = result.get("status")
    alpha_id = result.get("alpha_id")
    alpha = result.get("alpha") or {}
    m = alpha.get("is") or {}
    checks = alpha.get("checks") or []
    blocking = [c.get("name") for c in checks if c.get("result") == "FAIL"]
    pending = [c.get("name") for c in checks if c.get("result") == "PENDING"]
    sharpe = m.get("sharpe")
    fitness = m.get("fitness")
    sub_u = m.get("subUniverseSharpe")
    turnover = m.get("turnover")
    drawdown = m.get("drawdown")
    returns = m.get("returns")
    margin = m.get("margin")
    print("Status: " + str(status) + "  Alpha: " + str(alpha_id))
    print("Sharpe: " + str(sharpe) + "  Fitness: " + str(fitness) + "  Returns: " + str(returns))
    print("Turnover: " + str(turnover) + "  Sub-U: " + str(sub_u) + "  Drawdown: " + str(drawdown))
    print("Blocking: " + str(blocking) + "  Pending: " + str(pending))
    results.append({
        "name": name, "expr": expr, "alpha_id": alpha_id, "status": status,
        "sharpe": sharpe, "fitness": fitness, "returns": returns,
        "turnover": turnover, "sub_u": sub_u, "drawdown": drawdown, "margin": margin,
        "blocking": blocking, "pending": pending,
    })
    # Early stop if 2+ seeds share the same blocking check
    for b in blocking:
        fail_counts[b] = fail_counts.get(b, 0) + 1
        if fail_counts[b] >= 2:
            print("\nEARLY STOP: blocking check '" + b + "' has triggered on 2+ seeds.")

print("\n\n=== LEADERBOARD ===")
ranked = sorted(results, key=lambda x: (x["fitness"] or -99), reverse=True)
for row in ranked:
    print(row["name"] + "  " + str(row["alpha_id"]) + "  Sharpe=" + str(row["sharpe"]) + "  Fitness=" + str(row["fitness"]) + "  Sub-U=" + str(row["sub_u"]) + "  Blocking=" + str(row["blocking"]))
