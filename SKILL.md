---
name: quantitative-investment-agent
description: >-
  Automated institutional dual-market quantitative investment agent for recurring capital allocation.
  Use when the user requests executing monthly investments, running the investment agent, screening
  high-beta tech stocks (US / Tickertape) or secular capex/power compounders (India / Zerodha Kite), auditing
  portfolio balances across brokers, or previewing/executing trade plans.
---

# Quantitative Investment Agent (Production Runbook & Self-Improving Feedback Loop)

An institutional-grade, multi-agent quantitative system designed for recurring capital allocation across dual global markets:
1. **US Equities**: High-beta, high-momentum technology and semiconductor monopolies via **Tickertape / DriveWealth** (live fractional execution) and **Alpaca** (virtual shadow testing).
2. **Indian Equities**: High-conviction secular industrial, capex, and power engineering compounders via **Zerodha Kite Connect v3** (live delivery cash / GTT order execution) and **Tickertape PRO India**.

Equipped with a **closed feedback loop, SOTA multi-agent deliberation, and persistent agent memory**, the system automatically audits previous executions, runs an adversarial debate to evaluate realized alpha and drawdown, calibrates its factor scoring weights, and evolves continuously over time while strictly preserving the **Fiduciary Anti-Ruin Mandate**.

---

## 1. System Architecture & Dual-Broker Topology

```
┌───────────────────────────────────────────────────────────────────────────┐
│              CONTINUOUS AGENT LEARNING & BROKER TOPOLOGY                  │
├─────────────────────────────────────┬─────────────────────────────────────┤
│   US BROKER: Tickertape / DriveWealth│   INDIAN BROKER: Zerodha Kite Connect│
│   • Cash Equity Fractional Orders   │   • Segment: Delivery Cash (CNC)    │
│   • Funded via RBI LRS (INR -> USD) │   • Direct Order API & 1-Year GTT   │
│   • Brokerage: 0.15% (Pro Tier)     │   • Automated Execution & AMO Queue │
├─────────────────────────────────────┴─────────────────────────────────────┤
│                     PERSISTENT AGENT MEMORY STORE                         │
│   • trade_journal.jsonl: Immutable record of past trades & entry factors  │
│   • factor_weights.json: Dynamic quantitative model weights & invariants  │
│   • retrospective_log.jsonl: Historical multi-agent adversarial reviews  │
│   • lessons_learned.md: Synthesized post-mortem knowledge repository     │
├───────────────────────────────────────────────────────────────────────────┤
│               PHASE 0: CONTINUOUS ADVERSARIAL FEEDBACK LOOP               │
│   • Performance Attribution: Evaluates active picks vs SOXX / Nifty Midcap│
│   • Quant Auditor vs Risk Challenger: Automated adversarial debate in code│
│   • Recursive Calibration: Gradient-adjusted weights persisted to disk    │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Continuous Retrospective & Recursive Feedback Loop (Phase 0)

Every monthly cycle begins with an automated retrospective of all historical positions held in the portfolio:

### A. How the Feedback Loop Works:
1. **Performance Accountability**:
   - The bot pulls holding period return from live account holdings (`ASML`, `TSM`, and newly bought assets).
   - Computes portfolio aggregate return and benchmarks against proxies (`SOXX` for US, `Nifty Midcap 150` for IN).
   - Evaluates **Realized Active Alpha** ($\text{Return}_{portfolio} - \text{Return}_{benchmark}$).
2. **Automated Adversarial Review Debate**:
   - **Quant Auditor**: Assesses whether momentum velocity or earnings growth accurately forecasted alpha.
   - **Risk & Drawdown Challenger**: Evaluates whether high beta produced uncompensated drawdown or volatility whipsaw.
3. **Recursive Factor Calibration**:
   - If alpha outperformed, reinforces the 6-month momentum weight for trend persistence.
   - If alpha underperformed, tilts weighting toward forward EPS growth revisions and valuation upside.
   - Logs the decision rationale into [`retrospective_log.jsonl`](memory/retrospective_log.jsonl) and writes updated weights directly to [`memory/factor_weights.json`](memory/factor_weights.json).

### B. High-Risk, High-Return Hard Invariants:
To prevent the adaptive model from experiencing "risk-aversion drift", the feedback loop enforces strict mathematical boundaries:
- **Minimum Portfolio Beta $\ge 1.40$**: Always targets high-beta leaders.
- **Concentrated Conviction ($\le 3$ Assets per Market)**: Never dilutes capital across 5–10 stocks; maintains concentrated allocation.
- **Minimum Momentum Weight $\ge 20\%$**: Price velocity and relative strength always hold top priority.
- **Pure-Play Market Monopolies**: Avoids speculative micro-caps or low-liquidity penny stocks.

---

## 3. Dynamic Portfolio Rebalancing, Exit Rules & Capital Recycling

In addition to recurring monthly accumulation, the bot includes a full **Portfolio Rebalancing & Capital Recycling Engine**:

### A. Core Exit & Trimming Triggers:
1. **Hard Stop-Loss Liquidation (-12%)**:
   - Liquidates 100% of an asset immediately if loss breaches -12% to preserve core capital.
2. **Take-Profit Harvesting (+35%)**:
   - Trims 50% of the position upon reaching +35% gain to lock in profits while letting remainder run.
3. **60-Day Anti-Churn Tenure Lock**:
   - Assets held for $< 60$ days are **strictly locked** against discretionary rebalancing churn, saving 1.17% round-trip fees and 31.2% Indian STCG tax on foreign assets.

### B. Capital Recycling Economics:
- When a position is liquidated or trimmed, its freed cash is pooled together with fresh monthly inflows.
- The consolidated pool is automatically split across the top conviction basket, compounding capital into highest-conviction assets.
- Live execution handles sell orders before buy legs, with automatic quote-lock refreshes and Zero-Limbo residual absorption.

---

## 4. Simplified 2-Step User Workflow (Human-in-the-Loop)

You do not need to memorize multiple flags, pick stocks, or write complex code. The system is designed around a strict, intuitive **2-Command UX Contract**:

### 🛡️ Seamless Execution Mandate (Zero Codebase Digging)
* **DO NOT read source code, inspect internal files, or run git log/diff** when running the trading cycle. `agent.py run` is completely self-contained and handles all audits, screening, and status reporting in a single command.
* **Exact Python Command**: Always invoke using `.\.venv\Scripts\python.exe agent.py run` directly. Never test python paths, check pip lists, or inspect repo code before executing.
* **If Zerodha Kite session is expired**: `agent.py run` exits cleanly (code 0) and displays the 1-click authorization link directly in its output. Present it cleanly to the user. When the user provides the token/URL, run `.\.venv\Scripts\python.exe agent.py kite-login --token <TOKEN>`, then re-run `.\.venv\Scripts\python.exe agent.py run` to formulate the live plan.

```
Step 1: You say: "run investment agent" (or "run trading agent")
        └──> Agent executes: .\.venv\Scripts\python.exe agent.py run
             (Audits dual wallets, Phase 0 retrospectives, whole-market screeners from scratch,
              multi-agent committee deliberations, and previews exact dual-market allocations)

