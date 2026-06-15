"""
Simplified retail version of the d5QNpnwv dual-gated institutional flow alpha.

Original Brain expression:
  rank(reverse(ts_corr(
    multiply(group_zscore(returns, subindustry),
             multiply(max(subtract(ts_std_dev(returns,21),
                                    ts_mean(ts_std_dev(returns,21),63)), 0),
                      max(subtract(volume, ts_mean(volume, 63)), 0))),
    ts_delta(volume,1), 55)))

Mechanism (in plain English):
  Short stocks whose peer-relative returns correlate with volume surges
  during high-volatility, high-volume regimes. This is the fingerprint of
  temporary institutional buying pressure that tends to mean-revert.

Simplifications vs Brain version:
  - Uses GICS sector (8 buckets) instead of subindustry (~150 buckets)
  - Uses Yahoo Finance data (free, daily, survivorship-biased)
  - No survivorship-bias correction
  - Single-threaded, no portfolio optimization
  - Output is a simple ranked list, not a full long-short book

Usage:
  pip install -r requirements.txt
  python signal.py
"""

from __future__ import annotations

import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# ── Config ──────────────────────────────────────────────────────────
WATCHLIST_CSV = Path(__file__).parent / "watchlist.csv"
CACHE_FILE = Path(__file__).parent / "data_cache.pkl"
CACHE_HOURS = 6  # re-download after this many hours

LOOKBACK_DAYS = 400  # enough for vol baseline (63) + corr window (55) + buffer
CORR_WINDOW = 55
VOL_WINDOW = 21
VOL_BASELINE = 63
VOLUME_BASELINE = 63


# ── Data ────────────────────────────────────────────────────────────

def load_watchlist() -> tuple[list[str], dict[str, str]]:
    """Return (tickers, ticker→sector map)."""
    df = pd.read_csv(WATCHLIST_CSV)
    df["ticker"] = df["ticker"].str.strip()
    df["sector"] = df["sector"].str.strip()
    return df["ticker"].tolist(), dict(zip(df["ticker"], df["sector"]))


