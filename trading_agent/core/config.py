"""
Centralized Configuration & Fiduciary Constants for AQTA
"""

import os
import sys
from datetime import datetime

# Root paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MEMORY_DIR = os.path.join(REPO_ROOT, "memory")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

# Memory files
TRADE_JOURNAL_FILE = os.path.join(MEMORY_DIR, "trade_journal.jsonl")
FACTOR_WEIGHTS_FILE = os.path.join(MEMORY_DIR, "factor_weights.json")
RETROSPECTIVE_LOG_FILE = os.path.join(MEMORY_DIR, "retrospective_log.jsonl")
LESSONS_LEARNED_FILE = os.path.join(MEMORY_DIR, "lessons_learned.md")
EVIDENCE_LEDGER_FILE = os.path.join(MEMORY_DIR, "evidence_ledger.jsonl")

# Load .env if present
ENV_FILE = os.path.join(REPO_ROOT, ".env")
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

# Credential files
LOCAL_TOKEN_FILE = os.path.join(REPO_ROOT, "tickertape_token.json")
GLOBAL_CONFIG_DIR = os.path.expanduser("~/.gemini/config")
GLOBAL_TOKEN_FILE = os.path.join(GLOBAL_CONFIG_DIR, "tickertape_token.json")
GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, "mcp_config.json")

# Endpoints & Keys (Strictly resolved from environment or local .env)
MCP_ENDPOINT = os.environ.get("TICKERTAPE_MCP_URL", "https://mcp.tickertape.in/mcp")
ALPACA_KEY = os.environ.get("ALPACA_KEY", "")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
AV_API_KEY = os.environ.get("AV_API_KEY", "")

# Quantitative Fiduciary Constants & Hard Collars
MAX_PORTFOLIO_ASSETS = 3
MIN_BETA_INVARIANT = 1.40
MIN_BETA_COLLAR = 1.40
MAX_BETA_COLLAR = 2.80
STOP_LOSS_PCT = -12.0
TAKE_PROFIT_PCT = 35.0
TURNOVER_SCORE_DELTA = 20.0
SLIPPAGE_TOLERANCE_PCT = 1.0  # +1.0% limit price ceiling
TENURE_LOCK_DAYS = 60
WALLET_DRAIN_SAFETY_LIMIT = 0.50  # 50% max spend in rolling 60-min window

# Earnings Calendar (Configurable / Dynamically refreshed)
EARNINGS_CALENDAR = {
    "MU": "2026-09-30",
    "NVDA": "2026-11-17",
    "ALAB": "2026-11-05",
    "TSM": "2026-10-15",
    "ASML": "2026-10-14",
    "SOXX": None,
    "SMH": None
}

def is_earnings_within_48h(ticker: str) -> bool:
    """Checks whether an asset reports earnings within +/- 48 hours of today."""
    edate_str = EARNINGS_CALENDAR.get(ticker)
    if not edate_str:
        return False
    try:
        edate = datetime.strptime(edate_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (edate - today).days
        return -2 <= delta <= 2
    except Exception:
        return False
