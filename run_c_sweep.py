"""C-sweep: B1 follow-up design-choice isolation from npnbjY0a anchor."""
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient
from worldquant_mcp.models import SimulationSettings

config = WorldQuantConfig.from_env()
client = WorldQuantClient(config)
client.authenticate()
print("Auth OK")

settings = SimulationSettings()  # USA/TOP3000/delay=1/decay=5/SUBINDUSTRY/truncation=0.08

SEEDS = [
    ("C1", "rank(reverse(ts_corr(ts_zscore(returns, 55), ts_delta(volume,1), 55)))"),
    ("C2", "rank(reverse(ts_corr(returns, group_zscore(ts_delta(volume,1), subindustry), 55)))"),
    ("C3", "rank(reverse(ts_corr(group_zscore(returns, subindustry), group_zscore(ts_delta(volume,1), subindustry), 55)))"),
    ("C4", "rank(reverse(ts_corr(group_zscore(returns, subindustry), ts_delta(volume,1), 65)))"),
    ("C5", "rank(ts_decay_linear(reverse(ts_corr(group_zscore(returns, subindustry), ts_delta(volume,1), 55)), 7))"),
]

BASELINE = {"name": "npnbjY0a", "sharpe": 1.20, "fitness": 0.75}
FITNESS_PASS = 1.0
SHARPE_PASS = 1.25

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
    checks = m.get("checks") or []

    sharpe = m.get("sharpe")
    fitness = m.get("fitness")
    returns = m.get("returns")
    turnover = m.get("turnover")
    drawdown = m.get("drawdown")
    margin = m.get("margin")

    blocking = [(c.get("name"), c.get("limit"), c.get("value")) for c in checks if c.get("result") == "FAIL"]
    pending = [c.get("name") for c in checks if c.get("result") == "PENDING"]
    sub_u = next((c.get("value") for c in checks if c.get("name") == "LOW_SUB_UNIVERSE_SHARPE"), None)
    sub_u_result = next((c.get("result") for c in checks if c.get("name") == "LOW_SUB_UNIVERSE_SHARPE"), None)

    print("Status: " + str(status) + "  Alpha: " + str(alpha_id))
    print("Sharpe=" + str(sharpe) + "  Fitness=" + str(fitness) + "  Returns=" + str(returns) + "  Turnover=" + str(turnover))
    print("Drawdown=" + str(drawdown) + "  Margin=" + str(margin) + "  Sub-U=" + str(sub_u) + " (" + str(sub_u_result) + ")")
    print("Blocking (name/limit/value)=" + str(blocking))
    print("Pending=" + str(pending))

    # Flag submission candidates
    if sharpe is not None and fitness is not None:
        if sharpe >= SHARPE_PASS and fitness >= FITNESS_PASS:
            print(">>> SUBMISSION CANDIDATE: Sharpe=" + str(sharpe) + " >= 1.25 AND Fitness=" + str(fitness) + " >= 1.0")

    results.append({
        "name": name, "expr": expr, "alpha_id": alpha_id, "status": status,
        "sharpe": sharpe, "fitness": fitness, "returns": returns,
        "turnover": turnover, "drawdown": drawdown, "margin": margin,
        "sub_u": sub_u, "sub_u_result": sub_u_result,
        "blocking": blocking, "pending": pending,
    })

    # Early-stop: same blocking check on 2+ seeds
    for b_name, b_limit, b_val in blocking:
        fail_counts[b_name] = fail_counts.get(b_name, 0) + 1
        if fail_counts[b_name] >= 2 and b_name not in ("LOW_SHARPE", "LOW_FITNESS"):
            print("\nEARLY STOP: blocking check '" + b_name + "' triggered on 2+ seeds.")

print("\n\n=== LEADERBOARD (sorted by fitness) ===")
print("Baseline npnbjY0a: Sharpe=" + str(BASELINE["sharpe"]) + "  Fitness=" + str(BASELINE["fitness"]))
print("-" * 70)
ranked = sorted(results, key=lambda x: (x["fitness"] or -99), reverse=True)
for row in ranked:
    flag = ""
    if row["sharpe"] and row["fitness"] and row["sharpe"] >= SHARPE_PASS and row["fitness"] >= FITNESS_PASS:
        flag = " *** SUBMITTABLE ***"
    print(row["name"] + "  " + str(row["alpha_id"]) + "  Sharpe=" + str(row["sharpe"]) +
          "  Fitness=" + str(row["fitness"]) + "  Sub-U=" + str(row["sub_u"]) +
          "  Pending=" + str(row["pending"]) + flag)