def fetch_data(tickers: list[str], lookback_days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download daily Close and Volume. Uses local cache to avoid re-downloading."""
    # Check cache
    if CACHE_FILE.exists():
        age_hours = (datetime.now() - datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)).total_seconds() / 3600
        if age_hours < CACHE_HOURS:
            print(f"  Using cached data ({age_hours:.1f}h old)")
            with open(CACHE_FILE, "rb") as f:
                close, volume = pickle.load(f)
            # Keep only tickers that exist in both cache and current watchlist
            available = [t for t in tickers if t in close.columns]
            return close[available], volume[available]

    print(f"  Downloading {lookback_days}d of data for {len(tickers)} tickers...")
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    raw = yf.download(
        tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
        auto_adjust=True, progress=False, group_by="column",
    )

    # yfinance returns MultiIndex columns (Price, Ticker) when group_by="column"
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
        volume = raw["Volume"].copy()
    else:
        # Single ticker fallback
        close = raw[["Close"]].copy()
        close.columns = [tickers[0]]
        volume = raw[["Volume"]].copy()
        volume.columns = [tickers[0]]

    # Save cache
    with open(CACHE_FILE, "wb") as f:
        pickle.dump((close, volume), f)
    print(f"  Cached to {CACHE_FILE}")

    return close, volume


# ── Signal computation ──────────────────────────────────────────────

def compute_signal(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    sector_map: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute the simplified dual-gated signal.

    Returns (raw_signal, ranked_signal) where:
      raw_signal  = -correlation  (positive → short, negative → long)
      ranked_signal = cross-sectional percentile (1.0 = strongest short)
    """
    tickers = list(close.columns)
    returns = close.pct_change()

    # ── 1. Peer-relative return (group_zscore within sector) ──
    peer_zscore = pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)

    sectors_in_data = {sector_map.get(t, "Unknown") for t in tickers}
    for sector in sectors_in_data:
        sector_tickers = [
            t for t in tickers
            if sector_map.get(t, "Unknown") == sector and t in returns.columns
        ]
        if len(sector_tickers) < 2:
            continue
        sec_rets = returns[sector_tickers]
        mean = sec_rets.mean(axis=1, skipna=True)
        std = sec_rets.std(axis=1, skipna=True)
        std = std.replace(0, np.nan)  # avoid div-by-zero
        peer_zscore[sector_tickers] = sec_rets.sub(mean, axis=0).div(std, axis=0)

    # ── 2. Volatility gate ──
    vol_21d = returns.rolling(VOL_WINDOW, min_periods=10).std()
    vol_baseline = vol_21d.rolling(VOL_BASELINE, min_periods=30).mean()
    vol_gate = (vol_21d - vol_baseline).clip(lower=0)

    # ── 3. Volume gate ──
    vol_mean_63 = volume.rolling(VOLUME_BASELINE, min_periods=30).mean()
    volume_gate = (volume - vol_mean_63).clip(lower=0)

    # ── 4. Double gate ──
    gate = vol_gate * volume_gate

    # ── 5. Gated signal ──
    gated = peer_zscore * gate

    # ── 6. Volume delta ──
    vol_delta = volume.diff(1)

    # ── 7. Rolling 55-day correlation ──
    corr = pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)

    for ticker in tickers:
        gs = gated[ticker]
        vd = vol_delta[ticker]
        # Align and drop NaN
        mask = gs.notna() & vd.notna()
        gs_aligned = gs[mask]
        vd_aligned = vd[mask]
        if len(gs_aligned) < CORR_WINDOW:
            continue
        # Rolling Pearson correlation
        roll_corr = gs_aligned.rolling(CORR_WINDOW, min_periods=30).corr(vd_aligned)
        corr[ticker] = roll_corr

    # ── 8. Reverse (short high corr) & rank ──
    raw_signal = -corr
    rank_signal = raw_signal.rank(axis=1, pct=True)

    return raw_signal, rank_signal


# ── Output ──────────────────────────────────────────────────────────

