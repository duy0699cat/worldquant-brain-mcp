"""FastMCP server for WorldQuant Brain workflows."""

from __future__ import annotations

import asyncio
from functools import lru_cache

from mcp.server.fastmcp import Context, FastMCP

from .client import WorldQuantClient
from .config import WorldQuantConfig
from .reference.index import ReferenceIndex
from .tools.reference import list_reference_operators, search_reference
from .tools.research import (
    get_account_info,
    get_alpha_details,
    get_simulation_status,
    get_submission_status,
    list_data_fields,
    list_operators,
    list_recent_alphas,
    submit_simulation,
    wait_for_simulation,
)
from .models import SimulationSettings
from .tools.lab import (
    _sort_summaries,
    _summarize_alpha,
    analyze_expression_novelty,
    ingest_research_sources,
    list_logged_experiments,
    log_experiment,
    map_hypothesis_to_proxies,
    mutate_expression,
    run_parallel_hypothesis_search,
    summarize_alpha_batch,
    validate_logged_expression_novelty_shadow,
)
from .tools.submission import submit_alpha, validate_alpha_submission


mcp = FastMCP("WorldQuant MCP", json_response=True)
DEFAULT_TOOL_TIMEOUT_SECONDS = 360


@lru_cache(maxsize=1)
def get_config() -> WorldQuantConfig:
    return WorldQuantConfig.from_env()


@lru_cache(maxsize=1)
def get_client() -> WorldQuantClient:
    return WorldQuantClient(get_config())


@lru_cache(maxsize=1)
def get_reference_index() -> ReferenceIndex:
    config = get_config()
    return ReferenceIndex.load(config.reference_chunks_path, config.reference_markdown_path)


@mcp.tool()
def healthcheck() -> dict:
    """Verify credentials and report local reference corpus status."""
    client = get_client()
    auth = client.authenticate()
    index = get_reference_index()
    return {
        "authenticated": True,
        "user": auth.get("user"),
        "referenceChunks": len(index.chunks),
    }


@mcp.tool()
def get_account() -> dict:
    """Fetch basic account profile information for the current WorldQuant user."""
    return get_account_info(get_client())


@mcp.tool()
def get_platform_operators() -> dict:
    """Fetch operator metadata from the live WorldQuant API."""
    return list_operators(get_client())


@mcp.tool()
def search_local_reference(query: str, limit: int = 5) -> dict:
    """Search the OCR-converted local WorldQuant reference corpus."""
    return search_reference(get_reference_index(), query, limit=limit)


@mcp.tool()
def get_reference_operators(limit: int = 100) -> dict:
    """List operator names found in the local reference corpus."""
    return list_reference_operators(get_reference_index(), limit=limit)


