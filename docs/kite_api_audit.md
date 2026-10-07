# Zerodha Kite Connect v3 API Architectural & Functional Specification
**System**: Autonomous Quantitative Trading Agent (AQTA)  
**API Specification**: Kite Connect API v3 (`kiteconnect>=5.2.2`)  
**Scope**: Production Indian equity execution architecture, margin controller, and GTT bracket management.

---

## 1. Executive Summary

**Zerodha Kite Connect v3** serves as the primary programmatic execution engine for Indian equities (NSE & BSE) within the Autonomous Quantitative Trading Agent (AQTA). The system utilizes the official Kite Connect Python SDK to perform automated, unattended Delivery Cash (CNC) order routing, real-time margin and collateral tracking, demat holdings auditing, After-Market Orders (AMO), and 1-year Good-Till-Triggered (GTT) OCO stop-loss and take-profit brackets.

---

## 2. API Capabilities & Operational Architecture

| Capability | Production Endpoint / Method | Operational Scope & Usage in AQTA |
| :--- | :--- | :--- |
| **Direct Order Placement** | `kite.place_order(...)` | Executes Cash & Carry (`CNC`) Delivery limit orders with ask-spread boundaries. |
| **After Market Orders (AMO)** | `kite.place_order(variety=VARIETY_AMO)` | Auto-queues orders during exchange holidays and off-market hours. |
| **GTT Triggers (OCO)** | `kite.place_gtt(...)` | Establishes 1-year stop-loss (-12%) and profit target (+35%) brackets. |
| **Margin & Cash Balance** | `kite.margins(segment="equity")` | Audits available cash margin; enforces statutory cash buffers (~₹500 INR). |
| **Holdings & Positions** | `kite.holdings()` | Real-time demat portfolio audit; enforces 60-day anti-churn tenure locks. |
| **Order History & Trades** | `kite.orders()`, `kite.order_history()` | Reconciles fills into immutable trade journal (`memory/trade_journal.jsonl`). |
| **Market Screening** | Tickertape PRO India API | Scans 5,000+ NSE/BSE stocks for beta, margins, ROE, and debt metrics. |

---

## 3. Endpoint Mapping & Execution Protocol

### 3.1 Authentication & Session Management
* **OAuth 2.0 Flow**:
  1. Login URL: `https://kite.zerodha.com/connect/login?api_key={api_key}&v=3`
  2. Local Redirect Callback: `http://127.0.0.1:8000/?action=login&status=success&request_token={request_token}`
  3. Token Exchange: `kite.generate_session(request_token, api_secret=api_secret)`
  4. Local Caching: `.kite_token.json` (persisted locally with restricted permissions, excluded from Git).
* **Token Lifecycle Rules**:
  * Zerodha systematically flushes access tokens daily between **5:00 AM and 8:30 AM IST**.
  * The system provides `python agent.py kite-login` (or `python agent.py auth`) to capture and generate daily session tokens seamlessly via local HTTP callback.

### 3.2 Real-Time Margin & Cash Controller
* **Method**: `kite.margins(segment="equity")`
* **Production Integration** (`trading_agent/core/zerodha.py`):
  * Retrieves `available.cash` and `available.live_balance`.
  * Deducts a statutory cash buffer (approx. 2% or ₹500 INR) for STT, SEBI turnover charges, and GST.
  * Calculates integer share quantities: $\text{Quantity} = \lfloor \text{Target Allocation} / \text{Limit Price} \rfloor$.

### 3.3 Demat Holdings & Anti-Churn Tracking
* **Method**: `kite.holdings()`
* **Production Integration** (`trading_agent/core/zerodha.py`):
  * Maps active demat positions, average purchase prices, and unrealized P&L.
  * Intersects holdings with `memory/trade_journal.jsonl` to calculate holding tenure in days.
  * Enforces the **60-day anti-churn tenure lock**: holdings $< 60$ days cannot be rotated out for momentum churn.

### 3.4 Direct Order Placement (Delivery / CNC)
* **Method**: `kite.place_order(...)`
* **Parameters**:
  * `variety`: `kite.VARIETY_REGULAR` (Market hours) or `kite.VARIETY_AMO` (After hours / holidays)
  * `exchange`: `kite.EXCHANGE_NSE`
  * `tradingsymbol`: Asset ticker (e.g. `SIGMAADV`, `KIRLOSENG`, `MARINE`)
  * `transaction_type`: `kite.TRANSACTION_TYPE_BUY`
  * `quantity`: Integer share count
  * `product`: `kite.PRODUCT_CNC` (Cash & Carry Delivery)
  * `order_type`: `kite.ORDER_TYPE_LIMIT`
  * `price`: Limit order price
* **Mainboard Filter**: Pre-filters symbols with `is_nse_mainboard_tradable()` (`LotSize == 1`) to eliminate SME odd-lot rejections.

### 3.5 Good-Till-Triggered (GTT) Bracket Protection
* **Method**: `kite.place_gtt(...)`
* **Trigger Type**: `kite.GTT_TYPE_OCO`
* **Lifespan**: Valid for **1 calendar year** on NSE/BSE without manual intervention.
* **Stop-Loss Collar**: Set at -12.0% below execution price.
* **Take-Profit Collar**: Set at +35.0% above execution price.

---

## 4. Production Integration & Verification

The Kite Connect v3 integration is organized across the following core modules:
1. **`trading_agent/core/zerodha.py`**: Core API wrapper for authentication, margins, holdings, quote retrieval, and order routing.
2. **`trading_agent/core/in_engine.py`**: 7-phase execution pipeline for Indian equities.
3. **`trading_agent/core/orchestrator.py`**: Unified dual-market orchestrator coordinating US and Indian allocations.
4. **`scripts/kite_auth.py`**: Local HTTP listener and OAuth callback handler.
