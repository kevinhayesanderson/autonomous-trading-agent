"""
Order Placement & Execution Resilience Layer
Handles quote-lock expiration, timeout recovery, slippage ceilings, and Zero-Limbo absorption.
"""

from typing import Dict, Any, Optional
from .broker import call_tickertape_mcp, verify_recent_order

def place_order_with_resilience(
    token: str,
    ticker: str,
    action: str,
    amount: float,
    session_id: Optional[str] = None,
    limit_ceiling: Optional[float] = None
) -> Dict[str, Any]:
    """
    Executes an order with quote-lock auto-refresh, timeout recovery, and slippage guard.
    Handles SESSION_NOT_FOUND by regenerating a fresh single-leg preview immediately.
    """
    # Step 1: If session_id provided, attempt execution
    if session_id:
        pres = call_tickertape_mcp(token, "us_trade_place", {"sessionId": session_id}, timeout=20)
        
        # Case A: Success
        if isinstance(pres, dict) and pres.get("success") is True:
            order_id = pres.get("orderId") or pres.get("data", {}).get("orderId")
            return {"status": "SUCCESS", "orderId": order_id, "details": pres}
            
        # Case B: Network/HTTP Timeout -> Check trade list before assuming failure
        err_msg = str(pres.get("error", ""))
        if "HTTP" in err_msg or "timed out" in err_msg.lower():
            print(f"    [?] Network timeout on {ticker}. Querying trade list for broker confirmation...")
            found_id, status = verify_recent_order(token, ticker, action)
            if found_id:
                print(f"    [RECOVERED] Order {found_id} was confirmed placed by broker! Status: {status}")
                return {"status": "SUCCESS", "orderId": found_id, "details": {"recovered": True}}

        # Case C: Check if blocked code is SESSION_NOT_FOUND
        blocked = pres.get("blocked", {}) if isinstance(pres, dict) else {}
        code = blocked.get("code")
        if code != "SESSION_NOT_FOUND":
            return {"status": "FAILED", "code": code or err_msg, "details": pres}
        print(f"    [!] Session expired for {ticker} (SESSION_NOT_FOUND). Requesting fresh quote lock...")

    # Step 2: Fresh Single-Leg Preview & Re-Quote
    prev_args = {
        "ticker": ticker,
        "transactionType": action.lower(),
        "orderType": "notional",
        "amount": {"currency": "usd", "value": round(float(amount), 2)}
    }
    prev_res = call_tickertape_mcp(token, "us_trade_preview", prev_args, timeout=15)
    if not isinstance(prev_res, dict) or not prev_res.get("success"):
        b_msg = prev_res.get("blocked", {}).get("message") if isinstance(prev_res, dict) else ""
        err_code = prev_res.get("blocked", {}).get("code", "PREVIEW_FAILED") if isinstance(prev_res, dict) else "PREVIEW_FAILED"
        print(f"    [!] Preview blocked for {ticker}: {b_msg or err_code}")
        return {"status": "FAILED", "code": err_code, "details": prev_res}

    fresh_sid = prev_res.get("data", {}).get("sessionId")
    exec_price_str = str(prev_res.get("data", {}).get("executionPrice", "0")).replace("$", "").replace(",", "")
    try:
        exec_price = float(exec_price_str)
    except Exception:
        exec_price = 0.0

    # Slippage Guard: Verify fresh quote hasn't gapped unfavorably
    if limit_ceiling:
        if action.lower() == "buy" and exec_price > limit_ceiling:
            return {
                "status": "FAILED",
                "code": "SLIPPAGE_EXCEEDED",
                "details": f"BUY execution price ${exec_price:.2f} exceeded ceiling ${limit_ceiling:.2f}"
            }
        elif action.lower() == "sell" and exec_price < limit_ceiling:
            return {
                "status": "FAILED",
                "code": "SLIPPAGE_EXCEEDED",
                "details": f"SELL execution price ${exec_price:.2f} fell below floor ${limit_ceiling:.2f}"
            }

    # Step 3: Place with fresh single-leg session ID
    pres2 = call_tickertape_mcp(token, "us_trade_place", {"sessionId": fresh_sid}, timeout=20)
    if isinstance(pres2, dict) and (pres2.get("success") is True or ("data" in pres2 and "blocked" not in pres2)):
        order_id = pres2.get("orderId") or pres2.get("data", {}).get("orderId") or pres2.get("data", {}).get("tradeId") or "CONFIRMED"
        return {"status": "SUCCESS", "orderId": order_id, "details": pres2}
    else:
        found_id, status = verify_recent_order(token, ticker, action)
        if found_id:
            return {"status": "SUCCESS", "orderId": found_id, "details": {"recovered": True}}
        code = pres2.get("blocked", {}).get("code") if isinstance(pres2, dict) else "PLACE_FAILED"
        return {"status": "FAILED", "code": code, "details": pres2}
