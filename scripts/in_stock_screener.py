#!/usr/bin/env python3
"""
Generic Indian Stock Market Screener CLI (NSE/BSE)
Powered by Tickertape PRO. Screens 5,000+ Indian equities without confirmation bias.

Usage:
    python scripts/in_stock_screener.py
    python scripts/in_stock_screener.py --min-beta 1.5 --min-mcap 5000 --sort-by roe
    python scripts/in_stock_screener.py --max-price 1000 --min-inst 15
"""

import sys
import os
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from trading_agent.core.in_screener import screen_indian_stocks

def main():
    parser = argparse.ArgumentParser(description="Algorithmic Screener for Indian Equities (Tickertape PRO)")
    parser.add_argument("--min-beta", type=float, default=1.40, help="Minimum Beta (default: 1.40)")
    parser.add_argument("--max-beta", type=float, default=2.80, help="Maximum Beta (default: 2.80)")
    parser.add_argument("--min-mcap", type=float, default=2000.0, help="Minimum Market Cap in Crores (default: 2000)")
    parser.add_argument("--min-roe", type=float, default=12.0, help="Minimum ROE % (default: 12.0)")
    parser.add_argument("--min-opmg", type=float, default=10.0, help="Minimum Operating Margin % (default: 10.0)")
    parser.add_argument("--max-price", type=float, default=5500.0, help="Maximum Share Price in INR (default: 5500)")
    parser.add_argument("--min-price", type=float, default=15.0, help="Minimum Share Price in INR (default: 15)")
    parser.add_argument("--min-inst", type=float, default=0.0, help="Minimum Institutional Ownership % (default: 0)")
    parser.add_argument("--sort-by", type=str, default="12mpctN", help="Field to sort by: 12mpctN, roe, opmg, mrktCapf (default: 12mpctN)")
    parser.add_argument("--limit", type=int, default=10, help="Max results to display (default: 10)")

    args = parser.parse_args()

    print("=" * 110)
    print(f" [ALGORITHMIC INDIAN STOCK SCREENER | UNBIASED MARKET AUDIT]")
    print(f" Constraints: Beta [{args.min_beta} - {args.max_beta}] | MCap >= Rs {args.min_mcap:,.0f}Cr | ROE >= {args.min_roe}% | OPMG >= {args.min_opmg}%")
    print(f" Price Range: Rs {args.min_price} - Rs {args.max_price} | Sort By: {args.sort_by} (Descending)")
    print("=" * 110)

    results = screen_indian_stocks(
        min_beta=args.min_beta,
        max_beta=args.max_beta,
        min_mcap_cr=args.min_mcap,
        min_roe=args.min_roe,
        min_opmg=args.min_opmg,
        max_price=args.max_price,
        min_price=args.min_price,
        min_inst_own=args.min_inst,
        sort_by=args.sort_by,
        limit=args.limit
    )

    if not results:
        print("\n[!] No stocks matched the active screener filters. Try loosening parameters.\n")
        return

    print(f"{'TICKER':<12} | {'PRICE (Rs)':<10} | {'BETA':<5} | {'1Y RET':<8} | {'ROE':<6} | {'OPMG':<6} | {'MCAP (Cr)':<10} | {'INST %':<7} | {'SECTOR'}")
    print("-" * 110)
    for r in results:
        m = r.get("metrics", {})
        ticker = r.get("ticker", "N/A")
        lp = m.get("lastPrice") or 0.0
        b = m.get("beta") or 0.0
        ret = m.get("12mpctN") or 0.0
        roe = m.get("roe") or 0.0
        opmg = m.get("opmg") or 0.0
        mcap = m.get("mrktCapf") or 0.0
        inst = m.get("instown") or 0.0
        sec = r.get("sector") or m.get("sector") or "N/A"
        print(f"{ticker:<12} | Rs {lp:<7.1f} | {b:<5.2f} | {ret:<6.1f}% | {roe:<5.1f}% | {opmg:<5.1f}% | Rs {mcap:<7.0f}Cr | {inst:<5.1f}% | {sec}")
    print("=" * 110 + "\n")

if __name__ == "__main__":
    main()
