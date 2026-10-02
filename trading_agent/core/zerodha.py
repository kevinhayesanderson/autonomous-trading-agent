"""
Zerodha Kite Connect v3 Broker Integration Module
Enables automated order routing, GTT placement, margin auditing, portfolio holdings sync,
and market calendar resolution directly with the user's Zerodha demat account.
"""

import os
import json
import socket
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, time, timezone, timedelta

# Enforce IPv4 egress for kite.trade hosts to guarantee matching whitelisted static IP
_orig_getaddrinfo = socket.getaddrinfo
def _kite_getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    if host and "kite.trade" in str(host):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _kite_getaddrinfo_ipv4

from kiteconnect import KiteConnect

TOKEN_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".kite_token.json"))
GLOBAL_TOKEN_FILE = os.path.expanduser("~/.kite_token.json")

# Indian Standard Time (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Standard NSE / BSE Trading Holidays (2026 Reference)
NSE_HOLIDAYS_2026 = {
    "2026-01-26": "Republic Day",
    "2026-02-17": "Mahashivratri",
    "2026-03-03": "Holi",
    "2026-03-20": "Id-ul-Fitr (Ramzan Id)",
    "2026-03-27": "Ram Navami",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id (Eid al-Adha)",
    "2026-06-25": "Muharram",
    "2026-08-15": "Independence Day",
    "2026-09-04": "Milad-un-Nabi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas"
}

def load_kite_token() -> Optional[Dict[str, Any]]:
    """Loads cached Kite session token from local project or user directory."""
    for path in [TOKEN_FILE, GLOBAL_TOKEN_FILE]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("access_token"):
                        return data
            except Exception:
                pass
    return None

def get_kite_client() -> Optional[KiteConnect]:
    """Initializes and returns an authenticated KiteConnect client."""
    api_key = os.environ.get("KITE_API_KEY")
    api_secret = os.environ.get("KITE_API_SECRET")

    if not api_key or not api_secret:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k == "KITE_API_KEY" and not api_key:
                            api_key = v
                        elif k == "KITE_API_SECRET" and not api_secret:
                            api_secret = v

    token_data = load_kite_token()
    if not api_key and token_data and token_data.get("api_key"):
        api_key = token_data["api_key"]

    if not api_key:
        return None

    if not token_data or not token_data.get("access_token"):
        return None

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token_data["access_token"])
    return kite

def is_nse_market_open(dt: Optional[datetime] = None) -> Tuple[bool, str]:
    """
    Evaluates whether the National Stock Exchange (NSE) is currently open for live trading.
    Checks day of week, NSE national holidays, and normal market hours (9:15 AM - 3:30 PM IST).
    """
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    else:
        dt = dt.astimezone(IST)

    date_str = dt.strftime("%Y-%m-%d")
    weekday = dt.weekday()  # Monday = 0, Sunday = 6

    # 1. Weekend Check
    if weekday == 5:
        return False, "CLOSED (Saturday Weekend)"
    if weekday == 6:
        return False, "CLOSED (Sunday Weekend)"

    # 2. National Holiday Check
    if date_str in NSE_HOLIDAYS_2026:
        holiday_name = NSE_HOLIDAYS_2026[date_str]
        return False, f"CLOSED (Market Holiday: {holiday_name})"

    # 3. Market Hours Check (9:15 AM to 3:30 PM IST)
    market_open = time(9, 15)
    market_close = time(15, 30)
    current_time = dt.time()

    if current_time < market_open:
        return False, "CLOSED (Pre-Market Session - Opens at 9:15 AM IST)"
    elif current_time > market_close:
        return False, "CLOSED (Post-Market Session - Closed at 3:30 PM IST)"

    return True, "OPEN (Live Market Session)"

