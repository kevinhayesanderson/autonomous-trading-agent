# Quantitative Agent Memory & Lessons Learned Log

This repository records empirical insights, performance post-mortems, and adversarial challenge results from each monthly cycle to drive recursive self-improvement while maintaining the **High-Risk, High-Return** mandate.

---

## Retrospective Log: October 1–2, 2026 Multi-Agent Adversarial System Review
* **Date**: October 2, 2026
* **Cycle**: Dual-Market Unification & SOTA Pipeline Audit
* **Panel**: Independent 6-Specialist Adversarial Review Council
* **Adversarial Audit Findings & Remediations**:
  1. **Groww Decommissioned & Migration to Zerodha Kite Connect v3**:
     - *Finding*: Audit of Groww's MCP tool catalog confirmed that Groww exposes market data, depth, technical indicators, candlestick history, margins, and demat holdings, but **does not expose a direct order placement API** (no `place_order` or `create_gtt` in its tool catalog).
     - *Action*: Decommissioned Groww completely. Migrated Indian equity execution to **Zerodha Kite Connect v3** (`kiteconnect`), providing 100% automated direct Delivery (CNC) limit orders, After-Market Orders (AMO) for market holiday execution, native 1-year Good-Till-Triggered (GTT) OCO stop-loss (-12%) and take-profit (+35%) brackets, and live demat holdings sync.
  2. **Elimination of Static Blueprints & Ad-Hoc Scripts**:
     - *Finding*: Previous sessions created ad-hoc scripts (`scripts/in_execute_plan.py`) with hardcoded tickers (`KIRLOSENG`, `TIMKEN`, `ISGEC`) and static prices, violating the dynamic screening mandate.
     - *Action*: Purged `scripts/in_execute_plan.py` from the filesystem and Git history. Removed all `--plan blueprint-a/b` flags. Whole-market screening runs 100% dynamically from scratch on every run without carry-over or solution-fitting bias.
  3. **Step A Sell Execution Loop Fixed**:
     - *Finding*: In `trading_agent/core/engine.py`, rebalancing logic computed sell orders for Stop-Loss (-12%) and Take-Profit (+35%) triggers, but the loop actually placing those sell orders with the broker was completely omitted.
     - *Action*: Implemented the sell execution loop with `place_order_with_resilience()` before buy basket sizing.
  4. **Bidirectional Slippage Guard Repaired**:
     - *Finding*: In `trading_agent/core/execution.py`, `exec_price > limit_ceiling` was evaluated on all orders. On a `SELL` order, this failed to prevent severe downward slippage.
     - *Action*: Enforced directional checks: `BUY <= limit_ceiling` and `SELL >= limit_ceiling` (limit floor).
  5. **60-Day Anti-Churn Tenure Lock Fixed**:
     - *Finding*: `get_holding_tenure_days()` matched the earliest entry rather than the most recent BUY record, and defaulted to 999 days if unrecorded.
     - *Action*: Updated to match the latest BUY date and default unrecorded holdings to 0 days (locked), safeguarding new acquisitions against premature liquidation.
  6. **Zero-Limbo Capital Absorption Fixed**:
     - *Finding*: On buy leg failures, unspent cash was stranded because absorption logic attempted to use the failed ticker's quote.
     - *Action*: Re-engineered the absorption pool to dynamically roll unspent funds into the primary successful fill using the target ticker's live execution price.
  7. **Dynamic Factor Recalibration Persisted to Disk**:
     - *Finding*: `run_adversarial_retrospective()` calculated updated factor weights based on benchmark outperformance, but never wrote them back to `memory/factor_weights.json`.
     - *Action*: Added persistent JSON serialization on live execution runs (`is_preview=False`), closing the adaptive feedback loop.
  8. **Max-2 Interactions Contract Formalized**:
     - *Finding*: User interactions required multiple steps and choices.
     - *Action*: Strictly standardized on 2 interactions:
       - Step 1: User prompts `"run investment agent"` -> `python agent.py run` (analyzes dual wallets, whole-market screening from scratch, multi-agent committee deliberation, synthesized dual allocation plan).
       - Step 2: User prompts `"execute"` -> `python agent.py run --execute` (executes live orders, journals trades, updates watchlists, commits to Git).

---

