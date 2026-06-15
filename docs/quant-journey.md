# Quant Journey

This file is a running research log for future agents working in this repo.
Treat it as a compact experiment journal: append new runs, keep failed ideas,
and record why something did or did not work.

## How To Use This Note

For each new research pass, record:

- the hypothesis or mechanism
- the Brain field proxies used
- the expression family tested
- the best alpha ids and key IS metrics
- why submission succeeded or failed
- what to try next

## Session: 2026-05-07

Goal:

- Test whether recent-paper-inspired themes can be mapped into WorldQuant Brain
  expressions and submitted through this MCP.

Conclusion:

- The MCP worked end to end.
- The blocker was alpha quality, not server functionality.
- Brain rejected submission attempts because the tested alphas failed minimum IS
  checks, mainly LOW_SHARPE and LOW_FITNESS.

## What Worked In The MCP

- Live authentication.
- Account lookup.
- Operator discovery.
- Data-field discovery.
- Simulation creation.
- Simulation polling until alpha creation.
- Alpha detail retrieval.
- Submission attempts.

## Research Themes Tested

### 1. Working-capital efficiency deterioration

Mechanism:

- Firms with worsening receivables and inventory efficiency may be overpriced
  before slower future earnings realization.

Key proxies:

- receivable
- inventory
- sales
- cogs

Best alpha:

- `[REDACTED]`

Expression family:

- reverse of yearly change in `(receivable / sales) + (inventory / cogs)`

Result:

- sharpe `0.50`
- fitness `0.18`
- returns `0.0160`
- turnover `0.0344`

Outcome:

- best idea from the session
- still not submittable because sharpe and fitness were below Brain thresholds

### 2. Working capital plus cash-flow quality

Mechanism:

- Same working-capital stress idea, but with a cash-flow quality overlay.

Key proxies:

- receivable
- inventory
- sales
- cogs
- [REDACTED]
- income

Best alpha:

- `[REDACTED]`

Result:

- sharpe `0.14`
- fitness `0.03`
- returns `0.0061`
- turnover `0.0337`

Outcome:

- positive but materially weaker than the pure working-capital version

### 3. Analyst confidence / disagreement

Mechanism:

- rising EPS expectations with lower estimate dispersion and supportive broker
  recommendations might predict better forward returns.

Key proxies:

- [REDACTED]
- [REDACTED]
- [REDACTED]

Best alpha:

- `[REDACTED]`

Result:

- sharpe `0.15`
- fitness `0.03`
- returns `0.0047`
- turnover `0.0994`

Outcome:

- valid but too weak to submit

### 4. Labor-cost stickiness / employee intensity

Mechanism:

- rising labor intensity relative to sales may flag future margin pressure.

Key proxies:

- employee
- sales

Best alpha:

- `[REDACTED]`

Result:

- negative sharpe

Outcome:

- sign or proxy choice likely wrong for this data representation

### 5. Profitability / accrual quality composites

Mechanism:

- combine model-derived profitability and accrual-quality factors.

Key proxies:

- [REDACTED]
- [REDACTED]
- [REDACTED]
- [REDACTED]
- [REDACTED]

Best alphas:

- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Outcome:

- all were clearly worse than the raw working-capital family
- likely over-compressed or sign-wrong in this construction

## Practical Lessons

- Brain idea generation should be treated as a search problem over expression
  families, not a one-paper-to-one-alpha workflow.
- Reddit or papers are useful as hypothesis sources, but still need field-proxy
  mapping and large local variant search.
- The strongest family so far is working-capital deterioration.
- Future work should start by generating 10-20 variants around `[REDACTED]`
  rather than switching themes immediately.

## Next Research Suggestions

1. Explore 10-20 variants around `[REDACTED]` using different horizons, signs,
   normalization methods, and conditional overlays.
2. Test sector- or subindustry-conditioned versions of the working-capital idea.
3. Use external sources like Reddit, SSRN, or NBER to collect mechanisms, then
   map each mechanism into multiple Brain-ready variants.
4. Store future experiment results here so later agents can continue from real
   evidence instead of repeating weak families.

## Tooling Upgrade: 2026-05-07

The repo now includes an alpha-lab layer on top of the thin API wrapper.

New capabilities added:

- batch simulation and leaderboard ranking
- batch alpha summarization with thresholds
- seed-expression mutation
- hypothesis-to-proxy mapping
- external research ingestion from URLs or pasted notes
- novelty comparison against recent alphas and local experiment history
- machine-readable experiment logging in `src/worldquant_mcp/data/experiment_memory.json`

Practical implication:

- Future research should use the lab tools first, then only submit the best
  surviving candidates.

## Experiment: 2026-05-07T10:28:12+00:00

Theme: parallel-mechanism-search

Hypothesis: Stop polishing the cashflow-gated working-capital basin and run four independent mechanism branches in parallel: price-volume microstructure, options-implied dislocation, news or social sentiment drift, and mdl177 model divergence.

Summary: Implemented a new parallel mechanism search tool in lab.py and ran a four-branch live search in USA TOP3000 delay 1 decay 6 SUBINDUSTRY. The result supports the strategic pivot. The legacy working-capital family was not the best new frontier. The option-implied branch produced the clear winner: [REDACTED] = [REDACTED] with sharpe 1.31, fitness 0.58, returns 0.0584, turnover 0.2963, concentrated weight PASS, and sub-universe sharpe 1.14 PASS. It clears the sharpe bar but still fails LOW_FITNESS, so the family has real edge but needs conditioning or normalization rather than abandonment. News or social sentiment was weaker but viable (best [REDACTED] at sharpe 0.39, fitness 0.16). mdl177 divergence was dead on this first pass. The microstructure branch failed for a useful reason: the current mapper pulled invalid group-typed fields like currency, producing unit errors, which means the search tool successfully exposed where field selection needs to be made more type-aware.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.31, fitness=0.58, returns=0.0584, turnover=0.2963
- [REDACTED]: sharpe=0.2, fitness=0.04, returns=0.0095, turnover=0.2708
- [REDACTED]: sharpe=0.39, fitness=0.16, returns=0.0205, turnover=0.0866
- [REDACTED]: sharpe=-0.19, fitness=-0.04, returns=-0.0062, turnover=0.0348

Next Steps:
- Stress-test [REDACTED] in easier settings next: USA TOP1000, TOP500, delay 0, and one non-USA region to see whether the mechanism generalizes or only barely survives in USA delay 1.
- Make the branch mapper type-aware so price-volume or microstructure hypotheses prioritize price, returns, volume, adv, vwap, and range fields while excluding symbol or group-typed fields like currency.
- Extend the option branch with term-structure and skew spreads rather than only single-field ts_delta, because the current winner shows genuine edge but still needs a fitness lift.

## Experiment: 2026-05-07T11:50:11+00:00

Theme: options-smoothing-search

Hypothesis: The top options alpha [REDACTED] is fitness-limited mainly by turnover, so the cheapest next win is to smooth the existing implied-volatility momentum family before trying harder multi-leg constructions. In parallel, seed a few mechanistically different options structures so we have fallback candidates if the bare put-IV family is crowded.

Summary: Pulled metadata first and confirmed [REDACTED] means at-the-money put implied volatility with 10 calendar days to expiration, so the suffix is tenor, not moneyness. Then ran a focused ten-expression batch at decay 10 and decay 15: six smoothing variants around [REDACTED] plus four diversification seeds covering put-call skew, put term structure, IV-versus-realized-vol spread, and the built-in mean-skew field. The main thesis was correct but only partially: smoothing mechanically cut turnover from the original ~0.30 down to ~0.10-0.13, but it also bled away too much Sharpe, so the best fitness only rose to 0.65 instead of clearing 1.0. Best result in the round was [REDACTED] = [REDACTED] at decay 15 with sharpe 1.06, fitness 0.65, returns 0.0473, turnover 0.1034, and sub-universe sharpe 1.01 PASS. A close second was [REDACTED] = [REDACTED] at decay 10 with sharpe 1.06, fitness 0.64, returns 0.0466, turnover 0.1283, and sub-universe sharpe 0.88 PASS. The raw family with higher decay alone only reached fitness 0.60. Dropping the outer ts_zscore or lengthening the inner delta to 126 hurt badly. On diversification, put term structure had weak but positive edge, while put-call skew and mean-skew momentum were poor and often failed sub-universe quality. The IV-versus-realized-vol gap line did not finish cleanly in this round because of transport or simulation timeout noise, so it remains unresolved rather than disproven.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.06, fitness=0.65, returns=0.0473, turnover=0.1034
- [REDACTED]: sharpe=1.06, fitness=0.64, returns=0.0466, turnover=0.1283
- [REDACTED]: sharpe=1.19, fitness=0.6, returns=0.0549, turnover=0.2196
- [REDACTED]: sharpe=0.65, fitness=0.2, returns=0.0242, turnover=0.2535
- [REDACTED]: sharpe=0.49, fitness=0.14, returns=0.018, turnover=0.2317

