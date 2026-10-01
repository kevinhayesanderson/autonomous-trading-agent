"""
Smart Wallet Drain & Capital Optimizer
Recursively drains settled funds into high-conviction assets while strictly
obeying broker 50% rolling 60-minute wallet-drain limits.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from .auth import get_tickertape_token
from .broker import call_tickertape_mcp
from .execution import place_order_with_resilience
from .config import MEMORY_DIR, TRADE_JOURNAL_FILE

def record_drain_trade(ticker: str, amount: float, price: float):
    """Appends drain trade entry to the persistent trade journal."""
    import os, json
    entry = {
        "id": f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticker}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ticker": ticker,
        "name": ticker,
        "action": "BUY",
        "shares": 0.0,
        "price": float(price),
        "amount": float(amount),
        "entry_factors": {"wallet_drain": True},
        "cycle": datetime.now().strftime("%Y-%m"),
        "reason": f"Automated Fiduciary Wallet Drain into {ticker}"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(TRADE_JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def drain_wallet_to_asset(ticker: str = "ASML") -> Dict[str, Any]:
    """
    Evaluates current available settled cash, determines the maximum allowable order amount
    under Tickertape's 50% wallet safety limit, and executes a top-up into the target asset.
    """
    print("=" * 80)
    print(f" DRAIN WALLET DIRECTLY INTO {ticker.upper()}")
    print("=" * 80)

    token = get_tickertape_token()
    bal = call_tickertape_mcp(token, "us_account_balance")
    avail = float(bal.get("availableFunds", 0.0)) if isinstance(bal, dict) else 0.0
    print(f"[*] Current Available Funds: ${avail:.2f} USD")

    if avail < 1.0:
        print("[!] Insufficient funds to place trade (minimum $1.00 USD required).")
        return {"status": "INSUFFICIENT_FUNDS", "available": avail}

    # Generate descending candidate test amounts
    max_test = min(avail, 500.0)
    test_amounts = []
    curr = round(max_test - 0.10, 2)
    while curr >= 1.0:
        test_amounts.append(round(curr, 2))
        if curr > 20.0:
            curr -= 2.0
        elif curr > 5.0:
            curr -= 0.50
        else:
            curr -= 0.25

    chosen_amt = None
    chosen_preview = None

    for amt in test_amounts:
        if amt > avail or amt < 1.0:
            continue
        prev = call_tickertape_mcp(token, "us_trade_preview", {
            "ticker": ticker.upper(),
            "transactionType": "buy",
            "orderType": "notional",
            "amount": {"currency": "usd", "value": amt}
        })
        if prev.get("success"):
            chosen_amt = amt
            chosen_preview = prev
            break
        else:
            code = prev.get("blocked", {}).get("code", "UNKNOWN")

    if not chosen_amt:
        print(f"[!] No allowable order amount found within Tickertape safety constraints for {ticker}.")
        return {"status": "NO_ALLOWABLE_AMOUNT", "available": avail}

    print(f"[+] Optimal allowable order size: ${chosen_amt:.2f} USD")
    sid = chosen_preview.get("data", {}).get("sessionId")
    exec_price_str = str(chosen_preview.get("data", {}).get("executionPrice", "0")).replace("$", "").replace(",", "")
    try:
        exec_price = float(exec_price_str)
    except Exception:
        exec_price = 1800.0

    print(f"[*] Placing BUY order for {ticker} (${chosen_amt:.2f} USD)...")
    res = place_order_with_resilience(token, ticker=ticker.upper(), action="buy", amount=chosen_amt, session_id=sid)

    if res.get("status") == "SUCCESS":
        order_id = res.get("orderId")
        print(f"[SUCCESS] {ticker} BUY filled: Order ID {order_id}")
        record_drain_trade(ticker.upper(), chosen_amt, exec_price)
        
        # Check post-trade balance
        post_bal = call_tickertape_mcp(token, "us_account_balance")
        post_avail = post_bal.get("availableFunds", "unknown") if isinstance(post_bal, dict) else "unknown"
        print(f"[*] Remaining Available Funds: ${post_avail} USD")
        return {"status": "SUCCESS", "orderId": order_id, "amount": chosen_amt, "remaining": post_avail}
    else:
        print(f"[FAILURE] Order placement failed: {res}")
        return {"status": "FAILED", "details": res}
