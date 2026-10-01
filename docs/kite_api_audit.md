# Zerodha Kite Connect v3 API Architectural & Functional Audit

**Date of Audit**: October 2, 2026  
**Auditor**: Autonomous Quantitative Trading Agent (AQTA) Core Engineering  
**API Specification**: Kite Connect API v3 (`kiteconnect>=5.2.2`)  
**Target User Profile**: Kevin Hayes Anderson (`VXA630`)  
**Scope**: Full replacement and decommissioning of Groww, transitioning Indian equity operations to Zerodha Kite Connect v3.

---

## 1. Executive Summary

Groww's Model Context Protocol (MCP) server was audited and identified as **strictly read-only** for portfolio monitoring and market data, lacking native programmatic order execution endpoints. In contrast, **Zerodha Kite Connect v3** provides a production-grade REST API and Python SDK capable of 100% automated, unattended order routing, live margin auditing, demat holdings synchronization, After-Market Orders (AMO), and 1-year Good-Till-Triggered (GTT) OCO stop-loss/take-profit brackets.

This document details the functional capabilities of the Kite Connect v3 API, maps each system requirement to specific endpoints, analyzes API tiers, outlines session management protocols, and defines the migration strategy from Groww to Kite.

---

## 2. API Tier Comparison: Personal App vs Connect App

Zerodha Developer Platform (`developers.kite.trade`) supports two primary API configurations:

| Capability | Personal App (Free) | Connect App (Paid - 500 Credits/mo) | AQTA Architectural Decision |
| :--- | :--- | :--- | :--- |
| **Direct Order Placement** | ✅ Full Access (`CNC`, `MIS`, `LIMIT`, `MARKET`) | ✅ Full Access | Handled natively by Kite Connect v3 |
| **After Market Orders (AMO)** | ✅ Supported (`VARIETY_AMO`) | ✅ Supported (`VARIETY_AMO`) | Auto-routes during market closures & holidays |
| **GTT Triggers (Single & OCO)** | ✅ Supported (`place_gtt`) | ✅ Supported (`place_gtt`) | Native 1-year stop-loss (-12%) & target (+35%) |
| **Margin & Cash Balance** | ✅ Supported (`margins("equity")`) | ✅ Supported (`margins("equity")`) | Real-time cash, collateral & CNC balance check |
| **Holdings & Positions** | ✅ Supported (`holdings()`, `positions()`) | ✅ Supported (`holdings()`, `positions()`) | Real-time demat portfolio audit |
| **Order History & Trades** | ✅ Supported (`orders()`, `order_history()`) | ✅ Supported (`orders()`, `order_history()`) | Immutable trade journal reconciliation |
| **Historical Candlestick API** | ❌ Restricted | ✅ Full Access | Sourced via Tickertape PRO & Alpha Vantage |
| **Streaming WebSockets** | ❌ Restricted | ✅ Full Access (Ticker) | AQTA operates on EOD/periodic batch execution; streaming ticks not required |
| **Screening & Fundamentals** | ❌ Not available on Kite | ❌ Not available on Kite | Powered by Tickertape PRO Screener API |

**Conclusion**: The **Personal App (Free)** tier provides 100% of the operational and execution capabilities required by AQTA (margins, holdings, orders, AMO, GTT). Market screening, fundamental ratios (ROE, Operating Margin, Net Margin, Debt-to-Equity), and institutional scorecards are sourced via Tickertape PRO, forming a robust, zero-cost, institutional-grade stack.

---

## 3. Detailed Endpoint Mapping & Functional Verification

### 3.1 Authentication & Session Management
* **OAuth 2.0 Flow**:
  1. Login URL: `https://kite.zerodha.com/connect/login?api_key={api_key}&v=3`
  2. Redirect Callback: `http://127.0.0.1:8000/?action=login&status=success&request_token={request_token}`
  3. Token Exchange: `kite.generate_session(request_token, api_secret=api_secret)`
  4. Local Caching: `.kite_token.json` (persisted with 0600 file permissions, excluded from Git).
* **Token Lifecycle Rules**:
  * **Daily Invalidation**: Zerodha systematically flushes all access tokens every morning between **5:00 AM and 8:30 AM IST**.
  * **Single-Use Request Token**: Each `request_token` can only be exchanged once.
  * **Session Collision**: Logging in via the Kite web terminal or mobile app can invalidate an active API access token due to shared underlying session state.
  * **Refresh Mechanism**: AQTA provides `python agent.py kite-login` to capture and generate a new session token in one step.

