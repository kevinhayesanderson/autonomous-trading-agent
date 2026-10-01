"""
7-Phase Quantitative Execution Engine (AQTA)
Orchestrates market audit, multi-factor screening, committee consensus,
rebalancing calculations, order execution, Zero-Limbo absorption, and Git synchronization.
"""

import sys
from datetime import datetime
from typing import Optional

from .auth import get_tickertape_token
from .broker import call_tickertape_mcp, get_live_ticker_quote
from .risk import audit_lrs_settlement, audit_portfolio_health
from .screener import run_quantitative_screener
from .consensus import score_candidates_with_consensus
from .rebalance import evaluate_portfolio_rebalance
from .execution import place_order_with_resilience
from .memory import (
    load_factor_weights,
    record_trade_execution,
    run_adversarial_retrospective
)

def run_pipeline(
    budget: str = "auto",
    mode: str = "live",
    plan: str = "dynamic",
    execute: bool = False,
    rebalance: bool = True,
    ignore_in_flight: bool = False
):
    budget_label = f"${float(budget):.2f}" if (budget != "auto" and budget is not None) else "AUTO-SIZED"
    print("=" * 96)
    print(f" QUANTITATIVE US INVESTMENT BOT - [{mode.upper()} MODE] - ALLOCATION: {budget_label}")
    print("=" * 96)

    tt_token = get_tickertape_token()

    # Phase 0 & 1: Audit Holdings & LRS Capital Controller
    if mode == "live":
        bal = call_tickertape_mcp(tt_token, "us_account_balance")
        avail_cash = float(bal.get("availableFunds", 0.0)) if isinstance(bal, dict) else 0.0
        pending_deposits = audit_lrs_settlement(tt_token)
        health_alerts, holdings_summary = audit_portfolio_health(tt_token)

        # 3-State Capital Controller
        if pending_deposits:
            print(f"\n[CAPITAL CONTROLLER] Active in-flight Indian banking deposit detected ({len(pending_deposits)} wire).")
            if ignore_in_flight:
                print("  -> User Override Active (--ignore-in-flight): Proceeding with already-settled cash.")
            else:
                print("  -> ZERO-LIMBO SAFETY HALT: Outward remittance is in transit.")
                print(f"     Settled Funds: ${avail_cash:.2f} USD | Status: CAPITAL_IN_FLIGHT")
                print("     Run with --ignore-in-flight to deploy already-settled funds.")
                return

        # Phase 0: Adversarial Retrospective
        run_adversarial_retrospective(holdings_summary, is_preview=(not execute))
    else:
        holdings_summary = []

    # Phase 2: Screener & Technical Scan
    print("\n[Phase 2] Running Dynamic Screener with Tickertape PRO & Adaptive Consensus...")
    weights_cfg = load_factor_weights()
    active_weights = weights_cfg.get("current_weights", {})
    candidates = run_quantitative_screener(tt_token, active_weights, count=10)
    candidates = score_candidates_with_consensus(candidates, active_weights)

    print("\n" + "-" * 118)
    print(f" {'Rank':<4} | {'Ticker':<6} | {'Price':<8} | {'Beta':<5} | {'6M Ret':<8} | {'Fwd EPS':<8} | {'Net Marg':<8} | {'AV RSI':<7} | {'Vote':<6} | {'Consensus Q':<11}")
    print("-" * 118)
    for idx, c in enumerate(candidates, 1):
        rsi_str = f"{c['rsi']:.1f}" if c['rsi'] else "N/A"
        vote_str = c.get("committee_vote", {}).get("recommendation", "HOLD")
        print(f" #{idx:<3} | {c['ticker']:<6} | ${c['price']:<7.2f} | {c['beta']:<5.2f} | {c['ret_6m']:<7.1f}% | {c['eps_fwd']:<7.1f}% | {c['net_margin']:>+6.1f}% | {rsi_str:<7} | {vote_str:<6} | {c['consensus_q']:<11.2f}")
    print("-" * 118)

    # Phase 3 & 4: Portfolio Rebalancing
    if rebalance:
        print("\n[Phase 3] Dynamic Portfolio Rebalancing & Capital Recycling...")
        fresh_cash = 0.0
        if mode == "live":
            is_auto = (budget is None or str(budget).lower() == "auto")
            if is_auto:
                fresh_cash = min(500.0, max(10.0, avail_cash * 0.49))
            else:
                fresh_cash = float(budget)
        else:
            fresh_cash = 55.0 if (budget is None or budget == "auto") else float(budget)

        rebal_res = evaluate_portfolio_rebalance(holdings_summary, candidates, fresh_cash=fresh_cash)
        sells_to_execute = [ra for ra in rebal_res["rebalance_actions"] if ra.get("amount_freed", 0.0) > 0.0]
        target_buys = rebal_res["target_buys"]
        net_spendable = rebal_res["net_spendable"]

        # Phase 5: Rebalance Preview
        print(f"\n[Phase 4] Preparing [{mode.upper()}] Rebalancing Orders...")
        print("\n" + "=" * 96)
        print(" --- PORTFOLIO EXIT & TRIM ORDERS (SELL LEGS) ---")
        if sells_to_execute:
            print(f" {'Asset':<8} | {'Action':<24} | {'Current Val':<12} | {'P&L %':<9} | {'Amount Freed':<13} | {'Reason'}")
            print(" " + "-" * 94)
            for s in sells_to_execute:
                print(f" {s['ticker']:<8} | {s['action']:<24} | ${s['current_value']:<11.2f} | {s['pnl_pct']:>+7.2f}% | ${s['amount_freed']:<12.2f} | {s['reason']}")
        else:
            print("  [OK] No exit or trim triggers fired.")
            print("       Existing holdings are retained under 60-Day Tenure Lock and Turnover Collar.")

        print("\n --- TARGET REINVESTMENT BASKET (BUY LEGS) ---")
        print(f" {'Asset':<8} | {'Broker':<10} | {'Order Type':<14} | {'Amount':<9} | {'Est Price':<10} | {'Limit Ceiling':<14} | {'Est Fees'}")
        print(" " + "-" * 98)
        for b in target_buys:
            t = b["ticker"]
            p = get_live_ticker_quote(tt_token, t) or b.get("price", 100.0)
            b["price"] = p
            limit_ceiling = round(p * 1.01, 2)
            b["limit_ceiling"] = limit_ceiling
            top_up_tag = " [TOP-UP]" if b.get("is_top_up") else ""
            print(f" {t:<8} | {'Tickertape':<10} | {'Notional Limit':<14} | ${b['amount']:<8.2f} | ${p:<9.2f} | ${limit_ceiling:<13.2f} | $0.03 (0.15%){top_up_tag}")
        print(" " + "-" * 98)
        print(f"  * Fresh Cash Allocation:  ${fresh_cash:.2f} USD ({mode.upper()})")
        print(f"  * Recycled Sell Proceeds: ${rebal_res['freed_cash']:.2f} USD")
        print(f"  * Total Rebalance Pool:   ${rebal_res['total_pool']:.2f} USD")
        print(f"  * Net Buy Outlay:         ${net_spendable:.2f} USD")

        if not execute:
            print("\n [PREVIEW COMPLETE] Zero orders submitted. Run with --execute to commit live trades.")
            return

        # Phase 6: Live Execution with Zero-Limbo Protection
        print("\n[Phase 5] Placing Confirmed LIVE Rebalance Orders with Zero-Limbo Protection...")
        
        # Step A: Execute Sell Orders (Stop-Loss / Take-Profit)
        if sells_to_execute:
            print("\n  --- EXECUTING PORTFOLIO SELL LEGS ---")
            for s in sells_to_execute:
                t = s["ticker"]
                amt = s["amount_freed"]
                print(f"  -> Placing SELL order for {t} (${amt:.2f} USD) | Trigger: {s['action']}...")
                s_res = place_order_with_resilience(tt_token, ticker=t, action="sell", amount=amt)
                if s_res.get("status") == "SUCCESS":
                    print(f"  [SUCCESS] {t} SELL filled: Order ID {s_res.get('orderId')}")
                    record_trade_execution(t, t, 0.0, s.get("current_value", amt), amt, {}, datetime.now().strftime("%Y-%m"), "SELL", reason=s.get("reason", "Stop/Profit Trigger"))
                else:
                    print(f"  [WARNING] {t} SELL failed! Error: {s_res.get('code')}")

        # Step B: Execute Buy Orders with Zero-Limbo Protection
        print("\n  --- EXECUTING PORTFOLIO BUY LEGS ---")
        filled_buys = []
        stranded_cash = 0.0
        for idx, b in enumerate(target_buys):
            t = b["ticker"]
            amt = b["amount"]
            p = b.get("price", 0.0)
            ceil = b.get("limit_ceiling")
            print(f"  -> Placing BUY order for {t} (${amt:.2f} USD)...")
            res = place_order_with_resilience(tt_token, ticker=t, action="buy", amount=amt, limit_ceiling=ceil)
            if res.get("status") == "SUCCESS":
                oid = res.get("orderId")
                print(f"  [SUCCESS] {t} BUY filled: Order ID {oid}")
                filled_buys.append((t, amt, oid, p))
                target_obj = next((x for x in candidates if x["ticker"] == t), {})
                record_trade_execution(t, b.get("name", t), 0.0, p, amt, target_obj.get("factors", {}), datetime.now().strftime("%Y-%m"), "BUY")
            else:
                print(f"  [FAILURE] {t} BUY failed! Reason: {res.get('code')}")
                stranded_cash += amt

        # Step C: Zero-Limbo Absorption across any failed leg
        if stranded_cash >= 0.50 and filled_buys:
            fallback_ticker, _, _, fb_price = filled_buys[0]
            print(f"\n  [ZERO-LIMBO ABSORPTION] Reallocating stranded ${stranded_cash:.2f} USD into {fallback_ticker}...")
            fb_res = place_order_with_resilience(tt_token, ticker=fallback_ticker, action="buy", amount=stranded_cash)
            if fb_res.get("status") == "SUCCESS":
                print(f"  [RECOVERY SUCCESS] ${stranded_cash:.2f} absorbed into {fallback_ticker}. ZERO limbo capital!")
                record_trade_execution(fallback_ticker, fallback_ticker, 0.0, fb_price, stranded_cash, {}, datetime.now().strftime("%Y-%m"), "BUY", reason="Zero-Limbo Absorption")

        print(f"\n [SUCCESS] Monthly execution complete. {len(filled_buys)} buy orders verified filled.")

        # Phase 7: Git Sync
        try:
            from scripts.git_sync import sync_system_to_git
            sync_system_to_git(f"Cycle {datetime.now().strftime('%Y-%m')}: Live trade execution & factor calibration")
        except Exception as e:
            print(f"  [!] Git sync notice: {e}")
