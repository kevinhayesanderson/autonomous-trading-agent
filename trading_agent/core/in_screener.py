"""
Indian Stock Market Quantitative Screener & Tickertape PRO Forensic Intelligence Layer
Enables first-principles algorithmic screening, multi-factor filtering, and deep forensic audits
across the entire Indian equity universe (NSE/BSE).
"""

import json
from typing import Dict, Any, List, Optional
from .auth import get_tickertape_token
from .broker import call_tickertape_mcp

def resolve_sid_for_ticker(token: str, ticker: str) -> Optional[str]:
    """Resolves Indian stock ticker to internal Tickertape SID using fast letter discovery."""
    ticker_clean = ticker.strip().upper()
    letter = ticker_clean[0]
    res = call_tickertape_mcp(token, "in_stock_search_read", {"letter": letter})
    if isinstance(res, str):
        for line in res.splitlines():
            if f"|ticker:{ticker_clean}|" in line or f":{ticker_clean}|" in line:
                parts = line.split("|")
                return parts[0].split(":")[1]
    return None

def screen_indian_stocks(
    min_beta: float = 1.40,
    max_beta: float = 2.80,
    min_mcap_cr: float = 2000.0,
    min_roe: float = 12.0,
    min_opmg: float = 10.0,
    max_price: float = 5500.0,
    min_price: float = 15.0,
    min_inst_own: float = 0.0,
    sort_by: str = "12mpctN",
    sort_order: int = -1,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Executes an unbiased algorithmic screener across all 5,000+ Indian stocks via Tickertape PRO.
    Enforces strict high-beta, institutional liquidity, profitability, and integer-execution constraints.
    """
    token = get_tickertape_token()
    match_cond: Dict[str, Any] = {
        "beta": {"g": min_beta, "l": max_beta},
        "mrktCapf": {"g": min_mcap_cr},
        "roe": {"g": min_roe},
        "opmg": {"g": min_opmg},
        "lastPrice": {"l": max_price, "g": min_price}
    }
    if min_inst_own > 0:
        match_cond["instown"] = {"g": min_inst_own}

    query = {
        "match": json.dumps(match_cond),
        "sortBy": sort_by,
        "sortOrder": sort_order,
        "project": [
            "lastPrice", "beta", "12mpctN", "roe", "opmg", "mrktCapf",
            "sector", "dbtEqt", "epsg", "instown", "14dRsi", "upside"
        ],
        "limit": min(limit, 10)  # Tickertape PRO screener max limit per call is 10
    }
    res = call_tickertape_mcp(token, "in_screen_stocks_read", query)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except Exception:
            return []
    return res.get("results", [])

def audit_indian_stock(ticker: str) -> Dict[str, Any]:
    """
    Performs a deep forensic Tickertape PRO audit on an Indian stock.
    Returns Scorecards, Investment Checklists, ASM/GSM Surveillance, Float Ownership, and Analyst Forecasts.
    """
    token = get_tickertape_token()
    sid = resolve_sid_for_ticker(token, ticker)
    if not sid:
        return {"success": False, "error": f"Could not resolve SID for ticker {ticker}"}

    # 1. Overview & Quote
    ov = call_tickertape_mcp(token, "in_stock_overview_read", {"sids": [sid]})
    q = (ov.get("quotes") or [{}])[0] if isinstance(ov, dict) else {}

    # 2. Scorecard & Checklists
    analysis = call_tickertape_mcp(token, "in_stock_analysis_read", {
        "sid": sid,
        "checklistType": "pro",
        "sections": ["scorecard", "checklists", "ai_summary", "commentaries"],
        "commentaryKeys": ["forecasts", "overview", "financialStatement"]
    })

    # 3. Ownership & Surveillance
    own = call_tickertape_mcp(token, "in_stock_ownership_read", {
        "sid": sid,
        "sections": ["holdings", "surveillance"]
    })

    scorecard_map = {}
    if isinstance(analysis, dict):
        for sc in analysis.get("scorecard", []):
            name = sc.get("name")
            val = (sc.get("score") or {}).get("value", "N/A")
            tag = sc.get("tag", "N/A")
            desc = sc.get("description", "")
            scorecard_map[name] = {"value": val, "tag": tag, "desc": desc}

    checklists_map = {}
    if isinstance(analysis, dict):
        for ch in analysis.get("checklists", []):
            checklists_map[ch.get("title")] = {
                "state": ch.get("state"),
                "desc": ch.get("description"),
                "explanation": ch.get("explanation", "")
            }

    surv = own.get("surveillance", {}) if isinstance(own, dict) else {}
    is_asm = bool(surv.get("asm"))
    is_gsm = bool(surv.get("gsm"))

    holdings_list = own.get("holdings", []) if isinstance(own, dict) else []
    latest_holdings = holdings_list[-1] if isinstance(holdings_list, list) and holdings_list else {}

    forecasts = analysis.get("commentaries", {}).get("forecasts", {}) if isinstance(analysis, dict) else {}

    return {
        "success": True,
        "ticker": ticker.upper(),
        "sid": sid,
        "price": q.get("price") or q.get("close"),
        "change": q.get("change"),
        "volume": q.get("volume"),
        "scorecard": scorecard_map,
        "checklists": checklists_map,
        "surveillance": {
            "clean": not (is_asm or is_gsm),
            "asm": is_asm,
            "gsm": is_gsm,
            "details": surv
        },
        "holdings": latest_holdings,
        "forecasts": forecasts
    }