### 3.2 Real-Time Margin & Cash Controller
* **Method**: `kite.margins(segment="equity")`
* **Response Payload**:
  ```json
  {
    "enabled": true,
    "net": 16000.0,
    "available": {
      "cash": 16000.0,
      "collateral": 0.0,
      "intraday_payin": 0.0
    },
    "utilised": {
      "debits": 0.0,
      "span": 0.0,
      "holding_sales": 0.0
    }
  }
  ```
* **AQTA Integration**:
  * Extracted via `trading_agent.core.zerodha.get_zerodha_margin()`.
  * Protects against over-allocation; reserves statutory cash buffer (approx. 2% or ₹500 INR) for STT, SEBI turnover fees, and GST.

### 3.3 Demat Holdings & Anti-Churn Tracking
* **Method**: `kite.holdings()`
* **Response Payload**:
  ```json
  [
    {
      "tradingsymbol": "VMARCIND",
      "exchange": "NSE",
      "isin": "INE0L6001018",
      "quantity": 10,
      "average_price": 500.0,
      "last_price": 525.0,
      "pnl": 250.0,
      "product": "CNC"
    }
  ]
  ```
* **AQTA Integration**:
  * Extracted via `trading_agent.core.zerodha.get_zerodha_holdings()`.
  * Enforces the **60-day anti-churn holding tenure** lock. Active holdings with tenure < 60 days cannot be liquidated for momentum churn unless a hard stop-loss is breached.

### 3.4 Direct Order Placement (Delivery / CNC)
* **Method**: `kite.place_order(...)`
* **Parameters**:
  * `variety`: `kite.VARIETY_REGULAR` (Market hours) or `kite.VARIETY_AMO` (Market holidays / After hours)
  * `exchange`: `kite.EXCHANGE_NSE`
  * `tradingsymbol`: Asset ticker (e.g. `SIGMAADV`, `VMARCIND`, `KIRLOSENG`)
  * `transaction_type`: `kite.TRANSACTION_TYPE_BUY`
  * `quantity`: Integer share count (e.g. 11, 10, 10)
  * `product`: `kite.PRODUCT_CNC` (Cash & Carry Delivery)
  * `order_type`: `kite.ORDER_TYPE_LIMIT`
  * `price`: Limit order price (calculated from screened LTP)
* **Exception Handling**:
  * Automatic AMO fallback: If regular order returns `Market is closed`, the agent automatically catches the exception and retries with `variety=kite.VARIETY_AMO`.

### 3.5 Good-Till-Triggered (GTT) Bracket Protection
* **Method**: `kite.place_gtt(...)`
* **Trigger Type**: `kite.GTT_TYPE_OCO` or `kite.GTT_TYPE_SINGLE`
* **Lifespan**: Valid for **1 calendar year** on NSE/BSE without manual intervention.
* **Stop-Loss Collar**: Set at -12.0% below execution price.
* **Take-Profit Collar**: Set at +35.0% above execution price.
* **Function in AQTA**: Ensures immediate risk protection even if the local agent process is stopped after execution.

---

## 4. Decommissioning Plan for Groww

To ensure a clean, maintainable architecture with zero dead code or conflicting brokers:

1. **Broker Isolation**:
   * All Indian equity routing in `trading_agent/core/orchestrator.py` directs exclusively to **Zerodha Kite Connect v3**.
   * Replace Groww margin and holdings checks in `trading_agent/core/in_engine.py` with `get_zerodha_margin()` and `get_zerodha_holdings()`.
2. **CLI Modernization**:
   * Replace `python agent.py groww-status` with `python agent.py kite-status`.
   * Add `python agent.py kite-login` for single-step OAuth login and token refresh.
3. **Market Calendar**:
   * Implement a native NSE holiday and market hours validator in `trading_agent/core/zerodha.py` to eliminate external dependency on Groww's `resolve_market_time_and_calendar`.
4. **Deliberation Price Feeds**:
   * In `trading_agent/core/deliberation.py`, replace Groww MCP calls with Zerodha Kite LTP and Tickertape PRO live price feeds.
5. **Memory & Trade Journal**:
   * Ensure `trading_agent/core/memory.py` filters historical records seamlessly by market (`IN` / `US`) and broker (`Zerodha`).
