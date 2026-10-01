"""
Risk Management, Fiduciary Guardrails & Tenure Lock Controller
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from .config import (
    TRADE_JOURNAL_FILE,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    MIN_BETA_INVARIANT,
    MAX_BETA_COLLAR,
    TENURE_LOCK_DAYS
)
from .broker import call_tickertape_mcp

def get_holding_tenure_days(ticker: str) -> int:
    """Calculates days elapsed since the most recent recorded purchase of an asset."""
    latest_entry = None
    if os.path.exists(TRADE_JOURNAL_FILE):
        try:
            with open(TRADE_JOURNAL_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    if entry.get("ticker") == ticker and entry.get("action", "BUY").upper() == "BUY":
                        d_str = entry.get("date")
                        if d_str:
                            t_entry = datetime.strptime(d_str, "%Y-%m-%d")
                            if latest_entry is None or t_entry > latest_entry:
                                latest_entry = t_entry
        except Exception:
            pass
    if latest_entry:
        return max(0, (datetime.now() - latest_entry).days)
    return 0  # Default to locked (0 days) if not found, protecting new holdings from churn

def audit_tenure_lock(ticker: str, tenure_days: Optional[int] = None) -> Tuple[bool, int]:
    """Audits whether an asset is locked under the 60-day anti-churn tenure rule."""
    if tenure_days is None:
        tenure_days = get_holding_tenure_days(ticker)
    return (tenure_days < TENURE_LOCK_DAYS), tenure_days

def audit_lrs_settlement(token: str) -> List[Dict[str, Any]]:
    """Audits RBI LRS outward remittances and detects in-flight bank transfers."""
    print("\n--- RBI LRS & Banking Clearance Audit (HDFC -> US Broker) ---")
    trans_res = call_tickertape_mcp(token, "us_account_transactions", {"type": "deposit", "limit": 5})
    transactions = trans_res.get("transactions", []) if isinstance(trans_res, dict) else []
    
    pending = []
    for tx in transactions:
        status = tx.get("status", "").lower()
        if status in ["pending", "processing", "initiated", "in_transit"]:
            pending.append(tx)
        elif status == "completed":
            meta = tx.get("metadata", {})
            try:
                init_time = datetime.fromisoformat(tx.get("createdAt").replace("Z", "+00:00"))
                comp_time = datetime.fromisoformat(tx.get("updatedAt").replace("Z", "+00:00"))
                hrs = (comp_time - init_time).total_seconds() / 3600.0
                tag_str = "Fast Transfer" if "fast_transfer" in meta.get("tags", []) else "Normal"
                print(f"  * Empirical Clearing Latency: {hrs:.1f} hours ({tag_str})")
            except Exception:
                pass
                
    if pending:
        for p in pending:
            pmeta = p.get("metadata", {})
            print(f"  * [!] IN-FLIGHT DEPOSIT DETECTED: ₹{pmeta.get('sourceAmount', 'N/A')} INR (${p.get('amount')} USD) | Status: {p.get('status')}")
    else:
        print("  * In-Flight LRS Transfers: None currently in transit.")

    print("  * Operational Banking Rule: HDFC outward remittance cut-off is 1:00 PM IST.")
    print("  * [CRITICAL CALENDAR ALERT]: Friday, October 2, 2026 is Gandhi Jayanti (Indian National Bank Holiday).")
    print("    If deposit is initiated on Thursday, Oct 1 after 1:00 PM IST, funds will NOT clear until Monday, Oct 5!")
    print("    Rule: Initiate INR deposit on T-2 (Tuesday Sep 29 / Wednesday Sep 30 before 12:00 PM IST) for Oct 1 execution.")
    return pending

def audit_portfolio_health(token: str) -> Tuple[List[Tuple[str, str, float]], List[Dict[str, Any]]]:
    """Runs stop-loss (-12%) and take-profit (+35%) checks on active holdings."""
    print("\n--- Portfolio Health Check (Stop-Loss / Take-Profit) ---")
    holdings_res = call_tickertape_mcp(token, "pf_useq_holdings")
    securities = holdings_res.get("securities", []) if isinstance(holdings_res, dict) else []
    
    health_alerts = []
    holdings_summary = []
    for s in securities:
        t = s.get("ticker")
        detail = call_tickertape_mcp(token, "us_account_holding_detail", {"ticker": t})
        pnl_pct = 0.0
        cur_val = 0.0
        inv_amt = 0.0
        if isinstance(detail, dict):
            pnl_pct = float(detail.get("profitLossPercentage") or 0.0)
            cur_val = float(detail.get("currentValue") or 0.0)
            inv_amt = float(detail.get("investedAmount") or 0.0)
            
        status = "HEALTHY"
        if pnl_pct <= STOP_LOSS_PCT:
            status = f"STOP-LOSS TRIGGERED ({pnl_pct:.2f}%)"
            health_alerts.append((t, "STOP_LOSS", pnl_pct))
        elif pnl_pct >= TAKE_PROFIT_PCT:
            status = f"TAKE-PROFIT TARGET REACHED (+{pnl_pct:.2f}%)"
            health_alerts.append((t, "TAKE_PROFIT", pnl_pct))
            
        print(f"  * {t:<5} | Invested: ${inv_amt:<6.2f} | Current: ${cur_val:<6.2f} | P&L: {pnl_pct:>+6.2f}% | [{status}]")
        holdings_summary.append({
            "ticker": t,
            "invested": inv_amt,
            "current": cur_val,
            "pnl_pct": pnl_pct
        })
        
    return health_alerts, holdings_summary
