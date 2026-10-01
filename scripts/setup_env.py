"""
Turnkey Environment Bootstrapper & Verification Script
Verifies all prerequisites, credentials, connectivity, and Antigravity (AGY) readiness.
Run on any freshly cloned computer:
    python scripts/setup_env.py
"""

import os
import sys
import shutil
import urllib.request
import json
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

def check_python():
    print("1. Checking Python Environment...")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major >= 3 and minor >= 10:
        print(f"   [OK] Python {major}.{minor} detected (meets requirement >= 3.10).")
        return True
    else:
        print(f"   [FAIL] Python {major}.{minor} detected. Please upgrade to Python 3.10+.")
        return False

def check_git():
    print("2. Checking Git & Remote Synchronization...")
    try:
        res = subprocess.run(["git", "remote", "-v"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if res.returncode == 0 and "trading-agent" in res.stdout:
            print("   [OK] Git repository and remote origin verified.")
            return True
        elif res.returncode == 0:
            print(f"   [OK] Git repository verified. Remote: {res.stdout.splitlines()[0] if res.stdout else 'none'}")
            return True
    except Exception as e:
        print(f"   [WARN] Git check error: {e}")
    return False

def check_env_files():
    print("3. Checking Configuration & .env...")
    env_file = os.path.join(REPO_ROOT, ".env")
    env_example = os.path.join(REPO_ROOT, ".env.example")

    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            shutil.copyfile(env_example, env_file)
            print("   [CREATED] Created local .env from .env.example template.")
        else:
            print("   [WARN] .env.example missing.")
    else:
        print("   [OK] Local .env file present.")

    # Check Antigravity GEMINI.md
    gemini_md = os.path.join(REPO_ROOT, "GEMINI.md")
    if os.path.exists(gemini_md):
        print("   [OK] AGY workspace rules (GEMINI.md) active.")
    else:
        print("   [WARN] GEMINI.md not found in repository root.")
    return True

def check_alpaca():
    print("4. Checking Alpaca Paper Trading Sandbox...")
    # Load from environment or local .env
    key = os.environ.get("ALPACA_KEY", "")
    secret = os.environ.get("ALPACA_SECRET", "")
    base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")

    if not key or not secret:
        print("   [SKIP] ALPACA_KEY or ALPACA_SECRET not set in environment or .env.")
        return False

    if not base_url.startswith("https://"):
        print("   [ERROR] Insecure ALPACA_BASE_URL scheme.")
        return False

    try:
        req = urllib.request.Request(
            f"{base_url}/account",
            headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            eq = data.get("equity", "0")
            print(f"   [OK] Connected to Alpaca Paper Account {data.get('account_number')} (Equity: ${float(eq):,.2f} USD).")
            return True
    except Exception as e:
        print(f"   [WARN] Alpaca check notice: {e}")
        return False

def check_tickertape():
    print("5. Checking Tickertape Token & Intelligence...")
    try:
        from trading_agent.core.auth import get_tickertape_token
        token = get_tickertape_token()
        if token:
            print("   [OK] Tickertape access token active.")
            return True
    except Exception as e:
        print(f"   [ACTION REQUIRED] No active Tickertape token found: {e}")
        print("   -> Run `python agent.py tt-login` (or `python agent.py auth`) to authenticate.")
        return False

def check_zerodha():
    print("6. Checking Zerodha Kite Connect v3...")
    try:
        from trading_agent.core.zerodha import audit_kite_status
        st = audit_kite_status()
        if st.get("authenticated"):
            print(f"   [OK] Zerodha Kite Connect authenticated as {st.get('user_name')} ({st.get('user_id')}).")
            print(f"        Available Margin: Rs {st.get('cnc_margin', 0.0):,.2f} INR")
            return True
        elif st.get("token_available"):
            print(f"   [NOTICE] Kite credentials detected, session requires daily authentication.")
            print(f"   -> Run `python agent.py kite-login` (or `python agent.py auth`).")
            return True
        else:
            print(f"   [NOTICE] KITE_API_KEY or KITE_API_SECRET missing in .env.")
            return False
    except Exception as e:
        print(f"   [WARN] Zerodha check notice: {e}")
        return False

def main():
    print("\n" + "=" * 76)
    print(" AUTONOMOUS QUANTITATIVE TRADING AGENT (AQTA) - ENVIRONMENT VERIFICATION")
    print("=" * 76 + "\n")

    p_ok = check_python()
    g_ok = check_git()
    e_ok = check_env_files()
    a_ok = check_alpaca()
    t_ok = check_tickertape()
    k_ok = check_zerodha()

    print("\n" + "=" * 76)
    print(" VERIFICATION SUMMARY")
    print("=" * 76)
    if p_ok and g_ok and e_ok:
        print(" [READY FOR DUAL-MARKET OPERATIONS]")
        print(" To run the agent on this computer:")
        print("   1. Authenticate sessions:   python agent.py auth")
        print("   2. Preview allocations:     python agent.py run (or in-preview)")
        print("   3. Commit live trades:      python agent.py execute (or in-execute)")
    else:
        print(" [ATTENTION] Some prerequisites need review above before running live trades.")
    print("=" * 76 + "\n")

if __name__ == "__main__":
    main()
