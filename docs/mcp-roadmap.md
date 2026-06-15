# MCP Roadmap

This roadmap is focused on one goal: make the MCP more useful for discovering,
screening, and submitting WorldQuant Brain alphas instead of only acting as a
thin API wrapper.

## Current State

What already works well:

- Authentication and account access.
- Operator and data-field discovery.
- Simulation submission and polling.
- Alpha and submission-status retrieval.
- Local reference search.
- Pre-submit readiness validation for a single alpha.
- Batch simulation and ranking.
- Seed-expression mutation.
- Research-to-proxy mapping.
- External research ingestion into heuristic mechanisms.
- Local experiment memory and novelty checks.

Main bottleneck observed in live usage:

- The MCP now covers the main research loop, but the heuristics still need to
  be improved by using the new tools on larger research sets.

## Implemented Improvements

### 1. Batch simulation

Add a tool that accepts a list of expressions plus shared settings and returns:

- simulation ids
- alpha ids when complete
- IS metrics
- blocking checks
- a sorted leaderboard

Why: profitable-alpha search is a search problem, not a single-expression
problem.

### 2. Alpha mutation from a seed

Add a tool that takes one seed expression and generates nearby variants across:

- sign flips
- lookback windows
- decay
- normalization method
- neutralization choice
- conditional overlays

Why: most useful ideas need structured local search around a mechanism.

### 3. Research-to-proxy workflow

Add a helper that turns a text hypothesis into:

- candidate field ids
- likely operator patterns
- 5-10 expression templates

Why: papers and forum posts are usually too abstract to simulate directly.

### 4. Result ranking and filtering

Add a tool that scores alphas by a configurable rule such as:

- sharpe threshold
- fitness threshold
- sub-universe sharpe threshold
- turnover range
- duplicate-risk or similarity score

Why: this makes the MCP useful as a triage layer before submission.

## Implemented Mid-Term Foundations

### 1. External research ingestion

Build opt-in ingestion for sources such as:

- Reddit threads used as hypothesis sources
- SSRN or NBER abstracts
- blog posts or quant notes

Output should be structured as:

- mechanism summary
- likely field proxies
- caveats
- candidate expression families

Important: use these sources for hypothesis discovery, not direct formula reuse.

### 2. Experiment memory

Persist prior alpha runs with:

- expression
- settings
- theme
- metrics
- blockers
- follow-up ideas

Why: repeated failures are often caused by forgetting what was already tried.

### 3. Novelty and crowding checks

Compare new candidates against recent local experiments and account history to
flag near-duplicates before simulation.

## Next Iteration Targets

1. Improve mutation heuristics with parser-aware edits instead of string-level substitutions.
2. Improve research ingestion with source-specific parsing for Reddit, SSRN, and NBER.
3. Add automated batch pipelines that chain hypothesis mapping, mutation, novelty checks, and simulation.
4. Add richer scoring that combines metrics, blockers, and novelty into one ranking rule.