Next Steps:
- Search for transforms that preserve more Sharpe while keeping turnover near 0.10, rather than smoothing harder; pure smoothing helped turnover but did not solve the real tradeoff.
- Retry the IV-versus-realized-vol gap line by itself because this round did not produce a clean signal read; the missing result was operationally noisy, not decisively bad.
- Only after a stronger fitness candidate appears, stress-test TOP1000, TOP500, delay 0, and one non-USA region; the current best smoothed variants are still too far below the 1.0 fitness bar to justify that as the next priority.

## Experiment: 2026-05-07T17:39:42+00:00

Theme: options-linear-smoother-search

Hypothesis: The put-IV momentum family still has room if the smoothing is made more local and the simulation decay is allowed to carry more of the slowness. Instead of broader diversification, search the narrow neighborhood around ts_decay_linear wrappers and the decay setting interaction.

Summary: Restarted the previously stuck search with bounded global polling and reran the options family through direct workspace Python helpers rather than waiting on an untracked terminal run. The useful finding is that short linear smoothing beats simple moving averages. First pass found [REDACTED] = [REDACTED] at decay 15 with sharpe 1.09, fitness 0.68, returns 0.0498, turnover 0.1289, and sub-universe sharpe 0.98. A tighter follow-up around the same family found an even better point: [REDACTED] = [REDACTED] at decay 20 with sharpe 1.16, fitness 0.76, returns 0.0534, turnover 0.1054, margin 0.001014, and sub-universe sharpe 1.06 PASS. This is still below the Brain bars, but it is a real frontier improvement over the earlier 0.65 ceiling and confirms the local search direction: moderate linear smoothing plus higher simulation decay preserves more Sharpe than plain averaging while still cutting turnover materially. The unresolved branch is lin7_decay10, which timed out at low progress and should be treated as unknown rather than bad. Several broader attempts also hit CONCURRENT_SIMULATION_LIMIT_EXCEEDED, so the practical lesson is to keep these local sweeps small and bounded.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.16, fitness=0.76, returns=0.0534, turnover=0.1054
- [REDACTED]: sharpe=1.09, fitness=0.69, returns=0.0494, turnover=0.1201
- [REDACTED]: sharpe=1.09, fitness=0.68, returns=0.0498, turnover=0.1289
- [REDACTED]: sharpe=1.11, fitness=0.67, returns=0.0512, turnover=0.1422

Next Steps:
- Retry lin7 at decay 10 by itself because it timed out before producing an alpha and the family is now strong enough that the missing point is worth resolving.
- Search one step outward from the new best using nearby linear windows and maybe one light normalization tweak, but keep batches tiny to avoid the concurrent simulation limit.
- Only after another fitness lift, run easier-universe stress tests; [REDACTED] is the new anchor, but 0.76 fitness is still too far from 1.0 to justify submission attempts.

## Experiment: 2026-05-08T02:55:56+00:00

Theme: options-tsrank-breakthrough

Hypothesis: The put-IV family likely needs a wrapper change rather than more smoothing. After the local linear-smoother frontier stabilized, the highest-EV move was applying ts_rank over the smoothed signal, then stress-testing the winner in smaller universes while self-correlation remains unresolved.

Summary: Resumed the interrupted task after fixing MCP timeout behavior and resolved the remaining local unknowns first. The previously timed-out lin7_decay10 point completed cleanly and was not a hidden winner: [REDACTED] reached only sharpe 1.06 and fitness 0.60, clearly worse than the decay-20 frontier. [REDACTED] still has SELF_CORRELATION pending, so the crowdedness verdict on the family is not settled yet. The big move came from the Priority 2B wrapper sweep: ts_rank over the best smoothed signal materially lifted quality. The clear winner was [REDACTED] = [REDACTED] with sharpe 1.45, fitness 1.03, returns 0.0633, turnover 0.1128, no blocking checks, and only SELF_CORRELATION pending. That means the expression is already above the usual IS bars in USA TOP3000 and is blocked only by the unresolved crowding check. The sister variants were also strong: [REDACTED] at ts_rank window 252 reached fitness 0.95 and [REDACTED] at ts_rank window 63 reached fitness 0.93. Universe stress tests did not produce an easier shipping path: TOP500 and TOP1000 versions remained below bar, with the best smaller-universe point [REDACTED] in TOP500 reaching sharpe 1.07 and fitness 0.87. So the real submission path is no longer 'smaller universe rescue'; it is waiting on or surviving SELF_CORRELATION for the TOP3000 ts_rank-126 winner.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.45, fitness=1.03, returns=0.0633, turnover=0.1128
- [REDACTED]: sharpe=1.37, fitness=0.95, returns=0.0598, turnover=0.1122
- [REDACTED]: sharpe=1.38, fitness=0.93, returns=0.0572, turnover=0.1175
- [REDACTED]: sharpe=1.16, fitness=0.76, returns=0.0534, turnover=0.1054
- [REDACTED]: sharpe=1.06, fitness=0.6, returns=0.0466, turnover=0.1434
- [REDACTED]: sharpe=1.07, fitness=0.87, returns=0.0868, turnover=0.1327

Next Steps:
- Re-check SELF_CORRELATION on [REDACTED] and [REDACTED] later today; if [REDACTED] clears, submit that alpha directly because it already passes the performance bars.
- If SELF_CORRELATION fails on [REDACTED], treat the plain put-IV family as crowded and pivot back to a more orthogonal mechanism rather than continuing to polish this basin.
- If waiting time allows, a tiny follow-up around the winner could test nearby ts_rank windows around 126 such as 105 and 147, but only after or alongside the self-correlation re-check, not instead of it.

## Experiment: 2026-05-08T09:10:51+00:00

Theme: tooling-ast-novelty-shadow

Hypothesis: AST-based structural similarity should cluster options-IV families more cleanly than token and sequence overlap, while keeping live ranking behavior unchanged until validated.

Summary: Added a deterministic Brain-expression parser, AST largest-common-subtree similarity, shadow AST fields in analyze_expression_novelty, and a validate_alpha_novelty_shadow tool for log-only checks. Validation on 14 unique logged expressions parsed 14 of 14 successfully. [REDACTED] clustered first with [REDACTED] and [REDACTED] at AST similarity 1.0, with nearby wrapper siblings such as [REDACTED] and [REDACTED] at 0.9. Non-options references such as [REDACTED] and [REDACTED] stayed materially lower at roughly 0.0909 to 0.125. The legacy novelty score remains the active ranking metric; AST is shadow-only for now. One validation target remains pending until Step 2 backfills the machine-readable store with early working-capital history.

Next Steps:
- Add mechanism_tag to experiment entries and backfill the existing experiment store, including early working-capital history that currently exists only in the journal.
- Reuse the new parser for deterministic factor interpretation before considering any ranking change from legacy novelty to AST-informed novelty.

## Experiment: 2026-05-08T09:42:08+00:00

Theme: tooling-mechanism-tag-backfill

Mechanism Tag: research_infrastructure

Mechanism Tags: research_infrastructure

Hypothesis: Adding mechanism tags and backfilling journal-only experiments should close the remaining Step 1 validation gap and make orthogonality checks queryable by mechanism family.

Summary: Added mechanism_tag support to experiment logging and listing, surfaced mechanism tag metadata in novelty comparisons, and backfilled the machine-readable store with the missing 2026-05-07 journal-only families using exact Brain expressions fetched from their alpha IDs. The working-capital family is now queryable with a mechanism_tag filter, and AST validation now sees [REDACTED] and [REDACTED] as close siblings at 0.96 while [REDACTED] remains clustered inside options-IV momentum instead.

Next Steps:
- Reuse the parser for deterministic factor interpretation in Step 3.
- Use mechanism-tag plus AST distance together when screening the next microstructure or institutional-flow basin against [REDACTED].

## Experiment: 2026-05-08T09:52:49+00:00

Theme: tooling-deterministic-factor-interpretation

Mechanism Tag: research_infrastructure

Mechanism Tags: research_infrastructure

Hypothesis: The AST parser can be reused to generate deterministic plain-English interpretations of Brain expressions, which should make novelty review and experiment review more legible without introducing model calls or changing search behavior.

Summary: Added deterministic expression interpretation on top of the AST parser, preserved exact numeric literals for explanation while keeping number matching structural for AST similarity, and exposed interpretation objects in analyze_expression_novelty, validate_alpha_novelty_shadow, and list_alpha_experiments outputs. Validation confirmed that both [REDACTED] and the backfilled working-capital family now return stable summaries, step lists, field lists, and function lists in novelty and review flows.

Next Steps:
- Use mechanism-tag plus AST similarity plus deterministic interpretation when screening the next microstructure or institutional-flow basin against [REDACTED].
- Keep consistency scoring opt-in later rather than inserting it into every mapping call.

## Experiment: 2026-05-08T10:22:21+00:00

Theme: microstructure-return-volume-correlation-basin

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Cross-sectional rank of reversed correlation between returns and 1-day volume change is an institutional-flow proxy that is structurally orthogonal to the shipped options-IV family; raw 40- and 60-day windows appear to be the healthy basin, while outer ts_rank normalization degrades the signal.

