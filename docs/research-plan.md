# Alpha Research Pipeline

Last updated: 2026-06-16

## Shipped (3)

| # | Alpha ID | Mechanism | Expression | Sharpe | Fitness | Stage |
|---|----------|-----------|------------|--------|---------|-------|
| 1 | QP2NPG6X | Options-IV momentum with ts_rank | `ts_rank(ts_decay_linear(ts_zscore(ts_delta(ts_backfill(implied_volatility_put_10,63),63),63),7), 126)` | 1.45 | 1.03 | OS/ACTIVE |
| 2 | d5QNpnwv | Microstructure dual-gated return-volume correlation | `rank(reverse(ts_corr(multiply(group_zscore(returns, subindustry), multiply(max(subtract(ts_std_dev(returns,21), ts_mean(ts_std_dev(returns,21),63)), 0), max(subtract(volume, ts_mean(volume, 63)), 0))), ts_delta(volume,1), 55)))` | 1.50 | 1.03 | OS/ACTIVE |
| 3 | XgKd2a5m | 35-day momentum reversal | `rank(reverse(ts_zscore(ts_sum(returns, 35), 252)))` | 1.29 | 1.14 | OS/ACTIVE |

## Exhausted / Dead Families

- Sentiment/attention (peak Fitness 0.09)
- Empire-building / capital allocation (peak 0.16)
- Working-capital stress (peak 0.18)
- Model-feature divergence (peak -0.04)
- Liquidity premium (peak -0.35, A3)
- Competitive overlap (indeterminate, A5)
- Call/put IV skew (peak 0.16, ATM parity kills signal)
- Analyst EPS revisions (peak 0.10, fundamental data too slow)

## Active Pipeline

### ✅ P1 — Momentum Reversal — SHIPPED as XgKd2a5m (2026-06-16)
- **Expression**: `rank(reverse(ts_zscore(ts_sum(returns, 35), 252)))`
- **Sharpe 1.29, Fitness 1.14, OS/ACTIVE**
- SELF_CORRELATION PASS at 0.48

### 🟡 P2 — Earnings Surprise + Revision Momentum
- **Status**: Not started
- **Why**: Earlier "analyst confidence" attempt (E5gVLQ2r) used weak proxies (anl4_mark, anl4_qf_az_eps_mean). A cleaner earnings-surprise construct using the actual surprise magnitude could work.
- **Key fields**: `anl4_fs_detail_estimates_basic_qf_delay1_v4_nd_eps_mean`, actual reported EPS
- **Risk**: Fundamental data cadence unknown; earlier EPS revision attempts failed

### 🟡 P3 — Options Flow / Put-Call Imbalance
- **Status**: Not started
- **Why**: Only mined put-IV momentum. Call side, put-call volume ratio, and options open interest are untouched.
- **Key fields**: Options volume / open interest (need to verify availability)
- **Risk**: Brain may not have options volume/flow data; only IV fields confirmed

### 🟡 P4 — Short-Interest / Crowded-Short Dynamics
- **Status**: Not started
- **Why**: Short-squeeze and short-crowding signals are mechanically different from both shipped alphas. Biweekly FINRA cadence is acceptable for medium-horizon signals.
- **Key fields**: `twelve_month_short_interest_change`, `mdl177_liquidityriskfactor_si_ratio_alt`, `mdl77_shortsentimentfactor_tni_ths`
- **Risk**: Cadence is biweekly (external knowledge); avoid daily-lag sweeps. API cadence unverifiable.

### 🟡 P5 — Cross-Asset / Macro Sensitivity Beta
- **Status**: Not started
- **Why**: Stocks with high sensitivity to rates, gold, VIX, or oil that are mispriced relative to that sensitivity. Completely different data domain.
- **Key fields**: Need to discover macro/beta fields
- **Risk**: Macro fields may not be available at daily frequency for individual stocks

### 🟡 P6 — Merger Arb / Corporate Event Probability
- **Status**: Not started
- **Why**: Relationship fields (pv13) might have deal-related data (M&A probability, event risk).
- **Key fields**: `rel_num_all`, `rel_ret_all`, other pv13 fields
- **Risk**: Cadence opaque for pv13 fields; A5 closure flagged this. Proceed only if cadence can be verified.

## Key Learnings (Portable)

1. **ts_rank works on trend/momentum, destroys correlation/mean-reversion signals**
2. **Input-leg neutralization (group_zscore before ts_corr) beats output neutralization**
3. **Volume leg must NOT be neutralized in return-volume correlation**
4. **ts_decay_linear hurts correlation signals** (reduces turnover but kills fitness)
5. **Double gate (vol × volume) > single gate** for microstructure signals
6. **Regime gate design: test ratio/clip/sign-modulate; winner reveals regime structure**
7. **SELF_CORRELATION is OS-stage, not IS-gate** — PENDING ≠ FAIL for submission
8. **Fundamental data (analyst, working capital, empire) consistently fails** on this platform
9. **Price/volume/options data is the sweet spot** — higher frequency, cleaner signal
10. **ATM call/put IV ratio has no signal** — put-call parity makes them nearly identical
