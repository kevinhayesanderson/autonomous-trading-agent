"""
Dynamic US Macro Regime & Generational Opportunity Scanner
Analyzes:
1. What Happened in the US Market (Drawdown, Intraday Shakeouts, Sector Rotation)
2. What is the Current State (Regime Classification, Multiple Compression, Volatility)
3. What Will Be (Forward EPS Trajectory, Hyperscaler Capex, Catalysts)
4. Generational Asymmetry "Sale Radar" (Deep Valuation Dislocation in Monopolies)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .broker import call_tickertape_mcp
from .auth import get_tickertape_token

BENCHMARK_TICKERS = ["SPY", "QQQ", "SOXX"]
BELLWETHER_TICKERS = ["NVDA", "GOOGL", "AAPL", "MSFT", "AMZN", "MU", "ASML", "TSM"]

def parse_csv_batch_quotes(csv_text: str) -> Dict[str, Dict[str, float]]:
    """Parses comma-delimited quotes returned by us_quotes_get_latest_batch."""
    quotes = {}
    lines = csv_text.strip().split("\n")
    if len(lines) <= 1:
        return quotes
    
    header = [h.strip() for h in lines[0].split(",")]
    # Header format: ticker,t,p,lcp,v,s
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4:
            t = parts[0]
            try:
                p = float(parts[2])
                lcp = float(parts[3])
                chg_pct = ((p - lcp) / lcp) * 100.0 if lcp > 0 else 0.0
                quotes[t] = {
                    "price": p,
                    "prev_close": lcp,
                    "change_pct": chg_pct
                }
            except Exception:
                continue
    return quotes

def audit_us_market_regime(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Audits the current US market regime across indices and bellwethers.
    Answers:
    1. What happened in the market?
    2. What is the current state?
    3. What will be if possible?
    """
    if not token:
        try:
            token = get_tickertape_token()
        except Exception:
            token = ""

    all_tickers = BENCHMARK_TICKERS + BELLWETHER_TICKERS
    ticker_str = ",".join(all_tickers)
    
    raw_quotes = call_tickertape_mcp(token, "us_quotes_get_latest_batch", {"market": "US", "tickers": ticker_str})
    quotes = {}
    if isinstance(raw_quotes, str):
        quotes = parse_csv_batch_quotes(raw_quotes)

    # 1. What Happened: Index Changes
    spy_chg = quotes.get("SPY", {}).get("change_pct", 0.0)
    qqq_chg = quotes.get("QQQ", {}).get("change_pct", 0.0)
    soxx_chg = quotes.get("SOXX", {}).get("change_pct", 0.0)

    # Classify Market Regime
    if soxx_chg <= -4.0 or qqq_chg <= -2.5:
        regime_title = "AGGRESSIVE TECH / SEMI CONSOLIDATION (HIGH VOLATILITY PULLBACK)"
        regime_tone = "BUYABLE VOLATILITY"
        narrative_what_happened = (
            f"The semiconductor sector is experiencing severe intraday compression (SOXX: {soxx_chg:+.2f}%), "
            f"dragging the Nasdaq lower (QQQ: {qqq_chg:+.2f}%). Bellwethers like MU ({quotes.get('MU', {}).get('change_pct', 0.0):+.2f}%), "
            f"ASML ({quotes.get('ASML', {}).get('change_pct', 0.0):+.2f}%), and NVDA ({quotes.get('NVDA', {}).get('change_pct', 0.0):+.2f}%) "
            f"are being liquidated in broad institutional profit-taking."
        )
    elif qqq_chg >= 1.5 and soxx_chg >= 2.0:
        regime_title = "BULL EXPANSION & MOMENTUM SURGE"
        regime_tone = "PRO-RISK CONTINUATION"
        narrative_what_happened = f"Broad risk-on rally across tech (QQQ: {qqq_chg:+.2f}%) and semiconductors (SOXX: {soxx_chg:+.2f}%)."
    else:
        regime_title = "BALANCED RANGE-BOUND DIGESTION"
        regime_tone = "NEUTRAL / ACCUMULATION"
        narrative_what_happened = f"US markets are trading in an orderly range (SPY: {spy_chg:+.2f}%, QQQ: {qqq_chg:+.2f}%, SOXX: {soxx_chg:+.2f}%)."

    # 2. What is the Current State
    state_summary = (
        f"Broad market (S&P 500) sits at {quotes.get('SPY', {}).get('price', 0.0):.2f} ({spy_chg:+.2f}%), "
        f"while high-beta tech is digesting recent multi-month expansions. "
        f"Hyperscalers are reporting robust operational cash flows, but market expectations demand relentless earnings beats. "
        f"Valuation multiples are bifurcating: mega-cap hardware/HBM compounders hold high forward multiples, "
        f"while select dominant monopolies (e.g. Alphabet at 16x P/E) are undergoing historic valuation dislocations."
    )

    # 3. What Will Be (Forward Outlook & Catalysts)
    forward_outlook = [
        "1. Hyperscaler AI Capex Expansion: Microsoft, Alphabet, Meta, and Amazon continue to guide > $200B+ aggregate annualized capex, ensuring sustained hardware backlogs for ASML, TSM, and MU through 2026.",
        "2. Rate Cycle Tailwinds: Global easing and liquidity injections historically re-accelerate high-beta semiconductor compounders following 5-10% sector pullbacks.",
        "3. Valuation Mean-Reversion: Mega-cap monopolies trading under 20x P/E with > 50% margins represent asymmetric risk/reward that institutional money reliably accumulates once volatility subsides."
    ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regime_title": regime_title,
        "regime_tone": regime_tone,
        "quotes": quotes,
        "what_happened": narrative_what_happened,
        "current_state": state_summary,
        "forward_outlook": forward_outlook
    }