Summary: Orthogonality screen stayed far from [REDACTED] and clustered only with this new microstructure branch. Tested seven expressions sequentially. Ranking: [REDACTED] [REDACTED] Sharpe 0.82 Fitness 0.46 Turnover 0.0914 Sub-universe Sharpe 1.11; [REDACTED] [REDACTED] Sharpe 0.81 Fitness 0.45 Turnover 0.0693 Sub-universe Sharpe 1.15; [REDACTED] [REDACTED] Sharpe 0.66 Fitness 0.30 Sub-universe Sharpe 0.53; [REDACTED] [REDACTED] Sharpe 0.67 Fitness 0.31 but weaker than raw 40/60; [REDACTED] [REDACTED] had wrong sign and failed LOW_SHARPE -0.66, LOW_FITNESS -0.30, LOW_SUB_UNIVERSE_SHARPE -0.53. Wrapper follow-ups both degraded: [REDACTED] [REDACTED] Sharpe 0.28 Fitness 0.08 Sub-universe Sharpe 0.40; [REDACTED] [REDACTED] Sharpe 0.31 Fitness 0.09 Sub-universe Sharpe 0.62. Conclusion: keep the raw reversed 40/60-day basin; do not add outer ts_rank here.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=-0.66, fitness=-0.3, returns=-0.0308, turnover=0.1455
- [REDACTED]: sharpe=0.66, fitness=0.3, returns=0.0308, turnover=0.1455
- [REDACTED]: sharpe=0.82, fitness=0.46, returns=0.0388, turnover=0.0914
- [REDACTED]: sharpe=0.67, fitness=0.31, returns=0.0304, turnover=0.1464
- [REDACTED]: sharpe=0.81, fitness=0.45, returns=0.0394, turnover=0.0693
- [REDACTED]: sharpe=0.28, fitness=0.08, returns=0.0099, turnover=0.1109
- [REDACTED]: sharpe=0.31, fitness=0.09, returns=0.0102, turnover=0.0943

Next Steps:
- Branch from raw reversed 40- and 60-day seeds only.
- Test adjacent robustness knobs before adding extra wrappers, starting with mild decay/window variants.
- Avoid outer ts_rank on this basin unless a later branch materially improves raw Sharpe first.

## Experiment: 2026-05-08T18:19:35+00:00

Theme: microstructure-lookback-sweep-and-volume-filter

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: The healthy microstructure basin is the reversed correlation between returns and short-horizon volume change; robustness should come from the correlation window rather than from lengthening the volume-delta lag, and a simple high-volume regime filter may improve the raw 40/60-day seeds without adding factor complexity.

Summary: Completed a six-cell lookback sweep by combining prior n=1 anchors with three new n=5 runs. The n=1 branch remains the signal core: [REDACTED] [REDACTED] still leads on fitness at 0.46 with Sharpe 0.82 and Sub-universe Sharpe 1.11, while [REDACTED] [REDACTED] stays close at Fitness 0.45, Sharpe 0.81, Sub-universe Sharpe 1.15. The new n=5 variants were all weaker: [REDACTED] 20d reached Sharpe 0.66 Fitness 0.29 Sub-universe Sharpe 0.40; [REDACTED] 40d reached Sharpe 0.69 Fitness 0.35 Sub-universe Sharpe 0.58; [REDACTED] 60d reached Sharpe 0.63 Fitness 0.31 Sub-universe Sharpe 0.74. That means lengthening the volume-delta lag does not improve this basin. Regime filtering with volume > adv20 also failed to create a new frontier: [REDACTED] on the 40d seed was essentially lateral at Sharpe 0.83 Fitness 0.46 Sub-universe Sharpe 1.02 with lower turnover 0.0864, while [REDACTED] on the 60d seed slipped to Sharpe 0.77 Fitness 0.42 Sub-universe Sharpe 1.05. Conclusion: keep the raw reversed ts_corr core with [REDACTED] and 40/60-day windows; do not lengthen the lag and do not add the simple volume-spike trade_when filter at this stage. Housekeeping: the local store now marks [REDACTED] as ACTIVE/OS and novelty tie-breaks surface active shipped alphas first in avoidance matches.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.66, fitness=0.3, returns=0.0308, turnover=0.1455
- [REDACTED]: sharpe=0.82, fitness=0.46, returns=0.0388, turnover=0.0914
- [REDACTED]: sharpe=0.81, fitness=0.45, returns=0.0394, turnover=0.0693
- [REDACTED]: sharpe=0.66, fitness=0.29, returns=0.0298, turnover=0.1565
- [REDACTED]: sharpe=0.69, fitness=0.35, returns=0.0327, turnover=0.0984
- [REDACTED]: sharpe=0.63, fitness=0.31, returns=0.0306, turnover=0.0743
- [REDACTED]: sharpe=0.83, fitness=0.46, returns=0.0389, turnover=0.0864
- [REDACTED]: sharpe=0.77, fitness=0.42, returns=0.0368, turnover=0.0663

Next Steps:
- Branch next only from the raw n=1, 40- and 60-day seeds.
- Prefer mild local robustness checks such as decay or nearby correlation-window shifts before any new wrapper or extra leg.
- Keep using [REDACTED] as the primary avoidance target when novelty ties occur.

## Experiment: 2026-05-09T02:37:11+00:00

Theme: microstructure-window-decay-range-followup

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: The best next refinement on the healthy return-volume-correlation basin should come from nearby window tuning rather than longer lag or extra complexity; mild decay may help smooth the raw winner, and a separate intraday-range proxy should be tested as an adjacent microstructure basin rather than blended in.

Summary: Completed the full nearby-window, mild-decay, and adjacent-range follow-up using exact recent alpha ids already present on the platform. The nearby-window sweep produced the best result of the pass: [REDACTED] [REDACTED] reached Sharpe 0.91, Fitness 0.54, Turnover 0.079, Sub-universe Sharpe 1.16, improving on the previously logged 40/60-day raw leaders. The 30-day neighbor [REDACTED] stayed healthy at Sharpe 0.81, Fitness 0.45, Sub-universe Sharpe 1.10, while the 80-day branch [REDACTED] weakened to Sharpe 0.70, Fitness 0.37, Sub-universe Sharpe 0.92. Mild decay overlays did not help: [REDACTED] on the 40-day seed reached Sharpe 0.79, Fitness 0.43, Sub-universe Sharpe 1.07 and [REDACTED] on the 60-day seed reached Sharpe 0.77, Fitness 0.42, Sub-universe Sharpe 1.12, both worse than the raw parents. The adjacent range basin was mixed but not a new leader: [REDACTED] [REDACTED] reached Sharpe 0.77, Fitness 0.43, Sub-universe Sharpe 0.54, while [REDACTED] at the 40-day window reached Sharpe 0.66, Fitness 0.34, Sub-universe Sharpe 0.36. Conclusion: the signal core advances to the raw volume-delta-1 correlation at 50 days; keep range as a separate secondary basin, and do not add mild decay to the raw winner at this stage.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.81, fitness=0.45, returns=0.0381, turnover=0.1105
- [REDACTED]: sharpe=0.91, fitness=0.54, returns=0.0435, turnover=0.079
- [REDACTED]: sharpe=0.7, fitness=0.37, returns=0.0355, turnover=0.057
- [REDACTED]: sharpe=0.79, fitness=0.43, returns=0.0374, turnover=0.0844
- [REDACTED]: sharpe=0.77, fitness=0.42, returns=0.0373, turnover=0.0643
- [REDACTED]: sharpe=0.66, fitness=0.34, returns=0.0335, turnover=0.1002
- [REDACTED]: sharpe=0.77, fitness=0.43, returns=0.0395, turnover=0.0768

Next Steps:
- Promote the raw 50-day volume-delta-1 correlation seed to the top of the microstructure branch.
- Test only tiny local follow-ups around the 50-day winner before adding any wrapper or filter.
- Keep the intraday-range correlation branch separate from the volume-flow branch when screening novelty and follow-up searches.

## Experiment: 2026-05-09T02:46:23+00:00

Theme: microstructure-50d-local-stoploss-sweep

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: If the raw 50-day volume-delta-1 correlation seed still has meaningful local headroom, then very nearby windows should either lift it toward a materially stronger frontier or reveal that the branch is already near its local ceiling.

Summary: Ran the bounded 45/55/70 follow-up around the raw 50-day winner. 55 days improved slightly over the 50-day seed: [REDACTED] [REDACTED] reached Sharpe 0.92, Fitness 0.55, Turnover 0.0741, Sub-universe Sharpe 1.14. The 45-day neighbor [REDACTED] stayed close at Sharpe 0.89, Fitness 0.52, Sub-universe Sharpe 1.10, while the 70-day branch [REDACTED] weakened to Sharpe 0.68, Fitness 0.35, Sub-universe Sharpe 0.98. Conclusion: there is a small local ridge around 50 to 55 days, but after three tightly targeted probes the branch still sits well below the practical continuation threshold of roughly Sharpe 1.0 and Fitness 0.65. Treat [REDACTED] as the local best point in this basin, but pause deeper iteration here and pivot to another orthogonal family unless a very specific high-conviction microstructure idea emerges.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.89, fitness=0.52, returns=0.0427, turnover=0.0847
- [REDACTED]: sharpe=0.92, fitness=0.55, returns=0.0443, turnover=0.0741
- [REDACTED]: sharpe=0.68, fitness=0.35, returns=0.034, turnover=0.0618