## Retrospective Log: September 2026 Audit Cycle
* **Date**: September 27, 2026
* **Cycle**: Pre-October 1 Deployment
* **Portfolio State**: Active holdings in `TSM` (+4.40% P&L) and `ASML` (+0.77% P&L).
* **Adversarial Audit Findings**:
  1. **Beta Distortion on Post-IPO Assets**: Astera Labs (`ALAB`) exhibited a raw beta of 3.78, which monopolized the Q-Score and crowded out established leaders. *Action*: Clamped beta score input to 2.50 max while keeping candidate screening threshold `beta > 1.40`.
  2. **Earnings Proximity Shock**: Micron (`MU`) was ranked #1 by raw momentum and forward EPS (+787%), but reports fiscal Q4 earnings on Sept 30 post-market. Entering on Oct 1 morning carries extreme binary gap risk (+/-15%). *Action*: Implemented dynamic 48-hour earnings proximity penalty (-25 points) and routed capital into `SOXX` (ETF alternative with Beta 2.33 and 0 single-stock earnings risk).
  3. **LRS Settlement Latency & Holiday Blackout**: Empirical bank clearing latency is 21.0 hours (HDFC -> DriveWealth). October 2 is Gandhi Jayanti (Indian National Gazetted Holiday — all outward remittance desks shut). *Action*: Established the mandatory **T-2 Pre-Funding Rule** (initiate transfer by Sep 29/30 before 12:00 PM IST).
  4. **Wallet Sizing Reality**: ₹5,000 remittance yields ~$51.49 USD after FX spread and $1 bank fee. *Action*: Implemented dynamic wallet auto-sizing (`--budget auto`), automatically adjusting to `settled_cash - $0.12 - $0.20 cushion`.
  5. **Session Expiration on Tickertape**: DriveWealth session IDs lock quotes for 60 seconds. *Action*: Enforce atomic batch preview and fresh session generation inside the execution commit block.

---

## Hard Invariants for High-Risk, High-Return Preservation
The adaptive learner must **NEVER** violate these guardrails regardless of historical drawdowns:
1. **Minimum Portfolio Beta $\ge 1.40$**: We do not trade low-beta defensives (utilities, consumer staples) or cash-preservation funds.
2. **Concentrated Conviction ($\le 3$ Assets per Market)**: Never dilute capital across 5–10 positions. High-return compounding requires concentrated exposure.
3. **Pure-Play Tech & Capex Monopolies**: Target the core compute infrastructure layer of artificial intelligence and domestic secular industrial growth.
4. **Volatility Efficiency Over Volatility Avoidance**: We accept high variance; we penalize only uncompensated downside, blow-off exhaustion tops (RSI > 75), and binary earnings surprises.

---

## AI Agentic Architecture Evolution: September 28, 2026
* **Upgrade**: Autonomous AI Agentic Meta-Audit, Self-Verification Gate & Evidence Ledger
* **Foundational Literature**: NeurIPS 2025 Workshop on Generative AI in Finance (AgenticTrading), TradingAgents (arXiv:2412.20138), and FinRobot.
* **Architectural Pillars Integrated**:
  1. **Automated Self-Verification Gate (`scripts/test_system.py`)**: Unit and integration test suite executing automatically before any market screening or order generation. Formally verifies the Beta >= 1.40 floor, max 3 asset concentration, 60-day holding tenure lock, 0.15% Pro brokerage tariff, and zero credential leakage.
  2. **Layer-by-Layer System Meta-Audit**:
     - *Layer 1 (Perception)*: Paid Tickertape PRO, Alpha Vantage technicals, Alpaca shadow inference, Zerodha Kite Connect v3 API.
     - *Layer 2 (Reasoning)*: Multi-agent consensus committee (Fundamental, Technical, Risk Veto, Portfolio Manager), Cross-Sectional Z-Scores, and 48h binary earnings proximity penalty.
     - *Layer 3 (Memory)*: 4-tier memory store (Episodic trade journal, Semantic factor weights, Reflective retrospective log, Procedural runbook).
     - *Layer 4 (Safety & Control)*: Zero-Limbo Capital Controller, 60-day anti-churn tenure lock, quote-lock auto-requote resilience, and client-agnostic Git sync.
  3. **Verifiable Evidence Ledger (`memory/evidence_ledger.jsonl`)**: Standardized audit log documenting consensus decision DAGs, factor inputs, and system verification hashes.
  4. **Dynamic 0.15% Pro Tariff Modeling**: Calibrated base brokerage to the official 0.15% Tickertape Pro tariff with statutory allowances.
