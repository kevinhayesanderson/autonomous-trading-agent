"""
Portfolio Rebalancing & Capital Recycling Engine
Enforces 60-Day Tenure Locks, Turnover Collars, and Fiduciary Concentration Caps.
"""

from typing import Dict, Any, List
from .config import (
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    MAX_PORTFOLIO_ASSETS,
    TURNOVER_SCORE_DELTA,
    TENURE_LOCK_DAYS
)
from .risk import get_holding_tenure_days

def evaluate_portfolio_rebalance(
    active_holdings: List[Dict[str, Any]],
    screened_candidates: List[Dict[str, Any]],
    fresh_cash: float = 51.49
) -> Dict[str, Any]:
    """
    Evaluates active holdings and screened candidates:
    1. Checks Stop-Loss (-12%) and Take-Profit (+35%).
    2. Protects holdings under 60-Day Anti-Churn Tenure Lock.
    3. Replaces seasoned positions only if capacity is full AND delta >= 20.0 pts.
    4. Pools freed capital + fresh inflow.
    5. Sizes target buy baskets (top-ups if full, new leaders if slots available).
    """
    rebalance_actions = []
    freed_cash = 0.0
    retained_holdings = []

    print("\n" + "=" * 96)
    print(" [PORTFOLIO REBALANCING & CAPITAL RECYCLING ENGINE]")
    print("=" * 96)

    # Step 1: Scan active holdings for mandatory exits
    for h in active_holdings:
        t = h.get("ticker")
        pnl = h.get("pnl_pct", 0.0)
        cur_val = h.get("current", 0.0)
        tenure_days = get_holding_tenure_days(t)
        
        cand_match = next((c for c in screened_candidates if c.get("ticker") == t), None)
        holding_q = cand_match.get("consensus_q", cand_match.get("q_score", 55.0)) if cand_match else 55.0

        action = "HOLD"
        reason = f"Operating normally (Score: {holding_q:.1f}, Tenure: {tenure_days}d)"
        amount_to_free = 0.0

        if pnl <= STOP_LOSS_PCT:
            action = "LIQUIDATE_STOP_LOSS"
            reason = f"Loss breached {STOP_LOSS_PCT:.1f}% threshold ({pnl:.2f}%). Capital preservation."
            amount_to_free = cur_val
            freed_cash += cur_val
        elif pnl >= TAKE_PROFIT_PCT:
            action = "TRIM_TAKE_PROFIT"
            reason = f"Gain reached +{TAKE_PROFIT_PCT:.1f}% target (+{pnl:.2f}%). Harvesting 50% profits."
            amount_to_free = round(cur_val * 0.50, 2)
            freed_cash += amount_to_free
            retained_holdings.append({
                "ticker": t,
                "holding_q": holding_q,
                "current_value": cur_val - amount_to_free,
                "tenure_days": tenure_days
            })
        else:
            retained_holdings.append({
                "ticker": t,
                "holding_q": holding_q,
                "current_value": cur_val,
                "tenure_days": tenure_days
            })

        rebalance_actions.append({
            "ticker": t,
            "action": action,
            "current_value": cur_val,
            "pnl_pct": pnl,
            "amount_freed": amount_to_free,
            "reason": reason,
            "tenure_days": tenure_days
        })

    # Step 2: Evaluate Concentration Cap (<= 3 assets) with 60-Day Tenure Lock
    retained_holdings.sort(key=lambda x: x.get("holding_q", 50.0))
    top_candidates = [c for c in screened_candidates if not c.get("has_earnings_risk")]
    best_new_q = top_candidates[0].get("consensus_q", top_candidates[0].get("q_score", 0.0)) if top_candidates else 0.0
    best_new_ticker = top_candidates[0].get("ticker") if top_candidates else None

    # Replace only if capacity exceeded AND tenure >= 60 days AND delta >= 20 pts
    while (len(retained_holdings) + min(2, len(top_candidates))) > MAX_PORTFOLIO_ASSETS and retained_holdings:
        weakest = retained_holdings[0]
        t = weakest["ticker"]
        cur_q = weakest.get("holding_q", 50.0)
        tenure = weakest.get("tenure_days", 0)

        # 60-day tenure protection against churn
        if tenure < TENURE_LOCK_DAYS:
            print(f"  [TENURE LOCK] {t} held for {tenure} days (< {TENURE_LOCK_DAYS} days). Protected from discretionary replacement.")
            break

        if (best_new_q - cur_q) >= TURNOVER_SCORE_DELTA and t not in [c["ticker"] for c in top_candidates[:2]]:
            for ra in rebalance_actions:
                if ra["ticker"] == t and ra["action"] == "HOLD":
                    val = ra["current_value"]
                    ra["action"] = "REPLACE_MOMENTUM_DECAY"
                    ra["reason"] = f"Capacity capped ({MAX_PORTFOLIO_ASSETS} assets, held {tenure}d). Replaced by leader {best_new_ticker} (Delta: +{best_new_q - cur_q:.1f} pts)."
                    ra["amount_freed"] = val
                    freed_cash += val
                    retained_holdings.pop(0)
                    break
        else:
            break

    # Step 3: Capital Recycling & Target Buy Allocation
    total_rebalance_pool = fresh_cash + freed_cash
    sells_count = len([ra for ra in rebalance_actions if ra['amount_freed'] > 0])
    fee_estimate = round((total_rebalance_pool * 0.0015) + ((sells_count + 2) * 0.02), 2)
    net_spendable = max(0.0, total_rebalance_pool - fee_estimate - 0.20)

    print("  --- [1. Rebalance Audit on Active Holdings] ---")
    for ra in rebalance_actions:
        print(f"  * {ra['ticker']:<5} | Status: {ra['action']:<24} | Val: ${ra['current_value']:<6.2f} | P&L: {ra['pnl_pct']:>+6.2f}% | Freed: ${ra['amount_freed']:<5.2f}")
        print(f"    -> Rationale: {ra['reason']}")

    print("\n  --- [2. Capital Recycling Pool] ---")
    print(f"  * Fresh Monthly Inflow:  ${fresh_cash:.2f} USD")
    print(f"  * Proceeds from Sells:   ${freed_cash:.2f} USD")
    print(f"  * Total Rebalance Pool:  ${total_rebalance_pool:.2f} USD (Net Spendable: ${net_spendable:.2f} after fees & buffer)")

    # Step 4: Determine Target Buys obeying Concentration Cap (<= 5 positions)
    available_slots = max(0, MAX_PORTFOLIO_ASSETS - len(retained_holdings))
    target_buys = []

    # Priority: Deploy fresh uncommitted capital into top-scoring screened candidates
    # If a top candidate is already held (e.g. MU), it represents a high-conviction top-up.
    # If a top candidate is new (e.g. DELL), it represents an approved fresh entry.
    candidates_to_buy = top_candidates[:min(max(available_slots, 2), 2)]

    if candidates_to_buy and (available_slots > 0 or any(c["ticker"] in [rh["ticker"] for rh in retained_holdings] for c in candidates_to_buy)):
        split_buy_amt = round(net_spendable / len(candidates_to_buy), 2)
        print("\n  --- [3. Target Buy Allocations (Objective Screener Leaders)] ---")
        for c in candidates_to_buy:
            t = c["ticker"]
            q_val = c.get("consensus_q", c.get("q_score", 0.0))
            is_already_held = t in [rh["ticker"] for rh in retained_holdings]
            label = "TOP-UP" if is_already_held else "BUY"
            target_buys.append({
                "ticker": t,
                "name": c.get("name", t),
                "price": c.get("price", 0.0),
                "amount": split_buy_amt,
                "q_score": q_val,
                "is_top_up": is_already_held
            })
            print(f"  * {label} {t:<5} (${c.get('name', '')[:25]}): ${split_buy_amt:.2f} USD (Consensus Score: {q_val:.2f})")
    elif available_slots == 0:
        # If capacity is full, allocate fresh capital strictly into the highest-scoring screener leaders that are already held
        print("\n  --- [3. Capacity Full: Conviction Top-Up on Highest-Scoring Retained Leader(s)] ---")
        scored_retained = []
        for rh in retained_holdings:
            t = rh["ticker"]
            matching_cand = next((c for c in top_candidates if c.get("ticker") == t), None)
            q_score = matching_cand.get("consensus_q", matching_cand.get("q_score", rh.get("holding_q", 50.0))) if matching_cand else rh.get("holding_q", 50.0)
            scored_retained.append((rh, q_score))
        scored_retained.sort(key=lambda x: x[1], reverse=True)
        top_retained_to_fund = [sr[0] for sr in scored_retained[:min(2, len(scored_retained))]]
        
        split_buy_amt = round(net_spendable / len(top_retained_to_fund), 2) if top_retained_to_fund else 0.0
        for rh in top_retained_to_fund:
            t = rh["ticker"]
            target_buys.append({
                "ticker": t,
                "name": t,
                "price": 0.0,
                "amount": split_buy_amt,
                "q_score": rh.get("holding_q", 50.0),
                "is_top_up": True
            })
            print(f"  * TOP-UP {t:<5}: ${split_buy_amt:.2f} USD (Highest Scoring Retained Leader, Score: {rh.get('holding_q', 50.0):.1f})")
    else:
        split_buy_amt = round(net_spendable / len(candidates_to_buy), 2) if candidates_to_buy else 0.0
        print("\n  --- [3. Target Buy Allocations (Concentrated Conviction Basket)] ---")
        for c in candidates_to_buy:
            q_val = c.get("consensus_q", c.get("q_score", 0.0))
            target_buys.append({
                "ticker": c["ticker"],
                "name": c.get("name", c["ticker"]),
                "price": c.get("price", 0.0),
                "amount": split_buy_amt,
                "q_score": q_val,
                "is_top_up": False
            })
            print(f"  * BUY {c['ticker']:<5} (${c.get('name', '')[:25]}): ${split_buy_amt:.2f} USD (Consensus Score: {q_val:.2f})")

    return {
        "rebalance_actions": rebalance_actions,
        "freed_cash": freed_cash,
        "total_pool": total_rebalance_pool,
        "net_spendable": net_spendable,
        "target_buys": target_buys
    }