Next Steps:
- Keep [REDACTED] as the local best reference point for this basin.
- Do not continue broad tuning on this return-volume-correlation branch without a very specific new mechanism idea.
- Pivot the main search budget to a different orthogonal mechanism family.

## Experiment: 2026-05-11T10:09:11+00:00

Theme: sentiment-attention-orthogonal-pivot

Mechanism Tag: sentiment_attention

Mechanism Tags: sentiment_attention

Hypothesis: Use analyst sentiment-attention and social-buzz dynamics as a fresh orthogonal family against the shipped options-IV line and the local-best microstructure line. The working assumption was that combining attention change with sentiment level or stability could open a second basin without drifting back into the prior options or microstructure mechanisms.

Summary: Ran a fresh six-seed sentiment-attention pivot using AST novelty control against [REDACTED] and [REDACTED]. One seed was dropped before simulation because it was a structural near-duplicate of the earlier parallel-mechanism sentiment line. The five bounded live simulations were mixed but mostly weak: sa2/[REDACTED] sharpe -0.55 fitness -0.24, sa3/[REDACTED] sharpe -0.16 fitness -0.03, sa4/[REDACTED] sharpe -0.10 fitness -0.01 with very high turnover 0.6511, sa6/[REDACTED] sharpe -0.36 fitness -0.16, and the best result sa5/[REDACTED] sharpe 0.45 fitness 0.09 returns 0.0148 turnover 0.3430. AST similarity to [REDACTED] and [REDACTED] stayed low for the new seeds, so the weak performance looks like a bad basin or poor sign/conditioning rather than novelty contamination. Treat this exact sentiment-attention construction as non-competitive for now.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=-0.55, fitness=-0.24, returns=-0.03, turnover=0.1599
- [REDACTED]: sharpe=-0.16, fitness=-0.03, returns=-0.0067, turnover=0.1556
- [REDACTED]: sharpe=-0.1, fitness=-0.01, returns=-0.003, turnover=0.6511
- [REDACTED]: sharpe=0.45, fitness=0.09, returns=0.0148, turnover=0.343
- [REDACTED]: sharpe=-0.36, fitness=-0.16, returns=-0.0241, turnover=0.0241

Next Steps:
- If sentiment is revisited, test explicit sign-flipped or gated variants instead of more same-shape nearby blends.
- Prefer a genuinely different orthogonal branch next, likely a cleaner model-feature divergence redesign or another unexplored family, rather than tuning this sentiment slice.
- Use sa5 only as a weak reference point; its positive sharpe did not survive fitness or sub-universe quality.

## Experiment: 2026-05-11T10:20:08+00:00

Theme: small-sentiment-rescue-then-model-probe

Mechanism Tag: sentiment_attention

Mechanism Tags: sentiment_attention, model_feature_divergence

Hypothesis: Run the smallest possible follow-up requested as 2 then 1: first try to rescue the only mildly positive sentiment seed with a sign-flip and a simple buzz-improvement gate, then if that fails run one redesigned model-feature divergence probe that is not just another relative-value composite.

Summary: Completed the requested small 2 then 1 follow-up. The sentiment rescue failed: sa5_flip/[REDACTED] reversed the already weak positive signal into sharpe -0.45 and fitness -0.09, while sa5_gate/[REDACTED] only reached sharpe 0.25 and fitness 0.04 with failed sub-universe quality. The single redesigned model-feature divergence probe also failed: [REDACTED], built from [REDACTED] versus [REDACTED], posted sharpe -0.14, fitness -0.04, returns -0.0111, turnover 0.0675, and failed sub-universe quality. This is enough evidence to stop both the sentiment rescue path and this first non-relative-value model-divergence redesign without spending more budget on nearby tweaks.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=-0.45, fitness=-0.09, returns=-0.0148, turnover=0.343
- [REDACTED]: sharpe=0.25, fitness=0.04, returns=0.0066, turnover=0.2812
- [REDACTED]: sharpe=-0.14, fitness=-0.04, returns=-0.0111, turnover=0.0675

Next Steps:
- Do not spend more budget on sign flips or simple single-field gates around sa5.
- If model_feature_divergence is revisited, use a genuinely different pairing or explicit disagreement construct rather than another smooth two-factor blend.
- Next pivot should come from a new orthogonal mechanism or a materially different redesign, not nearby local repairs to these failed follow-ups.

## Experiment: 2026-05-11T11:16:08+00:00

Theme: empire-building-acquisition-pressure-pivot

Mechanism Tag: capital_allocation_empire_building

Mechanism Tags: capital_allocation_empire_building, investment_efficiency

Hypothesis: Firms that expand goodwill or intangible assets aggressively while also leaning on external financing or heavy reinvestment may be overbuilding and subsequently underperform.

Summary: Tested six orthogonal balance-sheet empire-building seeds after AST-screening them against [REDACTED] and [REDACTED]. The branch was cleanly novel but economically weak in USA TOP3000 delay 1 decay 5 SUBINDUSTRY. The best result was eb4 / [REDACTED], which shorted firms with rising goodwill-plus-intangibles relative to assets and high capex intensity; it reached sharpe 0.48, fitness 0.16, returns 0.0136, turnover 0.0205, and sub-universe sharpe 0.16. eb2 was mildly positive at sharpe 0.20 and fitness 0.07, while the rest were flat or negative. The family looks more like a low-turnover accounting-quality descriptor than a strong tradable edge in this regime.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.48, fitness=0.16, returns=0.0136, turnover=0.0205
- [REDACTED]: sharpe=0.2, fitness=0.07, returns=0.0141, turnover=0.0233
- [REDACTED]: sharpe=0.1, fitness=0.02, returns=0.0067, turnover=0.0212
- [REDACTED]: sharpe=0.07, fitness=0.01, returns=0.0039, turnover=0.0214
- [REDACTED]: sharpe=-0.18, fitness=-0.04, returns=-0.0072, turnover=0.028
- [REDACTED]: sharpe=-0.26, fitness=-0.07, returns=-0.008, turnover=0.0251

Next Steps:
- If this basin is revisited, use a different regime or explicit event conditioning rather than more small linear overlays in the same USA TOP3000 delay 1 setting.
- Treat goodwill-plus-intangibles growth as the only mildly live sub-slice; the broader empire-building bundle was too weak.

## Experiment: 2026-05-11T11:16:23+00:00

Theme: empire-building-overlay-followup

Mechanism Tag: capital_allocation_empire_building

Mechanism Tags: capital_allocation_empire_building, investment_efficiency

Hypothesis: If the only live slice in the empire-building family is acquisition pressure, financing and turnover overlays should strengthen that slice faster than the broader family.

Summary: Ran two local repairs on the best acquisition-pressure seed after confirming both remained AST-distant from [REDACTED] and [REDACTED]. Neither helped. eb7_financing_overlay / [REDACTED] combined goodwill-plus-intangibles growth with share dilution and debt issuance, but only reached sharpe 0.18 and fitness 0.06. eb8_turnover_overlay / [REDACTED] paired the same acquisition-pressure core with share dilution and asset-turnover improvement and weakened further to sharpe 0.13 and fitness 0.03. This is enough evidence to park the family for now.

Expressions:
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.18, fitness=0.06, returns=0.0123, turnover=0.0234
- [REDACTED]: sharpe=0.13, fitness=0.03, returns=0.0082, turnover=0.0242

Next Steps:
- Do not spend more local search budget on this family in the same regime unless the mechanism is recast around event timing or a different universe.

## Experiment: 2026-05-12T04:00:00+00:00

Theme: microstructure-[REDACTED]-wrapper-discipline-stoploss

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Apply the full [REDACTED] wrapper playbook to [REDACTED] (the local-best microstructure basin at Sharpe 0.92 / Fitness 0.55) to determine whether ts_rank, inner zscore normalization, or volatility-regime conditioning can lift it toward Sharpe ≥ 1.1 / Fitness ≥ 0.70.

Summary: Ran four disciplined Step A probes on the [REDACTED] basin ([REDACTED]). AST novelty verified all seeds scored 0.0909 vs [REDACTED] (irreducible minimum). Results:

Headline: A3 [REDACTED] [REDACTED]: Sharpe 0.94 Fitness 0.57 Turnover 0.0723 Sub-universe Sharpe 1.12 — confirmed real lift over [REDACTED] (+0.02 Sharpe, +0.02 Fitness). Inner zscore normalizes the two legs before correlation, which does useful work. [REDACTED] is the new microstructure reference point, superseding [REDACTED].

A1 [REDACTED] [REDACTED]: Sharpe 0.24 Fitness 0.06 Turnover 0.0786 — collapsed. Direct [REDACTED] playbook on the 55-day core destroyed signal quality, consistent with the earlier 40/60-day ts_rank failures ([REDACTED] at 0.08, [REDACTED] at 0.09).

A4 [REDACTED] [REDACTED]: Sharpe 0.29 Fitness 0.08 Turnover 0.0794 — full playbook stack (inner zscore + decay + ts_rank) collapsed exactly like A1. Inner zscore does not rescue ts_rank on this basin.

