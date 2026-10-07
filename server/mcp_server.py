#!/usr/bin/env python3
"""
Autonomous Quantitative Trading Agent - Modern Model Context Protocol (MCP) Server
Exposes institutional trading tools, portfolio audits, quantitative screeners,
multi-agent deliberation, resources, and prompts using the 2026 official MCP 2.x standard.

Supports stdio transport for Antigravity, Claude Code, Cursor, and Windsurf.
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from trading_agent.core.auth import get_tickertape_token
from trading_agent.core.broker import call_tickertape_mcp
from trading_agent.core.risk import audit_portfolio_health, audit_lrs_settlement
from trading_agent.core.engine import run_pipeline
from trading_agent.core.memory import load_factor_weights, load_trade_journal, run_adversarial_retrospective
from trading_agent.core.wallet import drain_wallet_to_asset
from trading_agent.core.deliberation import deliberate_ticker
from trading_agent.core.config import (
    MIN_BETA_INVARIANT,
    MAX_BETA_COLLAR,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    TENURE_LOCK_DAYS,
    WALLET_DRAIN_SAFETY_LIMIT
)

SERVER_NAME = "autonomous-trading-agent"
SERVER_VERSION = "2.4.0"

# Check for official MCP 2.x SDK
try:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations
    USE_OFFICIAL_MCP = True
except ImportError:
    USE_OFFICIAL_MCP = False
    ToolAnnotations = None

# =============================================================================
# TOOL METADATA & FIDUCIARY SAFETY ANNOTATIONS (M8ven & OpenAI Conformance)
# =============================================================================

TOOL_METADATA = {
    "trading_get_portfolio_status": {
        "title": "Get Portfolio Status",
        "description": "Fetches real-time portfolio holdings, cash balances, P&L %, tenure days, stop-loss/take-profit status, and pending RBI LRS bank transfers.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "trading_run_screener": {
        "title": "Run Quantitative Screener",
        "description": "Runs the quantitative multi-factor screener against high-beta US technology and semiconductor leaders, enforcing the Fiduciary Anti-Ruin positive margin floor.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    "trading_deliberate_ticker": {
        "title": "Deliberate Ticker",
        "description": "Executes SOTA Multi-Agent Deliberation (Fundamental, Technical, Risk) with test-time reasoning traces and strict Pydantic output on a specific ticker.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    "trading_preview_rebalance": {
        "title": "Preview Rebalance",
        "description": "Generates a non-mutating preview of the monthly rebalancing plan, evaluating 60-day anti-churn tenure locks and capital recycling pools.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    "trading_execute_rebalance": {
        "title": "Execute Rebalance",
        "description": "Executes confirmed live monthly rebalancing trades on Tickertape / Alpaca with Zero-Limbo capital protection and auto-quote refresh.",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "trading_drain_wallet": {
        "title": "Drain Wallet",
        "description": "Dynamically deploys remaining settled cash into a high-conviction target holding respecting the rolling 60-minute 50% wallet-drain limit.",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "trading_get_memory_state": {
        "title": "Get Memory State",
        "description": "Inspects 4-tier persistent memory, active factor weights, and historical trade counts.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "trading_run_system_test": {
        "title": "Run System Test",
        "description": "Runs the comprehensive 7-test mathematical and safety verification suite.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "trading_run_agent_evals": {
        "title": "Run Agent Evals",
        "description": "Runs the 2026 SOTA Agentic Evaluation and Fiduciary Anti-Ruin benchmark test suite.",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}

def make_annotations(tool_name: str) -> Optional[Any]:
    meta = TOOL_METADATA.get(tool_name, {})
    if ToolAnnotations:
        return ToolAnnotations(
            title=meta.get("title"),
            read_only_hint=meta.get("readOnlyHint", True),
            destructive_hint=meta.get("destructiveHint", False),
            idempotent_hint=meta.get("idempotentHint", True),
            open_world_hint=meta.get("openWorldHint", False)
        )
    return {
        "readOnlyHint": meta.get("readOnlyHint", True),
        "destructiveHint": meta.get("destructiveHint", False),
        "idempotentHint": meta.get("idempotentHint", True),
        "openWorldHint": meta.get("openWorldHint", False)
    }

# =============================================================================
# TOOL HANDLERS
# =============================================================================

def handle_get_portfolio_status() -> Dict[str, Any]:
    token = get_tickertape_token()
    h_res = call_tickertape_mcp(token, "pf_useq_holdings")
    holdings = h_res.get("securities", []) if isinstance(h_res, dict) else []
    
    b_res = call_tickertape_mcp(token, "us_account_balance")
    balances = b_res.get("balance", {}) if isinstance(b_res, dict) else {}
    if not balances and isinstance(b_res, dict):
        balances = b_res
    
    lrs_pending = audit_lrs_settlement(token)
    alerts, summary = audit_portfolio_health(token)
    
    return {
        "status": "success",
        "cash_available": balances.get("availableToInvest", balances.get("availableFunds", 0.0)),
        "cash_withdrawable": balances.get("withdrawableBalance", balances.get("availableWithdrawal", 0.0)),
        "holdings_count": len(summary) if summary else len(holdings),
        "holdings": summary if summary else holdings,
        "health_alerts": alerts,
        "lrs_in_flight": lrs_pending,
        "fiduciary_collars": {
            "beta_bounds": [MIN_BETA_INVARIANT, MAX_BETA_COLLAR],
            "tenure_lock_days": TENURE_LOCK_DAYS,
            "stop_loss_pct": STOP_LOSS_PCT,
            "take_profit_pct": TAKE_PROFIT_PCT
        }
    }

def handle_run_screener(count: int = 10) -> Dict[str, Any]:
    token = get_tickertape_token()
    weights = load_factor_weights()
    from trading_agent.core.screener import run_quantitative_screener
    candidates = run_quantitative_screener(token, weights, count=count)
    return {
        "status": "success",
        "candidates_count": len(candidates),
        "candidates": candidates
    }

def handle_deliberate_ticker(ticker: str) -> Dict[str, Any]:
    token = get_tickertape_token()
    delib = deliberate_ticker(ticker.upper(), token=token)
    return {
        "status": "success",
        "deliberation": delib.model_dump() if hasattr(delib, "model_dump") else delib.__dict__
    }

def handle_preview_rebalance(budget: str = "auto", mode: str = "live", plan: str = "dynamic", ignore_in_flight: bool = False) -> Dict[str, Any]:
    res = run_pipeline(
        budget=budget,
        mode=mode,
        plan=plan,
        execute=False,
        rebalance=True,
        ignore_in_flight=ignore_in_flight
    )
    return {"status": "success", "preview_result": res}

def handle_execute_rebalance(budget: str = "auto", mode: str = "live", plan: str = "dynamic", ignore_in_flight: bool = False) -> Dict[str, Any]:
    res = run_pipeline(
        budget=budget,
        mode=mode,
        plan=plan,
        execute=True,
        rebalance=True,
        ignore_in_flight=ignore_in_flight
    )
    return {"status": "success", "execution_result": res}

def handle_drain_wallet(ticker: str = "ASML") -> Dict[str, Any]:
    res = drain_wallet_to_asset(ticker=ticker.upper())
    return {"status": "success", "drain_result": res}

def handle_get_memory_state() -> Dict[str, Any]:
    weights = load_factor_weights()
    journal = load_trade_journal()
    return {
        "status": "success",
        "factor_weights": weights,
        "historical_trades_count": len(journal),
        "tenure_mandate_days": TENURE_LOCK_DAYS
    }

def handle_run_system_test() -> Dict[str, Any]:
    import subprocess
    test_script = os.path.join(REPO_ROOT, "scripts", "test_system.py")
    res = subprocess.run([sys.executable, test_script], capture_output=True, text=True, cwd=REPO_ROOT)
    return {
        "status": "success" if res.returncode == 0 else "failed",
        "return_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }

def handle_run_agent_evals() -> Dict[str, Any]:
    import subprocess
    eval_script = os.path.join(REPO_ROOT, "scripts", "run_evals.py")
    res = subprocess.run([sys.executable, eval_script], capture_output=True, text=True, cwd=REPO_ROOT)
    return {
        "status": "success" if res.returncode == 0 else "failed",
        "return_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }

# =============================================================================
# MODERN MCP 2.x INITIALIZATION
# =============================================================================

if USE_OFFICIAL_MCP:
    mcp_app = MCPServer(SERVER_NAME)

    # 1. Tools Registration with Full Four Hints Annotations
    @mcp_app.tool(
        name="trading_get_portfolio_status",
        title="Get Portfolio Status",
        description="Fetches real-time portfolio holdings, cash balances, P&L %, tenure days, stop-loss/take-profit status, and pending RBI LRS bank transfers.",
        annotations=make_annotations("trading_get_portfolio_status")
    )
    def trading_get_portfolio_status() -> str:
        """Fetches real-time portfolio holdings, cash balances, P&L %, tenure days, stop-loss/take-profit status, and pending RBI LRS bank transfers."""
        return json.dumps(handle_get_portfolio_status(), indent=2)

    @mcp_app.tool(
        name="trading_run_screener",
        title="Run Quantitative Screener",
        description="Runs the quantitative multi-factor screener against high-beta US technology and semiconductor leaders, enforcing the Fiduciary Anti-Ruin positive margin floor.",
        annotations=make_annotations("trading_run_screener")
    )
    def trading_run_screener(count: int = 10) -> str:
        """Runs the quantitative multi-factor screener against high-beta US technology and semiconductor leaders, enforcing the Fiduciary Anti-Ruin positive margin floor."""
        return json.dumps(handle_run_screener(count), indent=2)

    @mcp_app.tool(
        name="trading_deliberate_ticker",
        title="Deliberate Ticker",
        description="Executes SOTA Multi-Agent Deliberation (Fundamental, Technical, Risk) with test-time reasoning traces and strict Pydantic output on a specific ticker.",
        annotations=make_annotations("trading_deliberate_ticker")
    )
    def trading_deliberate_ticker(ticker: str) -> str:
        """Executes SOTA Multi-Agent Deliberation (Fundamental, Technical, Risk) with test-time reasoning traces and strict Pydantic output on a specific ticker."""
        return json.dumps(handle_deliberate_ticker(ticker), indent=2)

    @mcp_app.tool(
        name="trading_preview_rebalance",
        title="Preview Rebalance",
        description="Generates a non-mutating preview of the monthly rebalancing plan, evaluating 60-day anti-churn tenure locks and capital recycling pools.",
        annotations=make_annotations("trading_preview_rebalance")
    )
    def trading_preview_rebalance(budget: str = "auto", mode: str = "live", plan: str = "dynamic", ignore_in_flight: bool = False) -> str:
        """Generates a non-mutating preview of the monthly rebalancing plan, evaluating 60-day anti-churn tenure locks and capital recycling pools."""
        return json.dumps(handle_preview_rebalance(budget, mode, plan, ignore_in_flight), indent=2)

    @mcp_app.tool(
        name="trading_execute_rebalance",
        title="Execute Rebalance",
        description="Executes confirmed live monthly rebalancing trades on Tickertape / Alpaca with Zero-Limbo capital protection and auto-quote refresh.",
        annotations=make_annotations("trading_execute_rebalance")
    )
    def trading_execute_rebalance(budget: str = "auto", mode: str = "live", plan: str = "dynamic", ignore_in_flight: bool = False) -> str:
        """Executes confirmed live monthly rebalancing trades on Tickertape / Alpaca with Zero-Limbo capital protection and auto-quote refresh."""
        return json.dumps(handle_execute_rebalance(budget, mode, plan, ignore_in_flight), indent=2)

    @mcp_app.tool(
        name="trading_drain_wallet",
        title="Drain Wallet",
        description="Dynamically deploys remaining settled cash into a high-conviction target holding respecting the rolling 60-minute 50% wallet-drain limit.",
        annotations=make_annotations("trading_drain_wallet")
    )
    def trading_drain_wallet(ticker: str = "ASML") -> str:
        """Dynamically deploys remaining settled cash into a high-conviction target holding respecting the rolling 60-minute 50% wallet-drain limit."""
        return json.dumps(handle_drain_wallet(ticker), indent=2)

    @mcp_app.tool(
        name="trading_get_memory_state",
        title="Get Memory State",
        description="Inspects 4-tier persistent memory, active factor weights, and historical trade counts.",
        annotations=make_annotations("trading_get_memory_state")
    )
    def trading_get_memory_state() -> str:
        """Inspects 4-tier persistent memory, active factor weights, and historical trade counts."""
        return json.dumps(handle_get_memory_state(), indent=2)

    @mcp_app.tool(
        name="trading_run_system_test",
        title="Run System Test",
        description="Runs the comprehensive 7-test mathematical and safety verification suite.",
        annotations=make_annotations("trading_run_system_test")
    )
    def trading_run_system_test() -> str:
        """Runs the comprehensive 7-test mathematical and safety verification suite."""
        return json.dumps(handle_run_system_test(), indent=2)

    @mcp_app.tool(
        name="trading_run_agent_evals",
        title="Run Agent Evals",
        description="Runs the 2026 SOTA Agentic Evaluation and Fiduciary Anti-Ruin benchmark test suite.",
        annotations=make_annotations("trading_run_agent_evals")
    )
    def trading_run_agent_evals() -> str:
        """Runs the 2026 SOTA Agentic Evaluation and Fiduciary Anti-Ruin benchmark test suite."""
        return json.dumps(handle_run_agent_evals(), indent=2)

    # 2. Resources Registration
    @mcp_app.resource("resource://portfolio/status")
    def get_portfolio_status_resource() -> str:
        """Real-time portfolio status resource."""
        return json.dumps(handle_get_portfolio_status(), indent=2)

    @mcp_app.resource("resource://portfolio/rules")
    def get_portfolio_rules_resource() -> str:
        """Fiduciary Anti-Ruin rules and portfolio invariants resource."""
        return json.dumps({
            "min_beta": MIN_BETA_INVARIANT,
            "max_beta": MAX_BETA_COLLAR,
            "stop_loss_pct": STOP_LOSS_PCT,
            "take_profit_pct": TAKE_PROFIT_PCT,
            "tenure_lock_days": TENURE_LOCK_DAYS,
            "wallet_drain_limit": WALLET_DRAIN_SAFETY_LIMIT
        }, indent=2)

    @mcp_app.resource("resource://portfolio/memory")
    def get_portfolio_memory_resource() -> str:
        """Persistent factor weights and agent memory resource."""
        return json.dumps(handle_get_memory_state(), indent=2)

    # 3. Prompts Registration
    @mcp_app.prompt()
    def committee_deliberation(ticker: str) -> str:
        """Prompt to initiate a full multi-agent investment committee debate on a ticker."""
        return (
            f"You are the Investment Committee Chair for the Autonomous Quantitative Trading Agent. "
            f"Please conduct an adversarial multi-agent debate on ticker '{ticker}'. "
            f"Consult the Fundamental Analyst (economic moat, net margin floor, Wall Street forward EPS revisions, "
            f"institutional analyst consensus, smart-money float sponsorship, and promoter pledge forensics), "
            f"Technical Analyst (6M/1M relative momentum, 200-day trend integrity, weekly RSI oscillator, and institutional accumulation flow), "
            f"and Fiduciary Risk Manager (beta collar 1.4-2.8, 48h earnings blackout, 60d anti-churn tenure locks, "
            f"SEBI ASM/GSM surveillance filters, and 50% wallet-drain limits). Enforce absolute veto power against ruin."
        )

# =============================================================================
# ENTRYPOINT
# =============================================================================

def run_server():
    if USE_OFFICIAL_MCP:
        sys.stderr.write(f"[*] Starting {SERVER_NAME} v{SERVER_VERSION} using official MCP 2.x SDK...\n")
        mcp_app.run(transport="stdio")
    else:
        sys.stderr.write(f"[*] Starting {SERVER_NAME} v{SERVER_VERSION} using raw stdio JSON-RPC fallback...\n")
        # Raw stdio fallback loop
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            try:
                req = json.loads(line)
            except Exception:
                continue
            req_id = req.get("id")
            method = req.get("method")
            if method == "tools/list":
                tools_list = []
                for t_name, t_meta in TOOL_METADATA.items():
                    tools_list.append({
                        "name": t_name,
                        "title": t_meta["title"],
                        "description": t_meta["description"],
                        "readOnlyHint": t_meta["readOnlyHint"],
                        "destructiveHint": t_meta["destructiveHint"],
                        "idempotentHint": t_meta["idempotentHint"],
                        "openWorldHint": t_meta["openWorldHint"],
                        "annotations": {
                            "title": t_meta["title"],
                            "readOnlyHint": t_meta["readOnlyHint"],
                            "destructiveHint": t_meta["destructiveHint"],
                            "idempotentHint": t_meta["idempotentHint"],
                            "openWorldHint": t_meta["openWorldHint"]
                        },
                        "inputSchema": {"type": "object", "properties": {}}
                    })
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_server()
