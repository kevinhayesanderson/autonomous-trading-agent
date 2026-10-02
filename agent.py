#!/usr/bin/env python3
"""
Autonomous Quantitative Trading Agent (AQTA) - Unified Entry Point & CLI
Institutional Multi-Agent US Equity Allocation, Fiduciary Anti-Ruin Guardrails,
and Model Context Protocol (MCP) Interface.

Usage:
    python agent.py run [--execute]
    python agent.py cycle [--execute]
    python agent.py status
    python agent.py preview
    python agent.py execute [--ignore-in-flight] [--budget BUDGET]
    python agent.py drain --ticker ASML
    python agent.py retrospective
    python agent.py test
    python agent.py sync
    python agent.py serve-mcp
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

# Set default UTF-8 encoding on standard streams
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_ROOT)

from trading_agent.core.auth import get_tickertape_token
from trading_agent.core.broker import call_tickertape_mcp
from trading_agent.core.risk import audit_portfolio_health, audit_lrs_settlement
from trading_agent.core.engine import run_pipeline
from trading_agent.core.memory import load_factor_weights, load_trade_journal, run_adversarial_retrospective
from trading_agent.core.wallet import drain_wallet_to_asset
from trading_agent.core.orchestrator import run_dual_investment_agent
from scripts.git_sync import sync_system_to_git

def cmd_run(args):
    """Executes the unified dual-market investment agent cycle completely from scratch."""
    is_exec = getattr(args, "execute", False) or getattr(args, "confirm", False)
    raw_b = getattr(args, "budget", None) or getattr(args, "in_budget", None)
    in_budget = float(raw_b) if raw_b and raw_b != "auto" else None
    run_dual_investment_agent(execute=is_exec, in_budget=in_budget)

def cmd_status(args):
    """Audits live portfolio balances, active positions, P&L, and in-flight deposits."""
    print("=" * 80)
    print(" [PORTFOLIO STATUS & FIDUCIARY HEALTH AUDIT]")
    print("=" * 80)
    
    token = get_tickertape_token()
    
    # 1. Cash Balances
    bal = call_tickertape_mcp(token, "us_account_balance")
    avail = bal.get("availableFunds", "N/A") if isinstance(bal, dict) else "N/A"
    withdrawable = bal.get("availableWithdrawal", "N/A") if isinstance(bal, dict) else "N/A"
    print(f"\n[*] CASH BALANCES:")
    print(f"  * Available Funds:      ${avail} USD")
    print(f"  * Withdrawable Funds:   ${withdrawable} USD")
    
    # 2. In-Flight LRS Transfers
    print(f"\n[*] CAPITAL CONTROLLER (LRS Deposits):")
    pending = audit_lrs_settlement(token)
    
    # 3. Active Holdings
    print(f"\n[*] ACTIVE HOLDINGS:")
    alerts, summary = audit_portfolio_health(token)
    
    # 4. Memory & Factor Model Status
    weights_cfg = load_factor_weights()
    trades = load_trade_journal()
    print(f"\n[*] AGENT MEMORY:")
    print(f"  * Active Factor Model:  v{weights_cfg.get('version', '2.0.0')}")
    print(f"  * Recorded Executions:  {len(trades)} historical trades")
    print(f"  * Invariant Collars:    Beta >= {weights_cfg.get('hard_invariants', {}).get('min_beta', 1.40)} | Max Holdings <= {weights_cfg.get('hard_invariants', {}).get('max_assets', 3)}")
    print("=" * 80)

def cmd_preview(args):
    """Executes a non-mutating preview of the monthly rebalancing plan."""
    print("=" * 80)
    print(" [PREVIEW REBALANCING PLAN - NON-MUTATING]")
    print("=" * 80)
    run_pipeline(
        budget=args.budget,
        mode=args.mode,
        plan=args.plan,
        execute=False,
        rebalance=True,
        ignore_in_flight=args.ignore_in_flight
    )

def cmd_execute(args):
    """Executes confirmed live trades on Tickertape / Alpaca with Zero-Limbo safety."""
    print("=" * 80)
    print(" [CONFIRMED LIVE TRADE EXECUTION]")
    print("=" * 80)
    run_pipeline(
        budget=args.budget,
        mode=args.mode,
        plan=args.plan,
        execute=True,
        rebalance=True,
        ignore_in_flight=args.ignore_in_flight
    )

def cmd_drain(args):
    """Executes recursive micro-drain of settled funds into target asset."""
    ticker = getattr(args, "ticker", "ASML") or "ASML"
    drain_wallet_to_asset(ticker=ticker)

def cmd_retrospective(args):
    """Runs automated Phase 0 adversarial review & factor tuning."""
    token = get_tickertape_token()
    _, summary = audit_portfolio_health(token)
    run_adversarial_retrospective(summary, is_preview=False)

def cmd_test(args):
    """Runs the 7-test self-verification suite."""
    test_script = os.path.join(REPO_ROOT, "scripts", "test_system.py")
    res = subprocess.run([sys.executable, test_script], cwd=REPO_ROOT)
    sys.exit(res.returncode)

def cmd_sync(args):
    """Synchronizes persistent memory and repository state to remote Git."""
    msg = args.message or f"Cycle {datetime.now().strftime('%Y-%m')}: Agent state & memory synchronization"
    sync_system_to_git(msg)

def cmd_debate(args):
    """Executes SOTA Multi-Agent Deliberation on a ticker with test-time reasoning traces."""
    from trading_agent.core.deliberation import deliberate_ticker
    ticker = getattr(args, "ticker", "ASML") or "ASML"
    print(f"\n[*] Initiating Multi-Agent Committee Deliberation on {ticker.upper()}...")
    delib = deliberate_ticker(ticker.upper())
    print("\n" + "=" * 80)
    print(f" [COMMITTEE DELIBERATION: {ticker.upper()} | RECOMMENDATION: {delib.recommendation}]")
    print(f" Confidence Score: {delib.confidence_score * 100:.1f}% | Quorum: {delib.buy_votes} BUY, {delib.hold_votes} HOLD, {delib.veto_votes} VETO")
    print("=" * 80)
    if delib.thinking_trace:
        print("\n--- [Test-Time Reasoning Trace] ---")
        print(delib.thinking_trace)
    print("\n--- [Specialist Agent Votes & Rationales] ---")
    print(f"  * Fundamental: [{delib.fundamental.vote}] Moat={delib.fundamental.moat_score}/10 | Margin={delib.fundamental.net_margin_pct:+.1f}% | {delib.fundamental.thesis}")
    print(f"  * Technical:   [{delib.technical.vote}] 6M Ret={delib.technical.ret_6m_pct:+.1f}% | RSI={delib.technical.rsi_14w or 'N/A'} | {delib.technical.trend_status}")
    print(f"  * Fiduciary:   [{delib.risk.vote}] Beta={delib.risk.beta:.2f} | {delib.risk.ruin_prevention_memo}")
    print("\n--- [Committee Synthesis Memo] ---")
    print(f"  {delib.synthesis_memo}\n")

def cmd_eval(args):
    """Runs the 2026 SOTA Agentic Evaluation and Fiduciary Benchmark Suite."""
    eval_script = os.path.join(REPO_ROOT, "scripts", "run_evals.py")
    res = subprocess.run([sys.executable, eval_script], cwd=REPO_ROOT)
    sys.exit(res.returncode)

def cmd_serve_mcp(args):
    """Launches the native Model Context Protocol (MCP) server over stdio."""
    mcp_script = os.path.join(REPO_ROOT, "server", "mcp_server.py")
    subprocess.run([sys.executable, mcp_script], cwd=REPO_ROOT)

def cmd_in_screen(args):
    """Executes generic algorithmic screener across Indian equities (NSE/BSE)."""
    script = os.path.join(REPO_ROOT, "scripts", "in_stock_screener.py")
    cmd = [sys.executable, script, "--min-beta", str(args.min_beta), "--max-beta", str(args.max_beta),
           "--min-mcap", str(args.min_mcap), "--min-roe", str(args.min_roe), "--min-opmg", str(args.min_opmg),
           "--max-price", str(args.max_price), "--sort-by", str(args.sort_by), "--limit", str(args.limit)]
    subprocess.run(cmd, cwd=REPO_ROOT)

def cmd_in_audit(args):
    """Runs deep forensic audit on an Indian stock symbol using Tickertape PRO."""
    script = os.path.join(REPO_ROOT, "scripts", "in_stock_audit.py")
    subprocess.run([sys.executable, script, args.ticker], cwd=REPO_ROOT)

def cmd_in_preview(args):
    """Executes full 7-phase institutional preview for Indian equities with Zerodha Kite routing."""
    from trading_agent.core.in_engine import run_in_pipeline
    run_in_pipeline(
        budget=args.budget,
        mode=args.mode,
        execute=False,
        rebalance=True
    )

def cmd_in_execute(args):
    """Executes confirmed live Indian equity allocation with Zerodha Kite order formulation."""
    from trading_agent.core.in_engine import run_in_pipeline
    run_in_pipeline(
        budget=args.budget,
        mode=args.mode,
        execute=True,
        rebalance=True
    )

def cmd_in_retrospective(args):
    """Runs Phase 0 adversarial review & factor tuning on Indian equity portfolio."""
    from trading_agent.core.zerodha import get_zerodha_holdings
    holdings_summary = get_zerodha_holdings()
    run_adversarial_retrospective(holdings_summary, benchmark_ret=1.80, is_preview=False, market="IN")

def cmd_kite_status(args):
    """Audits Zerodha Kite Connect v3 connectivity, live cash balance, CNC margin, and demat holdings."""
    from trading_agent.core.zerodha import audit_kite_status, get_zerodha_holdings
    st = audit_kite_status()
    print("=" * 80)
    print(" [ZERODHA KITE CONNECT v3 STATUS & LIVE DEMAT ACCOUNT AUDIT]")
    print("=" * 80)
    print(f"  * Session Token Cached:    {'YES' if st['token_available'] else 'NO'}")
    print(f"  * Authenticated:           {'YES (Active)' if st['authenticated'] else 'NO (Session Expired / Pending)'}")
    print(f"  * Client Account:          {st['user_name']} ({st['user_id']})")
    print(f"  * Registered Email:        {st['email']}")
    print(f"  * Market Session Status:   {st['market_status']}")
    print(f"  * Current Public IP:       {st.get('public_ip', 'Unknown')}")
    
    if st['authenticated']:
        print(f"\n[*] LIVE ZERODHA ACCOUNT BALANCES:")
        print(f"  * Clear Cash Balance:      ₹{st['clear_cash']:,.2f} INR")
        print(f"  * CNC Available Margin:    ₹{st['cnc_margin']:,.2f} INR")
        
        holdings = get_zerodha_holdings()
        print(f"\n[*] LIVE ZERODHA DEMAT HOLDINGS ({len(holdings)} active positions):")
        if not holdings:
            print("  * No active demat holdings settled (Ready for fresh allocation).")
        else:
            for h in holdings:
                avg_p = (h.get('invested', 0.0) / h['shares']) if h['shares'] > 0 else 0.0
                print(f"  * {h['ticker']}: {h['shares']} shares @ avg Rs {avg_p:.2f} | P&L: {h['pnl_pct']:>+5.2f}%")
    else:
        print(f"\n  [!] Action Required:")
        print(f"      {st.get('error') or 'Session token expired or missing.'}")
        print("      Run: python agent.py kite-login to authenticate your daily session.")
    print("=" * 80)

def cmd_kite_login(args):
    """Initiates OAuth 2.0 login flow for Zerodha Kite Connect v3."""
    from scripts.kite_auth import authenticate
    direct_token = getattr(args, "token", None) or getattr(args, "url", None)
    authenticate(direct_token=direct_token)

def cmd_tt_login(args):
    """Initiates OAuth 2.1 PKCE interactive login flow for Tickertape PRO."""
    from scripts import tickertape_auth
    print("=" * 80)
    print(" [TICKERTAPE PRO OAUTH 2.1 PKCE LOGIN]")
    print("=" * 80)
    tok = tickertape_auth.get_valid_token(force_login=True)
    if tok:
        print("\n[SUCCESS] Tickertape PRO session successfully stored and verified.")
    else:
        print("\n[ERROR] Tickertape login failed.")

def cmd_auth(args):
    """
    Unified Step 1 Authentication: Validates and authenticates both Tickertape PRO and Zerodha Kite Connect v3.
    """
    print("=" * 80)
    print(" [AQTA DUAL-MARKET AUTHENTICATION SUITE - STEP 1]")
    print("=" * 80)

    # 1. Tickertape PRO
    print("\n[1/2] TICKERTAPE PRO AUTHENTICATION (US & Indian Forensic Screener)...")
    skip_tt = getattr(args, "kite_only", False)
    tt_ok = False
    if skip_tt:
        print("  * Skipped (--kite-only specified).")
    else:
        try:
            from scripts import tickertape_auth
            force_tt = getattr(args, "force", False)
            tok = tickertape_auth.get_valid_token(force_login=force_tt)
            if tok:
                tt_ok = True
                print("  [SUCCESS] Tickertape PRO session is ACTIVE and verified.")
            else:
                print("  [!] Tickertape token not verified.")
        except Exception as e:
            print(f"  [!] Tickertape authentication notice: {e}")
            print("      Run 'python agent.py tt-login' to authenticate Tickertape interactively.")

    # 2. Zerodha Kite Connect v3
    print("\n[2/2] ZERODHA KITE CONNECT v3 AUTHENTICATION (Indian Execution Broker)...")
    skip_kite = getattr(args, "tt_only", False)
    kite_ok = False
    if skip_kite:
        print("  * Skipped (--tt-only specified).")
    else:
        from trading_agent.core.zerodha import audit_kite_status
        direct_token = getattr(args, "token", None) or getattr(args, "url", None)
        force_kite = getattr(args, "force", False)
        
        current_status = audit_kite_status()
        if current_status.get("authenticated") and not direct_token and not force_kite:
            kite_ok = True
            print(f"  [SUCCESS] Zerodha Kite Connect session is already ACTIVE ({current_status.get('user_name', '')}).")
        else:
            try:
                from scripts.kite_auth import authenticate
                authenticate(direct_token=direct_token)
                fresh_status = audit_kite_status()
                kite_ok = fresh_status.get("authenticated", False)
            except Exception as e:
                print(f"  [!] Zerodha Kite login notice: {e}")
                print("      Run 'python agent.py kite-login' to retry.")

    # Summary
    print("\n" + "=" * 80)
    print(" [STEP 1 AUTHENTICATION SUMMARY]")
    print("=" * 80)
    from trading_agent.core.auth import get_tickertape_token
    from trading_agent.core.zerodha import audit_kite_status
    try:
        tt_active = bool(get_tickertape_token())
    except Exception:
        tt_active = False
    
    st = audit_kite_status()
    kite_active = st.get("authenticated", False)
    
    print(f"  * [1] Tickertape PRO:     {'[CONNECTED & READY]' if tt_active else '[DISCONNECTED / ACTION REQUIRED]'}")
    print(f"  * [2] Zerodha Kite v3:    {'[CONNECTED & READY]' if kite_active else '[PENDING / ACTION REQUIRED]'}")
    if kite_active:
        print(f"        Account:            {st.get('user_name')} ({st.get('user_id')})")
        print(f"        Available Margin:   Rs {st.get('cnc_margin', 0.0):,.2f} INR")
    
    print("=" * 80)
    if tt_active and kite_active:
        print("\n[READY] Both Tickertape PRO and Zerodha Kite v3 are authenticated for Step 1.")
        print("You can now proceed to Step 2:")
        print("  * Preview Indian allocation:  python agent.py in-preview")
        print("  * Preview Dual-market cycle:  python agent.py run")
    elif not kite_active:
        print("\n[!] Zerodha Kite daily authentication still required.")
        print("    Run: python agent.py kite-login")
    elif not tt_active:
        print("\n[!] Tickertape PRO authentication still required.")
        print("    Run: python agent.py tt-login")
    print("=" * 80)

def cli_entrypoint():
    parser = argparse.ArgumentParser(
        description="Autonomous Quantitative Trading Agent (AQTA) - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Agent command to execute")

    # run / cycle (Unified Dual-Market Investment Agent)
    for c_name in ["run", "cycle"]:
        p_run = subparsers.add_parser(c_name, help="Run unified dual-market investment agent (Tickertape US + Zerodha Kite IN)")
        p_run.add_argument("--execute", "--confirm", action="store_true", help="Commit confirmed live allocations to both brokers")
        p_run.add_argument("--budget", "--in-budget", default="auto", help="Target Indian equity budget in INR (default: auto from Kite clear cash)")

    # status
    p_status = subparsers.add_parser("status", help="Audit live balances, holdings, and in-flight capital")

    # auth / login (Unified Step 1 Authentication)
    for a_cmd in ["auth", "login"]:
        p_auth = subparsers.add_parser(a_cmd, help="Authenticate both Tickertape PRO and Zerodha Kite Connect v3 (Step 1)")
        p_auth.add_argument("--token", "-t", default=None, help="Direct request_token for Kite")
        p_auth.add_argument("--url", "-u", default=None, help="Full callback URL for Kite")
        p_auth.add_argument("--force", action="store_true", help="Force interactive login even if tokens exist")
        p_auth.add_argument("--kite-only", action="store_true", help="Authenticate only Zerodha Kite")
        p_auth.add_argument("--tt-only", action="store_true", help="Authenticate only Tickertape PRO")

    # tt-login / tickertape-login
    for tt_cmd in ["tt-login", "tickertape-login"]:
        p_tt = subparsers.add_parser(tt_cmd, help="Authenticate Tickertape PRO via OAuth 2.1 PKCE")

    # debate
    p_debate = subparsers.add_parser("debate", help="Execute multi-agent committee debate with reasoning traces on a ticker")
    p_debate.add_argument("ticker", nargs="?", default="ASML", help="Stock ticker symbol (default: ASML)")

    # eval
    p_eval = subparsers.add_parser("eval", help="Run 2026 SOTA agentic evals and fiduciary benchmark suite")

    # preview
    p_prev = subparsers.add_parser("preview", help="Preview monthly allocation and rebalancing plan")
    p_prev.add_argument("--budget", default="auto", help="Budget in USD (default: auto)")
    p_prev.add_argument("--mode", choices=["live", "paper"], default="live", help="Execution broker")
    p_prev.add_argument("--plan", choices=["dynamic", "defensive", "ai-pureplay"], default="dynamic")
    p_prev.add_argument("--ignore-in-flight", action="store_true", help="Evaluate with settled cash")

    # execute
    p_exec = subparsers.add_parser("execute", help="Execute confirmed live rebalancing trades")
    p_exec.add_argument("--budget", default="auto", help="Budget in USD (default: auto)")
    p_exec.add_argument("--mode", choices=["live", "paper"], default="live", help="Execution broker")
    p_exec.add_argument("--plan", choices=["dynamic", "defensive", "ai-pureplay"], default="dynamic")
    p_exec.add_argument("--ignore-in-flight", action="store_true", help="Execute with settled cash even if transfer is pending")

    # drain
    p_drain = subparsers.add_parser("drain", help="Drain settled cash into target leader respecting wallet safety")
    p_drain.add_argument("--ticker", default="ASML", help="Target ticker symbol (default: ASML)")

    # retrospective
    p_retro = subparsers.add_parser("retrospective", help="Run adversarial retrospective and factor weight tuning")

    # test
    p_test = subparsers.add_parser("test", help="Run 7-test mathematical and safety verification suite")

    # sync
    p_sync = subparsers.add_parser("sync", help="Synchronize agent memory and state to GitHub")
    p_sync.add_argument("--message", default=None, help="Custom commit message")

    # serve-mcp
    p_mcp = subparsers.add_parser("serve-mcp", help="Launch native Model Context Protocol (MCP) server")

    # in-screen
    p_in_screen = subparsers.add_parser("in-screen", help="Algorithmic multi-factor screener across Indian equities (NSE/BSE)")
    p_in_screen.add_argument("--min-beta", type=float, default=1.40, help="Minimum Beta (default: 1.40)")
    p_in_screen.add_argument("--max-beta", type=float, default=2.80, help="Maximum Beta (default: 2.80)")
    p_in_screen.add_argument("--min-mcap", type=float, default=2000.0, help="Min Market Cap in Crores (default: 2000)")
    p_in_screen.add_argument("--min-roe", type=float, default=12.0, help="Min ROE % (default: 12.0)")
    p_in_screen.add_argument("--min-opmg", type=float, default=10.0, help="Min Operating Margin % (default: 10.0)")
    p_in_screen.add_argument("--max-price", type=float, default=5500.0, help="Max Share Price in INR (default: 5500)")
    p_in_screen.add_argument("--sort-by", type=str, default="12mpctN", help="Sort field (default: 12mpctN)")
    p_in_screen.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # in-audit
    p_in_audit = subparsers.add_parser("in-audit", help="Deep forensic Tickertape PRO audit of an Indian stock")
    p_in_audit.add_argument("ticker", help="NSE/BSE stock ticker (e.g. VMARCIND, KIRLOSENG, MARINE)")

    # in-preview
    p_in_prev = subparsers.add_parser("in-preview", help="Preview full 7-phase allocation for Indian equities (Zerodha Kite routing)")
    p_in_prev.add_argument("--budget", default="auto", help="Budget in INR (default: auto from Zerodha Kite)")
    p_in_prev.add_argument("--mode", choices=["live", "paper"], default="live", help="Execution mode")

    # in-execute
    p_in_exec = subparsers.add_parser("in-execute", help="Execute confirmed live rebalancing trades for Indian equities (Zerodha Kite)")
    p_in_exec.add_argument("--budget", default="auto", help="Budget in INR (default: auto from Zerodha Kite)")
    p_in_exec.add_argument("--mode", choices=["live", "paper"], default="live", help="Execution mode")

    # in-retrospective
    p_in_retro = subparsers.add_parser("in-retrospective", help="Run Phase 0 adversarial review on Indian equity portfolio")

    # kite-status
    p_kite_stat = subparsers.add_parser("kite-status", help="Audit Zerodha Kite Connect v3 connectivity, cash balance, and holdings")

    # kite-login
    p_kite_log = subparsers.add_parser("kite-login", help="Authenticate daily Zerodha Kite Connect session")
    p_kite_log.add_argument("--token", "-t", default=None, help="Direct request_token from callback URL")
    p_kite_log.add_argument("--url", "-u", default=None, help="Full callback URL with request_token")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "run": cmd_run,
        "cycle": cmd_run,
        "status": cmd_status,
        "auth": cmd_auth,
        "login": cmd_auth,
        "tt-login": cmd_tt_login,
        "tickertape-login": cmd_tt_login,
        "debate": cmd_debate,
        "eval": cmd_eval,
        "preview": cmd_preview,
        "execute": cmd_execute,
        "drain": cmd_drain,
        "retrospective": cmd_retrospective,
        "test": cmd_test,
        "sync": cmd_sync,
        "serve-mcp": cmd_serve_mcp,
        "in-screen": cmd_in_screen,
        "in-audit": cmd_in_audit,
        "in-preview": cmd_in_preview,
        "in-execute": cmd_in_execute,
        "in-retrospective": cmd_in_retrospective,
        "kite-status": cmd_kite_status,
        "kite-login": cmd_kite_login,
    }
    cmds[args.command](args)

if __name__ == "__main__":
    cli_entrypoint()