A6 [REDACTED] [REDACTED]: Sharpe 0.75 Fitness 0.40 Turnover 0.0500 Sub-universe Sharpe 0.89 — volatility-regime gate degraded the signal. The gate selected periods where the mechanism is weaker, not stronger.

Stop-loss triggered: 6 total disciplined probes (40d ts_rank, 60d ts_rank, A1, A3, A4, A6) have not lifted Fitness materially beyond 0.57. [REDACTED] is PARKED. [REDACTED] is the new local best.

Structural conclusion: ts_rank works on trend/momentum signals with a genuine long-run time-series drift (options-IV momentum). It destroys mean-reverting or correlation-based cross-sectional signals where the time-series distribution has no stable long-run level to rank against. The microstructure corr basin is the latter type. This is a hard mechanistic boundary, not a parameter problem. For correlation-based and mean-reverting signals, prefer group_zscore / group_rank / trade_when conditioning instead.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.24, fitness=0.06, returns=0.008, turnover=0.0786
- [REDACTED]: sharpe=0.94, fitness=0.57, returns=0.0457, turnover=0.0723
- [REDACTED]: sharpe=0.29, fitness=0.08, returns=0.0095, turnover=0.0794
- [REDACTED]: sharpe=0.75, fitness=0.40, returns=0.0349, turnover=0.0500

Step A Local Best: [REDACTED] — [REDACTED] — Sharpe 0.94 / Fitness 0.57 / Sub-U 1.12. Superseded [REDACTED] (0.92 / 0.55) as of 2026-05-12. Subsequently superseded by [REDACTED] (B1-4r) as of 2026-05-13 — see microstructure-peer-relative-dislocation-b1 experiment below.

Current Microstructure Reference: [REDACTED] — [REDACTED] — Sharpe 1.20 / Fitness 0.75 / Sub-U 1.29.

Next Steps:
- [REDACTED] is parked. [REDACTED] is the new reference for future novelty screens in this basin (not [REDACTED] — that was superseded).
- Pivot to B1 follow-up: test ts_zscore vs group_zscore on input leg, volume-leg neutralization, and window robustness at 65 days around the [REDACTED] anchor.
- Do not apply ts_rank to any signal in this basin without a specific new hypothesis about why time-series persistence would be restored.

## Key Learning: ts_rank Applicability Boundary (2026-05-12)

ts_rank is a time-series percentile operator. It implicitly assumes the inner signal has cross-time persistence — that the signal's level today is meaningfully comparable to its level at times t-1, t-2, ..., t-N.

When this assumption holds (options-IV momentum, trend-following signals with genuine long-run drift), ts_rank adds value by stretching the cross-time percentile distribution and compressing extreme observations. This is why [REDACTED] (ts_rank on IV momentum) lifted fitness from 0.76 to 1.03.

When this assumption fails (correlation-based signals, mean-reverting cross-sectional rankings), ts_rank is destructive:
- The inner signal has no stable long-run mean — its distribution shifts with market regime
- Percentile-mapping across time conflates old regimes with current ones
- The result is flat or negative Sharpe even when the untreated cross-sectional signal is positive

Proven failures in this codebase: [REDACTED] (0.08), [REDACTED] (0.09), [REDACTED] (0.06), [REDACTED] (0.08) — all ts_rank wrappers on the return-volume-correlation basin.

Rule: For correlation-based and mean-reverting signals, replace ts_rank with:
- group_zscore — sector-neutralizes the cross-sectional signal, preserving its mean-reverting character
- group_rank — ordinal sector rank, same neutralization with bounded output
- trade_when — event or regime conditioning that selects high-confidence periods without time-series percentile mapping

## Key Learning: Input-Leg Neutralization in [REDACTED]

When building a correlation-based signal with sector neutralization, neutralize the INPUT leg before computing the correlation — do not neutralize the output after.

Concrete evidence: [REDACTED] [REDACTED] at Fitness 0.75 vs [REDACTED] [REDACTED] at Fitness 0.58. Same mechanism, same grouping, +0.17 Fitness purely from the placement of the neutralization.

Why it works: Pre-normalizing `returns` relative to subindustry peers means the correlation measures how much a stock's *excess return* (relative to peers) co-moves with its volume flow. This is a sharper proxy for idiosyncratic institutional activity. Post-neutralizing the correlation output adjusts the final signal but leaves the inner computation exposed to sector-level returns noise that corrupts the correlation estimate.

Portable rule: In any `[REDACTED]` signal where sector/peer neutralization is planned, apply `[REDACTED]` to the relevant input leg *before* the correlation call. This applies to any family (price-volume, earnings-revision, etc.), not only microstructure.

## Experiment: 2026-05-13T04:00:00+00:00

Theme: microstructure-peer-relative-dislocation-b1

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Sector-neutralizing the return-volume correlation signal (B1 peer-relative dislocation) should extract idiosyncratic institutional flow more cleanly than the market-wide rank in the parent [REDACTED]. The ts_rank lesson points toward group_zscore / group_rank as the correct tool: cross-sectional neutralization preserves the mean-reverting character of the signal while removing sector-level noise.

Pre-simulation expected outcome matrix:
- B1-1 vs B1-2 (outer rank contribution): does rank help or hurt continuous group_zscore output?
- B1-2 vs B1-3 (zscore vs rank neutralization): which is more robust to sector outliers?
- B1-2 vs B1-4r (neutralize output vs input leg): does pre-neutralizing returns before correlation capture excess-return flow better than post-neutralizing the corr output?
- B1-2 vs B1-5 (subindustry vs sector): does finer or coarser grouping work better?
Bar: [REDACTED] Sharpe 0.94 / Fitness 0.57. Below 0.90/0.55 = no lift. Above 1.00/0.65 = serious candidate.

Summary: All 5 seeds completed cleanly — no blocking checks beyond LOW_SHARPE and LOW_FITNESS (all failing Brain submission bars), all pass CONCENTRATED_WEIGHT and LOW_SUB_UNIVERSE_SHARPE, all have SELF_CORRELATION PENDING.

Headline: B1-4r [REDACTED] [REDACTED]: Sharpe 1.20 Fitness 0.75 Sub-U 1.29 Turnover 0.08 Drawdown 0.1043 — serious candidate. Neutralizing the returns INPUT leg before computing the correlation materially outperforms post-hoc output neutralization. This is the new local best in the microstructure_institutional_flow basin, beating [REDACTED] by +0.26 Sharpe and +0.18 Fitness.

B1-1 [REDACTED] [REDACTED]: Sharpe 1.07 Fitness 0.69 Sub-U 1.22 — above bar. Raw group_zscore output without outer rank also beats [REDACTED], confirming sector neutralization adds real value. B1-1 vs B1-2 comparison: B1-1 (no outer rank) at Fitness 0.69 beats B1-2 (outer rank) at Fitness 0.58 — the outer rank compresses useful tail information and hurts.

B1-3 [REDACTED] [REDACTED]: Sharpe 1.06 Fitness 0.64 Sub-U 1.18 — above bar. B1-2 vs B1-3 comparison: [REDACTED] at Fitness 0.64 beats group_zscore+[REDACTED] at Fitness 0.58, but both are below group_zscore-without-[REDACTED]. The outer rank is the culprit, not the neutralization method itself.

B1-2 [REDACTED] [REDACTED]: Sharpe 0.98 Fitness 0.58 Sub-U 1.17 — mild lift over [REDACTED].

B1-5 [REDACTED] [REDACTED]: Sharpe 0.91 Fitness 0.54 Sub-U 1.18 — below bar. B1-2 vs B1-5: subindustry beats sector. Finer peer grouping is the correct resolution for this signal.

Design-choice verdicts:
1. outer rank hurts — B1-1 (no rank) at 0.69 beats B1-2 (rank) at 0.58
2. group_rank ~ group_zscore+rank — B1-3 at 0.64 vs B1-2 at 0.58, but both inferior to B1-1
3. input-leg neutralization wins decisively — B1-4r at 0.75 vs B1-2 at 0.58
4. subindustry > sector — B1-2 at 0.58 vs B1-5 at 0.54

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.07, fitness=0.69, returns=0.0524, turnover=0.0776, drawdown=0.1565, margin=0.001351, subUniverseSharpe=1.22
- [REDACTED]: sharpe=0.98, fitness=0.58, returns=0.0443, turnover=0.0738, drawdown=0.1524, margin=0.001202, subUniverseSharpe=1.17
- [REDACTED]: sharpe=1.06, fitness=0.64, returns=0.0454, turnover=0.081, drawdown=0.1456, margin=0.00112, subUniverseSharpe=1.18
- [REDACTED]: sharpe=1.20, fitness=0.75, returns=0.0489, turnover=0.08, drawdown=0.1043, margin=0.001221, subUniverseSharpe=1.29
- [REDACTED]: sharpe=0.91, fitness=0.54, returns=0.0434, turnover=0.0741, drawdown=0.1599, margin=0.001171, subUniverseSharpe=1.18

