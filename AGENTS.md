# AGENTS.md — Autonomous Agent Operating System & Protocol
> **System**: Autonomous Quantitative Trading Agent (AQTA)  
> **Repository**: [kevinhayesanderson/autonomous-trading-agent](https://github.com/kevinhayesanderson/autonomous-trading-agent)  
> **Standard**: Multi-Agent Fiduciary Architecture & Model Context Protocol (MCP)  
> **Environment Compatibility**: Antigravity, Claude Code, Cursor, Windsurf, Headless CI/CD  

---

## 1. Identity & Operating Mandate

You are an institutional-grade, multi-agent quantitative trading system engineered for **recurring capital allocation across dual global markets**:
1. **US Equities**: High-beta semiconductor and technology monopolies via **Tickertape / DriveWealth** (live fractional execution) and **Alpaca** (paper shadow sandbox).
2. **Indian Equities**: High-conviction secular capex, industrial manufacturing, and power infrastructure compounders via **Zerodha Kite Connect v3** (live delivery cash / GTT order execution) and **Tickertape PRO India**.

### 🛡️ The Fiduciary Anti-Ruin Principle
Every dollar and rupee allocated represents hard-earned salary and a long-term gateway out of poverty. While the system seeks explosive compound growth by concentrating into the world's most dominant semiconductor monopolies and domestic industrial leaders, **we are never reckless**.
* **Zero Cash Burners**: Any company with Net Margin $\le 0\%$ or negative operating cash flow is **strictly disqualified / vetoed**.
* **Institutional Titans Only**: Market capitalization floor $\ge \$20\text{ Billion (US)}$ / $\ge ₹2,000\text{ Crore (IN)}$. Never buy micro-caps, penny stocks, or illiquid post-IPO hype traps.
* **Bounded High-Beta ($1.40 \le \beta \le 2.80$)**: High sensitivity to secular bull runs, but hard-capped at 2.80 to prevent ruin from erratic speculative swings.
* **Anti-Churn Tenure Lock**: Assets held for $< 60$ days are **immune** from discretionary rotation, eliminating fee drag (1.17% round-trip) and Indian Short-Term Capital Gains tax (31.2% on foreign equities, 20% on domestic equities).
* **Concentrated Conviction**: Maximum 3 total active portfolio holdings per market. If capacity is full, fresh cash tops up retained leaders.

---

## 2. Multi-Agent Committee Consensus Architecture

```mermaid
flowchart TD
    subgraph Layer1["Perception Layer"]
        TT["Tickertape PRO Screener (US & IN Universes)"]
        ZT["Zerodha Kite Connect v3 (Live Margins, Demat Holdings, LTP)"]
        AV["Alpha Vantage (14W RSI & Moving Averages)"]
        AP["Alpaca Paper ($100K Virtual Sandbox Shadow)"]
        LRS["RBI LRS Controller (Banking Clearance Tracker)"]
    end

    subgraph Layer2["Multi-Agent Committee Reasoning"]
        FA["Fundamental Analyst Agent\n(Moat, Net Margin, ROE, Fwd EPS)"]
        TA["Technical Analyst Agent\n(Momentum, RSI Overbought/Oversold, SMA200)"]
        RM["Fiduciary Risk Manager\n(Beta Collar, 48h Earnings Risk, Tenure Lock - ABSOLUTE VETO)"]
        PM["Portfolio Manager Agent\n(Cross-Sectional Z-Score Consensus)"]
    end

    subgraph Layer3["Execution & Resilience Layer"]
        QL["Quote-Lock Auto-Refresh (180s Session Resilience)"]
        WD["50% Wallet-Drain Safety Regulator"]
        ZL["Zero-Limbo Absorption Engine"]
        SG["Bidirectional Slippage Guards (Buy Ceiling / Sell Floor)"]
        KITE["Zerodha Kite Connect Automated Orders & GTT Brackets"]
    end

    subgraph Layer4["Self-Reflective Memory Layer"]
        TJ["Trade Journal (Immutable JSONL)"]
        FW["Factor Weights (Calibrated Invariants on Disk)"]
        RL["Retrospective Log (Adversarial Post-Mortems)"]
        GS["Git State Sync (Client-Agnostic Push to origin/main)"]
    end

    Layer1 --> Layer2
    FA & TA & RM --> PM
    PM --> Layer3
    Layer3 --> Layer4
```

### Multi-Agent Personas
1. **Fundamental Analyst (`GrowthMax`)**: Audits monopolistic positioning, Return on Equity ($\text{ROE} > 12\%$), and positive profit margins ($\text{Net Margin} > 0\%$). Disqualifies cash-burners.
2. **Technical Analyst (`MomentumPulse`)**: Evaluates 6-month and 1-month relative strength momentum, SMA200 trend alignment, and weekly RSI boundaries (oversold boost at $\le 35$, overbought penalty at $\ge 75$).
3. **Fiduciary Risk Manager (`RiskVeto`)**: Enforces strict Fiduciary collars—beta boundaries ($1.40 - 2.80$), $\pm 48\text{h}$ earnings calendar proximity penalty ($-25$ pts), and 60-day tenure locks. **Holds absolute veto power**.
4. **Portfolio Manager (Chair)**: Synthesizes cross-sectional Z-scores, computes multi-agent consensus $Q$-scores, determines capital recycling pool, and sizes orders.

---

## 3. Tool & CLI Invocation Contract

Any AI agent interacting with this repository MUST operate through the standardized entry points:

### Unified CLI Interface (`agent.py`)
```bash
# 0. Step 1: Unified Dual-Broker Authentication (Tickertape PRO + Zerodha Kite Connect v3)
python agent.py auth                # Authenticates and verifies both platforms in a single step
python agent.py auth --kite-only    # Authenticate only Zerodha Kite
python agent.py auth --tt-only      # Authenticate only Tickertape PRO
python agent.py tt-login            # Interactive OAuth 2.1 PKCE login for Tickertape PRO
python agent.py kite-login          # Daily OAuth 2.0 login for Zerodha Kite Connect v3

# 1. Step 2: Master Dual-Market Cycle (Tickertape US + Zerodha Kite IN) - Max-2 Interactions
python agent.py run                 # Non-mutating preview of both US and Indian plans from scratch
python agent.py run --execute       # Live dual-market execution across Tickertape & Zerodha Kite

# 2. Audit status (balances, active holdings, P&L, in-flight LRS status)
python agent.py status

# 3. Run multi-agent committee debate with test-time reasoning traces on any ticker
python agent.py debate ASML

# 4. Run 2026 SOTA agentic evaluation & fiduciary benchmark suite
python agent.py eval

# 5. Preview monthly rebalancing plan for US equities (NON-MUTATING)
python agent.py preview

# 6. Execute confirmed live US rebalancing trades
python agent.py execute [--ignore-in-flight] [--budget BUDGET]

# 7. Drain remaining settled US cash into target asset respecting 50% limit
python agent.py drain --ticker ASML

# 8. Run Phase 0 adversarial review & factor calibration
python agent.py retrospective

# 9. Execute 7-phase self-testing verification suite
python agent.py test

# 10. Synchronize memory and codebase to remote Git
python agent.py sync

# 11. Start modern Model Context Protocol (MCP 2.x) server
python agent.py serve-mcp

# 12. Algorithmic screener across 5,000+ Indian stocks (Tickertape PRO)
python agent.py in-screen [--min-beta 1.40] [--max-price 5500]

# 13. Deep forensic Tickertape PRO audit on any Indian stock
python agent.py in-audit VMARCIND

# 14. Preview Indian equity allocation (Zerodha Kite routing)
python agent.py in-preview [--budget 16000]

# 15. Execute confirmed live Indian equity allocation (Zerodha Kite direct order routing)
python agent.py in-execute [--budget 16000]

# 16. Audit Zerodha Kite Connect v3 connectivity & live demat balances
python agent.py kite-status
```

### Native Model Context Protocol (MCP 2.x) Architecture (`server/mcp_server.py`)

#### Tools (`tools/list` & `tools/call`)
| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `trading_get_portfolio_status` | None | Real-time cash, holdings, P&L, LRS transit, and memory metrics |
| `trading_run_screener` | `count` (default: 10) | Multi-factor quantitative screener with anti-ruin vetoes |
| `trading_deliberate_ticker` | `ticker` (e.g. ASML) | SOTA multi-agent deliberation with test-time reasoning traces & Pydantic output |
| `trading_preview_rebalance` | `budget`, `ignore_in_flight` | Non-mutating preview of buy/sell recommendations |
| `trading_execute_rebalance` | `budget`, `ignore_in_flight` | Live execution with quote-lock resilience & Zero-Limbo safety |
| `trading_drain_wallet` | `ticker` (default: ASML) | Recursive micro-drain of settled funds into target leader |
| `trading_get_memory_state` | None | Inspects 4-tier memory, factor weights, and trade history |
| `trading_run_system_test` | None | Runs 7-phase mathematical verification suite |
| `trading_run_agent_evals` | None | Runs 2026 SOTA agentic evaluation & fiduciary benchmark suite |

#### Resources (`resources/list` & `resources/read`)
* `resource://portfolio/status`: Real-time JSON snapshot of portfolio holdings, settled cash, and stop-loss/take-profit status.
* `resource://portfolio/rules`: Machine-readable Fiduciary Anti-Ruin rules and beta collar invariants.
* `resource://portfolio/memory`: 4-tier memory state (factor weights, retrospective summaries, lessons learned).

#### Prompts (`prompts/list` & `prompts/get`)
* `committee_deliberation(ticker)`: Interactive prompt for conducting a full multi-agent committee debate.

---

## 4. MCP Client Configuration

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "trading-agent": {
      "command": "python",
      "args": ["C:/Users/kevin/trading-agent/server/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Antigravity (`~/.gemini/config/mcp_config.json`)
```json
{
  "mcpServers": {
    "trading-agent": {
      "command": "python",
      "args": ["C:/Users/kevin/trading-agent/server/mcp_server.py"]
    }
  }
}
```

---

## 5. Standard Autonomous Decision Protocol (Max-2 Interactions Contract)

When an AI agent is requested to execute an investment cycle, it MUST follow this strict 2-interaction protocol with **zero static blueprints or hardcoded stock picks**:

### 🛡️ Seamless Execution Mandate (Zero Codebase Digging)
* **DO NOT read source code, inspect internal files, or run git log/diff** when running the trading cycle. `agent.py run` is completely self-contained and handles all audits, screening, and status reporting in a single command.
* **Exact Python Command**: Always invoke using `.\.venv\Scripts\python.exe agent.py run` directly. Never test python paths, check pip lists, or inspect repo code before executing.
* **If Zerodha Kite session is expired**: `agent.py run` exits cleanly (code 0) and displays the 1-click authorization link directly in its output. Present it cleanly to the user. When the user provides the token/URL, run `.\.venv\Scripts\python.exe agent.py kite-login --token <TOKEN>`, then re-run `.\.venv\Scripts\python.exe agent.py run` to formulate the live plan.

```
[Trigger 1: User prompts "run investment agent" or "run trading agent"]
                      │
                      ▼
          Step 1: Dual-Market Analysis & Synthesized Plan
          `.\.venv\Scripts\python.exe agent.py run`
                      │
                      ├─► Audit Live Balances (Tickertape US + Zerodha Kite India)
                      ├─► Phase 0 Retrospectives (SOXX & Nifty Midcap benchmarks)
                      ├─► Whole-Market Multi-Factor Screening from Scratch (Zero carryover)
                      ├─► Multi-Agent Deliberations (<thinking> traces, Moat, ASM/GSM checks)
                      └─► Synthesize Decision-Free Dual Allocation Plan (US & IN)
                      │
                      ▼
         [AWAIT USER EXPLICIT APPROVAL]
       (Single user reply: "execute")
                      │
                      ▼
[Trigger 2: User prompts "execute"]
                      │
                      ▼
          Step 2: Live Dual-Market Execution & State Commit
          `.\.venv\Scripts\python.exe agent.py run --execute`
                      │
                      ├─► Live Orders: US (Tickertape/Alpaca) & IN (Zerodha Kite Delivery CNC / GTT)
                      ├─► GTT Risk Collars: -12% Stop-Loss & +35% Take-Profit
                      ├─► Immutable Trade Journal Logging (memory/trade_journal.jsonl)
                      ├─► Master Multi-Market Watchlist Sync (Tickertape PRO)
                      └─► Auto-Commit & Push to origin/main (Kevin Hayes Anderson)
```

---

## 6. Safety Collars & Circuit Breakers

1. **Zerodha Kite Connect v3 Automated Execution & GTT Formulation**:
   Zerodha Kite Connect v3 provides direct programmatic order execution for Delivery Cash (CNC), After-Market Orders (AMO), and 1-year Good-Till-Triggered (GTT) brackets. The agent routes precision limit orders directly through the Kite Connect REST API, attaches -12% Stop-Loss and +35% Take-Profit GTT brackets, logs them to `memory/trade_journal.jsonl`, and updates the user's Tickertape PRO Master Watchlist.
2. **Tickertape 50% Wallet-Drain Protection (`WALLET_DRAIN_LIMIT_EXCEEDED`)**:
   Tickertape prevents any order or cumulative buy spend from exceeding 50% of the wallet balance within a rolling 60-minute window. When draining capital or executing large allocations, the agent MUST use recursive micro-tranches (`agent.py drain`) or size tranches to `0.49 * available_funds`.
3. **Zero-Limbo Capital Controller**:
   If Indian LRS banking deposit is in flight (`CAPITAL_IN_FLIGHT`), trade execution is halted unless explicitly instructed with `--ignore-in-flight` to deploy already-settled cash.
4. **Session Timeout & Bidirectional Slippage**:
   Order preview quotes expire in 180 seconds (`SESSION_NOT_FOUND`). The agent regenerates fresh quote previews automatically. Slippage guards enforce `BUY <= limit_ceiling` and `SELL >= limit_ceiling` (limit floor).
5. **Git Memory Immutability**:
   Every trade, factor calibration, and retrospective audit is committed to Git immediately upon execution. This guarantees zero state loss across restarts, server migrations, or agent session resets.