def get_zerodha_margin() -> Dict[str, Any]:
    """Retrieves live available margin and clear cash from Zerodha."""
    kite = get_kite_client()
    if not kite:
        return {
            "clear_cash": 0.0,
            "cnc_balance_available": 0.0,
            "authenticated": False,
            "error": "Zerodha not authenticated. Run: python agent.py kite-login"
        }

    try:
        margins = kite.margins(segment="equity")
        available = margins.get("available", {})
        live_bal = float(available.get("live_balance", 0.0))
        net = float(margins.get("net", live_bal))
        cash = max(float(available.get("cash", 0.0)), live_bal, net)
        return {
            "clear_cash": cash,
            "cnc_balance_available": net,
            "net": net,
            "authenticated": True,
            "raw": margins
        }
    except Exception as e:
        return {
            "clear_cash": 0.0,
            "cnc_balance_available": 0.0,
            "authenticated": False,
            "error": str(e)
        }

def get_zerodha_holdings() -> List[Dict[str, Any]]:
    """Retrieves settled equity demat holdings from Zerodha."""
    kite = get_kite_client()
    if not kite:
        return []

    try:
        raw_holdings = kite.holdings()
        holdings = []
        for h in raw_holdings:
            qty = float(h.get("quantity", 0))
            avg_p = float(h.get("average_price", 0.0))
            cur_p = float(h.get("last_price", avg_p))
            inv = qty * avg_p
            cur_val = qty * cur_p
            holdings.append({
                "ticker": h.get("tradingsymbol", ""),
                "isin": h.get("isin", ""),
                "shares": qty,
                "invested": round(inv, 2),
                "current": round(cur_val, 2),
                "pnl_pct": round(((cur_val - inv) / inv * 100.0) if inv > 0 else 0.0, 2),
                "tenure_days": 1
            })
        return holdings
    except Exception as e:
        print(f"  [!] Failed to fetch Zerodha holdings: {e}")
        return []

def get_zerodha_positions() -> Dict[str, Any]:
    """Retrieves day and net open trading positions from Zerodha."""
    kite = get_kite_client()
    if not kite:
        return {"net": [], "day": []}

    try:
        return kite.positions()
    except Exception as e:
        return {"net": [], "day": [], "error": str(e)}

def get_zerodha_orders() -> List[Dict[str, Any]]:
    """Retrieves all orders placed in the current session from Zerodha."""
    kite = get_kite_client()
    if not kite:
        return []

    try:
        return kite.orders()
    except Exception as e:
        return []

def get_zerodha_gtts() -> List[Dict[str, Any]]:
    """Retrieves all active GTT (Good-Till-Triggered) triggers from Zerodha."""
    kite = get_kite_client()
    if not kite:
        return []

    try:
        return kite.get_gtts()
    except Exception as e:
        return []

def get_zerodha_ltp(ticker: str, exchange: str = "NSE") -> Optional[float]:
    """Fetches last traded price (LTP) from Kite Connect if available."""
    kite = get_kite_client()
    if not kite:
        return None

    try:
        symbol = f"{exchange}:{ticker}"
        quotes = kite.ltp([symbol])
        if symbol in quotes:
            return float(quotes[symbol].get("last_price", 0.0))
    except Exception:
        pass
    return None

_INSTRUMENT_MAP: Dict[str, str] = {}

def resolve_kite_tradingsymbol(ticker: str, exchange: str = "NSE") -> str:
    """
    Resolves base ticker symbol (e.g. SIGMAADV, VMARCIND) to Kite's tradingsymbol
    (e.g. SIGMAADV-BE, VMARCIND-SM, MARINE) using Kite's instrument master.
    """
    global _INSTRUMENT_MAP
    if not _INSTRUMENT_MAP:
        kite = get_kite_client()
        if kite:
            try:
                insts = kite.instruments(exchange)
                for i in insts:
                    sym = i.get("tradingsymbol", "")
                    base = sym.split("-")[0]
                    if base not in _INSTRUMENT_MAP:
                        _INSTRUMENT_MAP[base] = sym
                    _INSTRUMENT_MAP[sym] = sym
            except Exception:
                pass
    return _INSTRUMENT_MAP.get(ticker, ticker)