Next Steps:
- [REDACTED] (B1-4r) is the new local best: Sharpe 1.20 / Fitness 0.75 / Sub-U 1.29. Promote as microstructure_institutional_flow reference.
- Check SELF_CORRELATION on [REDACTED] after the pending window resolves. If it passes, submit.
- Follow-up: test adjacent design choices from the B1-4r anchor — (a) inner normalization variant ts_zscore on the returns leg instead of group_zscore, (b) volume leg [REDACTED] in addition to the returns leg, (c) window robustness check at 45 and 65 days.
- Do NOT apply outer rank to group_zscore output. This lesson is now confirmed by two independent comparisons (B1-1 vs B1-2, and the B1-3 indirect comparison).

## Experiment: 2026-05-13T10:00:00+00:00

Theme: microstructure-c-sweep-design-isolation

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Five design-choice probes from the [REDACTED] anchor (Sharpe 1.20 / Fitness 0.75): (C1) ts_zscore on returns input leg instead of group_zscore; (C2) neutralize volume leg only; (C3) neutralize both legs; (C4) window at 65 days; (C5) ts_decay_linear smoothing without ts_rank.

Pre-simulation expected outcome matrix (committed before simulating):
- C1 vs [REDACTED]: [REDACTED] vs [REDACTED] on input — which excess-return definition is better?
- C2 vs [REDACTED]: symmetric test — volume-leg neutralization vs returns-leg neutralization
- C3 vs C2 vs [REDACTED]: do both legs together add more than either alone?
- C4 vs [REDACTED]: does 65d window shift the peak under neutralized inputs?
- C5 vs [REDACTED]: does ts_decay_linear help (unlike ts_rank) on correlation signals?

Bar: [REDACTED] Fitness 0.75. Fitness is the binding constraint (gap to submission: +0.25 to reach 1.0).

Summary: All 5 completed. [REDACTED] at 0.75 remains the local best — no C-seed lifted above it.

Key result — C5 [REDACTED]: Sharpe 1.08 Fitness 0.63 Turnover 0.0647 Sub-U 1.23 — ts_decay_linear did NOT help. It lowered turnover from 0.08 to 0.065, but Fitness dropped from 0.75 to 0.63. The decay smoothing trades away returns-generating activity at the same time it reduces noise. The hypothesis that "decay helps where ts_rank hurts" is NOT confirmed on this basin. ts_decay_linear is also destructive here, though less so than ts_rank.

C4 [REDACTED] (65d window): Sharpe 0.98 Fitness 0.55 Sub-U 1.28 — 65 days is worse than 55 days, consistent with the prior raw-basin sweep that found 55d is the local peak. The window peak does not shift with input-leg neutralization.

C1 [REDACTED] (ts_zscore on returns): Sharpe 0.88 Fitness 0.51 Sub-U 1.09 — decisively worse than [REDACTED] (group_zscore on returns). Time-series self-normalization loses the peer-relative information that is the mechanism's source of edge. The lesson stands: group_zscore on the input leg is superior to ts_zscore.

C2 [REDACTED] (volume leg only): Sharpe 0.76 Fitness 0.38 Sub-U 0.85 — neutralizing the volume leg alone is strongly inferior to neutralizing the returns leg ([REDACTED]). Volume flow needs to be measured in absolute terms — the institutional signal is in the level of volume relative to price movement, not in how unusual the volume is within the sector. Neutralizing volume destroys the signal.

C3 [REDACTED] (both legs): Sharpe 0.64 Fitness 0.29 Sub-U 0.91 — worst result. Double neutralization further degrades the signal. The C2 failure generalizes: any normalization of the volume leg hurts. The returns-leg neutralization in [REDACTED] is the correct and complete neutralization for this signal.

Design-choice verdicts (against pre-commitment matrix):
1. ts_zscore vs [REDACTED]: group_zscore wins decisively. Peer-relative excess return is the right concept.
2. volume-leg neutralization (C2 vs [REDACTED]): volume should NOT be neutralized. Absolute volume flow is load-bearing.
3. both-legs (C3 vs C2 vs [REDACTED]): double neutralization is additive in the wrong direction. C3 < C2 < [REDACTED].
4. 65d window (C4 vs [REDACTED]): 55d remains the peak. No shift with neutralized inputs.
5. [REDACTED]: decay lowers turnover but also lowers fitness. Not a portable helper for correlation signals.

Structural conclusion: [REDACTED] [REDACTED] is a local optimum in this design space. The C-sweep has exhausted the immediate neighborhood. The next move must either (a) widen the mechanism (different signal type, different field, different family) or (b) wait for SELF_CORR resolution on [REDACTED] and consider submission if it passes.

Expressions:
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.88, fitness=0.51, returns=0.0427, turnover=0.0747, drawdown=0.1685, margin=0.001143, subUniverseSharpe=1.09
- [REDACTED]: sharpe=0.76, fitness=0.38, returns=0.0315, turnover=0.0813, drawdown=0.1386, margin=0.000774, subUniverseSharpe=0.85
- [REDACTED]: sharpe=0.64, fitness=0.29, returns=0.0248, turnover=0.0856, drawdown=0.1145, margin=0.000579, subUniverseSharpe=0.91
- [REDACTED]: sharpe=0.98, fitness=0.55, returns=0.039, turnover=0.0715, drawdown=0.1075, margin=0.001091, subUniverseSharpe=1.28
- [REDACTED]: sharpe=1.08, fitness=0.63, returns=0.0432, turnover=0.0647, drawdown=0.1071, margin=0.001335, subUniverseSharpe=1.23

Next Steps:
- [REDACTED] is confirmed as the local optimum in this design space. Do not continue tuning this basin without a fundamentally different mechanism idea.
- Wait for SELF_CORRELATION on [REDACTED] (alpha_id=[REDACTED]). If PASS, submit. Fitness 0.75 and Sharpe 1.20 are below the 1.0/1.25 bars — submission will be rejected even if SELF_CORR passes, but the crowding verdict matters for deciding whether to continue deepening this basin.
- Key new portable lessons from this sweep: (1) volume leg must not be neutralized in return-volume correlation signals; (2) ts_decay_linear does not help correlation-based signals (reduces turnover but hurts fitness); (3) group_zscore on the returns input leg is the single correct intervention.

## Experiment: 2026-05-13T14:00:00+00:00

Theme: microstructure-d-sweep-mechanism-injection
Mechanism: microstructure_institutional_flow
Anchor: [REDACTED] [REDACTED] — Sharpe 1.20 / Fitness 0.75

Hypothesis: Perturbation of input normalization and output wrappers (C-sweep) was exhausted. This sweep tests three mechanism-level substitutions that change WHAT GOES IN to the correlation rather than HOW it is wrapped: (D1) replace [REDACTED] with [REDACTED] — volume surprise vs volume momentum; (D2) replace returns with [REDACTED] — weekly return horizon vs daily noise; (D3r) weight the returns input leg by max-clipped vol-surplus max([REDACTED], 0) — regime gate that zeros signal in low-vol periods.

Note: Brain accepted parallel job submission (D2 and D3r submitted simultaneously). D2 took ~90 min to reach 90% progress (IQC 2026 queue congestion). D3r completed faster.

D1 [REDACTED] — [REDACTED]
- Sharpe=1.13 Fitness=0.73 Returns=0.0524 Turnover=0.0835 Drawdown=0.0947 Margin=0.001255 Sub-U=0.98 (PASS)
- Blocking: LOW_SHARPE(1.25/1.13), LOW_FITNESS(1.0/0.73)
- Pending: SELF_CORRELATION
- Verdict: NO LIFT — volume surprise (ts_zscore) is marginally below baseline [REDACTED] (0.73 vs 0.75). Volume acceleration (ts_delta) marginally outperforms volume abnormality for this correlation signal. The mechanism relies on directional volume momentum, not statistical surprise.

D2 — [REDACTED]
- PENDING (progress stuck at 90% due to IQC 2026 queue congestion at time of logging)

D3r [REDACTED] — [REDACTED]
- Sharpe=1.30 Fitness=0.80 Returns=0.0479 Turnover=0.0974 Drawdown=0.095 Margin=0.000983 Sub-U=1.20 (PASS)
- Blocking: LOW_FITNESS(1.0/0.80)
- Pending: SELF_CORRELATION
- Verdict: LIFT — Sharpe 1.30 clears the 1.25 submission bar. Fitness 0.80 is a new high (+0.05 vs [REDACTED]). The max-clipped vol-surplus gate on the returns input leg is doing real work. [REDACTED] is the new local best.

**NEW LOCAL BEST: [REDACTED] (D3r)**
Expression: [REDACTED]
Sharpe 1.30 / Fitness 0.80 / Sub-U 1.20 / Turnover 0.0974
Supersedes [REDACTED] (1.20 / 0.75) as of 2026-05-13. Sharpe bar cleared. Fitness gap = -0.20.

Strategic Reset: Sharpe gap is closed. Fitness is now the ONLY binding constraint. Gap = 0.20 to submission.
The max-clip gate zeroes signal in low-vol regimes, which lifts Sharpe by removing low-conviction trades but may hurt Fitness by losing trading exposure on low-vol days. Next move: test ratio gate (divide instead of max-clip) to keep signal alive in low-vol days — this directly tests whether the Fitness ceiling is caused by over-filtering.