def print_report(
    raw_signal: pd.DataFrame,
    rank_signal: pd.DataFrame,
    sector_map: dict[str, str],
):
    """Pretty-print the current signal state."""
    # Drop rows where ALL stocks are NaN
    valid = raw_signal.dropna(how="all")
    if valid.empty:
        print("\n  ❌ Not enough data yet. Need at least ~120 trading days of history.\n")
        return

    latest = valid.index[-1]
    today_raw = raw_signal.loc[latest].dropna()
    today_rank = rank_signal.loc[latest].dropna().sort_values(ascending=False)

    print(f"\n  📅 Signal Date: {latest.strftime('%Y-%m-%d')}")
    print(f"  📊 Stocks with valid signal: {len(today_rank)} / {len(rank_signal.columns)}")

    if today_rank.empty:
        print("  No valid signals today.\n")
        return

    # ── Top SHORTs ──
    print()
    print("  " + "─" * 58)
    print("  🔴  TOP 10 SHORT CANDIDATES")
    print("      (high corr → institutional buying pressure → mean-revert down)")
    print("  " + "─" * 58)
    print(f"  {'#':>3}  {'Ticker':<8} {'Sector':<22} {'Signal':>7}  {'Raw':>8}")
    print(f"  {'─'*3}  {'─'*6:<8} {'─'*20:<22} {'─'*5:>7}  {'─'*6:>8}")
    for i, (ticker, sig) in enumerate(today_rank.head(10).items(), 1):
        sector = sector_map.get(ticker, "?")
        raw = today_raw.get(ticker, np.nan)
        bar = "▓" * max(1, int(sig * 10))
        print(f"  {i:>3}  {ticker:<8} {sector:<22} {sig:>7.4f}  {raw:>+8.4f}  {bar}")

    # ── Top LONGs ──
    print()
    print("  " + "─" * 58)
    print("  🟢  TOP 10 BUY / LONG CANDIDATES")
    print("      (low/negative corr → potential reversal up)")
    print("  " + "─" * 58)
    print(f"  {'#':>3}  {'Ticker':<8} {'Sector':<22} {'Signal':>7}  {'Raw':>8}")
    print(f"  {'─'*3}  {'─'*6:<8} {'─'*20:<22} {'─'*5:>7}  {'─'*6:>8}")
    tail = today_rank.tail(10).sort_values(ascending=True)
    for i, (ticker, sig) in enumerate(tail.items(), 1):
        sector = sector_map.get(ticker, "?")
        raw = today_raw.get(ticker, np.nan)
        bar = "▓" * max(1, int((1 - sig) * 10))
        print(f"  {i:>3}  {ticker:<8} {sector:<22} {sig:>7.4f}  {raw:>+8.4f}  {bar}")

    # ── Sector summary ──
    print()
    print("  " + "─" * 58)
    print("  📊  SIGNAL BY SECTOR (avg rank, 0.5 = neutral)")
    print("  " + "─" * 58)
    sector_ranks: dict[str, list[float]] = {}
    for ticker, sig in today_rank.items():
        sector = sector_map.get(ticker, "?")
        sector_ranks.setdefault(sector, []).append(sig)

    for sector in sorted(sector_ranks, key=lambda s: np.mean(sector_ranks[s]), reverse=True):
        avg = np.mean(sector_ranks[sector])
        n = len(sector_ranks[sector])
        direction = "SHORT ▶" if avg > 0.55 else ("LONG  ◀" if avg < 0.45 else "NEUTRAL")
        bar = "█" * int(abs(avg - 0.5) * 40)
        print(f"  {sector:<24} {avg:.4f}  {direction}  ({n:>2})  {bar}")

    # ── Most active signals recently ──
    print()
    print("  " + "─" * 58)
    print("  📈  STRONGEST RECENT SIGNALS (5-day mean |raw|)")
    print("  " + "─" * 58)
    last_5 = raw_signal.dropna(how="all").index[-5:]
    recent_abs = raw_signal.loc[last_5].abs().mean()
    for ticker in recent_abs.nlargest(5).index:
        sector = sector_map.get(ticker, "?")
        direction = "↘ SHORT" if today_raw.get(ticker, 0) > 0 else "↗ LONG"
        print(f"  {ticker:<8} {sector:<22} {recent_abs[ticker]:>8.4f}  {direction}")

    print()
    print("  ⚠️  DISCLAIMER: Simplified research signal, NOT financial advice.")
    print("     Past performance ≠ future results. Always do your own due diligence.")
    print()


# ── Main ────────────────────────────────────────────────────────────

def main():
    print()
    print("  ╔" + "═" * 56 + "╗")
    print("  ║  d5QNpnwv — Dual-Gated Institutional Flow Signal     ║")
    print("  ║  Simplified Retail Version                           ║")
    print("  ╚" + "═" * 56 + "╝")

    # Load
    tickers, sector_map = load_watchlist()
    sectors = set(sector_map.values())
    print(f"\n  Watchlist: {len(tickers)} stocks in {len(sectors)} sectors")

    # Fetch
    close, volume = fetch_data(tickers, LOOKBACK_DAYS)
    available = list(close.columns)
    missing = [t for t in tickers if t not in close.columns]
    if missing:
        print(f"  ⚠ {len(missing)} tickers unavailable: {', '.join(missing[:8])}...")
    if len(available) < 10:
        print("  ❌ Too few stocks available. Check your internet or ticker names.")
        return

    # Compute
    print("  Computing signal...")
    raw_signal, rank_signal = compute_signal(close, volume, sector_map)

    # Report
    print_report(raw_signal, rank_signal, sector_map)


if __name__ == "__main__":
    main()
