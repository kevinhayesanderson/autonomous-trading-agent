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

def topup_active_holdings(mode: str = "balanced", execute: bool = False) -> Dict[str, Any]:
    """
    Tops up existing active conviction holdings (TSM, ASML, MU) using available settled cash.
    Modes:
    - 'balanced': Prioritizes underweight positions (e.g. MU) to bring all 3 into 33.3% equal portfolio weighting.
    - 'equal': Splits deployable funds equally across all 3 active holdings.
    """
    from .risk import audit_portfolio_health
    token = get_tickertape_token()
    bal = call_tickertape_mcp(token, "us_account_balance")
    avail = float(bal.get("availableFunds", 0.0)) if isinstance(bal, dict) else 0.0

    print("=" * 80)
    print(f" TOP-UP ACTIVE CONVICTION HOLDINGS (TSM, ASML, MU) | MODE: {mode.upper()}")
    print("=" * 80)
    print(f"[*] Available Settled Cash: ${avail:.2f} USD")

    if avail < 3.0:
        print("[!] Insufficient funds to top up holdings (minimum $3.00 USD required).")
        return {"status": "INSUFFICIENT_FUNDS", "available": avail}

    _, holdings = audit_portfolio_health(token)
    active_map = {h["ticker"]: h for h in holdings if float(h.get("current", 0.0)) > 1.0}
    active_tickers = list(active_map.keys())
    if not active_tickers:
        active_tickers = [h["ticker"] for h in holdings]

    if not active_tickers:
        print("[!] No active holdings found to top up.")
        return {"status": "NO_ACTIVE_HOLDINGS", "available": avail}

    total_current_equity = sum(h["current"] for h in active_map.values())
    total_capital = total_current_equity + avail
    target_equity_per_asset = total_capital / len(active_tickers)

    # Obey 50% rolling wallet drain limit for immediate execution tranche
    spendable_tranche = round(min(avail * 0.49, avail - 1.0), 2)
    print(f"[*] 50% Rolling Safety Tranche Limit: ${spendable_tranche:.2f} USD (Max allowable per 60m window)")

    allocations = []
    if mode == "balanced":
        # Calculate shortfall to reach target_equity_per_asset
        shortfalls = {}
        for t in active_tickers:
            sf = max(0.0, target_equity_per_asset - active_map[t]["current"])
            shortfalls[t] = sf
        total_sf = sum(shortfalls.values())
        if total_sf > 0:
            for t in active_tickers:
                alloc_amt = round((shortfalls[t] / total_sf) * spendable_tranche, 2)
                if alloc_amt >= 1.0:
                    allocations.append({"ticker": t, "amount": alloc_amt, "target": target_equity_per_asset})
        else:
            per_stock = round(spendable_tranche / len(active_tickers), 2)
            for t in active_tickers:
                allocations.append({"ticker": t, "amount": per_stock, "target": target_equity_per_asset})
    else:  # equal
        per_stock = round(spendable_tranche / len(active_tickers), 2)
        for t in active_tickers:
            allocations.append({"ticker": t, "amount": per_stock, "target": target_equity_per_asset})

    total_alloc = sum(a["amount"] for a in allocations)
    if total_alloc > spendable_tranche and allocations:
        allocations[0]["amount"] = round(allocations[0]["amount"] - (total_alloc - spendable_tranche), 2)

    print("\n--- Proposed Allocation Plan ---")
    print(f" {'Ticker':<8} | {'Current Equity':<16} | {'Proposed Top-Up':<18} | {'Target Weight'}")
    print("-" * 65)
    for a in allocations:
        t = a["ticker"]
        cur = active_map[t]["current"]
        new_tot = cur + a["amount"]
        proj_wt = (new_tot / (total_current_equity + spendable_tranche)) * 100.0
        print(f" {t:<8} | ${cur:>10.2f} USD   | +${a['amount']:>10.2f} USD     | {proj_wt:>5.1f}%")
    print("-" * 65)
    print(f"  * Total Tranche Deployed:  ${sum(a['amount'] for a in allocations):.2f} USD")
    print(f"  * Residual Cash for Next Window: ${avail - sum(a['amount'] for a in allocations):.2f} USD")

    if not execute:
        print("\n[PREVIEW MODE] To execute this top-up live, run: python agent.py topup --execute")
        return {"status": "PREVIEW", "allocations": allocations, "spendable_tranche": spendable_tranche}

    print("\n[*] Committing live top-up orders with resilience...")
    executed_orders = []
    for a in allocations:
        t = a["ticker"]
        amt = a["amount"]
        print(f"  -> Placing BUY for {t} (${amt:.2f} USD)...")
        res = place_order_with_resilience(token, ticker=t, action="buy", amount=amt)
        if res.get("status") == "SUCCESS":
            oid = res.get("orderId")
            print(f"  [SUCCESS] {t} BUY filled: Order ID {oid}")
            record_drain_trade(t, amt, res.get("executionPrice", 0.0))
            executed_orders.append({"ticker": t, "orderId": oid, "amount": amt})
        else:
            print(f"  [FAILURE] {t} order failed: {res.get('code')}")

    return {"status": "COMPLETED", "orders": executed_orders}