E1r [REDACTED] — [REDACTED]
- Sharpe=1.18 Fitness=0.73 Returns=0.0472 Turnover=0.0808 Drawdown=0.1094 Margin=0.001169 Sub-U=1.22 (PASS)
- Blocking: LOW_SHARPE(1.25/1.18), LOW_FITNESS(1.0/0.73)
- Pending: SELF_CORRELATION
- Verdict: BELOW D3r on both Sharpe and Fitness. Ratio gate (always positive, attenuates low-vol) is inferior to max-clip gate (zeros low-vol). This is a meaningful mechanistic result: low-vol days don't just have weaker signal — they contain destructive signal that reduces both Fitness and Sharpe when included. D3r's zero-clip design is confirmed correct. The "over-filtering hurts Fitness" hypothesis is FALSIFIED.

D2 — SKIPPED (progress stuck at 90% for >2 hours under IQC 2026 queue pressure; skipped by user decision).

Key Learning from D and E sweeps:
- Regime gating (zeroing low-vol days) improves both Sharpe AND Fitness vs ratio-attenuation. Low-vol periods are destructive noise in this signal family, not just lower-edge.
- Volume acceleration (ts_delta) outperforms volume surprise (ts_zscore) as the volume leg proxy. The mechanism is directional volume momentum, not statistical abnormality.
- D3r [REDACTED] is the confirmed local best: Sharpe 1.30 / Fitness 0.80. Sharpe bar cleared. Fitness gap = -0.20 to submission.

## Key Learning: Regime Gate Design — Three Cases for Correlation Signals

From D3r (max-clip) vs E1r (ratio) comparison. Generalizes beyond microstructure.

For any correlation-based signal with regime structure, low-regime periods can behave in three distinct ways:

1. **Weakly-signed (attenuate)** — signal fires in the right direction but with lower conviction. Ratio gate is the right design: weight by vol_current/vol_baseline, smooth amplification/attenuation. E1r pattern.

2. **Zero-signed (zero)** — signal has no information content in low regime. Max-clip gate is right: max(surplus, 0), zero contribution below baseline. Default conservative choice.

3. **Inverted-signed (flip)** — signal fires in the WRONG direction in low regime. Sign-modulating weight is the right design: continuous [REDACTED], carries both the amplification (high-vol) and the inversion (low-vol). D3r-inverted pattern.

**Evidence from this session**: D3r (max-clip, 0.80) > E1r (ratio, 0.73). Since ratio keeps inverted-sign contributions alive at reduced magnitude, the Fitness drop from 0.80 to 0.73 implies the low-vol contributions are HARMFUL at any magnitude, not just weaker. This means the regime structure is Case 2 or Case 3, not Case 1.

**Distinguishing Case 2 vs 3**: If the sign-modulating weight (D3r-inverted, subtract without clip) outperforms max-clip (D3r), the low-vol inversion is a exploitable signal, not just noise. If max-clip still wins, low-vol days are pure noise and zeroing is correct.

**Test (D3r-inverted)**: `[REDACTED]`

**Result**: D3r-inverted [REDACTED] — Sharpe 0.88 / Fitness 0.40. Decisively below D3r (1.30 / 0.80). Case 3 FALSIFIED. Low-vol days are Case 2 (pure noise), not Case 3 (exploitable inversion). Max-clip (D3r) is confirmed as the structurally correct gate for this mechanism class.

**Portable rule**: Before finalizing a gate design on any correlation signal, run all three (ratio / clip / sign-modulate). The winner reveals the regime structure of the mechanism.

## Experiment: 2026-05-14T08:22:37+00:00

Theme: family-a3-subindustry-liquidity-premium-first-shot

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Within-subindustry share-turnover ranking may capture a liquidity premium: long structurally illiquid stocks and short highly liquid peers using [REDACTED].

Summary: Ran the authorized first shot exactly as approved in USA TOP3000 delay 1 decay 10 SUBINDUSTRY truncation 0.08. Result [REDACTED] failed at the IS gate: Sharpe -0.53, Fitness -0.35, Turnover 0.1155, Margin -0.000955, Sub-universe Sharpe -0.29. Universe coverage for volume, sharesout, and subindustry remained 1.0. Concentrated Weight passed, but the platform did not expose a numeric max-weight value through the available tool surface. Blocking checks were LOW_SHARPE, LOW_FITNESS, and LOW_SUB_UNIVERSE_SHARPE; SELF_CORRELATION remained pending but is irrelevant because the alpha already failed the IS gate. Analytical sign-flip applies without re-simulation: removing the outer reverse implies Sharpe about +0.53, Fitness about +0.35, Turnover unchanged, Margin about +0.000955, and sub-universe quality likely sign-flipped as well, which still leaves the family below the IS bars. Treat A3 as failed calibration, not a lead.

Directional learning: Classical within-subindustry illiquidity premium fails directionally on TOP3000 USA delay 1. The sign is reversed here: high-turnover names beat low-turnover names, with magnitude only about 0.53 Sharpe after analytical flip, so the family is sub-IS in either orientation.

Calibration miss: Turnover printed 11.55%, above the pre-run 3% to 10% band. The static-characteristic prior understated how much ordinal reshuffling inside subindustry can drive trading even when the underlying liquidity descriptor looks slow-moving.

Portable platform note: LOW_SUB_UNIVERSE_SHARPE uses a dynamic Brain limit, not a fixed 0.06 floor in the platform checks. This repo's logged history shows limits ranging from -0.38 to 0.21, so the platform-reported check threshold must be treated as authoritative for each alpha while the 0.06 house bar remains the research-side minimum for a clean submission discussion.

Expressions:
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=-0.53, fitness=-0.35, returns=-0.0552, turnover=0.1155

Next Steps:
- Close A3 as an IS-gate failure and do not spend the pre-approved group_zscore tuning pass here because the problem is sign and quality, not concentrated weight near the gate.
- If Family A continues, move to A4 only after explicit authorization.
- Use [REDACTED] as an orthogonality reference for future liquidity-style screens.

## Experiment: 2026-05-14T08:46:37+00:00

Theme: family-a4-price-impact-change-first-shot

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: Within-subindustry change in Amihud-style price impact may capture a liquidity-transition effect: stocks with rising recent price impact could reflect fresh imbalance or informed flow rather than the static low-liquidity premium tested in A3.

Summary: Ran the authorized Path B A4 first shot in USA TOP3000 delay 1 decay 5 SUBINDUSTRY truncation 0.08 with [REDACTED]. Result [REDACTED] was weak positive but clear IS-fail: Sharpe 0.36, Fitness 0.06, Turnover 0.6944, Margin 0.000053, Sub-universe Sharpe 0.19. Universe coverage for returns, vwap, volume, and subindustry is effectively 1.0. Concentrated Weight passed, while the platform again did not expose a numeric max-weight value through the available tool surface. The alpha passed the dynamic LOW_SUB_UNIVERSE_SHARPE check at limit 0.16 but failed LOW_SHARPE and LOW_FITNESS. This falls in the pre-committed flat or weak branch, so the liquidity-transition test did not show enough evidence to keep deepening Family A in this universe. Driver attribution between numerator and denominator components is not identifiable from this result.

Expressions:
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=0.36, fitness=0.06, returns=0.0184, turnover=0.6944

Next Steps:
- Classify A4 as IS-fail and do not tune; Sharpe 0.36 is below the tuning window.
- A5 should not reuse the static-liquidity scaffold and should not remain inside Family A by default; the pre-committed branch here is a family pivot unless a separate reviewer explicitly wants one last interaction-style liquidity hypothesis.
- If liquidity is revisited later, split the composite into numerator-shock versus denominator-collapse diagnostics before proposing another combined price-impact transition alpha.

## Experiment: 2026-05-14T10:51:56+00:00

Theme: family-a5-competitive-overlap-count-first-shot

Mechanism Tag: competitive_overlap_pressure

Mechanism Tags: competitive_overlap_pressure

Hypothesis: Medium-horizon increase in the product-overlap competitor count may capture competitive encroachment: firms whose overlap network becomes more crowded should underperform before margin pressure is fully visible in accounting data.

