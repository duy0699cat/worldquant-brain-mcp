# WorldQuant MCP

A Python [MCP](https://modelcontextprotocol.io) server for automating WorldQuant BRAIN
alpha-research workflows, plus a local reference pipeline that converts documentation
into LLM-friendly artifacts. Built as a personal research-engineering project.

> **Note:** This is an independent, unofficial project and is not affiliated with or
> endorsed by WorldQuant. WorldQuant's platform documentation is **not** included in this
> repository — you supply your own PDF (see *Reference ingestion*). Use of the BRAIN API is
> subject to WorldQuant's own terms.

## Status

Initial working scaffold in place.

Current capabilities:

- Load credentials from `.env` or `WQ_BRAIN_*` environment variables.
- Convert scanned or text-based PDFs into markdown and chunked JSON.
- Authenticate against `api.worldquantbrain.com`.
- Search local operator/reference material.
- Fetch platform operators, account details, and data fields.
- Turn text hypotheses into field proxies and expression templates.
- Ingest external research links or notes into mechanism summaries.
- Mutate seed expressions into nearby variants.
- Submit simulations and poll simulation progress.
- Simulate batches of expressions and rank the results.
- Fetch alpha details and submission status.
- Validate whether an alpha is ready to submit and summarize blockers.
- Compare candidate expressions against recent alphas and logged experiments.
- Persist local experiment memory for future agents.
- Submit alphas behind an explicit confirmation flag.

## Reference ingestion

The first implemented component is the PDF ingestion pipeline.

```powershell
.venv/Scripts/python.exe -m pip install -e .
wq-ingest-reference --input wq-ops.pdf
```

Generated artifacts (produced locally, git-ignored — not committed):

- `src/worldquant_mcp/reference/data/wq-ops.md`
- `src/worldquant_mcp/reference/data/wq-ops.chunks.json`

If the PDF has no text layer, the ingester falls back to OCR using in-process
Python libraries so it still works on a clean Windows machine.

## Running the MCP server

Install the package in editable mode:

```powershell
.venv/Scripts/python.exe -m pip install -e .
```

Do not start the stdio MCP server manually if you want to use it from VS Code. VS Code should launch it for you from `mcp.json`.

Add this to your user-level `mcp.json` or workspace `.vscode/mcp.json`:

```json
{
  "servers": {
    "worldquant-mcp": {
      "type": "stdio",
      "command": ".venv/Scripts/worldquant-mcp.exe",
      "env": {
        "WQ_BRAIN_EMAIL": "<your-email>",
        "WQ_BRAIN_PASSWORD": "<your-password>"
      }
    }
  }
}
```

After saving `mcp.json`, use the VS Code MCP server management UI to reload or start the server. Once it shows as running, the tools from this server become available to Copilot agents.

If you want to run the server yourself for debugging only, use one of these commands:

```powershell
.venv/Scripts/worldquant-mcp.exe
```

Or run it via Python:

```powershell
.venv/Scripts/python.exe -m worldquant_mcp
```

## Timeout behavior

- Polling tools now default to bounded waits instead of open-ended multi-minute blocking.
- `wait_simulation`, `batch_simulate`, and `parallel_mechanism_search` default to `180` seconds.
- Override with `timeout_seconds` when you intentionally want a longer or shorter wait.
- Set `WQ_BRAIN_MAX_POLL_SECONDS` if you want to change the client-wide default used by direct code paths.
- 429 handling is now more robust in the shared client: temporary rate limits are retried with bounded backoff, and `CONCURRENT_SIMULATION_LIMIT_EXCEEDED` backs off more aggressively before failing.
- Tune `WQ_BRAIN_RATE_LIMIT_MAX_RETRIES` and `WQ_BRAIN_RATE_LIMIT_MAX_WAIT_SECONDS` if you want stricter or looser retry behavior.

## Example session

Once the server is running, an MCP-aware agent calls the tools directly. Illustrative output
below (metric values are synthetic and field/alpha names are placeholders — no real platform
data is shown):

```text
> healthcheck
{ "status": "ok", "authenticated": true }

> get_platform_operators
[ "rank", "zscore", "ts_delta", "ts_backfill", "ts_decay_linear", "group_zscore", ... ]

> create_simulation  expression="rank(<your_signal>)"  settings=USA/TOP3000/delay=1
{ "status": "COMPLETE", "alpha_id": "<id>",
  "is": { "sharpe": 1.21, "fitness": 0.74, "returns": 0.052, "turnover": 0.11 } }

> validate_alpha_submission_by_id  alpha_id="<id>"
{ "ready": false, "blocking": ["LOW_FITNESS"], "pending": ["SELF_CORRELATION"] }
```

The operator names above are part of BRAIN's public expression language; the pipeline never
hard-codes proprietary data fields or alpha identifiers.

## Implemented tools

- `healthcheck`
- `get_account`
- `get_platform_operators`
- `search_local_reference`
- `get_reference_operators`
- `get_data_fields`
- `get_recent_alphas`
- `get_alpha`
- `get_alpha_submission`
- `create_simulation`
- `batch_simulate`
- `summarize_alpha_batch_by_id`
- `mutate_alpha_expression`
- `map_research_hypothesis`
- `ingest_research_material`
- `get_simulation`
- `wait_simulation`
- `analyze_alpha_novelty`
- `log_alpha_experiment`
- `list_alpha_experiments`
- `validate_alpha_submission_by_id`
- `submit_alpha_by_id`

## Research Notes

- `docs/mcp-roadmap.md` tracks pragmatic MCP upgrades for alpha research.
- `docs/quant-journey.md` is a running experiment log for future agents.
- `src/worldquant_mcp/data/experiment_memory.json` stores the same experiments in machine-readable form.
