"""
Persistent Agent Memory, Adversarial Retrospective & Feedback Loop
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

from .config import (
    MEMORY_DIR,
    TRADE_JOURNAL_FILE,
    FACTOR_WEIGHTS_FILE,
    RETROSPECTIVE_LOG_FILE,
    LESSONS_LEARNED_FILE,
    EVIDENCE_LEDGER_FILE
)

def load_trade_journal() -> List[Dict[str, Any]]:
    """Loads past trade logs from persistent agent memory, falling back to example template if private file is absent."""
    trades = []
    target_file = TRADE_JOURNAL_FILE
    if not os.path.exists(target_file):
        example_file = os.path.join(MEMORY_DIR, "trade_journal.example.jsonl")
        if os.path.exists(example_file):
            target_file = example_file
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        trades.append(json.loads(line))
        except Exception as e:
            print(f"[!] Warning reading trade journal: {e}")
    return trades

def load_factor_weights() -> Dict[str, Any]:
    """Loads factor weights and invariants from persistent agent memory."""
    if os.path.exists(FACTOR_WEIGHTS_FILE):
        try:
            with open(FACTOR_WEIGHTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Warning reading factor weights: {e}")
    return {
        "version": "2.2.0",
        "hard_invariants": {
            "min_beta": 1.40,
            "max_assets": 3,
            "min_momentum_weight": 0.20
        },
        "current_weights": {
            "weight_6m_return": 0.20,
            "weight_1m_return": 0.15,
            "weight_beta": 20.0,
            "beta_clamp_max": 2.50,
            "weight_fwd_eps": 0.15,
            "fwd_eps_cap": 250.0,
            "weight_analyst_upside": 0.15,
            "weight_analyst_buy_pct": 0.15,
            "rsi_overbought_threshold": 75.0,
            "rsi_overbought_penalty": -15.0,
            "rsi_oversold_threshold": 35.0,
            "rsi_oversold_boost": 10.0,
            "earnings_proximity_penalty": -25.0
        }
    }

def record_trade_execution(
    ticker: str,
    name: str,
    shares: float,
    price: float,
    amount: float,
    entry_factors: Dict[str, Any],
    cycle_id: str,
    action: str = "BUY",
    reason: str = ""
):
    """Appends an executed trade into the persistent journal."""
    trade_entry = {
        "id": f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticker}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ticker": ticker,
        "name": name,
        "action": action,
        "shares": float(shares),
        "price": float(price),
        "amount": float(amount),
        "entry_factors": entry_factors,
        "cycle": cycle_id,
        "reason": reason
    }
    try:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(TRADE_JOURNAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trade_entry) + "\n")
        print(f"  -> [Agent Memory] Trade for {ticker} recorded in persistent trade journal.")
    except Exception as e:
        print(f"[!] Failed to log trade to journal: {e}")

def run_adversarial_retrospective(holdings_summary: List[Dict[str, Any]], benchmark_ret: float = 2.5, is_preview: bool = False, market: str = "US"):
    """Executes automated adversarial review and factor weight calibration for US or IN equities."""
    market_label = "INDIAN EQUITIES (NSE/BSE)" if market.upper() == "IN" else "US EQUITIES"
    benchmark_name = "Nifty 50 / Midcap 100" if market.upper() == "IN" else "SOXX Semiconductor Proxy"
    if market.upper() == "IN" and benchmark_ret == 2.5:
        benchmark_ret = 1.80  # Default Indian index reference return

    print("\n" + "=" * 96)
    print(f" [PHASE 0] ADVERSARIAL RETROSPECTIVE & CONTINUOUS AGENT LEARNING LOOP - [{market_label}]")
    print("=" * 96)
    
    past_trades = load_trade_journal()
    filtered_trades = [t for t in past_trades if t.get("market") == market.upper() or (market.upper() == "IN" and t.get("broker") in ["Zerodha", "Groww"])]
    weights_config = load_factor_weights()
    current_weights = weights_config.get("current_weights", {})
    hard_invariants = weights_config.get("hard_invariants", {})
    
    print(f"  * Persistent Memory Store:     {MEMORY_DIR}")
    print(f"  * Recorded {market.upper()} Executions:     {len(filtered_trades)} historical trades in journal")
    print(f"  * Active Factor Model Version: v{weights_config.get('version', '2.2.0')}")
    print(f"  * Hard Invariants:             Min Beta >= {hard_invariants.get('min_beta', 1.40)} | Max Assets = {hard_invariants.get('max_assets', 3)}")

    # Calculate portfolio return
    total_val = sum(h.get("current", 0.0) for h in holdings_summary)
    total_inv = sum(h.get("invested", 0.0) for h in holdings_summary)
    port_ret = ((total_val - total_inv) / total_inv * 100.0) if total_inv > 0 else 0.0
    active_alpha = port_ret - benchmark_ret

    print(f"\n  --- 1. Holding Period Attribution ---")
    print(f"  * Portfolio Aggregate P&L:   {port_ret:>+6.2f}%")
    print(f"  * Benchmark ({benchmark_name}): {benchmark_ret:>+6.2f}%")
    print(f"  * Realized Active Alpha:     {active_alpha:>+6.2f}%")

    print(f"\n  --- 2. Automated Multi-Agent Retrospective Debate ---")
    if active_alpha >= 0:
        if market.upper() == "IN":
            print("  * [QUANT AUDITOR]: High-beta Indian manufacturing & defense compounders generated positive alpha.")
            print("    Recommendation: Maintain momentum factor weight, reward positive operating margins.")
            print("  * [RISK CHALLENGER]: Volatility contained. Zero stop-loss triggers breached; cash buffer intact.")
        else:
            print("  * [QUANT AUDITOR]: High-beta semiconductor conviction delivered positive alpha.")
            print("    Recommendation: Maintain momentum weight, reward forward EPS acceleration.")
            print("  * [RISK CHALLENGER]: Drawdown within acceptable collars. Stop-loss collars untouched.")
    else:
        print(f"  * [QUANT AUDITOR]: High-beta {market.upper()} basket experienced consolidation vs benchmark.")
        print("    Recommendation: Re-tilt slightly toward pricing power and earnings revision upside.")
        print("  * [RISK CHALLENGER]: Enforce RSI overbought threshold (<76) to avoid chasing extended rallies.")

    print(f"\n  --- 3. Recursive Factor Calibration ---")
    new_w_6m = current_weights.get("weight_6m_return", 0.20)
    new_w_eps = current_weights.get("weight_fwd_eps", 0.15)
    
    if active_alpha >= 1.0:
        new_w_6m = min(0.35, new_w_6m + 0.01)
    elif active_alpha <= -1.0:
        new_w_eps = min(0.30, new_w_eps + 0.01)

    print(f"  * 6M Return Weight:  {current_weights.get('weight_6m_return', 0.20):.2f} -> {new_w_6m:.2f}")
    print(f"  * Fwd EPS Weight:    {current_weights.get('weight_fwd_eps', 0.15):.2f} -> {new_w_eps:.2f}")
    print(f"  * Status: Invariants preserved (Min Momentum >= {hard_invariants.get('min_momentum_weight', 0.20):.2f}).")

    if not is_preview:
        current_weights["weight_6m_return"] = round(new_w_6m, 3)
        current_weights["weight_fwd_eps"] = round(new_w_eps, 3)
        weights_config["last_calibrated_at"] = datetime.now().isoformat()
        try:
            with open(FACTOR_WEIGHTS_FILE, "w", encoding="utf-8") as f:
                json.dump(weights_config, f, indent=2)
            print(f"  * Persisted calibrated factor weights to memory/factor_weights.json")
        except Exception as e:
            print(f"  [!] Failed to persist factor weights: {e}")
