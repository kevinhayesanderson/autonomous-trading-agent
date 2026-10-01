"""
Authentication & Token Management for Tickertape MCP
"""

import os
import sys
import json
from .config import (
    REPO_ROOT,
    LOCAL_TOKEN_FILE,
    GLOBAL_TOKEN_FILE,
    GLOBAL_CONFIG_FILE
)

def get_tickertape_token() -> str:
    """
    Resolves a valid Tickertape access token with priority:
    1. Direct environment variable TICKERTAPE_TOKEN
    2. Local tickertape_token.json in repo root (with auto-refresh)
    3. Global ~/.gemini/config/tickertape_token.json
    4. ~/.gemini/config/mcp_config.json Authorization Bearer header
    """
    # 1. Local or global token file with auto-refresh (Primary)
    for tfile in [LOCAL_TOKEN_FILE, GLOBAL_TOKEN_FILE]:
        if os.path.exists(tfile):
            try:
                auth_script = os.path.join(REPO_ROOT, "scripts", "tickertape_auth.py")
                if os.path.exists(auth_script):
                    sys.path.insert(0, os.path.dirname(auth_script))
                    import tickertape_auth
                    refreshed = tickertape_auth.get_valid_token()
                    if refreshed:
                        os.environ["TICKERTAPE_TOKEN"] = refreshed
                        return refreshed
                with open(tfile, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tok = data.get("access_token") or data.get("token")
                    if tok:
                        return tok.strip()
            except Exception:
                pass

    # 2. Direct environment variable TICKERTAPE_TOKEN
    env_tok = os.environ.get("TICKERTAPE_TOKEN")
    if env_tok and env_tok.strip():
        return env_tok.strip()

    # 3. Global mcp_config.json
    if os.path.exists(GLOBAL_CONFIG_FILE):
        try:
            with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                h = cfg.get("mcpServers", {}).get("tickertape", {}).get("headers", {}).get("Authorization", "")
                if h.startswith("Bearer "):
                    return h.split("Bearer ")[1].strip()
        except Exception:
            pass

    raise RuntimeError(
        "No Tickertape access token found. Please run 'python scripts/tickertape_auth.py' to login."
    )