def place_zerodha_order(
    ticker: str,
    qty: int,
    price: float,
    is_amo: bool = False,
    exchange: str = "NSE"
) -> Dict[str, Any]:
    """
    Places a live Delivery (CNC) limit order on Zerodha.
    Supports regular market orders or AMO (After Market Orders) when exchanges are closed.
    """
    kite = get_kite_client()
    if not kite:
        raise RuntimeError("Zerodha Kite not authenticated. Run: python agent.py kite-login")

    symbol = resolve_kite_tradingsymbol(ticker, exchange=exchange)
    variety = kite.VARIETY_AMO if is_amo else kite.VARIETY_REGULAR
    try:
        order_id = kite.place_order(
            variety=variety,
            exchange=exchange,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=qty,
            order_type=kite.ORDER_TYPE_LIMIT,
            product=kite.PRODUCT_CNC,
            price=round(price, 2)
        )
        return {
            "status": "PLACED",
            "order_id": order_id,
            "variety": variety,
            "ticker": symbol,
            "qty": qty,
            "price": price
        }
    except Exception as e:
        # If regular order failed due to market closed, retry automatically as AMO
        if not is_amo and ("market is closed" in str(e).lower() or "amo" in str(e).lower()):
            try:
                order_id = kite.place_order(
                    variety=kite.VARIETY_AMO,
                    exchange=exchange,
                    tradingsymbol=symbol,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=qty,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    product=kite.PRODUCT_CNC,
                    price=round(price, 2)
                )
                return {
                    "status": "PLACED_AMO",
                    "order_id": order_id,
                    "variety": "amo",
                    "ticker": symbol,
                    "qty": qty,
                    "price": price,
                    "note": "Automatically converted to AMO because market is closed"
                }
            except Exception as e2:
                raise RuntimeError(f"Zerodha AMO placement failed: {e2}")
        raise RuntimeError(f"Zerodha order placement failed: {e}")

def place_zerodha_gtt(
    ticker: str,
    qty: int,
    price: float,
    stop_loss_trigger: float,
    take_profit_trigger: Optional[float] = None,
    exchange: str = "NSE"
) -> Dict[str, Any]:
    """
    Places a native Zerodha GTT (Good Till Triggered) order.
    Remains active for 1 year until triggered, ideal for automated entries, stop losses, and market holidays.
    """
    kite = get_kite_client()
    if not kite:
        raise RuntimeError("Zerodha Kite not authenticated. Run: python agent.py kite-login")

    symbol = resolve_kite_tradingsymbol(ticker, exchange=exchange)
    orders = [{
        "transaction_type": kite.TRANSACTION_TYPE_BUY,
        "quantity": qty,
        "order_type": kite.ORDER_TYPE_LIMIT,
        "product": kite.PRODUCT_CNC,
        "price": round(price, 2)
    }]

    # Zerodha GTT trigger requirement: Trigger price must differ from last_price by > 0.25%
    # For limit buy entry, set trigger at 0.5% below limit price
    trigger_val = round(price * 0.995, 1)

    try:
        trigger_id = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=symbol,
            exchange=exchange,
            trigger_values=[trigger_val],
            last_price=round(price, 2),
            orders=orders
        )
        return {
            "status": "PLACED_GTT",
            "trigger_id": trigger_id,
            "ticker": symbol,
            "qty": qty,
            "trigger_price": trigger_val,
            "limit_price": price
        }
    except Exception as e:
        raise RuntimeError(f"Zerodha GTT placement failed: {e}")

def get_public_ip() -> Optional[str]:
    """Retrieves current external public IP address used for broker API egress."""
    import urllib.request
    for url in ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None

def audit_kite_status() -> Dict[str, Any]:
    """Provides a complete health and connectivity audit for Zerodha Kite Connect v3."""
    token_data = load_kite_token()
    token_present = bool(token_data and token_data.get("access_token"))
    margin = get_zerodha_margin()
    is_open, session_status = is_nse_market_open()

    return {
        "token_available": token_present,
        "authenticated": margin.get("authenticated", False),
        "user_name": token_data.get("user_name", "N/A") if token_data else "N/A",
        "user_id": token_data.get("user_id", "N/A") if token_data else "N/A",
        "email": token_data.get("email", "N/A") if token_data else "N/A",
        "clear_cash": margin.get("clear_cash", 0.0),
        "cnc_margin": margin.get("cnc_balance_available", 0.0),
        "holdings_count": len(get_zerodha_holdings()) if margin.get("authenticated") else 0,
        "market_open": is_open,
        "market_status": session_status,
        "public_ip": get_public_ip(),
        "error": margin.get("error")
    }