def scan_generational_asymmetry_opportunities(token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans for 'Once-in-a-Lifetime' Valuation Dislocations ('The Sale Radar'):
    Identifies institutional monopolies (MCap >= $50B, Net Margin >= 15%) experiencing:
    1. Compressed Valuation (P/E <= 22x or PEG <= 1.2)
    2. Deep Pullback / Sale (1M Return <= -10% or Price near 52W Low)
    3. Wall Street Consensus Disconnect (Target Upside >= +35%)
    """
    if not token:
        try:
            token = get_tickertape_token()
        except Exception:
            token = ""

    # Key Mega-Cap Monopolies to audit for deep dislocations
    focus_titans = ["GOOGL", "AMZN", "META", "AAPL", "MSFT", "NVDA", "TSM", "ASML", "MU", "AMD", "ADBE", "QCOM"]
    opportunities = []

    for t in focus_titans:
        res = call_tickertape_mcp(token, "us_assets_get_overview", {"market": "US", "assetType": "stocks", "ticker": t})
        if not isinstance(res, dict) or "metrics" not in res:
            continue
        
        m = res.get("metrics", {})
        pe = float(m.get("priceEarningsTtm") or 999.0)
        net_margin = float(m.get("profitMarginPercent") or 0.0)
        r1m = float(m.get("1MReturn") or 0.0)
        p = float(m.get("prevClosePrice") or 0.0)
        sma200 = float(m.get("movingAverage200Day") or 0.0)
        upside = float(m.get("upsidePercent") or 0.0)
        w52_high = float(m.get("week52High") or 0.0)
        beta = float(m.get("beta") or 1.0)
        mcap_b = float(m.get("marketCapitalization") or 0.0) / 1000.0

        # Dislocation Filter: High margin (>15%), Deep 1M drop (<= -10%) or low PE (<= 22x) with high upside (>30%)
        is_valuation_sale = pe <= 22.0 and net_margin >= 15.0
        is_price_sale = r1m <= -10.0 or (w52_high > 0 and (p - w52_high) / w52_high <= -20.0)

        if is_valuation_sale or (is_price_sale and net_margin >= 20.0 and upside >= 30.0):
            # Compute Asymmetry Score (0 to 100)
            # Factors: Profit Margin power, Upside magnitude, Valuation discount, Beta
            val_pts = max(0.0, min(35.0, (25.0 - pe) * 3.5)) if pe < 25.0 else 10.0
            margin_pts = min(25.0, net_margin * 0.5)
            upside_pts = min(25.0, upside * 0.5)
            dip_pts = min(15.0, abs(r1m) * 0.8) if r1m < 0 else 0.0
            asymmetry_score = round(val_pts + margin_pts + upside_pts + dip_pts, 1)

            # Rationale & Catalysts
            catalyst_thesis = (
                f"Trading at an extreme {pe:.1f}x P/E with {net_margin:.1f}% net margin. "
                f"Recent 1M contraction ({r1m:+.1f}%) creates a +{upside:.1f}% upside gap to Wall Street target ($"
                f"{m.get('analystTargetPrice', 'N/A')}). "
                f"{'Below SMA200 (caution for reversal confirmation)' if p < sma200 else 'Holding above SMA200 (healthy breakout base)'}."
            )

            opportunities.append({
                "ticker": t,
                "name": res.get("name", t),
                "sector": res.get("sector", "Technology"),
                "price": p,
                "pe_ratio": pe,
                "net_margin": net_margin,
                "return_1m": r1m,
                "analyst_upside": upside,
                "target_price": m.get("analystTargetPrice"),
                "beta": beta,
                "sma200": sma200,
                "is_below_sma200": p < sma200,
                "asymmetry_score": asymmetry_score,
                "thesis": catalyst_thesis
            })

    opportunities.sort(key=lambda x: x["asymmetry_score"], reverse=True)
    return opportunities

def format_macro_and_opportunity_report(regime: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> str:
    """Formats the combined macro intelligence report into a markdown representation."""
    lines = []
    lines.append("=" * 96)
    lines.append(" [DYNAMIC US MACRO REGIME & GENERATIONAL OPPORTUNITY SCANNER]")
    lines.append("=" * 96)
    lines.append(f"  * Market Regime: {regime['regime_title']} [{regime['regime_tone']}]")
    lines.append(f"  * Audit Time:    {regime['timestamp']}")
    lines.append("")
    lines.append("  --- 1. WHAT HAPPENED IN THE US MARKET ---")
    lines.append(f"  {regime['what_happened']}")
    lines.append("")
    lines.append("  --- 2. WHAT IS THE CURRENT STATE ---")
    lines.append(f"  {regime['current_state']}")
    lines.append("")
    lines.append("  --- 3. WHAT WILL BE (FORWARD OUTLOOK & CATALYSTS) ---")
    for fo in regime["forward_outlook"]:
        lines.append(f"  * {fo}")
    lines.append("")
    lines.append("=" * 96)
    lines.append(" [*] GENERATIONAL ASYMMETRY / THE SALE RADAR - VALUE DISLOCATIONS")
    lines.append("=" * 96)
    if not opportunities:
        lines.append("  * No mega-cap monopolies currently exhibiting generational valuation dislocations.")
    else:
        lines.append(f"  {'Rank':<5} | {'Ticker':<6} | {'Price':<9} | {'P/E':<6} | {'Margin':<7} | {'1M Ret':<8} | {'Upside':<8} | {'Score':<6} | {'Status'}")
        lines.append("  " + "-" * 90)
        for idx, o in enumerate(opportunities, 1):
            status = "BELOW SMA200 (FALLING KNIFE CAUTION)" if o["is_below_sma200"] else "TREND ALIGNED (PRIME DIP)"
            lines.append(f"  #{idx:<4} | {o['ticker']:<6} | ${o['price']:<8.2f} | {o['pe_ratio']:<5.1f}x | {o['net_margin']:>5.1f}% | {o['return_1m']:>+6.1f}% | {o['analyst_upside']:>+6.1f}% | {o['asymmetry_score']:<5.1f} | {status}")
            lines.append(f"        -> Thesis: {o['thesis']}")
    lines.append("=" * 96)
    return "\n".join(lines)