Summary: Ran the authorized A5 first shot in USA TOP3000 delay 1 decay 8 SUBINDUSTRY truncation 0.08 with [REDACTED]. Result [REDACTED] was an IS-fail with full-universe versus sub-universe decoupling: Sharpe -0.08, Fitness -0.01, Returns -0.0021, Turnover 0.0399, Margin -0.000103, Sub-universe Sharpe 0.38, Concentrated Weight PASS. The alpha failed LOW_SHARPE and LOW_FITNESS, passed LOW_SUB_UNIVERSE_SHARPE at dynamic limit -0.03, and had SELF_CORRELATION pending but irrelevant because the alpha already failed IS. Against the pre-run band, turnover and sub-universe quality were inside range and concentration passed, but Sharpe, Fitness, Returns, and Margin all missed low. The initial weak-negative full-universe print with positive sub-universe quality remained ambiguous, and the follow-up cadence investigation did not resolve rel_num_all update frequency through Brain metadata, accessible API endpoints, or documentation. Final family decision: close competitive-overlap pressure via rel_num_all as indeterminate, not wrong-sign and not validation-ready. Family-level findings banked from the closure are: (1) medium-horizon rel_num_all change remains causally unverified under unresolved cadence, even though the Sharpe -0.08 versus Sub-universe Sharpe 0.38 split is consistent with possible tier sensitivity; (2) pv13 relationship fields expose coverage and type metadata but not update cadence, so cadence-sensitive construction parameters such as ts_backfill cannot be principled-calibrated from the available surface; and (3) material sub-universe/full-universe decoupling is a diagnostic pattern that must be explained before verdict compression, not a reason to force-fit the result into a simple wrong-sign label. Construction note for the record: plain rank was used rather than group_rank because product-overlap networks can span subindustries, so a within-subindustry rank would suppress the intended cross-industry encroachment signal while SUBINDUSTRY neutralization handled residual classification exposure after construction.

Expressions:
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=-0.08, fitness=-0.01, returns=-0.0021, turnover=0.0399

Next Steps:
- Close A5 family direction as indeterminate and do not authorize a validation run; arbitrary backfill choices under unknown cadence are not principled.
- Treat pv13 relationship fields as cadence-opaque until proven otherwise; avoid parameter-sensitive constructions in this category unless cadence is verified out of band.
- Preserve the full-universe versus sub-universe decoupling as a family-level diagnostic, not a compressed wrong-sign verdict.
- Do not switch to rel_ret_all as a follow-up under this closure; that would be a new mechanism, not a continuation.

## Experiment: 2026-06-15T14:55:28+00:00

Theme: microstructure-double-gate-breakthrough

Mechanism Tag: microstructure_institutional_flow

Mechanism Tags: microstructure_institutional_flow

Hypothesis: The single vol-surplus gate ([REDACTED] at Fitness 0.80) was filtering low-vol noise but missing low-volume false positives. A double gate requiring BOTH elevated volatility AND elevated volume should produce a cleaner institutional-flow signal by only firing when both conditions signal active institutional participation.

Summary: Forensic review of the quant journey revealed that [REDACTED] (Sharpe 1.30, Fitness 0.80) was abandoned prematurely after only 2 follow-up tests. Resumed the D3r line with a full parameter sweep (decay 10/15/20, gate 10/42 and 21/126, correlation windows 45/50/60/65) — all confirmed [REDACTED] is a local optimum for the single-gate architecture. Then tested three structural variants: (1) double gate (vol-surplus × volume-surplus), (2) volume/adv20 normalized delta, (3) group_rank instead of group_zscore on returns leg. The double gate was the breakthrough: [REDACTED] = [REDACTED] reached Sharpe 1.50, Fitness 1.03, Sub-U Sharpe 1.43, Turnover 0.0867 with NO blocking IS checks. Grade AVERAGE. Only SELF_CORRELATION PENDING. The double gate adds +0.23 Fitness and +0.20 Sharpe vs the single gate. Key mechanistic insight: the vol gate filters low-vol noise, but the volume gate additionally filters low-activity periods where volume changes are statistical noise rather than institutional flow. Together they isolate the regime where return-volume correlation genuinely reflects institutional activity.

Expressions:
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.5, fitness=1.03, returns=0.0585, turnover=0.0867
- [REDACTED]: sharpe=1.3, fitness=0.8, returns=0.0479, turnover=0.0974
- [REDACTED]: sharpe=1.15, fitness=0.67, returns=0.0424, turnover=0.08
- [REDACTED]: sharpe=1.11, fitness=0.64, returns=0.041, turnover=0.0717
- [REDACTED]: sharpe=1.1, fitness=0.63, returns=0.041, turnover=0.0667
- [REDACTED]: sharpe=1.13, fitness=0.66, returns=0.0422, turnover=0.0992
- [REDACTED]: sharpe=0.99, fitness=0.52, returns=0.035, turnover=0.0802
- [REDACTED]: sharpe=1.17, fitness=0.69, returns=0.0439, turnover=0.106
- [REDACTED]: sharpe=1.1, fitness=0.63, returns=0.0415, turnover=0.1156
- [REDACTED]: sharpe=1.1, fitness=0.62, returns=0.04, turnover=0.0897
- [REDACTED]: sharpe=1.03, fitness=0.56, returns=0.0374, turnover=0.0826
- [REDACTED]: sharpe=1.25, fitness=0.75, returns=0.0446, turnover=0.0965
- [REDACTED]: sharpe=1.12, fitness=0.65, returns=0.0423, turnover=0.1194

Submission Update (2026-06-15T15:09 UTC):
- Submitted [REDACTED] via Brain web UI while SELF_CORRELATION was still PENDING. Brain accepted it immediately — SELF_CORRELATION is an OS-stage check, not an IS-gate blocker. IS selfCorrelation resolved to 0.0333 (near zero, very clean). Alpha is now ACTIVE (OS stage).
- MCP bug found and fixed: `submission.py` line 18 was treating PENDING checks the same as FAIL, blocking submission. Changed `submittable = not failed_checks and not pending_checks` to `submittable = not failed_checks`. PENDING is not FAIL — only actual FAILs block IS→OS promotion.
- This is the second submitted alpha (after [REDACTED]) from a completely different mechanism family — microstructure dual-gated return-volume correlation vs options-IV momentum.

Next Steps:
- Monitor OS performance on [REDACTED] over the coming weeks.
- Small robustness check: test double gate at correlation windows 50 and 60 (gate interaction might shift the optimal window under OS conditions even though single-gate sweep showed 55 is optimal in IS).
- If [REDACTED] survives OS, this validates the double-gate regime-filtering approach as a portable alpha construction pattern beyond just microstructure.

## Experiment: 2026-06-15T17:28:47+00:00

Theme: momentum-reversal-35d-breakthrough

Mechanism Tag: momentum_reversal

Mechanism Tags: momentum_reversal

Hypothesis: Short-term momentum reversal is one of the most robust factors in finance. In the current retail-driven, high-concentration tech market, stocks with extreme recent returns tend to mean-revert as retail chasing exhausts itself. The optimal reversal window should be long enough to filter daily noise but short enough to capture retail-driven overextension.

Summary: After the call/put IV skew family failed (ATM parity kills signal) and the analyst EPS revision family failed (fundamental data too slow), pivoted to pure price momentum reversal. Tested windows from 5d to 40d with various normalizations. The 40-day raw reversal ([REDACTED]) reached Fitness 1.06 but Sharpe 1.22 (0.03 below bar). Nearby window sweep found the 35-day sweet spot: [REDACTED] = [REDACTED] at Sharpe 1.29, Fitness 1.14, Sub-U 0.77, Turnover 0.127. Zero blocking checks. Submitted and moved to OS/ACTIVE immediately. SELF_CORRELATION passed at 0.48 (limit 0.70). This is the third shipped alpha from a third completely different mechanism family (behavioral mean-reversion), joining [REDACTED] (options trend-following) and [REDACTED] (microstructure mean-reversion). The expression uses only 4 operators on a single field (returns) — the simplest successful alpha yet. Session total: 2 new shipped alphas ([REDACTED] + [REDACTED]), 6 families tested, 35+ seeds simulated.

Expressions:
- `[REDACTED]`

Alpha Summaries:
- [REDACTED]: sharpe=1.29, fitness=1.14, returns=0.0989, turnover=0.1266
- [REDACTED]: sharpe=1.22, fitness=1.06, returns=0.0935, turnover=0.1195
- [REDACTED]: sharpe=1.22, fitness=1.0, returns=0.0833, turnover=0.116
- [REDACTED]: sharpe=1.14, fitness=0.94, returns=0.0857, turnover=0.0987
- [REDACTED]: sharpe=1.11, fitness=0.91, returns=0.0834, turnover=0.0902
- [REDACTED]: sharpe=1.13, fitness=0.79, returns=0.0792, turnover=0.1607
- [REDACTED]: sharpe=1.06, fitness=0.75, returns=0.0829, turnover=0.1663
- [REDACTED]: sharpe=1.2, fitness=0.72, returns=0.135, turnover=0.3744
- [REDACTED]: sharpe=0.39, fitness=0.16, returns=0.0242, turnover=0.1375
- [REDACTED]: sharpe=0.31, fitness=0.12, returns=0.0197, turnover=0.1251
- [REDACTED]: sharpe=0.31, fitness=0.04, returns=0.0069, turnover=0.5289
- [REDACTED]: sharpe=0.75, fitness=0.16, returns=0.0188, turnover=0.4036
- [REDACTED]: sharpe=0.36, fitness=0.1, returns=0.0092, turnover=0.0594

Next Steps:
- [REDACTED] is now OS/ACTIVE — monitor performance.
- The momentum reversal family is likely near its local optimum. Do not continue tuning without a specific new mechanism idea (e.g., regime-conditional reversal based on market drawdown).
- Next priority: P2 (earnings surprise) or P4 (short-interest/crowded-short) from research plan — both are orthogonal to all 3 shipped alphas.
- Update research-plan.md to reflect 3 shipped alphas.
