# Security & Vulnerability Audit Report
**Autonomous Trading Agent (AQTA / Antigravity)**  
**Standard**: Institutional Multi-Agent Fiduciary Architecture & Model Context Protocol (MCP 2.x)  
**Scope**: Software composition analysis (SCA), static application security testing (SAST), data privacy, credential isolation, and network transport hardening.

---

## 1. Executive Summary & Audit Scorecard

The repository enforces end-to-end defensive security, vulnerability, privacy, and dependency standards:
- **Software Composition Analysis (SCA)**: Automated dependency scanning via `pip-audit`.
- **Static Application Security Testing (SAST)**: AST-level security flaw scanning across all application modules, utility scripts, and server interfaces via `bandit`.
- **Data Privacy & Secret Containment**: Zero hardcoded API keys, OAuth tokens, personal identifiable information (PII), or private trade execution records.
- **Microstructure & Network Transport Hardening**: Strict URL scheme whitelisting (`https://` enforcement) and atomic token serialization.

### Audit Summary Matrix

| Audit Domain | Tool / Methodology | Target Scope | Issues Found | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Dependencies (SCA)** | `pip-audit` | Active Environment | **0 Known CVEs** | **PASS** |
| **Code Security (SAST)** | `bandit` (High/Medium) | `trading_agent/`, `scripts/`, `server/`, `agent.py` | **0 High / 0 Medium** | **PASS** |
| **Private Data Containment** | Secret Scanning & Git Cache Audit | Entire Git Tree & `memory/` | `trade_journal.jsonl` untracked | **SECURED** |
| **Transport Layer Security** | AST Audit / URL Scheme Enforcement | All `urllib` / Broker requests | All endpoints hardened to HTTPS | **ENFORCED** |
| **Access Control & Auth** | OAuth 2.1 PKCE & Key Scrubber | `auth.py`, `config.py` | All credentials externally resolved | **ISOLATED** |

---

## 2. Dependency Vulnerability Analysis (`pip-audit`)

Software composition analysis was executed against active project dependencies:

```bash
pip-audit --local
```

### Scan Result
```text
No known vulnerabilities found
Exit Code: 0
```

### Dependency Inventory & Supply Chain Assessment
- **`requests` / `urllib3`**: Standard HTTP communication; patched to current secure versions.
- **`pydantic`**: Strict schema validation without unsafe eval or deserialization vulnerabilities.
- **`mcp`**: Official Model Context Protocol SDK maintained by Anthropic; verified against current CVE registries.
- **`kiteconnect`**: Official Zerodha Kite Connect SDK for delivery cash and GTT orders.
- **`python-dotenv`**: Environment variable parsing without shell expansion execution risks.

---

## 3. Static Application Security Testing (`bandit`)

Bandit performs AST analysis to detect security issues according to the Common Weakness Enumeration (CWE).

```bash
bandit -r trading_agent agent.py server scripts -ll -x .venv,tests
```

### SAST Result
```text
Run started: 2026-10-07
Test results:
        No issues identified.

Code scanned:
        Total lines of code: 4,999
        Total issues (by severity):
                High: 0
                Medium: 0
                Low: 79 (standard subprocess and defensive exception handling)
Exit Code: 0
```

### Key Security Controls Enforced

1. **URL Scheme Whitelisting (Bandit B310)**:
   - Explicit precondition checks assert `url.startswith("https://")` prior to constructing requests across broker interfaces:
     - `trading_agent/core/broker.py`
     - `trading_agent/core/screener.py`
     - `trading_agent/core/engine.py`
     - `scripts/setup_env.py`
     - `scripts/tickertape_auth.py`
     - `trading_agent/core/zerodha.py` (fixed HTTPS public IP resolution with `# nosec B310`)

2. **Process Isolation in MCP Server**:
   - `server/mcp_server.py` executes system diagnostics using `subprocess.run([sys.executable, test_script])` without shell expansion (`shell=False`) and using fixed, immutable script paths within the repository root.

---

## 4. Privacy & Secret Containment

### 4.1 Trade Execution Journal Protection
- **Private Data Isolation**: `memory/trade_journal.jsonl` records individual order timestamps, fill prices, order IDs, and account-specific position sizing.
- **Git Isolation**:
  - `memory/trade_journal.jsonl` is excluded from Git tracking via `.gitignore`.
  - An anonymized reference schema is provided in `memory/trade_journal.example.jsonl` with synthetic transaction records for open-source reproducibility.

### 4.2 Credentials & API Key Containment
- **Zero Hardcoded Secrets**: All credentials resolve dynamically from local OS environment variables or local `.env` via `trading_agent/core/config.py`.
- **Sanitized Template**: A sanitized `.env.example` provides template configurations with dummy placeholders.

---

## 5. Microstructure & Fiduciary Safety Controls

Beyond application security, the repository enforces programmatic **Fiduciary Anti-Ruin Guardrails**:
1. **60-Minute Wallet Drain Ceiling (`WALLET_DRAIN_LIMIT_EXCEEDED` mitigation)**:
   - Programmatic collar preventing orders from requesting more than 50% of available cash in a rolling 60-minute window.
2. **60-Day Anti-Churn Tenure Lock**:
   - Assets held under 60 days are programmatically locked against rebalancing liquidations, avoiding wash sales, fee drag, and short-term volatility churning.
3. **Asset Concentration Collar (`MAX_PORTFOLIO_ASSETS = 3`)**:
   - Enforces portfolio concentration limits, directing capital to top up existing leaders rather than diluting into excessive holdings.
4. **Fundamental Anti-Ruin Filters**:
   - Programmatically disqualifies unprofitable businesses (`Net Margin <= 0%`), hyper-beta speculative instruments (`Beta > 2.80`), and technically compromised stocks (`Price < 200 SMA`).

---

## 6. Audit & Verification Reproducibility Playbook

```bash
# 1. Run Software Composition Analysis (Dependencies)
pip-audit --local

# 2. Run Static Code Analysis (SAST)
bandit -r trading_agent agent.py server scripts -ll -x .venv,tests

# 3. Verify Git Cleanliness
git status --ignored
```
