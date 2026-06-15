"""Alpha ideation, batch simulation, novelty, and experiment-memory helpers."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

import httpx

from ..client import WorldQuantClient
from ..config import WorldQuantConfig
from ..expression_ast import ast_similarity, describe_expression, try_parse_expression
from ..models import SimulationSettings
from ..reference.index import ReferenceIndex


TOKEN_PATTERN = re.compile(r"[a-z][a-z0-9_]{1,}")
COMMON_LOOKBACKS = (5, 10, 20, 21, 30, 42, 63, 84, 120, 126, 180, 252, 365)
HTML_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HTML_SCRIPT_STYLE_PATTERN = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "alpha",
    "among",
    "an",
    "and",
    "are",
    "around",
    "because",
    "been",
    "before",
    "being",
    "between",
    "brain",
    "can",
    "could",
    "data",
    "from",
    "have",
    "idea",
    "into",
    "latest",
    "likely",
    "many",
    "more",
    "most",
    "need",
    "other",
    "paper",
    "papers",
    "recent",
    "research",
    "should",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "these",
    "they",
    "this",
    "through",
    "using",
    "very",
    "what",
    "when",
    "which",
    "with",
    "worldquant",
    "would",
}
MECHANISM_KEYWORDS = {
    "working_capital": {"inventory", "receivable", "receivables", "sales", "cogs", "cash", "conversion"},
    "analyst_expectations": {"analyst", "analysts", "estimate", "estimates", "dispersion", "revision", "recommendation", "consensus", "surprise"},
    "labor_intensity": {"employee", "employees", "labor", "wage", "headcount", "salary", "staff"},
    "quality_profitability": {"accrual", "accruals", "profitability", "quality", "cashflow", "cash", "margin", "roic", "roe", "roa"},
    "investment_efficiency": {"capex", "investment", "assets", "turnover", "efficiency", "invested", "capital"},
    "microstructure": {"volume", "turnover", "liquidity", "illiquidity", "range", "vwap", "spread", "intraday", "volatility"},
    "news_sentiment": {"news", "sentiment", "buzz", "headline", "relevance", "coverage", "nws", "scl"},
    "cross_asset_relative": {"sector", "etf", "relative", "spread", "constituent", "peer", "industry", "benchmark"},
    "model_features": {"model", "mdl", "mdl177", "score", "residual", "forecast", "prediction", "alpha"},
    "options_implied": {"option", "options", "implied", "skew", "term", "structure", "breakeven", "call", "put", "volatility"},
}
MECHANISM_TAG_KEYWORDS = {
    "options_iv_momentum": {"option", "options", "implied", "volatility", "skew", "term", "put", "call", "iv", "breakeven"},
    "working_capital_stress": {"working", "capital", "receivable", "receivables", "inventory", "sales", "cogs", "cashflow_op", "income"},
    "microstructure_institutional_flow": {"microstructure", "volume", "adv", "vwap", "turnover", "liquidity", "illiquidity", "spread", "range", "flow"},
    "sentiment_attention": {"sentiment", "attention", "news", "headline", "buzz", "coverage", "focus", "social", "snt1"},
    "model_feature_divergence": {"model", "mdl", "mdl177", "residual", "forecast", "prediction", "divergence", "relativevaluefactor"},
    "analyst_expectations_disagreement": {"analyst", "analysts", "estimate", "estimates", "eps", "dispersion", "recommendation", "consensus", "revision"},
    "labor_cost_stickiness": {"employee", "employees", "labor", "headcount", "salary", "wage", "staff"},
    "quality_profitability_composite": {"quality", "profitability", "accrual", "accruals", "cashflow", "roic", "ocfroi", "noato", "opmb", "fcfroi", "ttmaccu", "margin"},
    "research_infrastructure": {"tooling", "novelty", "parser", "similarity", "ast", "backfill", "mechanism_tag", "journal"},
}
MICROSTRUCTURE_ALLOW_TOKENS = {
    "adv",
    "close",
    "dollar",
    "high",
    "illiquidity",
    "liquidity",
    "low",
    "open",
    "price",
    "range",
    "return",
    "spread",
    "turnover",
    "value",
    "volume",
    "volatility",
    "vwap",
}
MICROSTRUCTURE_DENY_TOKENS = {
    "country",
    "currency",
    "exchange",
    "gics",
    "group",
    "industry",
    "isin",
    "name",
    "region",
    "sector",
    "sedol",
    "subindustry",
    "symbol",
    "ticker",
}


def batch_simulate_expressions(
    client: WorldQuantClient,
    expressions: list[str],
    *,
    region: str = "USA",
    universe: str = "TOP3000",
    delay: int = 1,
    decay: int = 5,
    neutralization: str = "SUBINDUSTRY",
    truncation: float = 0.08,
    instrument_type: str = "EQUITY",
    timeout_seconds: int | None = None,
    sort_by: str = "fitness",
    descending: bool = True,
) -> dict[str, Any]:
    if not expressions:
        raise ValueError("expressions must contain at least one expression")

    settings = SimulationSettings(
        instrument_type=instrument_type,
        region=region,
        universe=universe,
        delay=delay,
        decay=decay,
        neutralization=neutralization,
        truncation=truncation,
    )
    submissions: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for index, expression in enumerate(expressions, start=1):
        try:
            submission = client.submit_simulation(expression=expression, settings=settings)
            item: dict[str, Any] = {
                "index": index,
                "expression": expression,
                "progressUrl": submission.get("progress_url"),
                "statusCode": submission.get("status_code"),
            }

            progress_url = submission.get("progress_url")
            if progress_url:
                result = client.wait_for_simulation(progress_url, timeout_seconds=timeout_seconds)
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

    leaderboard = _sort_summaries(summaries, sort_by=sort_by, descending=descending)
    return {
        "request": {
            "expressionCount": len(expressions),
            "instrumentType": instrument_type,
            "region": region,
            "universe": universe,
            "delay": delay,
            "decay": decay,
            "neutralization": neutralization,
            "truncation": truncation,
            "timeoutSeconds": timeout_seconds,
            "sortBy": sort_by,
            "descending": descending,
        },
        "submittedCount": sum(1 for item in submissions if "error" not in item),
        "completedCount": len(summaries),
        "errorCount": sum(1 for item in submissions if "error" in item),
        "leaderboard": leaderboard,
        "submissions": submissions,
    }


def summarize_alpha_batch(
    client: WorldQuantClient,
    alpha_ids: list[str],
    *,
    sort_by: str = "fitness",
    descending: bool = True,
    sharpe_threshold: float | None = None,
    fitness_threshold: float | None = None,
    turnover_min: float | None = None,
    turnover_max: float | None = None,
    sub_universe_sharpe_threshold: float | None = None,
) -> dict[str, Any]:
    if not alpha_ids:
        raise ValueError("alpha_ids must contain at least one alpha id")

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for alpha_id in alpha_ids:
        alpha = client.get_alpha(alpha_id)
        summary = _summarize_alpha(alpha)
        reasons = _filter_reasons(
            summary,
            sharpe_threshold=sharpe_threshold,
            fitness_threshold=fitness_threshold,
            turnover_min=turnover_min,
            turnover_max=turnover_max,
            sub_universe_sharpe_threshold=sub_universe_sharpe_threshold,
        )
        if reasons:
            rejected.append({"alphaId": alpha_id, "reasons": reasons, "summary": summary})
        else:
            accepted.append(summary)

    return {
        "request": {
            "alphaCount": len(alpha_ids),
            "sortBy": sort_by,
            "descending": descending,
            "sharpeThreshold": sharpe_threshold,
            "fitnessThreshold": fitness_threshold,
            "turnoverMin": turnover_min,
            "turnoverMax": turnover_max,
            "subUniverseSharpeThreshold": sub_universe_sharpe_threshold,
        },
        "accepted": _sort_summaries(accepted, sort_by=sort_by, descending=descending),
        "rejected": rejected,
    }


def mutate_expression(
    seed_expression: str,
    *,
    lookbacks: list[int] | None = None,
    wrappers: list[str] | None = None,
    decays: list[int] | None = None,
    neutralizations: list[str] | None = None,
    conditional_fields: list[str] | None = None,
    include_sign_flip: bool = True,
    max_variants: int = 20,
) -> dict[str, Any]:
    if not seed_expression.strip():
        raise ValueError("seed_expression must not be empty")

    lookbacks = lookbacks or [20, 63, 126, 252]
    wrappers = wrappers or ["rank", "zscore", "normalize"]
    decays = decays or [3, 5, 8, 10]
    neutralizations = neutralizations or ["SUBINDUSTRY", "INDUSTRY", "SECTOR"]
    conditional_fields = conditional_fields or []

    variants: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_variant(expression: str, rationale: str) -> None:
        normalized = _normalize_expression(expression)
        if normalized in seen or len(variants) >= max_variants:
            return
        seen.add(normalized)
        variant_index = len(variants)
        variants.append(
            {
                "expression": expression,
                "rationale": rationale,
                "suggestedSettings": {
                    "decay": decays[variant_index % len(decays)],
                    "neutralization": neutralizations[variant_index % len(neutralizations)],
                },
            }
        )

    add_variant(seed_expression, "seed expression")

    for lookback in lookbacks:
        replaced = _replace_common_lookbacks(seed_expression, lookback)
        if replaced != seed_expression:
            add_variant(replaced, f"replace common lookbacks with {lookback}")

    for wrapper in wrappers:
        wrapped = _wrap_expression(seed_expression, wrapper)
        if wrapped:
            add_variant(wrapped, f"apply {wrapper} wrapper")

    for expression, rationale in _trade_when_variants(seed_expression, conditional_fields):
        add_variant(expression, rationale)

    for expression, rationale in _payload_blend_variants(seed_expression, conditional_fields):
        add_variant(expression, rationale)

    if include_sign_flip:
        add_variant(f"reverse({seed_expression})", "flip signal direction")

    for field in conditional_fields:
        conditioned = (
            "trade_when(" 
            f"greater(ts_backfill({field}, 20), ts_delay(ts_backfill({field}, 20), 20)), "
            f"{seed_expression}, -1)"
        )
        add_variant(conditioned, f"only trade when {field} is improving")

    if "rank(" not in seed_expression:
        add_variant(f"rank({seed_expression})", "cross-sectional rank normalization")
    if "group_neutralize(" not in seed_expression:
        add_variant(f"group_neutralize({seed_expression}, subindustry)", "explicit group neutralization")

    return {
        "seedExpression": seed_expression,
        "variantCount": len(variants),
        "variants": variants,
    }


def map_hypothesis_to_proxies(
    client: WorldQuantClient,
    index: ReferenceIndex,
    hypothesis: str,
    *,
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
    instrument_type: str = "EQUITY",
    keyword_count: int = 6,
    field_limit_per_keyword: int = 5,
    template_limit: int = 10,
) -> dict[str, Any]:
    if not hypothesis.strip():
        raise ValueError("hypothesis must not be empty")

    keywords = _extract_keywords(hypothesis, keyword_count)
    candidate_fields: list[dict[str, Any]] = []
    seen_fields: set[str] = set()
    reference_matches: list[dict[str, Any]] = []
    operator_counter: Counter[str] = Counter()

    for keyword in keywords:
        response = client.list_data_fields(
            region=region,
            delay=delay,
            universe=universe,
            instrument_type=instrument_type,
            search=keyword,
            limit=field_limit_per_keyword,
        )
        results = _coerce_data_field_results(response)
        for result in results:
            field_id = result.get("id")
            if not isinstance(field_id, str) or field_id in seen_fields:
                continue
            seen_fields.add(field_id)
            candidate_fields.append(
                {
                    "matchedKeyword": keyword,
                    "id": field_id,
                    "description": result.get("description"),
                    "dataset": (result.get("dataset") or {}).get("id"),
                    "category": (result.get("category") or {}).get("id"),
                    "coverage": result.get("coverage"),
                    "userCount": result.get("userCount"),
                }
            )

        matches = index.search(keyword, limit=3)
        reference_matches.extend(matches)
        for match in matches:
            operator_counter.update(match.get("operators") or [])

    mechanism_guesses = _guess_mechanisms(" ".join(keywords))
    candidate_fields = _filter_candidate_fields(candidate_fields, mechanism_guesses)
    templates = _build_expression_templates(
        keywords=keywords,
        candidate_fields=candidate_fields,
        mechanism_guesses=mechanism_guesses,
        template_limit=template_limit,
    )

    default_operators = ["rank", "zscore", "reverse", "ts_delta", "ts_zscore", "group_rank"]
    operator_suggestions = list(dict.fromkeys(default_operators + [name for name, _ in operator_counter.most_common(10)]))

    return {
        "hypothesis": hypothesis,
        "keywords": keywords,
        "mechanismGuesses": mechanism_guesses,
        "candidateFields": candidate_fields,
        "operatorSuggestions": operator_suggestions,
        "referenceMatches": reference_matches[:10],
        "expressionTemplates": templates,
    }


def run_parallel_hypothesis_search(
    client: WorldQuantClient,
    index: ReferenceIndex,
    config: WorldQuantConfig,
    branches: list[dict[str, Any]],
    *,
    default_region: str = "USA",
    default_universe: str = "TOP3000",
    default_delay: int = 1,
    default_decay: int = 5,
    default_neutralization: str = "SUBINDUSTRY",
    default_truncation: float = 0.08,
    default_instrument_type: str = "EQUITY",
    timeout_seconds: int | None = None,
    sort_by: str = "fitness",
    descending: bool = True,
) -> dict[str, Any]:
    if not branches:
        raise ValueError("branches must contain at least one hypothesis branch")

    branch_results: list[dict[str, Any]] = []
    merged_leaderboard: list[dict[str, Any]] = []

    for branch_index, branch in enumerate(branches, start=1):
        hypothesis = str(branch.get("hypothesis") or "").strip()
        if not hypothesis:
            raise ValueError(f"branch {branch_index} is missing a hypothesis")

        region = str(branch.get("region") or default_region)
        universe = str(branch.get("universe") or default_universe)
        delay = int(branch.get("delay") or default_delay)
        decay = int(branch.get("decay") or default_decay)
        neutralization = str(branch.get("neutralization") or default_neutralization)
        truncation = float(branch.get("truncation") or default_truncation)
        instrument_type = str(branch.get("instrument_type") or default_instrument_type)
        mutation_budget = max(1, int(branch.get("mutation_budget") or 8))
        batch_sim_quota = max(1, int(branch.get("batch_sim_quota") or 6))
        template_limit = max(1, int(branch.get("template_limit") or 3))
        keyword_count = max(1, int(branch.get("keyword_count") or 6))
        field_limit_per_keyword = max(1, int(branch.get("field_limit_per_keyword") or 5))

        mapped = map_hypothesis_to_proxies(
            client,
            index,
            hypothesis,
            region=region,
            delay=delay,
            universe=universe,
            instrument_type=instrument_type,
            keyword_count=keyword_count,
            field_limit_per_keyword=field_limit_per_keyword,
            template_limit=template_limit,
        )

        candidate_fields = mapped.get("candidateFields") or []
        conditional_fields = [field.get("id") for field in candidate_fields if isinstance(field, dict) and field.get("id")]
        template_items = (mapped.get("expressionTemplates") or [])[:template_limit]
        seed_expressions = [str(item.get("expression")) for item in template_items if isinstance(item, dict) and item.get("expression")]

        manual_seed = branch.get("seed_expression")
        if isinstance(manual_seed, str) and manual_seed.strip():
            seed_expressions.insert(0, manual_seed.strip())

        if not seed_expressions:
            seed_expressions = ["rank(returns)"]

        branch_expressions: list[str] = []
        seen_expressions: set[str] = set()

        def add_expression(expression: str) -> None:
            normalized = _normalize_expression(expression)
            if normalized in seen_expressions:
                return
            seen_expressions.add(normalized)
            branch_expressions.append(expression)

        for seed_expression in seed_expressions:
            add_expression(seed_expression)
            mutation_result = mutate_expression(
                seed_expression,
                conditional_fields=conditional_fields[:3],
                include_sign_flip=False,
                max_variants=mutation_budget,
            )
            for variant in mutation_result.get("variants") or []:
                expression = variant.get("expression") if isinstance(variant, dict) else None
                if isinstance(expression, str):
                    add_expression(expression)

        novelty = analyze_expression_novelty(client, config, branch_expressions, recent_limit=25, top_matches=3)
        novelty_map = {
            result["expression"]: result
            for result in novelty.get("results") or []
            if isinstance(result, dict) and isinstance(result.get("expression"), str)
        }

        ranked_candidates = sorted(
            branch_expressions,
            key=lambda expression: float((novelty_map.get(expression) or {}).get("noveltyScore", 0.0)),
            reverse=True,
        )
        selected_expressions = ranked_candidates[:batch_sim_quota]

        simulation = batch_simulate_expressions(
            client,
            selected_expressions,
            region=region,
            universe=universe,
            delay=delay,
            decay=decay,
            neutralization=neutralization,
            truncation=truncation,
            instrument_type=instrument_type,
            timeout_seconds=timeout_seconds,
            sort_by=sort_by,
            descending=descending,
        )

        branch_leaderboard = simulation.get("leaderboard") or []
        for item in branch_leaderboard:
            if isinstance(item, dict):
                merged_item = dict(item)
                merged_item["branchIndex"] = branch_index
                merged_item["hypothesis"] = hypothesis
                merged_leaderboard.append(merged_item)

        branch_results.append(
            {
                "branchIndex": branch_index,
                "hypothesis": hypothesis,
                "request": {
                    "region": region,
                    "universe": universe,
                    "delay": delay,
                    "decay": decay,
                    "neutralization": neutralization,
                    "truncation": truncation,
                    "instrumentType": instrument_type,
                    "mutationBudget": mutation_budget,
                    "batchSimQuota": batch_sim_quota,
                },
                "mappedHypothesis": mapped,
                "candidateExpressionCount": len(branch_expressions),
                "selectedExpressions": selected_expressions,
                "novelty": novelty,
                "simulation": simulation,
            }
        )

    merged_leaderboard = _sort_summaries(merged_leaderboard, sort_by=sort_by, descending=descending)
    return {
        "request": {
            "branchCount": len(branches),
            "sortBy": sort_by,
            "descending": descending,
            "timeoutSeconds": timeout_seconds,
        },
        "branches": branch_results,
        "mergedLeaderboard": merged_leaderboard,
    }


def ingest_research_sources(
    sources: list[str],
    *,
    max_chars_per_source: int = 6000,
    keyword_count: int = 12,
) -> dict[str, Any]:
    if not sources:
        raise ValueError("sources must contain at least one URL or text snippet")

    documents: list[dict[str, Any]] = []
    aggregate_keywords: Counter[str] = Counter()

    for source in sources:
        title = None
        url = source if _looks_like_url(source) else None
        raw_text = source
        if url:
            with httpx.Client(follow_redirects=True, timeout=20.0) as http:
                response = http.get(url)
                response.raise_for_status()
                title = _extract_title(response.text) or title
                raw_text = _coerce_web_text(response.text, max_chars=max_chars_per_source)
        else:
            raw_text = _truncate_text(source, max_chars_per_source)

        keywords = _extract_keywords(raw_text, keyword_count)
        aggregate_keywords.update(keywords)
        mechanisms = _guess_mechanisms(raw_text)
        sentences = _extract_notable_sentences(raw_text, limit=5)
        documents.append(
            {
                "source": source,
                "url": url,
                "title": title,
                "keywords": keywords,
                "mechanismGuesses": mechanisms,
                "notableSentences": sentences,
                "candidateExpressionFamilies": _mechanism_expression_families(mechanisms),
            }
        )

    return {
        "count": len(documents),
        "aggregateKeywords": [keyword for keyword, _ in aggregate_keywords.most_common(keyword_count)],
        "documents": documents,
    }


def log_experiment(
    client: WorldQuantClient,
    config: WorldQuantConfig,
    *,
    theme: str,
    hypothesis: str,
    summary: str,
    alpha_ids: list[str] | None = None,
    mechanism_tag: str | None = None,
    mechanism_tags: list[str] | None = None,
    expressions: list[str] | None = None,
    follow_ups: list[str] | None = None,
) -> dict[str, Any]:
    mechanism_tags = mechanism_tags or []
    alpha_ids = alpha_ids or []
    expressions = expressions or []
    follow_ups = follow_ups or []

    alpha_summaries = [_summarize_alpha(client.get_alpha(alpha_id)) for alpha_id in alpha_ids]
    resolved_mechanism_tag, resolved_mechanism_tags = _resolve_mechanism_fields(
        mechanism_tag=mechanism_tag,
        mechanism_tags=mechanism_tags,
        theme=theme,
        hypothesis=hypothesis,
        summary=summary,
        expressions=expressions,
        alpha_summaries=alpha_summaries,
    )
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    entry = {
        "timestamp": timestamp,
        "theme": theme,
        "mechanism_tag": resolved_mechanism_tag,
        "mechanism_tags": resolved_mechanism_tags,
        "hypothesis": hypothesis,
        "summary": summary,
        "expressions": expressions,
        "alphas": alpha_summaries,
        "followUps": follow_ups,
    }

    entries = _load_experiment_entries(config.experiment_memory_path)
    entries.append(entry)
    _write_experiment_entries(config.experiment_memory_path, entries)
    _append_to_quant_journey(config.research_journal_path, entry)

    return {
        "saved": True,
        "path": str(config.experiment_memory_path),
        "journalPath": str(config.research_journal_path),
        "entry": entry,
    }


def list_logged_experiments(
    config: WorldQuantConfig,
    *,
    limit: int = 20,
    theme: str | None = None,
    mechanism_tag: str | None = None,
) -> dict[str, Any]:
    entries = _load_experiment_entries(config.experiment_memory_path)
    if theme:
        entries = [entry for entry in entries if str(entry.get("theme", "")).lower() == theme.lower()]
    if mechanism_tag:
        entries = [entry for entry in entries if _entry_matches_mechanism_tag(entry, mechanism_tag)]
    entries = [_attach_entry_interpretations(entry) for entry in entries]
    entries = list(reversed(entries[-limit:]))
    return {
        "count": len(entries),
        "entries": entries,
    }


def analyze_expression_novelty(
    client: WorldQuantClient,
    config: WorldQuantConfig,
    expressions: list[str],
    *,
    recent_limit: int = 25,
    top_matches: int = 5,
) -> dict[str, Any]:
    if not expressions:
        raise ValueError("expressions must contain at least one expression")

    comparators = _recent_expression_comparators(client, recent_limit)
    comparators.extend(_logged_expression_comparators(config))
    parsed_comparators = [_attach_ast_metadata(comparator) for comparator in comparators]
    crowded_tokens = Counter(token for comparator in comparators for token in set(_tokenize(comparator["expression"])))
    novelty_results: list[dict[str, Any]] = []

    for expression in expressions:
        parsed_expression, parse_error = try_parse_expression(expression)
        interpretation = describe_expression(expression, parsed_expression, parse_error)
        matches = []
        for comparator in parsed_comparators:
            similarity = _expression_similarity(expression, comparator["expression"])
            ast_score = _expression_ast_similarity(parsed_expression, comparator.get("_ast"))
            matches.append(
                {
                    "source": comparator["source"],
                    "id": comparator.get("id"),
                    "theme": comparator.get("theme"),
                    "mechanismTag": comparator.get("mechanismTag"),
                    "mechanismTags": comparator.get("mechanismTags") or [],
                    "status": comparator.get("status"),
                    "stage": comparator.get("stage"),
                    "similarity": round(similarity, 4),
                    "legacySimilarity": round(similarity, 4),
                    "astSimilarity": round(ast_score, 4),
                    "avoidancePriority": _comparator_avoidance_priority(comparator),
                    "astComparable": parsed_expression is not None and comparator.get("_ast") is not None,
                    "interpretation": comparator.get("_interpretation"),
                    "expression": comparator["expression"],
                }
            )
        matches.sort(
            key=lambda item: (item["similarity"], item["avoidancePriority"], item["astSimilarity"]),
            reverse=True,
        )
        top = matches[:top_matches]
        ast_top = sorted(
            matches,
            key=lambda item: (item["astSimilarity"], item["avoidancePriority"], item["similarity"]),
            reverse=True,
        )[:top_matches]
        best_similarity = top[0]["similarity"] if top else 0.0
        best_ast_similarity = ast_top[0]["astSimilarity"] if ast_top else 0.0
        novelty_results.append(
            {
                "expression": expression,
                "interpretation": interpretation,
                "noveltyScore": round(1.0 - best_similarity, 4),
                "astNoveltyScore": round(1.0 - best_ast_similarity, 4),
                "astParsed": parsed_expression is not None,
                "astParseError": parse_error,
                "topMatches": top,
                "astTopMatches": ast_top,
                "crowdedTokens": [token for token, _ in crowded_tokens.most_common(10) if token in _tokenize(expression)],
            }
        )

    return {
        "request": {
            "expressionCount": len(expressions),
            "recentLimit": recent_limit,
            "topMatches": top_matches,
        },
        "shadowMode": {
            "astSimilarityEnabled": True,
            "rankingMetric": "legacySimilarity",
            "shadowMetric": "astSimilarity",
        },
        "comparatorCount": len(comparators),
        "results": novelty_results,
    }


def validate_logged_expression_novelty_shadow(
    config: WorldQuantConfig,
    *,
    target_ids: list[str] | None = None,
    top_matches: int = 3,
) -> dict[str, Any]:
    comparators = _deduplicate_expression_comparators(_logged_expression_comparators(config))
    alpha_targets = [comparator for comparator in comparators if comparator["source"] == "experiment-alpha"]
    if target_ids:
        wanted = {target_id.lower() for target_id in target_ids}
        alpha_targets = [
            comparator
            for comparator in alpha_targets
            if any(str(linked_id).lower() in wanted for linked_id in comparator.get("linkedIds") or [])
        ]

    if not alpha_targets:
        raise ValueError("No logged experiment alphas matched the requested target ids")

    parsed_comparators = [_attach_ast_metadata(comparator) for comparator in comparators]
    parse_failures = [comparator for comparator in parsed_comparators if comparator.get("_ast") is None]
    results = []
    for target in alpha_targets:
        target_with_ast = _attach_ast_metadata(target)
        matches = []
        for comparator in parsed_comparators:
            if _normalize_expression(comparator["expression"]) == _normalize_expression(target["expression"]):
                continue
            legacy_score = _expression_similarity(target["expression"], comparator["expression"])
            ast_score = _expression_ast_similarity(target_with_ast.get("_ast"), comparator.get("_ast"))
            matches.append(
                {
                    "source": comparator["source"],
                    "id": comparator.get("id"),
                    "linkedIds": comparator.get("linkedIds") or [],
                    "theme": comparator.get("theme"),
                    "mechanismTag": comparator.get("mechanismTag"),
                    "mechanismTags": comparator.get("mechanismTags") or [],
                    "interpretation": comparator.get("_interpretation"),
                    "expression": comparator["expression"],
                    "legacySimilarity": round(legacy_score, 4),
                    "astSimilarity": round(ast_score, 4),
                }
            )
        results.append(
            {
                "id": target.get("id"),
                "linkedIds": target.get("linkedIds") or [],
                "theme": target.get("theme"),
                "interpretation": target_with_ast.get("_interpretation"),
                "expression": target["expression"],
                "astParsed": target_with_ast.get("_ast") is not None,
                "legacyTopMatches": sorted(matches, key=lambda item: item["legacySimilarity"], reverse=True)[:top_matches],
                "astTopMatches": sorted(matches, key=lambda item: item["astSimilarity"], reverse=True)[:top_matches],
            }
        )

    return {
        "comparatorCount": len(comparators),
        "targetCount": len(results),
        "parseSummary": {
            "parsed": len(parsed_comparators) - len(parse_failures),
            "failed": len(parse_failures),
        },
        "results": results,
    }


def _summarize_alpha(alpha: dict[str, Any]) -> dict[str, Any]:
    in_sample = alpha.get("is") or {}
    checks = in_sample.get("checks") or []
    blocking_checks = [check for check in checks if check.get("result") == "FAIL"]
    pending_checks = [check for check in checks if check.get("result") == "PENDING"]
    return {
        "alphaId": alpha.get("id"),
        "status": alpha.get("status"),
        "stage": alpha.get("stage"),
        "grade": alpha.get("grade"),
        "expression": ((alpha.get("regular") or {}).get("code")),
        "metrics": {
            "sharpe": in_sample.get("sharpe"),
            "fitness": in_sample.get("fitness"),
            "returns": in_sample.get("returns"),
            "turnover": in_sample.get("turnover"),
            "drawdown": in_sample.get("drawdown"),
            "margin": in_sample.get("margin"),
            "subUniverseSharpe": _sub_universe_sharpe(checks),
        },
        "blockingChecks": blocking_checks,
        "pendingChecks": pending_checks,
        "submittable": not blocking_checks and not pending_checks,
    }


def _sub_universe_sharpe(checks: list[dict[str, Any]]) -> float | None:
    for check in checks:
        if check.get("name") == "LOW_SUB_UNIVERSE_SHARPE":
            value = check.get("value")
            return float(value) if isinstance(value, (int, float)) else None
    return None


def _filter_reasons(
    summary: dict[str, Any],
    *,
    sharpe_threshold: float | None,
    fitness_threshold: float | None,
    turnover_min: float | None,
    turnover_max: float | None,
    sub_universe_sharpe_threshold: float | None,
) -> list[str]:
    metrics = summary.get("metrics") or {}
    reasons: list[str] = []

    sharpe = metrics.get("sharpe")
    if sharpe_threshold is not None and isinstance(sharpe, (int, float)) and sharpe < sharpe_threshold:
        reasons.append(f"sharpe {sharpe} < {sharpe_threshold}")

    fitness = metrics.get("fitness")
    if fitness_threshold is not None and isinstance(fitness, (int, float)) and fitness < fitness_threshold:
        reasons.append(f"fitness {fitness} < {fitness_threshold}")

    turnover = metrics.get("turnover")
    if turnover_min is not None and isinstance(turnover, (int, float)) and turnover < turnover_min:
        reasons.append(f"turnover {turnover} < {turnover_min}")
    if turnover_max is not None and isinstance(turnover, (int, float)) and turnover > turnover_max:
        reasons.append(f"turnover {turnover} > {turnover_max}")

    sub_universe = metrics.get("subUniverseSharpe")
    if (
        sub_universe_sharpe_threshold is not None
        and isinstance(sub_universe, (int, float))
        and sub_universe < sub_universe_sharpe_threshold
    ):
        reasons.append(f"sub-universe sharpe {sub_universe} < {sub_universe_sharpe_threshold}")

    return reasons


def _sort_summaries(summaries: list[dict[str, Any]], *, sort_by: str, descending: bool) -> list[dict[str, Any]]:
    def key(summary: dict[str, Any]) -> float:
        metrics = summary.get("metrics") or {}
        value = metrics.get(sort_by)
        if isinstance(value, (int, float)):
            return float(value)
        return float("-inf")

    return sorted(summaries, key=key, reverse=descending)


def _replace_common_lookbacks(expression: str, target: int) -> str:
    result = expression
    for lookback in COMMON_LOOKBACKS:
        if lookback == target:
            continue
        result = re.sub(rf"(?<![A-Za-z0-9_]){lookback}(?![A-Za-z0-9_])", str(target), result)
    return result


def _wrap_expression(expression: str, wrapper: str) -> str | None:
    wrapper = wrapper.strip().lower()
    if not wrapper:
        return None
    if wrapper == "normalize":
        return f"normalize({expression}, useStd=true)"
    return f"{wrapper}({expression})"


def _trade_when_variants(seed_expression: str, conditional_fields: list[str]) -> list[tuple[str, str]]:
    variants: list[tuple[str, str]] = []

    market_stability_condition = "less(ts_std_dev(returns, 20), 0.03)"
    market_stress_exit = "greater(ts_std_dev(returns, 20), 0.04)"
    turnover_exit = "less(inventory_turnover, ts_mean(inventory_turnover, 20))"

    trade_parts = _parse_top_level_trade_when(seed_expression)
    if trade_parts is None:
        variants.append(
            (
                f"trade_when({market_stability_condition}, {seed_expression}, -1)",
                "only trade when short-term market volatility is stable",
            )
        )
        variants.append(
            (
                f"trade_when({market_stability_condition}, {seed_expression}, {market_stress_exit})",
                "enter in stable volatility and exit on market stress",
            )
        )
        return variants

    entry_condition, alpha_expression, exit_condition = trade_parts
    variants.append(
        (
            f"trade_when(and({entry_condition}, {market_stability_condition}), {alpha_expression}, {exit_condition})",
            "require both the original entry condition and stable market volatility",
        )
    )
    variants.append(
        (
            f"trade_when({entry_condition}, {alpha_expression}, {market_stress_exit})",
            "keep original entry but exit on market stress",
        )
    )

    if conditional_fields:
        for field in conditional_fields[:2]:
            field_condition = f"greater(ts_backfill({field}, 20), ts_delay(ts_backfill({field}, 20), 20))"
            if _normalize_expression(field_condition) == _normalize_expression(entry_condition):
                continue
            variants.append(
                (
                    f"trade_when(and({entry_condition}, {field_condition}), {alpha_expression}, {exit_condition})",
                    f"require both the original entry condition and improving {field}",
                )
            )

    if "inventory_turnover" in seed_expression or conditional_fields:
        variants.append(
            (
                f"trade_when({entry_condition}, {alpha_expression}, {turnover_exit})",
                "keep original entry but exit when inventory turnover weakens",
            )
        )

    return variants


def _payload_blend_variants(seed_expression: str, conditional_fields: list[str]) -> list[tuple[str, str]]:
    trade_parts = _parse_top_level_trade_when(seed_expression)
    if trade_parts is None:
        entry_condition = None
        alpha_expression = seed_expression
        exit_condition = None
    else:
        entry_condition, alpha_expression, exit_condition = trade_parts

    variants: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add_payload_variant(payload_expression: str, rationale: str) -> None:
        expression = _compose_trade_when(entry_condition, payload_expression, exit_condition)
        normalized = _normalize_expression(expression)
        if normalized in seen:
            return
        seen.add(normalized)
        variants.append((expression, rationale))

    add_payload_variant(
        f"rank(add({alpha_expression}, reverse(zscore(ts_std_dev(returns, 20)))))",
        "blend payload with a low-volatility preference to reduce concentration",
    )
    add_payload_variant(
        f"normalize(add({alpha_expression}, reverse(zscore(ts_std_dev(returns, 20)))) , useStd=true)",
        "normalize a low-volatility blended payload to damp outliers",
    )

    for field in _candidate_blend_fields(seed_expression, conditional_fields):
        field_level = f"zscore(ts_backfill({field}, 252))"
        field_trend = f"zscore(ts_delta(ts_backfill({field}, 252), 63))"
        add_payload_variant(
            f"rank(add({alpha_expression}, {field_level}))",
            f"blend payload with {field} level information to broaden the cross-section",
        )
        add_payload_variant(
            f"rank(add({alpha_expression}, {field_trend}))",
            f"blend payload with {field} trend information to smooth concentration",
        )

    return variants


def _candidate_blend_fields(seed_expression: str, conditional_fields: list[str]) -> list[str]:
    candidates: list[str] = []
    for field in [*conditional_fields, "inventory_turnover", "sales", "cashflow_op"]:
        if field not in candidates and field in seed_expression or field in conditional_fields:
            candidates.append(field)
    return candidates[:2]


def _compose_trade_when(
    entry_condition: str | None,
    alpha_expression: str,
    exit_condition: str | None,
) -> str:
    if entry_condition is None or exit_condition is None:
        return alpha_expression
    return f"trade_when({entry_condition}, {alpha_expression}, {exit_condition})"


def _parse_top_level_trade_when(expression: str) -> tuple[str, str, str] | None:
    stripped = expression.strip()
    if not stripped.startswith("trade_when(") or not stripped.endswith(")"):
        return None

    inner = stripped[len("trade_when(") : -1]
    parts = _split_top_level_args(inner)
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def _split_top_level_args(value: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0

    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1

    parts.append(value[start:].strip())
    return parts


def _extract_keywords(text: str, limit: int) -> list[str]:
    counter: Counter[str] = Counter()
    for token in _tokenize(text):
        if token in STOPWORDS or token.isdigit():
            continue
        counter[token] += 1
    return [token for token, _ in counter.most_common(limit)]


def _filter_candidate_fields(candidate_fields: list[dict[str, Any]], mechanism_guesses: list[str]) -> list[dict[str, Any]]:
    if "microstructure" not in mechanism_guesses:
        return candidate_fields

    filtered: list[dict[str, Any]] = []
    for field in candidate_fields:
        haystack = " ".join(
            str(value).lower()
            for value in (field.get("id"), field.get("description"), field.get("category"), field.get("dataset"))
            if value
        )
        if any(token in haystack for token in MICROSTRUCTURE_DENY_TOKENS):
            continue
        if any(token in haystack for token in MICROSTRUCTURE_ALLOW_TOKENS):
            filtered.append(field)

    return filtered or candidate_fields


def _build_expression_templates(
    *,
    keywords: list[str],
    candidate_fields: list[dict[str, Any]],
    mechanism_guesses: list[str],
    template_limit: int,
) -> list[dict[str, str]]:
    field_ids = [field["id"] for field in candidate_fields if field.get("id")]
    templates: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_template(expression: str, rationale: str) -> None:
        normalized = _normalize_expression(expression)
        if normalized in seen or len(templates) >= template_limit:
            return
        seen.add(normalized)
        templates.append({"expression": expression, "rationale": rationale})

    if {"working_capital"} & set(mechanism_guesses) and len(field_ids) >= 2:
        numerator = field_ids[0]
        denominator = field_ids[1]
        add_template(
            f"rank(reverse(ts_delta(divide(ts_backfill({numerator},252), add(abs(ts_backfill({denominator},252)),1)),252)))",
            "working-capital deterioration or efficiency reversal",
        )

    if {"analyst_expectations"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(add(ts_zscore(ts_delta(ts_backfill({field_ids[0]},120),20),120), reverse(ts_zscore(ts_backfill({field_ids[1]},120),120))))",
            "estimate momentum with lower disagreement",
        )

    if {"labor_intensity"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(reverse(ts_delta(divide(ts_backfill({field_ids[0]},252), add(abs(ts_backfill({field_ids[1]},252)),1)),252)))",
            "labor intensity deterioration",
        )

    if {"quality_profitability", "investment_efficiency"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(add(zscore({field_ids[0]}), reverse(zscore({field_ids[1]}))))",
            "quality spread between supportive and adverse fundamentals",
        )

    if {"microstructure"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(reverse(add(zscore(ts_delta(ts_backfill({field_ids[0]},20),5)), zscore(ts_std_dev(ts_backfill({field_ids[1]},20),20)))))",
            "microstructure stress through short-horizon flow and volatility",
        )

    if {"news_sentiment"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(add(zscore(ts_delta(ts_backfill({field_ids[0]},63),5)), reverse(zscore(ts_std_dev(ts_backfill({field_ids[1]},63),20)))))",
            "improving sentiment with lower dispersion or instability",
        )

    if {"cross_asset_relative"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(subtract(zscore(ts_backfill({field_ids[0]},63)), zscore(ts_backfill({field_ids[1]},63))))",
            "relative spread between benchmark-linked or peer-linked fields",
        )

    if {"model_features"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(add(zscore(ts_backfill({field_ids[0]},63)), reverse(zscore(ts_backfill({field_ids[1]},63)))))",
            "blend between model signal level and an opposing model feature",
        )

    if {"options_implied"} & set(mechanism_guesses) and len(field_ids) >= 2:
        add_template(
            f"rank(add(zscore(ts_delta(ts_backfill({field_ids[0]},63),5)), reverse(zscore(ts_backfill({field_ids[1]},63)))))",
            "change in implied option signal versus opposing term or level signal",
        )

    if field_ids:
        add_template(
            f"rank(ts_zscore(ts_delta(ts_backfill({field_ids[0]},252),63),252))",
            "time-series momentum in the first candidate field",
        )
        add_template(
            f"rank(reverse(ts_zscore(ts_backfill({field_ids[0]},252),252)))",
            "mean-reversion or stress ranking on the first candidate field",
        )

    if len(field_ids) >= 2:
        add_template(
            f"rank(add(zscore({field_ids[0]}), zscore({field_ids[1]})))",
            "composite quality signal from the top two candidate fields",
        )
        add_template(
            f"rank(subtract(zscore({field_ids[0]}), zscore({field_ids[1]})))",
            "relative spread between the top two candidate fields",
        )

    if len(field_ids) >= 3:
        add_template(
            f"rank(add(zscore({field_ids[0]}), zscore({field_ids[1]}), reverse(zscore({field_ids[2]}))))",
            "three-leg composite with one adverse field reversed",
        )

    if not templates:
        add_template("rank(returns)", "fallback placeholder template when no fields were found")

    return templates


def _guess_mechanisms(text: str) -> list[str]:
    tokens = set(_tokenize(text))
    scored: list[tuple[int, str]] = []
    for name, keywords in MECHANISM_KEYWORDS.items():
        score = len(tokens & keywords)
        if score:
            scored.append((score, name))
    scored.sort(reverse=True)
    return [name for _, name in scored]


def _mechanism_expression_families(mechanisms: list[str]) -> list[str]:
    families: list[str] = []
    for mechanism in mechanisms:
        if mechanism == "working_capital":
            families.append("ratio deterioration, cash-conversion stress, inventory versus sales")
        elif mechanism == "analyst_expectations":
            families.append("estimate momentum, disagreement compression, recommendation overlays")
        elif mechanism == "labor_intensity":
            families.append("employee-to-sales drift, wage pressure proxies, staffing efficiency")
        elif mechanism == "quality_profitability":
            families.append("accrual quality spreads, cash-flow profitability, profitability versus margin")
        elif mechanism == "investment_efficiency":
            families.append("capex efficiency, asset-turnover drift, ROIC composites")
        elif mechanism == "microstructure":
            families.append("illiquidity drift, turnover shocks, range compression or expansion")
        elif mechanism == "news_sentiment":
            families.append("sentiment momentum, sentiment dispersion, attention shocks")
        elif mechanism == "cross_asset_relative":
            families.append("sector-versus-constituent spread, benchmark-relative mispricing, peer divergence")
        elif mechanism == "model_features":
            families.append("model-score divergence, residual composites, forecast disagreement")
        elif mechanism == "options_implied":
            families.append("implied skew drift, breakeven dislocation, option-term-structure spreads")
    return families


def _coerce_data_field_results(payload: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            results = data.get("results")
            if isinstance(results, list):
                return [item for item in results if isinstance(item, dict)]
        results = payload.get("results")
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        return []
    return [item for item in payload if isinstance(item, dict)]


def _coerce_web_text(text: str, *, max_chars: int) -> str:
    stripped = HTML_SCRIPT_STYLE_PATTERN.sub(" ", text)
    stripped = HTML_TAG_PATTERN.sub(" ", stripped)
    stripped = html.unescape(stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return _truncate_text(stripped, max_chars)


def _extract_title(text: str) -> str | None:
    match = HTML_TITLE_PATTERN.search(text)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def _extract_notable_sentences(text: str, *, limit: int) -> list[str]:
    sentences = [sentence.strip() for sentence in SENTENCE_PATTERN.split(text) if sentence.strip()]
    scored: list[tuple[int, str]] = []
    for sentence in sentences:
        tokens = set(_tokenize(sentence))
        score = sum(1 for keywords in MECHANISM_KEYWORDS.values() if tokens & keywords)
        if score:
            scored.append((score, sentence))
    scored.sort(key=lambda item: (-item[0], len(item[1])))
    return [sentence for _, sentence in scored[:limit]]


def _truncate_text(text: str, max_chars: int) -> str:
    return text[:max_chars].strip()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _normalize_expression(expression: str) -> str:
    return re.sub(r"\s+", "", expression).lower()


def _expression_similarity(left: str, right: str) -> float:
    left_tokens = set(_tokenize(left))
    right_tokens = set(_tokenize(right))
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, _normalize_expression(left), _normalize_expression(right)).ratio()
    return (jaccard + sequence) / 2


def _expression_ast_similarity(left_ast: Any, right_ast: Any) -> float:
    if left_ast is None or right_ast is None:
        return 0.0
    return ast_similarity(left_ast, right_ast)


def _attach_ast_metadata(comparator: dict[str, Any]) -> dict[str, Any]:
    parsed_expression, parse_error = try_parse_expression(comparator["expression"])
    return {
        **comparator,
        "_ast": parsed_expression,
        "_astParseError": parse_error,
        "_interpretation": describe_expression(comparator["expression"], parsed_expression, parse_error),
    }


def _attach_entry_interpretations(entry: dict[str, Any]) -> dict[str, Any]:
    interpreted_entry = dict(entry)
    expressions = [expression for expression in (entry.get("expressions") or []) if isinstance(expression, str)]
    interpreted_entry["expressionInterpretations"] = [
        {
            "expression": expression,
            "interpretation": describe_expression(expression),
        }
        for expression in expressions
    ]

    interpreted_alphas = []
    for alpha in entry.get("alphas") or []:
        if not isinstance(alpha, dict):
            interpreted_alphas.append(alpha)
            continue
        interpreted_alpha = dict(alpha)
        expression = interpreted_alpha.get("expression")
        if isinstance(expression, str):
            interpreted_alpha["interpretation"] = describe_expression(expression)
        interpreted_alphas.append(interpreted_alpha)
    interpreted_entry["alphas"] = interpreted_alphas
    return interpreted_entry


def _deduplicate_expression_comparators(comparators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[str, dict[str, Any]] = {}
    for comparator in comparators:
        expression = comparator.get("expression")
        if not isinstance(expression, str):
            continue
        key = _normalize_expression(expression)
        existing = deduplicated.get(key)
        if existing is None:
            deduplicated[key] = {
                **comparator,
                "linkedIds": [comparator.get("id")] if comparator.get("id") else [],
            }
            continue
        if _comparator_priority(comparator) > _comparator_priority(existing):
            retained_ids = existing.get("linkedIds") or []
            deduplicated[key] = {
                **comparator,
                "linkedIds": retained_ids,
            }
            existing = deduplicated[key]
        comparator_id = comparator.get("id")
        if comparator_id and comparator_id not in existing["linkedIds"]:
            existing["linkedIds"].append(comparator_id)
    return list(deduplicated.values())


def _comparator_priority(comparator: dict[str, Any]) -> int:
    source = comparator.get("source")
    if source == "experiment-alpha":
        return 3
    if source == "recent-alpha":
        return 2
    return 1


def _looks_like_url(value: str) -> bool:
    lowered = value.lower().strip()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _recent_expression_comparators(client: WorldQuantClient, limit: int) -> list[dict[str, Any]]:
    payload = client.list_recent_alphas(limit=limit)
    data = payload.get("results") if isinstance(payload, dict) else None
    if data is None and isinstance(payload, dict):
        data = (payload.get("data") or {}).get("results")
    if not isinstance(data, list):
        data = []

    comparators: list[dict[str, Any]] = []
    for alpha in data:
        if not isinstance(alpha, dict):
            continue
        expression = ((alpha.get("regular") or {}).get("code"))
        if not isinstance(expression, str):
            continue
        comparators.append(
            {
                "source": "recent-alpha",
                "id": alpha.get("id"),
                "theme": alpha.get("category"),
                "mechanismTag": alpha.get("category"),
                "mechanismTags": [alpha.get("category")] if alpha.get("category") else [],
                "status": alpha.get("status"),
                "stage": alpha.get("stage"),
                "expression": expression,
            }
        )
    return comparators


def _logged_expression_comparators(config: WorldQuantConfig) -> list[dict[str, Any]]:
    comparators: list[dict[str, Any]] = []
    for entry in _load_experiment_entries(config.experiment_memory_path):
        theme = entry.get("theme")
        mechanism_tag = entry.get("mechanism_tag")
        mechanism_tags = entry.get("mechanism_tags") or ([] if mechanism_tag is None else [mechanism_tag])
        for expression in entry.get("expressions") or []:
            if isinstance(expression, str):
                comparators.append(
                    {
                        "source": "experiment-log",
                        "id": entry.get("timestamp"),
                        "theme": theme,
                        "mechanismTag": mechanism_tag,
                        "mechanismTags": mechanism_tags,
                        "expression": expression,
                    }
                )
        for alpha in entry.get("alphas") or []:
            expression = alpha.get("expression") if isinstance(alpha, dict) else None
            if isinstance(expression, str):
                comparators.append(
                    {
                        "source": "experiment-alpha",
                        "id": alpha.get("alphaId"),
                        "theme": theme,
                        "mechanismTag": mechanism_tag,
                        "mechanismTags": mechanism_tags,
                        "status": alpha.get("status"),
                        "stage": alpha.get("stage"),
                        "expression": expression,
                    }
                )
    return comparators


def _comparator_avoidance_priority(comparator: dict[str, Any]) -> int:
    status = str(comparator.get("status") or "").upper()
    stage = str(comparator.get("stage") or "").upper()
    if status == "ACTIVE" and stage == "OS":
        return 3
    if status == "ACTIVE":
        return 2
    if stage == "OS":
        return 1
    return 0


def _load_experiment_entries(path: Path) -> list[dict[str, Any]]:
    _ensure_store(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_experiment_entries(path: Path, entries: list[dict[str, Any]]) -> None:
    _ensure_store(path)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _ensure_store(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]\n", encoding="utf-8")


def _append_to_quant_journey(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Quant Journey\n", encoding="utf-8")

    lines = [
        "",
        f"## Experiment: {entry['timestamp']}",
        "",
        f"Theme: {entry['theme']}",
    ]

    mechanism_tag = entry.get("mechanism_tag")
    if mechanism_tag:
        lines.extend(["", f"Mechanism Tag: {mechanism_tag}"])

    mechanism_tags = [tag for tag in (entry.get("mechanism_tags") or []) if isinstance(tag, str)]
    if mechanism_tags:
        lines.extend(["", f"Mechanism Tags: {', '.join(mechanism_tags)}"])

    lines.extend([
        "",
        f"Hypothesis: {entry['hypothesis']}",
        "",
        f"Summary: {entry['summary']}",
    ])

    expressions = entry.get("expressions") or []
    if expressions:
        lines.extend(["", "Expressions:"])
        for expression in expressions:
            lines.append(f"- `{expression}`")

    alphas = entry.get("alphas") or []
    if alphas:
        lines.extend(["", "Alpha Summaries:"])
        for alpha in alphas:
            metrics = alpha.get("metrics") or {}
            lines.append(
                "- "
                f"{alpha.get('alphaId')}: sharpe={metrics.get('sharpe')}, "
                f"fitness={metrics.get('fitness')}, returns={metrics.get('returns')}, "
                f"turnover={metrics.get('turnover')}"
            )

    follow_ups = entry.get("followUps") or []
    if follow_ups:
        lines.extend(["", "Next Steps:"])
        for step in follow_ups:
            lines.append(f"- {step}")

    path.write_text(path.read_text(encoding="utf-8") + "\n".join(lines) + "\n", encoding="utf-8")


def _resolve_mechanism_fields(
    *,
    mechanism_tag: str | None,
    mechanism_tags: list[str] | None,
    theme: str,
    hypothesis: str,
    summary: str,
    expressions: list[str],
    alpha_summaries: list[dict[str, Any]],
) -> tuple[str | None, list[str]]:
    explicit_tags = [tag.strip() for tag in (mechanism_tags or []) if isinstance(tag, str) and tag.strip()]
    normalized_primary = mechanism_tag.strip() if isinstance(mechanism_tag, str) and mechanism_tag.strip() else None
    if normalized_primary and normalized_primary not in explicit_tags:
        explicit_tags.insert(0, normalized_primary)
    if explicit_tags:
        return explicit_tags[0], explicit_tags

    inferred_scores = _infer_mechanism_tag_scores(
        theme=theme,
        hypothesis=hypothesis,
        summary=summary,
        expressions=expressions,
        alpha_summaries=alpha_summaries,
    )
    if not inferred_scores:
        return None, []

    inferred_tags = [tag for tag, _ in inferred_scores]
    primary = inferred_tags[0]
    if "parallel" in theme.lower() and len(inferred_tags) > 1:
        return "multi_mechanism_parallel_search", inferred_tags
    return primary, inferred_tags


def _infer_mechanism_tag_scores(
    *,
    theme: str,
    hypothesis: str,
    summary: str,
    expressions: list[str],
    alpha_summaries: list[dict[str, Any]],
) -> list[tuple[str, int]]:
    blobs = [theme, hypothesis, summary, *expressions]
    blobs.extend(
        alpha.get("expression", "")
        for alpha in alpha_summaries
        if isinstance(alpha, dict) and isinstance(alpha.get("expression"), str)
    )
    tokens: set[str] = set()
    for blob in blobs:
        if isinstance(blob, str):
            tokens.update(_tokenize(blob))

    scored: list[tuple[str, int]] = []
    for tag, keywords in MECHANISM_TAG_KEYWORDS.items():
        score = len(tokens & keywords)
        if score:
            scored.append((tag, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored


def _entry_matches_mechanism_tag(entry: dict[str, Any], mechanism_tag: str) -> bool:
    wanted = mechanism_tag.lower().strip()
    if not wanted:
        return True
    primary = str(entry.get("mechanism_tag") or "").lower()
    if primary == wanted:
        return True
    tags = [str(tag).lower() for tag in (entry.get("mechanism_tags") or [])]
    return wanted in tags