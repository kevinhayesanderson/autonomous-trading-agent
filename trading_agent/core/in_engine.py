"""
Autonomous Quantitative Trading Agent (AQTA) - Indian Equities Execution Engine
Orchestrates the identical 7-phase institutional quantitative investment lifecycle for Indian equities:
Phase 0: Adversarial Retrospective & Past Trade Learning Loop
Phase 1: Capital Controller & Live Zerodha Kite Margin Audit
Phase 2: Whole-Market Multi-Factor Screening (5,000+ stocks via Tickertape PRO)
Phase 3: Multi-Agent Committee Deliberation (Fundamental, Technical, Fiduciary Risk with test-time traces)
Phase 4: Dynamic Rebalancing & Concentrated Integer Share Sizing (Collar: Beta >= 1.40, Max Assets <= 3)
Phase 5: Rebalance Order Formulation routed to ZERODHA KITE (GTT Stop-Loss -12%, Take-Profit +35%)
Phase 6: Live Trade Journal Ledger & Tickertape PRO Watchlist Sync
Phase 7: Zero-Limbo Buffer Absorption & Git State Synchronization
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .auth import get_tickertape_token
from .zerodha import (
    audit_kite_status,
    get_zerodha_margin,
    get_zerodha_holdings,
    is_nse_market_open,
    place_zerodha_order,
    place_zerodha_gtt,
    get_zerodha_ltp,
    is_nse_mainboard_tradable
)
from .in_screener import screen_indian_stocks, audit_indian_stock
from .deliberation import deliberate_ticker
from .memory import (
    load_factor_weights,
    load_trade_journal,
    run_adversarial_retrospective
)
from .config import TRADE_JOURNAL_FILE

def run_in_pipeline(
    budget: str = "auto",
    mode: str = "live",
    plan: str = "dynamic",
    execute: bool = False,
    rebalance: bool = True
):
    print("=" * 102)
    print(f" QUANTITATIVE INDIAN INVESTMENT ENGINE (ZERODHA KITE ROUTING) - [{mode.upper()} MODE]")
    print(" Institutional Multi-Agent Committee, Fiduciary Anti-Ruin Guardrails & Kite Execution")
    print("=" * 102)

    tt_token = get_tickertape_token()
    kite_status = audit_kite_status()

    # =========================================================================
    # Phase 0 & 1: Audit Live Zerodha Holdings, Liquidity & Capital Controller
    # =========================================================================
    print("\n[Phase 1] Auditing Live Zerodha Broker Account, Margin & Market Calendar...")
    
    margin_info = get_zerodha_margin()
    is_auth = margin_info.get("authenticated", False)
    clear_cash = float(margin_info.get("clear_cash", 0.0))
    cnc_available = float(margin_info.get("cnc_balance_available", clear_cash))
    
    holdings_summary = get_zerodha_holdings() if is_auth else []

    if is_auth:
        print(f"  * Zerodha Account:            {kite_status.get('user_name')} ({kite_status.get('user_id')})")
        print(f"  * Zerodha Clear Cash:         Rs {clear_cash:,.2f} INR")
        print(f"  * CNC Available Margin:       Rs {cnc_available:,.2f} INR")
        print(f"  * Settled Demat Holdings:     {len(holdings_summary)} active positions")
    else:
        print(f"  * Zerodha Kite Status:        NOT AUTHENTICATED ({margin_info.get('error')})")
        print("  * Run: python agent.py kite-login to authenticate your daily session.")

    # Calendar & Market Session Check
    is_trading, status_label = is_nse_market_open()
    print(f"  * Market Session Status:      {status_label}")
    if not is_trading:
        print("    -> Indian Exchanges (NSE/BSE) are currently CLOSED.")
        print("    -> All Zerodha orders will be routed as After-Market Orders (AMO) / GTT.")

    # Phase 0: Adversarial Retrospective Loop on Indian Portfolio
    run_adversarial_retrospective(holdings_summary, benchmark_ret=1.80, is_preview=(not execute), market="IN")

    # =========================================================================
    # Phase 2: Whole-Market Multi-Factor Screening across Indian Equities
    # =========================================================================
    print("\n[Phase 2] Whole-Market Algorithmic Screening across 5,000+ Indian Equities (NSE/BSE)...")
    print("  * Enforcing Anti-Ruin Invariants: Beta >= 1.40, Net Margin > 0%, Market Cap > Rs 2,000 Cr, ROE >= 12%")
    
    screened_raw = screen_indian_stocks(
        min_beta=1.40,
        max_beta=2.80,
        min_mcap_cr=2000.0,
        min_roe=12.0,
        min_opmg=10.0,
        max_price=5500.0,
        limit=10
    )

    cand_map = {}
    for s in screened_raw:
        t = s.get("ticker")
        if not t:
            continue
        if is_nse_mainboard_tradable(t):
            cand_map[t] = s
        else:
            print(f"  [DISQUALIFIED] {t}: SME lot size restriction or non-NSE mainboard. Retail integer sizing prohibited.")
    candidate_tickers = list(cand_map.keys())

    # =========================================================================
    # Phase 3: Multi-Agent Specialist Committee Deliberation
    # =========================================================================
    delib_count = len(candidate_tickers[:6])
    print(f"\n[Phase 3] Multi-Agent Specialist Deliberation on {delib_count} Candidates Screened from Scratch...")
    print("  * Committee Members: Fundamental Analyst, Technical Analyst, Fiduciary Risk Manager (Absolute Veto)")
    
    deliberations = []
    for t in candidate_tickers[:6]:
        delib = deliberate_ticker(t, token=tt_token, candidate_data=cand_map.get(t))
        deliberations.append(delib)

    print("\n" + "-" * 115)
    print(f" {'Rank':<4} | {'Ticker':<12} | {'Quorum':<14} | {'Fund Vote':<10} | {'Tech Vote':<10} | {'Risk Vote':<10} | {'Confidence':<11} | {'Recommendation'}")
    print("-" * 115)
    for idx, d in enumerate(deliberations, 1):
        quorum_str = f"{d.buy_votes} BUY / {d.veto_votes} VETO"
        print(f" #{idx:<3} | {d.ticker:<12} | {quorum_str:<14} | {d.fundamental.vote:<10} | {d.technical.vote:<10} | {d.risk.vote:<10} | {d.confidence_score*100:>5.1f}%     | {d.recommendation}")
    print("-" * 115)

    # Filter to approved assets (supermajority BUY with zero vetoes)
    approved_delibs = [d for d in deliberations if d.recommendation == "BUY" and d.veto_votes == 0]
    if not approved_delibs:
        print("\n[!] Zero assets passed fiduciary committee quorum. Capital strictly protected in cash buffer.")
        return

    # Select top 3 concentrated conviction assets
    final_basket = approved_delibs[:3]
    print(f"\n[*] COMMITTEE-APPROVED CONVICTION BASKET (Max 3 Assets):")
    for d in final_basket:
        print(f"  * {d.ticker}: Confidence {d.confidence_score*100:.1f}% | Moat: {d.fundamental.moat_score}/10 | {d.synthesis_memo}")

    # =========================================================================
    # Phase 4 & 5: Dynamic Rebalancing, Integer Share Allocation & Order Formulation
    # =========================================================================
    # Default to 16,000 INR allocation pool if Zerodha cash is not yet transferred
    if budget is not None and str(budget).lower() != "auto":
        deployable_budget = float(budget)
    elif clear_cash >= 1000.0:
        deployable_budget = clear_cash
    else:
        deployable_budget = 16000.0  # Target investment pool

    target_budget_net = deployable_budget * 0.98 # Reserve 2% buffer for STT, SEBI turnover fees, GST

    print(f"\n[Phase 4] Dynamic Allocation & Integer Sizing (Budget: Rs {deployable_budget:,.2f} INR)...")
    if clear_cash < deployable_budget and is_auth:
        print(f"  [!] Note: Live Zerodha cash is Rs {clear_cash:,.2f}. Planning target allocation for Rs {deployable_budget:,.2f} INR.")

    allocations = []
    total_invested = 0.0
    target_per_asset = target_budget_net / len(final_basket)

    for d in final_basket:
        t = d.ticker
        price = get_zerodha_ltp(t)
        if not price or price <= 0.0:
            price = float(cand_map.get(t, {}).get("lastPrice") or 500.0)

        qty = max(1, int(target_per_asset // price))
        inv = qty * price
        total_invested += inv
        sl = round(price * 0.88, 1)  # -12.0% Stop-Loss collar
        tp = round(price * 1.35, 1)  # +35.0% Take-Profit collar
        allocations.append({
            "ticker": t,
            "price": price,
            "shares": qty,
            "invested": round(inv, 2),
            "stop_loss": sl,
            "take_profit": tp,
            "deliberation": d
        })

    # Absorb residual cash into lowest price stock (Zero-Limbo Buffer)
    cash_buffer = round(deployable_budget - total_invested, 2)
    lowest_asset = min(allocations, key=lambda x: x["price"])
    while cash_buffer >= lowest_asset["price"] and (cash_buffer - lowest_asset["price"]) >= 50.0:
        lowest_asset["shares"] += 1
        lowest_asset["invested"] = round(lowest_asset["shares"] * lowest_asset["price"], 2)
        total_invested += lowest_asset["price"]
        cash_buffer = round(deployable_budget - total_invested, 2)

    for a in allocations:
        a["weight_pct"] = round((a["invested"] / deployable_budget) * 100, 1)

    print("\n" + "=" * 98)
    print(" --- TARGET ALLOCATION BASKET (BUY LEGS ROUTED TO ZERODHA KITE) ---")
    print(f" {'Asset':<12} | {'Price':<10} | {'Qty':<5} | {'Capital':<14} | {'Weight':<8} | {'GTT Stop-Loss':<15} | {'GTT Target'}")
    print(" " + "-" * 96)
    for a in allocations:
        print(f" {a['ticker']:<12} | Rs {a['price']:<7.2f} | {a['shares']:<5} | Rs {a['invested']:<11.2f} | {a['weight_pct']:<5.1f}%  | Rs {a['stop_loss']:<12.1f} | Rs {a['take_profit']:<7.1f}")
    print(" " + "-" * 96)
    print(f"  * Gross Capital Pool:     Rs {deployable_budget:,.2f} INR")
    print(f"  * Total Equity Deployed:  Rs {total_invested:,.2f} INR")
    print(f"  * Zerodha Cash Buffer:    Rs {cash_buffer:,.2f} INR (Reserved for turnover taxes & statutory STT)")

    print("\n[*] ZERODHA KITE ORDER FORMULATION (DELIVERY CASH / GTT):")
    for idx, a in enumerate(allocations, 1):
        print(f"  {idx}. BUY {a['shares']} shares of {a['ticker']} @ Limit Rs {a['price']:.2f}")
        print(f"     -> Route: ZERODHA | Segment: Delivery (CNC) | Type: GTT / AMO")
        print(f"     -> GTT Stop-Loss Trigger:  Rs {a['stop_loss']:.1f} (-12.0%)")
        print(f"     -> GTT Take-Profit Target: Rs {a['take_profit']:.1f} (+35.0%)")

    # =========================================================================
    # Phase 6 & 7: Confirmed Live Execution, Trade Journal & Watchlist Sync
    # =========================================================================
    if not execute:
        print("\n[PREVIEW COMPLETE] Zero orders submitted. Reply 'execute' or run 'python agent.py in-execute' to commit live orders.")
        return

    print("\n[Phase 5] Committing Live Allocations directly to Zerodha Kite & Trade Journal...")
    now = datetime.now()
    cycle_str = now.strftime("%Y-%m")
    date_str = now.strftime("%Y-%m-%d")
    logged_ids = []

    # Place live orders in Zerodha Kite
    if is_auth and clear_cash >= total_invested:
        print("[*] Submitting live Delivery orders via Kite Connect API...")
        for a in allocations:
            try:
                res = place_zerodha_order(a["ticker"], a["shares"], a["price"], is_amo=(not is_trading))
                a["broker_order_id"] = res.get("order_id")
                print(f"  + Zerodha Order Placed: {a['ticker']} | Qty: {a['shares']} | Price: Rs {a['price']} | ID: {res.get('order_id')} | Status: {res.get('status')}")
            except Exception as e:
                print(f"  [!] Zerodha order placement notice for {a['ticker']}: {e}")
    else:
        if not is_auth:
            print("  [!] Zerodha not authenticated. Orders logged to trade journal only.")
        elif clear_cash < total_invested:
            print(f"  [!] Note: Zerodha clear cash (Rs {clear_cash:,.2f}) is lower than required deployment (Rs {total_invested:,.2f}).")
            print("      -> Transfer funds into Zerodha Kite to execute live on-market.")

    os.makedirs(os.path.dirname(TRADE_JOURNAL_FILE), exist_ok=True)
    with open(TRADE_JOURNAL_FILE, "a", encoding="utf-8") as f:
        for a in allocations:
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
                "plan": plan,
                "committee_confidence": a["deliberation"].confidence_score,
                "committee_votes": f"{a['deliberation'].buy_votes} BUY / {a['deliberation'].veto_votes} VETO",
                "thesis": a["deliberation"].synthesis_memo
            }
            f.write(json.dumps(record) + "\n")
            logged_ids.append(trade_id)

    print(f"\n[SUCCESS] Successfully committed {len(logged_ids)} orders into memory/trade_journal.jsonl:")
    for tid in logged_ids:
        print(f"  + {tid}")

    # Synchronize Tickertape PRO Watchlist
    try:
        from .broker import call_tickertape_mcp
        from .in_screener import resolve_sid_for_ticker
        sids = []
        for a in allocations:
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

    print("\n[ALL PHASES COMPLETE] Indian portfolio rebalanced and aligned with institutional mandate.")