@mcp.tool()
def get_data_fields(
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
    instrument_type: str = "EQUITY",
    search: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Fetch available data fields for a given region, universe, and delay."""
    return list_data_fields(
        get_client(),
        region=region,
        delay=delay,
        universe=universe,
        instrument_type=instrument_type,
        search=search or None,
        limit=limit,
        offset=offset,
    )


@mcp.tool()
def get_recent_alphas(limit: int = 20, offset: int = 0, status: str = "", region: str = "") -> dict:
    """List recent alphas for the authenticated account."""
    return list_recent_alphas(
        get_client(),
        limit=limit,
        offset=offset,
        status=status or None,
        region=region or None,
    )


@mcp.tool()
def get_alpha(alpha_id: str) -> dict:
    """Fetch an alpha and its check results by id."""
    return get_alpha_details(get_client(), alpha_id)


@mcp.tool()
def get_alpha_submission(alpha_id: str) -> dict:
    """Fetch submission status for an alpha by id."""
    return get_submission_status(get_client(), alpha_id)


@mcp.tool()
def create_simulation(
    expression: str,
    region: str = "USA",
    universe: str = "TOP3000",
    delay: int = 1,
    decay: int = 5,
    neutralization: str = "SUBINDUSTRY",
    truncation: float = 0.08,
    instrument_type: str = "EQUITY",
) -> dict:
    """Submit a WorldQuant simulation and return its progress URL."""
    return submit_simulation(
        get_client(),
        expression,
        region=region,
        universe=universe,
        delay=delay,
        decay=decay,
        neutralization=neutralization,
        truncation=truncation,
        instrument_type=instrument_type,
    )


@mcp.tool()
async def batch_simulate(
    ctx: Context,
    expressions: list[str],
    region: str = "USA",
    universe: str = "TOP3000",
    delay: int = 1,
    decay: int = 5,
    neutralization: str = "SUBINDUSTRY",
    truncation: float = 0.08,
    instrument_type: str = "EQUITY",
    timeout_seconds: int = DEFAULT_TOOL_TIMEOUT_SECONDS,
    sort_by: str = "fitness",
    descending: bool = True,
) -> dict:
    """Submit a batch of expressions, wait for results, and return a ranked leaderboard."""
    if not expressions:
        raise ValueError("expressions must contain at least one expression")
        
    client = get_client()
    settings = SimulationSettings(
        instrument_type=instrument_type,
        region=region,
        universe=universe,
        delay=delay,
        decay=decay,
        neutralization=neutralization,
        truncation=truncation,
    )
    submissions = []
    summaries = []
    total = len(expressions)

    for index, expression in enumerate(expressions, start=1):
        await ctx.report_progress(index - 1, total)
        await ctx.info(f"Simulating ({index}/{total}): {expression}")
        try:
            submission = await asyncio.to_thread(
                client.submit_simulation, expression=expression, settings=settings
            )
            item = {
                "index": index,
                "expression": expression,
                "progressUrl": submission.get("progress_url"),
                "statusCode": submission.get("status_code"),
            }

            progress_url = submission.get("progress_url")
            if progress_url:
                result = await asyncio.to_thread(
                    client.wait_for_simulation, progress_url, timeout_seconds=timeout_seconds
                )
                item["result"] = result
                alpha = result.get("alpha") if isinstance(result, dict) else None
                if isinstance(alpha, dict):
                    summary = _summarize_alpha(alpha)
                    summary["index"] = index
                    summary["expression"] = expression
                    summary["simulationStatus"] = result.get("status")
                    summaries.append(summary)
            submissions.append(item)
        except Exception as exc:
            submissions.append(
                {
                    "index": index,
                    "expression": expression,
                    "error": str(exc),
                }
            )

    await ctx.report_progress(total, total)
    leaderboard = _sort_summaries(summaries, sort_by=sort_by, descending=descending)
    
    return {
        "request": {
            "expressions": expressions,
            "region": region,
            "universe": universe,
        },
        "submittedCount": len(expressions),
        "completedCount": len(summaries),
        "errorCount": len([s for s in submissions if "error" in s]),
        "leaderboard": leaderboard,
        "submissions": submissions,
    }


@mcp.tool()
def summarize_alpha_batch_by_id(
    alpha_ids: list[str],
    sort_by: str = "fitness",
    descending: bool = True,
    sharpe_threshold: float | None = None,
    fitness_threshold: float | None = None,
    turnover_min: float | None = None,
    turnover_max: float | None = None,
    sub_universe_sharpe_threshold: float | None = None,
) -> dict:
    """Rank alpha ids and optionally filter them by quality thresholds."""
    return summarize_alpha_batch(
        get_client(),
        alpha_ids,
        sort_by=sort_by,
        descending=descending,
        sharpe_threshold=sharpe_threshold,
        fitness_threshold=fitness_threshold,
        turnover_min=turnover_min,
        turnover_max=turnover_max,
        sub_universe_sharpe_threshold=sub_universe_sharpe_threshold,
    )


@mcp.tool()
def mutate_alpha_expression(
    seed_expression: str,
    lookbacks: list[int] | None = None,
    wrappers: list[str] | None = None,
    decays: list[int] | None = None,
    neutralizations: list[str] | None = None,
    conditional_fields: list[str] | None = None,
    include_sign_flip: bool = True,
    max_variants: int = 20,
) -> dict:
    """Generate nearby expression variants from one seed expression."""
    return mutate_expression(
        seed_expression,
        lookbacks=lookbacks,
        wrappers=wrappers,
        decays=decays,
        neutralizations=neutralizations,
        conditional_fields=conditional_fields,
        include_sign_flip=include_sign_flip,
        max_variants=max_variants,
    )


@mcp.tool()
def map_research_hypothesis(
    hypothesis: str,
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
    instrument_type: str = "EQUITY",
    keyword_count: int = 6,
    field_limit_per_keyword: int = 5,
    template_limit: int = 10,
) -> dict:
    """Turn a text hypothesis into candidate fields, operator ideas, and expression templates."""
    return map_hypothesis_to_proxies(
        get_client(),
        get_reference_index(),
        hypothesis,
        region=region,
        delay=delay,
        universe=universe,
        instrument_type=instrument_type,
        keyword_count=keyword_count,
        field_limit_per_keyword=field_limit_per_keyword,
        template_limit=template_limit,
    )


@mcp.tool()
def ingest_research_material(
    sources: list[str],
    max_chars_per_source: int = 6000,
    keyword_count: int = 12,
) -> dict:
    """Fetch or parse external research material into mechanism and expression-family hints."""
    return ingest_research_sources(
        sources,
        max_chars_per_source=max_chars_per_source,
        keyword_count=keyword_count,
    )


@mcp.tool()
def log_alpha_experiment(
    theme: str,
    hypothesis: str,
    summary: str,
    alpha_ids: list[str] | None = None,
    mechanism_tag: str = "",
    expressions: list[str] | None = None,
    follow_ups: list[str] | None = None,
) -> dict:
    """Persist an experiment result to the machine-readable store and quant journey note."""
    return log_experiment(
        get_client(),
        get_config(),
        theme=theme,
        hypothesis=hypothesis,
        summary=summary,
        alpha_ids=alpha_ids,
        mechanism_tag=mechanism_tag or None,
        expressions=expressions,
        follow_ups=follow_ups,
    )


@mcp.tool()
def list_alpha_experiments(limit: int = 20, theme: str = "", mechanism_tag: str = "") -> dict:
    """List recent logged experiments from local experiment memory."""
    return list_logged_experiments(
        get_config(),
        limit=limit,
        theme=theme or None,
        mechanism_tag=mechanism_tag or None,
    )


@mcp.tool()
def analyze_alpha_novelty(
    expressions: list[str],
    recent_limit: int = 25,
    top_matches: int = 5,
) -> dict:
    """Compare candidate expressions against recent alphas and logged experiments."""
    return analyze_expression_novelty(
        get_client(),
        get_config(),
        expressions,
        recent_limit=recent_limit,
        top_matches=top_matches,
    )


@mcp.tool()
def validate_alpha_novelty_shadow(
    target_ids: list[str] | None = None,
    top_matches: int = 3,
) -> dict:
    """Validate AST-based novelty clustering against logged experiment alphas."""
    return validate_logged_expression_novelty_shadow(
        get_config(),
        target_ids=target_ids,
        top_matches=top_matches,
    )


@mcp.tool()
def parallel_mechanism_search(
    branches: list[dict],
    default_region: str = "USA",
    default_universe: str = "TOP3000",
    default_delay: int = 1,
    default_decay: int = 5,
    default_neutralization: str = "SUBINDUSTRY",
    default_truncation: float = 0.08,
    default_instrument_type: str = "EQUITY",
    timeout_seconds: int = DEFAULT_TOOL_TIMEOUT_SECONDS,
    sort_by: str = "fitness",
    descending: bool = True,
) -> dict:
    """Run multiple mechanism-diverse search branches and merge their leaderboards."""
    return run_parallel_hypothesis_search(
        get_client(),
        get_reference_index(),
        get_config(),
        branches,
        default_region=default_region,
        default_universe=default_universe,
        default_delay=default_delay,
        default_decay=default_decay,
        default_neutralization=default_neutralization,
        default_truncation=default_truncation,
        default_instrument_type=default_instrument_type,
        timeout_seconds=timeout_seconds,
        sort_by=sort_by,
        descending=descending,
    )


@mcp.tool()
def get_simulation(simulation_id_or_url: str) -> dict:
    """Fetch the current status payload for a simulation."""
    return get_simulation_status(get_client(), simulation_id_or_url)


@mcp.tool()
def wait_simulation(simulation_id_or_url: str, timeout_seconds: int = DEFAULT_TOOL_TIMEOUT_SECONDS) -> dict:
    """Poll a simulation until completion or timeout."""
    return wait_for_simulation(
        get_client(),
        simulation_id_or_url,
        timeout_seconds=timeout_seconds,
    )


@mcp.tool()
def submit_alpha_by_id(alpha_id: str, confirm: bool = False) -> dict:
    """Submit an alpha for review. Requires confirm=True because it is state-changing."""
    return submit_alpha(get_client(), alpha_id, confirm=confirm)


@mcp.tool()
def validate_alpha_submission_by_id(alpha_id: str) -> dict:
    """Check whether an alpha is currently ready for submission and summarize blockers."""
    return validate_alpha_submission(get_client(), alpha_id)


@mcp.resource("reference://worldquant/pdf")
def worldquant_reference_markdown() -> str:
    """Return the OCR-converted local WorldQuant reference markdown."""
    return get_reference_index().markdown


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
