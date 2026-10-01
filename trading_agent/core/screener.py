"""
Quantitative Multi-Factor Screener & Alpha Vantage Technical Scanner
"""

import json
import urllib.request
from typing import Dict, Any, List, Optional

from .config import (
    AV_API_KEY,
    MAX_BETA_COLLAR,
    is_earnings_within_48h
)
from .broker import call_tickertape_mcp

def get_alpha_vantage_rsi(symbol: str) -> Optional[float]:
    """Fetches 14-period weekly RSI with rate-limit and error resilience."""
    url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=weekly&time_period=14&series_type=close&apikey={AV_API_KEY}"
    if not url.startswith("https://"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-AQTA/2.2"})
        with urllib.request.urlopen(req, timeout=4) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            if "Information" in data or "Note" in data:
                return None
            rsi_dict = data.get("Technical Analysis: RSI", {})
            dates = list(rsi_dict.keys())
            if dates:
                return float(rsi_dict[dates[0]]["RSI"])
    except Exception:
        pass
    return None

def run_quantitative_screener(token: str, active_weights: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
    """
    Executes Tickertape PRO multi-factor screener and applies Fiduciary Anti-Ruin filters.
    Disqualifies:
    1. Cash-burners (Net Margin <= 0%)
    2. Hyper-beta lottery tickets (Beta > 2.80)
    3. Falling knives (Price < SMA 200)
    """
    query = {
        "filter": [
            {"field": "sector", "operator": "in", "values": ["Technology"]},
            {"field": "marketCap", "operator": "in", "values": ["Mega Cap", "Large Cap"]}
        ],
        "sortBy": "6MReturn,100,*", "sortOrder": -1, "count": count
    }
    res = call_tickertape_mcp(token, "us_screener_stocks", query)
    items = res.get("result", []) if isinstance(res, dict) else []

    candidates = []
    for item in items:
        m = item.get("metrics", {})
        ticker = item.get("ticker")
        p = float(m.get("prevClosePrice") or 0.0)
        beta = float(m.get("beta") or 1.0)
        r6m = float(m.get("6MReturn,100,*") or 0.0)
        r1m = float(m.get("1MReturn,100,*") or 0.0)
        upside = float(m.get("analystTargetPrice,prevClosePrice,-,prevClosePrice,/,100,*") or 0.0)
        eps_fwd = float(m.get("forecastEpsGrowthPercent") or 0.0)
        buy_pct = float(m.get("analystBuyPercent") or 0.0)
        
        # PRO Metrics
        net_margin = float(m.get("profitMarginPercent,100,*") or 0.0)
        roe = float(m.get("returnOnEquityTtm,100,*") or 0.0)
        sma50 = float(m.get("movingAverage50Day") or 0.0)
        sma200 = float(m.get("movingAverage200Day") or 0.0)

        # Fiduciary Anti-Ruin Guardrail 1: Strict Positive Net Margin Floor
        if net_margin <= 0.0:
            print(f"  [FIDUCIARY DISQUALIFIED] {ticker}: Cash-burning business (Net Margin: {net_margin:+.1f}%). Strict capital preservation active.")
            continue

        # Fiduciary Anti-Ruin Guardrail 2: Beta Ceiling (Anti-Lottery Volatility Filter)
        if beta > MAX_BETA_COLLAR:
            print(f"  [FIDUCIARY DISQUALIFIED] {ticker}: Hyper-beta speculative outlier (Beta: {beta:.2f} > {MAX_BETA_COLLAR:.2f}). Ruin risk prevented.")
            continue

        # Fiduciary Anti-Ruin Guardrail 3: Trend Integrity (Avoid Falling Knives)
        if sma200 > 0.0 and p < sma200:
            print(f"  [FIDUCIARY DISQUALIFIED] {ticker}: Below 200-day moving average (${p:.2f} < ${sma200:.2f}). Falling knife risk.")
            continue

        rsi_val = get_alpha_vantage_rsi(ticker)
        has_earn_risk = is_earnings_within_48h(ticker)

        candidates.append({
            "ticker": ticker,
            "name": item.get("name", ticker),
            "price": p,
            "beta": beta,
            "ret_6m": r6m,
            "ret_1m": r1m,
            "upside": upside,
            "eps_fwd": eps_fwd,
            "buy_pct": buy_pct,
            "net_margin": net_margin,
            "roe": roe,
            "rsi": rsi_val,
            "has_earnings_risk": has_earn_risk,
            "factors": {
                "beta": beta,
                "ret_6m": r6m,
                "ret_1m": r1m,
                "fwd_eps": eps_fwd,
                "upside": upside,
                "buy_pct": buy_pct,
                "rsi": rsi_val,
                "net_margin": net_margin
            }
        })

    return candidates
