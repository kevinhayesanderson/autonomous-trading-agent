#!/usr/bin/env python3
"""
Generic Indian Stock Forensic Audit CLI (Tickertape PRO)
Runs an exhaustive forensic audit on any NSE/BSE stock symbol:
- Scorecards (Profitability, Performance, Growth, Valuation, Entry Point)
- Investment Checklists & Quality Ratios
- Default Probability & Solvency
- ASM / GSM Regulatory Surveillance & Promoter Pledges
- Institutional Float Lock (FII, DII, Mutual Funds, Retail)
- Forward Analyst Consensus (EPS & Revenue Growth, 1Y Price Target)

Usage:
    python scripts/in_stock_audit.py KIRLOSENG
    python scripts/in_stock_audit.py ASTRAMICRO
    python scripts/in_stock_audit.py MARKSANS
"""

import sys
import os
import argparse
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from trading_agent.core.in_screener import audit_indian_stock

def main():
    parser = argparse.ArgumentParser(description="Deep Forensic Audit of Indian Equities via Tickertape PRO")
    parser.add_argument("ticker", help="NSE/BSE stock ticker symbol (e.g. KIRLOSENG, ASTRAMICRO, BEL, ZOMATO)")
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()
    print("=" * 90)
    print(f" [TICKERTAPE PRO FORENSIC AUDIT: {ticker}]")
    print("=" * 90)

    audit = audit_indian_stock(ticker)
    if not audit.get("success"):
        print(f"[!] Error: {audit.get('error')}")
        sys.exit(1)

    # 1. Market Quote
    p = audit.get("price")
    chg = audit.get("change")
    vol = audit.get("volume")
    vol_str = f"{vol:,}" if isinstance(vol, (int, float)) else "N/A"
    print(f"\n[*] LIVE QUOTE:")
    print(f"  * Price: Rs {p} (Change: {chg}) | Volume: {vol_str} shares")

    # 2. Scorecard
    print(f"\n[*] PRO SCORECARDS (Scale 0 - 10):")
    for name, data in audit.get("scorecard", {}).items():
        val = data.get("value")
        tag = data.get("tag")
        desc = data.get("desc")
        print(f"  * {name:<15}: {val}/10 [{tag}] - {desc}")

    # 3. Checklists
    print(f"\n[*] PRO INVESTMENT CHECKLISTS:")
    for title, data in audit.get("checklists", {}).items():
        st = data.get("state")
        desc = data.get("desc")
        badge = "[PASS]" if st == "checked" else ("[FAIL]" if st == "unchecked" else "[INFO]")
        print(f"  {badge:<6} {title:<22}: {desc}")

    # 4. Surveillance & Red Flags
    surv = audit.get("surveillance", {})
    print(f"\n[*] SURVEILLANCE & RED FLAGS:")
    if surv.get("clean"):
        print("  * Status: [PASS] Clean (0 ASM / GSM regulatory surveillance flags, no promoter pledge distress)")
    else:
        print(f"  * Status: [ALERT] Under Surveillance! Details: {surv.get('details')}")

    # 5. Institutional Ownership
    holdings = audit.get("holdings", {})
    if holdings:
        data = holdings.get("data", {})
        print(f"\n[*] INSTITUTIONAL FLOAT BREAKDOWN (Period: {holdings.get('date', 'N/A')[:10]}):")
        mf = data.get("mfPctT", 0.0)
        di = data.get("diPctT", 0.0)
        fi = data.get("fiPctT", 0.0)
        retail = data.get("rhPctT", 0.0)
        total_inst = di + fi
        print(f"  * Mutual Funds:         {mf:.2f}%")
        print(f"  * Domestic Inst (DII):  {di:.2f}%")
        print(f"  * Foreign Inst (FII):   {fi:.2f}%")
        print(f"  * Total Smart Money:    {total_inst:.2f}%")
        print(f"  * Retail Float:         {retail:.2f}%")

    # 6. Forward Analyst Forecasts
    fc = audit.get("forecasts", {})
    if fc:
        print(f"\n[*] FORWARD ANALYST CONSENSUS & FORECASTS:")
        for k, items in fc.items():
            if isinstance(items, list):
                for item in items:
                    mood = item.get("mood", "Neutral")
                    msg = item.get("message") or item.get("title")
                    print(f"  * [{mood.upper()}] {k.upper()}: {msg}")

    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    main()
