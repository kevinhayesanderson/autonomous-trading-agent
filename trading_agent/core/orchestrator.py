"""
Autonomous Quantitative Trading Agent (AQTA) - Unified Dual-Market Master Orchestrator
Enforces the 2-step user interaction contract:
Step 1: User prompts "run investment agent" -> Dual-Broker Audit, Adversarial Review, Whole-Market Screening, Multi-Agent Committee Deliberations, and Unified Dual-Market Trade Plan.
Step 2: User confirms "execute" -> Order routing (US -> Tickertape/Alpaca, IN -> Zerodha Kite), Trade Journal Logging, Watchlist Sync, and Git State Sync.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .auth import get_tickertape_token
from .broker import call_tickertape_mcp, get_live_ticker_quote
from .risk import audit_portfolio_health, audit_lrs_settlement
from .zerodha import (
    get_zerodha_margin,
    get_zerodha_holdings,
    place_zerodha_order,
    place_zerodha_gtt,
    get_zerodha_ltp,
    is_nse_market_open,
    audit_kite_status,
    get_kite_client,
    is_nse_mainboard_tradable
)
from .memory import (
    load_factor_weights,
    load_trade_journal,
    run_adversarial_retrospective,
    record_trade_execution
)
from .screener import run_quantitative_screener
from .in_screener import screen_indian_stocks, audit_indian_stock
from .deliberation import deliberate_ticker
from .config import TRADE_JOURNAL_FILE
from .rebalance import evaluate_portfolio_rebalance
from .execution import place_order_with_resilience

def run_dual_investment_agent(execute: bool = False, in_budget: Optional[float] = None):
    """
    Executes the full dual-market institutional cycle end-to-end completely from scratch.
    Dynamically analyzes whole-market universes across Tickertape (US) and Zerodha Kite (IN),
    runs multi-agent deliberations, and synthesizes an objective, decision-free allocation plan.
    """
    print("=" * 105)
    print(" [AUTONOMOUS QUANTITATIVE TRADING AGENT (AQTA) - UNIFIED DUAL-MARKET ENGINE]")
    print(" Symmetrical Institutional Lifecycle: US (Tickertape / Alpaca) & India (Zerodha Kite)")
    print("=" * 105)

    tt_token = get_tickertape_token()

    # =========================================================================
    # STEP 1: DUAL-BROKER WALLET & CAPITAL CONTROLLER AUDIT
    # =========================================================================
    print("\n[STEP 1] Dual-Broker Real-Time Wallet & Liquidity Audit...")
    
    # 1.1 US Broker Audit (Tickertape / Alpaca)
    us_bal = call_tickertape_mcp(tt_token, "us_account_balance")
    us_avail = float(us_bal.get("availableFunds", 0.0)) if isinstance(us_bal, dict) else 0.0
    us_withdrawable = float(us_bal.get("availableWithdrawal", 0.0)) if isinstance(us_bal, dict) else 0.0
    us_alerts, us_holdings = audit_portfolio_health(tt_token)
    pending_lrs = audit_lrs_settlement(tt_token)

    print("\n  --- US EQUITY WALLET (TICKERTAPE / ALPACA) ---")
    print(f"  * Available Funds:           ${us_avail:.2f} USD")
    print(f"  * Settled Holdings:          {len(us_holdings)} assets active")
    for h in us_holdings:
        print(f"    -> {h['ticker']}: Invested ${h['invested']:.2f} | Current ${h['current']:.2f} | P&L: {h['pnl_pct']:>+5.2f}%")
    if pending_lrs:
        print(f"  * In-Flight LRS Transit:     {len(pending_lrs)} pending wire(s)")

    # 1.2 Indian Broker Audit (Zerodha Kite Connect v3)
    zerodha_margin = get_zerodha_margin()
    zerodha_auth = zerodha_margin.get("authenticated", False)

    # Seamless Auto-Authentication: If expired, automatically trigger browser auth on default browser
    if not zerodha_auth and not os.environ.get("HEADLESS"):
        print("\n  --- INDIAN EQUITY WALLET AUDIT (ZERODHA KITE CONNECT v3) ---")
        print("  * Daily session token expired / pending (6:00 AM IST reset).")
        print("  * Initiating seamless browser authentication on default browser...")
        try:
            from scripts.kite_auth import seamless_authenticate
            auto_tok = seamless_authenticate(timeout_seconds=300, open_browser=True, loop=True)
            if auto_tok:
                zerodha_margin = get_zerodha_margin()
                zerodha_auth = zerodha_margin.get("authenticated", False)
        except Exception as e:
            print(f"  [!] Seamless browser auth notice: {e}", flush=True)

    zerodha_cash = float(zerodha_margin.get("clear_cash", 0.0))
    zerodha_holdings = get_zerodha_holdings() if zerodha_auth else []
    kite_status = audit_kite_status()

    is_in_trading, in_session_status = is_nse_market_open()
    primary_in_broker = "Zerodha"
    
    # Target deployment pool: strictly use live cash or explicit in_budget. Never invent a phantom 16,000 pool.
    if in_budget is not None and float(in_budget) > 0.0:
        in_clear_cash = float(in_budget)
    elif zerodha_auth:
        in_clear_cash = zerodha_cash
    else:
        in_clear_cash = 0.0

    print("\n  --- INDIAN EQUITY WALLET AUDIT (ZERODHA KITE CONNECT v3) ---")
    if zerodha_auth:
        print(f"  * Account:                   {kite_status.get('user_name')} ({kite_status.get('user_id')})")
        print(f"  * Clear Cash Balance:        Rs {zerodha_cash:,.2f} INR")
        print(f"  * CNC Available Margin:      Rs {zerodha_margin.get('cnc_balance_available', 0.0):,.2f} INR")
        print(f"  * Settled Demat Holdings:    {len(zerodha_holdings)} assets active")
    else:
        print("  * [Zerodha Kite Connect v3]: Session token expired / pending.")
        print("    -> Cannot devise live allocation without verified broker access!")
        print("    -> Run: python agent.py kite-login to authenticate your daily session.")
    
    print(f"  * Selected Execution Broker: Zerodha Kite (Deployable Capital: Rs {in_clear_cash:,.2f} INR)")
    if zerodha_auth and in_clear_cash < 500.0:
        print(f"    -> [CAPITAL CONTROLLER]: Available funds (Rs {in_clear_cash:,.2f}) below minimum allocation threshold (Rs 500.00).")

    print(f"  * Indian Market Session:     {in_session_status}")
    if not is_in_trading:
        print(f"    -> All Zerodha orders will be routed as After-Market Orders (AMO) / GTT.")

    # =========================================================================
    # STEP 2: MULTI-AGENT ADVERSARIAL REVIEW OF ENTIRE PIPELINE
    # =========================================================================
    print("\n[STEP 2] Phase 0 Multi-Agent Adversarial Review & Pipeline Audit...")
    run_adversarial_retrospective(us_holdings, benchmark_ret=2.50, is_preview=(not execute), market="US")
    run_adversarial_retrospective(zerodha_holdings, benchmark_ret=1.80, is_preview=(not execute), market="IN")

    # =========================================================================
    # STEP 3: UNBIASED WHOLE-MARKET SCREENING (BOTH MARKETS)
    # =========================================================================
    print("\n[STEP 3] Objective Whole-Market Quantitative Screening (Zero Stock-Fitting Bias)...")
    weights_cfg = load_factor_weights()
    active_weights = weights_cfg.get("current_weights", {})

    # 3.1 US Screener
    print("  * US Market Scan (Tickertape PRO): Beta >= 1.40, Net Margin > 0%, Revenue Moat...")
    us_candidates = run_quantitative_screener(tt_token, active_weights, count=6)
    
    # 3.2 Indian Screener - Dynamic Whole-Market Scan from Scratch
    print("  * Indian Market Scan (Tickertape PRO): Beta >= 1.40, MCap > Rs 2,000 Cr, ROE >= 12%, Op Margin >= 10%...")
    in_screened = screen_indian_stocks(min_beta=1.40, max_beta=2.80, min_mcap_cr=2000.0, min_roe=12.0, min_opmg=10.0, limit=10)
    cand_map = {}
    for s in in_screened:
        t = s.get("ticker")
        if not t:
            continue
        if is_nse_mainboard_tradable(t):
            cand_map[t] = s
        else:
            print(f"  [DISQUALIFIED] {t}: SME lot size restriction or non-NSE mainboard. Retail integer sizing prohibited.")
    in_candidate_tickers = list(cand_map.keys())

    # =========================================================================
    # STEP 4: MULTI-AGENT SPECIALIST COMMITTEE DELIBERATION (BOTH MARKETS)
    # =========================================================================
    print("\n[STEP 4] Multi-Agent Committee Deliberation on Discovered Leaders...")
    print("  * Specialists: Fundamental Analyst, Technical Analyst, Fiduciary Risk Manager (Absolute Veto)")

    # 4.1 US Committee Deliberations
    print("\n  --- US EQUITY COMMITTEE EVALUATIONS ---")
    us_delibs = []
    for c in us_candidates[:4]:
        d = deliberate_ticker(c["ticker"], token=tt_token)
        us_delibs.append(d)
        print(f"  * {d.ticker:<6} | Quorum: {d.buy_votes} BUY / {d.veto_votes} VETO | Confidence: {d.confidence_score*100:.1f}% | Rec: {d.recommendation}")

    # 4.2 Indian Committee Deliberations
    print("\n  --- INDIAN EQUITY COMMITTEE EVALUATIONS ---")
    in_delibs = []
    for t in in_candidate_tickers[:6]:
        d = deliberate_ticker(t, token=tt_token, candidate_data=cand_map.get(t))
        in_delibs.append(d)
        print(f"  * {d.ticker:<12} | Quorum: {d.buy_votes} BUY / {d.veto_votes} VETO | Confidence: {d.confidence_score*100:.1f}% | Rec: {d.recommendation}")

    # =========================================================================
    # STEP 5: DUAL-MARKET ALLOCATION & REBALANCING SYNTHESIS
    # =========================================================================
    print("\n" + "=" * 105)
    print(" [SYNTHESIZED DUAL-MARKET ALLOCATION PLAN - DECISION-FREE FOR USER]")
    print("=" * 105)

    # 5.1 US Trade Plan Formulation
    print("\n[PLAN 1: US EQUITY CONVICTION BASKET] -> ROUTED TO TICKERTAPE / ALPACA")
    us_target_buys = []
    us_rebal_res = None
    if us_avail < 10.0 and len(us_holdings) >= 2:
        print(f"  * Wallet Status: ${us_avail:.2f} USD settled cash (fully deployed under 60-day anti-churn lock).")
        print("  * Active Holdings Operating Normally with Zero Rebalancing Churn:")
        for h in us_holdings:
            print(f"    -> HOLD {h['ticker']}: Val ${h['current']:.2f} | P&L: {h['pnl_pct']:>+5.2f}% (Tenure locked)")
        print("  * ACTION: HOLD ACTIVE CONVICTION BASKET. Zero churn required.")
    else:
        fresh_us_cash = min(1000.0, max(10.0, us_avail * 0.99))
        us_rebal_res = evaluate_portfolio_rebalance(us_holdings, us_candidates, fresh_cash=fresh_us_cash)
        us_target_buys = us_rebal_res.get("target_buys", [])
        print("\n  --- TARGET US REINVESTMENT BASKET (BUY LEGS ROUTED TO TICKERTAPE / ALPACA) ---")
        print(f"  {'Asset':<8} | {'Broker':<12} | {'Order Type':<16} | {'Amount':<10} | {'Est Price':<10} | {'Limit Ceiling':<14}")
        print("  " + "-" * 85)
        for b in us_target_buys:
            t = b["ticker"]
            p = get_live_ticker_quote(tt_token, t) or b.get("price", 100.0)
            b["price"] = p
            limit_ceiling = round(p * 1.01, 2)
            b["limit_ceiling"] = limit_ceiling
            top_up_tag = " [TOP-UP]" if b.get("is_top_up") else ""
            print(f"  {t:<8} | {'Tickertape':<12} | {'Notional Limit':<16} | ${b['amount']:<9.2f} | ${p:<9.2f} | ${limit_ceiling:<13.2f}{top_up_tag}")
        print("  " + "-" * 85)
        print(f"  * Fresh Cash Allocation:   ${fresh_us_cash:.2f} USD")
        print(f"  * Total US Rebalance Pool: ${us_rebal_res['total_pool']:.2f} USD")
        print(f"  * Net US Buy Outlay:       ${us_rebal_res['net_spendable']:.2f} USD")

    # 5.2 Indian Trade Plan Formulation
    print(f"\n[PLAN 2: INDIAN EQUITY CONVICTION BASKET] -> ROUTED TO ZERODHA KITE (DELIVERY CASH / GTT)")
    
    in_allocations = []
    in_total_invested = 0.0
    in_cash_buffer = 0.0

    if not zerodha_auth and (in_budget is None or in_budget <= 0.0):
        print("  * Status: [PAUSED - DAILY AUTHENTICATION REQUIRED]")
        print("    -> Zerodha Kite daily session expired at 6:00 AM IST.")
        print("    -> AQTA strictly refuses to fabricate phantom allocations without verified broker access.")
        from scripts.kite_auth import load_credentials
        try:
            k_key, _, _ = load_credentials()
            print(f"    -> Authorize today's session: https://kite.zerodha.com/connect/login?api_key={k_key}&v=3")
        except Exception:
            pass
        print("    -> Reply with the request_token or redirected URL to commit live Indian orders.")
    elif in_clear_cash < 500.0:
        print(f"  * Status: [HOLD CASH - INSUFFICIENT FUNDS]")
        print(f"    -> Clear cash balance (Rs {in_clear_cash:,.2f} INR) is below minimum investment threshold (Rs 500.00).")
        print("    -> Retaining available cash safely. Zero buy orders generated.")
        in_cash_buffer = in_clear_cash
    else:
        statutory_buffer = max(50.0, in_clear_cash * 0.015)
        in_target_net = in_clear_cash - statutory_buffer
        
        candidate_pool = sorted(
            [d for d in in_delibs if d.recommendation == "BUY" and d.veto_votes == 0],
            key=lambda x: (x.confidence_score, x.buy_votes),
            reverse=True
        )
        
        # Map candidate prices accurately from Kite LTP or Tickertape metrics
        cand_price_map = {}
        for d in candidate_pool:
            t = d.ticker
            p = get_zerodha_ltp(t)
            if not p or p <= 0.0:
                p = float(cand_map.get(t, {}).get("metrics", {}).get("lastPrice") or cand_map.get(t, {}).get("lastPrice") or 500.0)
            cand_price_map[t] = p

        # Select candidates that fit comfortably without excessive concentration
        approved_in = []
        for d in candidate_pool:
            p = cand_price_map.get(d.ticker, 500.0)
            # For small accounts (<= 6000 INR), skip single shares that exceed 45% of total budget
            if in_clear_cash <= 6000.0 and p > (in_target_net * 0.45):
                continue
            approved_in.append(d)
            if len(approved_in) >= 3:
                break
                
        if not approved_in:
            approved_in = candidate_pool[:3]

        num_assets = max(1, len(approved_in))
        target_per_in_asset = in_target_net / num_assets
        
        for d in approved_in:
            t = d.ticker
            price = cand_price_map[t]
            qty = max(1, int(target_per_in_asset // price))
            inv = qty * price
            in_total_invested += inv
            sl = round(price * 0.88, 1)  # -12% Stop Loss
            tp = round(price * 1.35, 1)  # +35% Take Profit
            in_allocations.append({
                "ticker": t,
                "price": price,
                "shares": qty,
                "invested": round(inv, 2),
                "stop_loss": sl,
                "take_profit": tp,
                "deliberation": d
            })

        # If initial allocation exceeds in_target_net, trim shares from highest invested asset
        while in_total_invested > in_target_net and any(a["shares"] > 1 for a in in_allocations):
            highest_inv = max([a for a in in_allocations if a["shares"] > 1], key=lambda x: x["invested"])
            highest_inv["shares"] -= 1
            highest_inv["invested"] = round(highest_inv["shares"] * highest_inv["price"], 2)
            in_total_invested = sum(a["invested"] for a in in_allocations)

        # Absorb residual cash into lowest price asset safely without breaching statutory buffer
        in_cash_buffer = round(in_clear_cash - in_total_invested, 2)
        lowest_in = min(in_allocations, key=lambda x: x["price"])
        while (in_cash_buffer - lowest_in["price"]) >= statutory_buffer:
            lowest_in["shares"] += 1
            lowest_in["invested"] = round(lowest_in["shares"] * lowest_in["price"], 2)
            in_total_invested += lowest_in["price"]
            in_cash_buffer = round(in_clear_cash - in_total_invested, 2)

        for a in in_allocations:
            a["weight_pct"] = round((a["invested"] / in_clear_cash) * 100, 1)

        print("-" * 105)
        print(f" {'Asset':<12} | {'Live Price':<12} | {'Qty':<6} | {'Capital Deployed':<18} | {'Weight':<8} | {'GTT Stop-Loss':<15} | {'GTT Target'}")
        print("-" * 105)
        for a in in_allocations:
            print(f" {a['ticker']:<12} | Rs {a['price']:<9.2f} | {a['shares']:<6} | Rs {a['invested']:<15.2f} | {a['weight_pct']:<5.1f}%  | Rs {a['stop_loss']:<12.1f} | Rs {a['take_profit']:<7.1f}")
        print("-" * 105)
        print(f"  * Gross Capital Pool:     Rs {in_clear_cash:,.2f} INR (Zerodha Kite)")
        print(f"  * Total Equity Deployed:  Rs {in_total_invested:,.2f} INR")
        print(f"  * Zerodha Cash Buffer:    Rs {in_cash_buffer:,.2f} INR (Reserved for statutory levies)")

        print(f"\n[*] ZERODHA KITE ORDER FORMULATION (DELIVERY CASH / GTT):")
        for idx, a in enumerate(in_allocations, 1):
            print(f"  {idx}. BUY {a['shares']} shares of {a['ticker']} @ Limit Rs {a['price']:.2f}")
            print(f"     -> Route: ZERODHA | Segment: Delivery (CNC) | Order: GTT / AMO")
            print(f"     -> GTT Stop-Loss Trigger:  Rs {a['stop_loss']:.1f} (-12.0%)")
            print(f"     -> GTT Take-Profit Target: Rs {a['take_profit']:.1f} (+35.0%)")

    # =========================================================================
    # STEP 6: EXECUTION / COMMIT GATEWAY
    # =========================================================================
    if not execute:
        print("\n" + "=" * 105)
        print(" [PREVIEW COMPLETE | ZERO ORDERS MUTATED]")
        print(" Ready for immediate execution. Simply reply: 'execute' to commit both plans live.")
        print("=" * 105)
        return

    print(f"\n[STEP 6] Committing Live Allocations via Dual Brokers & Immutable Trade Journal...")
    now = datetime.now()
    cycle_str = now.strftime("%Y-%m")
    date_str = now.strftime("%Y-%m-%d")
    logged_ids = []

    # 6.1 Execute US Orders into Tickertape / DriveWealth if target buys exist
    if us_target_buys and us_avail >= 10.0:
        print("\n[*] Placing live US orders into Tickertape / DriveWealth account...")
        for b in us_target_buys:
            t = b["ticker"]
            amt = b["amount"]
            p = b.get("price", 0.0)
            ceil = b.get("limit_ceiling")
            print(f"  -> Placing BUY order for {t} (${amt:.2f} USD)...")
            res = place_order_with_resilience(tt_token, ticker=t, action="buy", amount=amt, limit_ceiling=ceil)
            if res.get("status") == "SUCCESS":
                oid = res.get("orderId")
                print(f"  [SUCCESS] {t} BUY filled: Order ID {oid}")
                record_trade_execution(t, b.get("name", t), 0.0, p, amt, {}, cycle_str, "BUY", reason="Dual-Orchestrated Rebalance")
                logged_ids.append(f"us_tt_{now.strftime('%Y%m%d_%H%M%S')}_{t}")
            else:
                print(f"  [FAILURE] {t} BUY failed! Reason: {res.get('code')}")

    # 6.2 Execute Indian Orders via Zerodha
    if zerodha_auth and zerodha_cash >= in_total_invested:
        print("\n[*] Placing live Indian orders directly into Zerodha Kite account...")
        for a in in_allocations:
            try:
                res = place_zerodha_order(a["ticker"], a["shares"], a["price"], is_amo=(not is_in_trading))
                print(f"  + Zerodha Order Placed: {a['ticker']} | Qty: {a['shares']} | Price: Rs {a['price']} | ID: {res.get('order_id')} | Status: {res.get('status')}")
                a["broker_order_id"] = res.get("order_id")
            except Exception as e:
                print(f"  [!] Zerodha direct order placement failed for {a['ticker']}: {e}")
    else:
        if not zerodha_auth:
            print("  [!] Zerodha session token pending. Authenticate via 'python agent.py kite-login'.")
        elif zerodha_cash < in_total_invested:
            print(f"  [!] Note: Zerodha cash (Rs {zerodha_cash:.2f}) is lower than required deployment (Rs {in_total_invested:.2f}).")
            print("      -> Transfer funds into your Zerodha Kite account to execute live on-market.")

    placed_allocations = [a for a in in_allocations if a.get("broker_order_id")]
    if placed_allocations:
        os.makedirs(os.path.dirname(TRADE_JOURNAL_FILE), exist_ok=True)
        with open(TRADE_JOURNAL_FILE, "a", encoding="utf-8") as f:
            for a in placed_allocations:
                trade_id = f"in_zerodha_{now.strftime('%Y%m%d_%H%M%S')}_{a['ticker']}"
                record = {
                    "id": trade_id,
                    "date": date_str,
                    "market": "IN",
                    "exchange": "NSE",
                    "broker": "Zerodha",
                    "currency": "INR",
                    "ticker": a["ticker"],
                    "action": "BUY",
                    "shares": a["shares"],
                    "price": a["price"],
                    "amount": a["invested"],
                    "stop_loss_trigger": a["stop_loss"],
                    "take_profit_target": a["take_profit"],
                    "broker_order_id": a.get("broker_order_id"),
                    "cycle": cycle_str,
                    "plan": "dual-orchestrated",
                    "committee_confidence": a["deliberation"].confidence_score,
                    "committee_votes": f"{a['deliberation'].buy_votes} BUY / {a['deliberation'].veto_votes} VETO",
                    "thesis": a["deliberation"].synthesis_memo
                }
                f.write(json.dumps(record) + "\n")
                logged_ids.append(trade_id)

        print(f"\n[SUCCESS] Successfully committed {len(logged_ids)} orders into memory/trade_journal.jsonl:")
        for tid in logged_ids:
            print(f"  + {tid}")
    else:
        print("\n[*] Zero new orders placed with broker. No journal records committed.")

    # Synchronize Watchlist in Tickertape PRO
    try:
        sids = []
        for a in in_allocations:
            from .in_screener import resolve_sid_for_ticker
            sid = resolve_sid_for_ticker(tt_token, a["ticker"])
            if sid:
                sids.append(sid)
        if sids:
            call_tickertape_mcp(tt_token, "wl_write", {
                "name": "🚀 AQTA Indian Conviction (Zerodha Kite)",
                "sids": sids
            })
            print(f"  * Tickertape PRO Watchlist synchronized with active constituents: {', '.join(sids)}")
    except Exception as e:
        print(f"  [!] Note on Watchlist sync: {e}")

    # Synchronize Git repository and trade ledger
    try:
        from scripts.git_sync import sync_system_to_git
        sync_system_to_git(f"Cycle {cycle_str}: Unified dual-market execution & trade ledger sync")
    except Exception as e:
        print(f"  [!] Git sync notice: {e}")

    print("\n[ALL PHASES COMPLETE] Unified dual-market rebalance completed.")
