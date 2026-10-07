# Workspace Rules: Autonomous Quantitative Dual-Market Investment Bot
> **System**: Autonomous Quantitative Trading Agent (AQTA)  
> **Repository**: [kevinhayesanderson/autonomous-trading-agent](https://github.com/kevinhayesanderson/autonomous-trading-agent)  
> **Markets**: US Equities (Tickertape / Alpaca) & Indian Equities (Zerodha Kite Connect v3)  

This workspace contains an institutional-grade, multi-agent quantitative trading system designed for monthly capital allocation across high-beta US technology monopolies and Indian domestic secular capex compounders.

---

## 1. User Command Contract (Max-2 Interactions Workflow)

Whenever the user prompts:
- *"run investment agent"* / *"run investment bot"* / *"monthly investment"* / *"invest salary"*

Strictly adhere to the **Max-2 Interactions Contract** (Zero user choosing, zero solution-fitting, zero blueprints, seamless dual-market execution):

### Interaction 1: User prompts "run investment agent"
* Agent executes: `python agent.py run` (or `python agent.py cycle`)
* What the agent performs autonomously:
  1. **Dual-Wallet & Capital Audit**: Audits both US (Tickertape / Alpaca) and Indian (Zerodha Kite Connect v3) live balances and active holdings.
  2. **Phase 0 Adversarial Retrospectives**: Multi-agent retrospective debate comparing US against SOXX benchmark and IN against Nifty Midcap benchmark, tuning factor weights recursively and persisting them to disk.
  3. **Unbiased Whole-Market Quantitative Screening from Scratch**: Algorithmic scan across both US and 5,000+ Indian stocks (NSE/BSE). Hard invariants: $\beta \ge 1.40$, Net Margin $> 0.0\%$, Market Cap $> ₹2,000\text{ Cr}$, $\text{ROE} \ge 12\%$, $\text{Op Margin} \ge 10\%$. Cash-burners and lottery tickets are strictly disqualified without bias. **No static blueprints, no hardcoded ticker pricing, zero carry-over**.
  4. **Multi-Agent Specialist Committee Deliberations**: Fundamental, Technical, and Fiduciary Risk Managers evaluate candidates with test-time reasoning traces (`<thinking>`), moat scorecards, and ASM/GSM surveillance checks.
  5. **Synthesized Dual-Market Allocation Plan**: Generates an objective, decision-free allocation plan:
     - **Plan 1 (US Equities)**: Routed to Tickertape / Alpaca. Evaluates 60-day anti-churn tenure locks and deployable cash.
     - **Plan 2 (Indian Equities)**: Formulates Zerodha Kite Delivery (CNC) limit orders with integer share sizing against available Kite cash, -12% Stop-Loss and +35% Take-Profit GTT brackets, and statutory cash buffer. (If daily Kite session is expired, prompts with the 1-click login link).
* Present the complete synthesized dual plan and await single user execution confirmation.

### 🛡️ Seamless Execution Mandate (Zero Codebase Digging)
* **DO NOT read source code, inspect internal files, or run git log/diff** when running the trading cycle. `agent.py run` is completely self-contained and handles all audits, screening, and status reporting in a single command.
* If Zerodha Kite daily session is expired, `agent.py run` provides the 1-click authorization link directly in its output. Present it cleanly to the user.
* When user provides the token/URL, run `python agent.py kite-login --token <TOKEN>`, then re-run `python agent.py run` to formulate the live plan.

### Interaction 2: User replies "execute"
* When user prompts: *"execute"* / *"execute the plan"* / *"proceed"* / *"execute confirmed trades"*:
* Agent executes: `python agent.py run --execute`
* What the agent performs:
  1. Live order execution for US (Tickertape / Alpaca) and automated Delivery CNC / GTT order routing for IN (Zerodha Kite Connect v3).
  2. Commits executed trades with timestamped IDs, committee votes, confidence scores, and thesis memos into `memory/trade_journal.jsonl`.
  3. Synchronizes master multi-market watchlist on Tickertape PRO.
  4. Commits memory state, factor weights, and trade logs to remote Git (`origin/main`) authored by `Kevin Hayes Anderson`.
  5. Reports completion status to user. Done in 2 interactions!

---

## 2. Core Quantitative Invariants & The Fiduciary Anti-Ruin Mandate

> **The Fiduciary Principle**: Every single rupee/dollar allocated represents hard-earned salary and a long-term gateway out of poverty. While we target explosive compound growth via high beta, **we are never reckless**. High return is achieved by owning the most dominant, cash-generating technology and semiconductor monopolies on earth and the highest-conviction domestic compounders—NEVER speculative lottery tickets, cash-burning biotechs, or post-IPO hype traps.

1. **Strict Positive Net Margin Floor**: Any company with Net Margin $\le 0\%$ or operating losses is **STRICTLY DISQUALIFIED / VETOED**. No hard-earned capital may ever flow to a cash-burning business.
2. **Institutional Market Cap Floor ($\ge \$20\text{B US} / \ge ₹2,000\text{Cr IN}$)**: We only invest in deeply liquid, institutionally sponsored titans with unassailable economic moats. No fragile penny stocks or illiquid small-caps.
3. **Bounded Beta Sweet Spot ($1.40 \le \text{Beta} \le 2.80$)**: We enforce high market sensitivity ($\ge 1.40$) to outcompete benchmarks during bull runs, but hard-cap beta at $\le 2.80$ to eliminate erratic post-IPO speculation.
4. **Concentrated Conviction**: Maximum 2 new assets per cycle, capped at $\le 3$ total active portfolio holdings per market.
5. **60-Day Anti-Churn Tenure Lock**: Assets held for $< 60$ days cannot be sold for discretionary rebalancing churn, saving 1.17% round-trip fees and 31.2% Indian STCG tax on US foreign equities.
6. **48-Hour Earnings Proximity Safeguard**: Deducts score penalties if an asset reports quarterly earnings within $\pm 48\text{h}$ to prevent binary post-earnings gap-down.
7. **No Falling Knives**: Assets trading below their 200-day simple moving average ($\text{Price} < \text{SMA}_{200}$) are disqualified from fresh accumulation.
8. **Zero-Limbo Capital Safety**: Unsettled LRS deposits lock cash from premature execution; unspent residual funds from failed legs are automatically reallocated into the primary successful position.

---

## 3. Environment & Credentials Resolution

The system automatically loads credentials with the following priority:
1. Environment variables (`TICKERTAPE_TOKEN`, `ALPACA_KEY`, `ALPACA_SECRET`, `AV_API_KEY`, `KITE_API_KEY`, `KITE_API_SECRET`).
2. Local [`.env`](./.env) file in the repository root (see [`.env.example`](./.env.example)).
3. Zerodha Kite daily session tokens cached in `.kite_token.json` and Tickertape tokens in `tickertape_token.json`.

To authenticate both Tickertape PRO and Zerodha Kite Connect v3 in 1 step:
```bash
python agent.py auth
```
*(Or individually: `python agent.py kite-login` for Zerodha Kite, `python agent.py tt-login` for Tickertape PRO).*

---

## 4. Key Verification & Self-Test Commands

To verify system integrity before or after changes:
```bash
# 1. Mathematical self-testing verification suite (7/7 tests)
python agent.py test

# 2. SOTA agentic evaluation & fiduciary benchmark suite (7/7 tests)
python agent.py eval
```

---

## 5. Key References & Documentation

- **Master Architectural Review**: [`docs/adversarial_review.md`](./docs/adversarial_review.md)
- **Master Agent Operating Standard**: [`AGENTS.md`](./AGENTS.md)
- **Master Skill Definition**: [`SKILL.md`](./SKILL.md)
- **Monthly Execution Runbook**: [`monthly_execution_workbook.md`](./monthly_execution_workbook.md)
- **Persistent Agent Memory**: [`memory/`](./memory/)
- **Git Synchronization**: [`scripts/git_sync.py`](./scripts/git_sync.py)
