"""
Broker Interface & Transport Layer (Tickertape MCP & Alpaca Paper)
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from .config import (
    MCP_ENDPOINT,
    ALPACA_KEY,
    ALPACA_SECRET,
    ALPACA_BASE_URL
)

def resolve_tool_name(tool_name: str) -> str:
    """Ensures MCP tool calls map properly to official _read or _write endpoints."""
    if tool_name.endswith("_read") or tool_name.endswith("_write"):
        return tool_name
    if tool_name in ["us_trade_place", "us_trade_cancel", "wl_write", "screener_manage"]:
        return f"{tool_name}_write"
    return f"{tool_name}_read"

def call_tickertape_mcp(token: str, tool_name: str, args: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Any:
    """
    Executes a JSON-RPC tool call directly against the Tickertape MCP endpoint.
    Parses SSE streams and standard JSON responses.
    """
    if args is None:
        args = {}
    actual_tool = resolve_tool_name(tool_name)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Antigravity-AQTA/2.2"
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": actual_tool, "arguments": args}
    }
    if not MCP_ENDPOINT.startswith("https://"):
        raise ValueError(f"Insecure MCP endpoint: {MCP_ENDPOINT}")
    req = urllib.request.Request(MCP_ENDPOINT, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
        return {"success": False, "error": f"HTTP {e.code}", "details": err_body}
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Parse SSE payload
    for line in raw.splitlines():
        if line.startswith("data:"):
            try:
                parsed = json.loads(line[5:].strip())
                if "result" in parsed and "content" in parsed["result"]:
                    for item in parsed["result"]["content"]:
                        if item.get("type") == "text":
                            try:
                                return json.loads(item["text"])
                            except Exception:
                                return item["text"]
                return parsed
            except Exception:
                pass
    try:
        return json.loads(raw)
    except Exception:
        return {"success": False, "raw": raw}

def get_live_ticker_quote(token: str, ticker: str) -> Optional[float]:
    """Fetches real-time price quote from Tickertape (handles CSV & JSON)."""
    try:
        res = call_tickertape_mcp(token, "us_quotes_get_latest", {"market": "US", "ticker": ticker})
        if isinstance(res, str) and "t,p,lcp" in res:
            lines = res.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split(",")
                if len(parts) >= 2:
                    return float(parts[1])
        elif isinstance(res, dict):
            if "quotes" in res and res["quotes"]:
                q = res["quotes"][0]
                price = float(q.get("lastPrice") or q.get("closePrice") or q.get("prevClosePrice") or 0.0)
                if price > 0:
                    return price
            p = float(res.get("price") or res.get("lastPrice") or res.get("p") or 0.0)
            if p > 0:
                return p
    except Exception:
        pass
    return None

def verify_recent_order(token: str, ticker: str, action: str, max_age_seconds: int = 90) -> Tuple[Optional[str], Optional[str]]:
    """Reconciles with broker trade list to prevent phantom order duplication on HTTP timeouts."""
    try:
        res = call_tickertape_mcp(token, "us_trade_list", {"limit": 5})
        trades = res.get("trades", []) if isinstance(res, dict) else []
        now = datetime.now().astimezone()
        for t in trades:
            sec_ticker = t.get("securityInfo", {}).get("ticker")
            ttype = t.get("transactionType", "").lower()
            if sec_ticker == ticker and ttype == action.lower():
                c_at_str = t.get("createdAt")
                if c_at_str:
                    c_at = datetime.fromisoformat(c_at_str.replace("Z", "+00:00"))
                    age = (now - c_at).total_seconds()
                    if age <= max_age_seconds:
                        return t.get("id"), t.get("status", "unknown")
    except Exception:
        pass
    return None, None

def alpaca_api_request(endpoint: str, method: str = "GET", body: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
    """Interacts with Alpaca Paper Trading REST API."""
    url = f"{ALPACA_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET,
        "Content-Type": "application/json"
    }
    data = json.dumps(body).encode("utf-8") if body else None
    if not url.startswith("https://"):
        raise ValueError(f"Insecure endpoint URL: {url}")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        return {"error": f"HTTP {e.code}", "details": err_msg, "status": "failed"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}