Step 2: You review the preview and say: "execute"
        └──> Agent executes: .\.venv\Scripts\python.exe agent.py run --execute
             (Commits confirmed US orders to Tickertape/Alpaca, routes Zerodha Kite CNC / GTT orders,
              records immutable trade journal logs, and synchronizes state to Git origin/main)
```

---

## 5. Execution Window & Capital Delay Management

### A. Real-World LRS Clearance Dynamics:
Inward USD deposits via HDFC outward remittance under RBI LRS take **21 to 53 hours** (or up to 100 hours over national holidays such as Gandhi Jayanti on October 2). The 3-State Capital Controller (`CAPITAL_IN_FLIGHT`) protects in-transit funds from premature commitment.

### B. Zerodha Kite Connect v3 Execution Truth:
Zerodha Kite Connect v3 provides direct programmatic order execution for Delivery Cash (CNC), After-Market Orders (AMO), and 1-year Good-Till-Triggered (GTT) brackets. The engine routes precision limit orders directly through the Kite Connect REST API, attaches -12% Stop-Loss and +35% Take-Profit GTT brackets, logs them to `memory/trade_journal.jsonl`, and updates the Tickertape PRO Master Watchlist.

---

## 6. Zero-Limbo Capital Safety Architecture

The user mandate is strict: **"Capital must not be lost in limbo."**
The system implements three mathematical and systems safety layers:
1. **In-Flight Deposit Lockout**: Never trades against unconfirmed or partial wire transfers.
2. **Quote-Lock Auto-Refresh**: If Tickertape's 180-second preview session expires (`SESSION_NOT_FOUND`), the bot automatically requests a fresh quote lock rather than aborting.
3. **Zero-Limbo Capital Absorption**: If Leg 1 fills, but Leg 2 fails (due to ticker halt or unexpected broker error), the bot **automatically absorbs unspent cash into the successful fill** using live fill prices.

---

## 7. Token Authentication & Auto-Refresh
To ensure the bot never crashes on token expiration:
- Use `python agent.py auth` (or `python agent.py login`) to authenticate both Tickertape PRO and Zerodha Kite Connect v3 in a single turnkey step.
- The helper script [`tickertape_auth.py`](scripts/tickertape_auth.py) manages OAuth 2.1 PKCE with public client registration and atomic file saves.
- Zerodha Kite daily session tokens are authenticated via `python agent.py kite-login` and cached in `.kite_token.json`.
