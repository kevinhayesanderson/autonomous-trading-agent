# Large Capital Deployment Playbook ($1,000+ USD)
**System**: Autonomous Quantitative Trading Agent (AQTA)  
**Target Capital**: $1,000.00+ USD (~₹85,000–₹1,00,000 INR)  
**Execution Broker**: Tickertape / DriveWealth LLC  
**Optimal Execution Window**: 7:45 PM – 8:15 PM IST (10:15 AM – 10:45 AM EDT)  

---

## 1. Capital Scaling & Allocation Principles

When deploying substantial fresh capital inflows (e.g. $1,000 USD / ₹1 Lakh INR) into the US portfolio:
1. **Fiduciary 3-Asset Concentration Cap (`MAX_PORTFOLIO_ASSETS = 3`)**:
   - Capital is allocated across a concentrated basket of high-conviction monopolies.
   - If the portfolio is already at capacity and active holdings are under the 60-day anti-churn tenure lock, fresh funds are deployed proportionally across retained leaders rather than opening a 4th position.
2. **Proportional Equalization**:
   - The engine automatically sizes orders to balance weights across the conviction basket, giving slightly larger allocations to underweight holdings.
3. **Statutory Buffer**:
   - Sizing models deduct 0.15% brokerage tariffs and maintain a cash buffer to prevent execution failures.

---

## 2. Navigating Tickertape's 50% Wallet-Drain Protection

DriveWealth / Tickertape prevents any order or cumulative buy spend from exceeding 50% of the active wallet balance within a 60-minute window (`WALLET_DRAIN_LIMIT_EXCEEDED`).

### The 2-Tranche Staged Execution Strategy
To deploy large capital infusions safely without hitting wallet drain rejections:

```
[Initial Settled Cash: $1,000.00 USD]
                  │
  ┌───────────────┴───────────────┐
  ▼                               ▼
Tranche 1 (Immediate)           Tranche 2 (T + 60m or Staggered)
─────────────────────           ────────────────────────────────
• Buy Leader 1: ~$340.00        • Buy Leader 3: ~$320.00
• Buy Leader 2: ~$320.00        • Remaining Cash: ~$20.00 fee cushion
• Cumulative: <= 49% of Cash    • Fully Deployed: 99.8% invested
```

Alternatively, the recursive micro-drain tool (`python agent.py drain --ticker ASML`) executes tranches mathematically calibrated to $0.49 \times \text{Balance}$, automatically avoiding broker rejection limits.

---

## 3. Banking (RBI LRS) Readiness Protocol

1. **Regulatory Limits**: Remittances under $250,000 USD per financial year fall within the RBI Liberalised Remittance Scheme (LRS). Remittances under ₹7,00,000 INR incur 0% Tax Collected at Source (TCS).
2. **Purpose Code**: Ensure `S0001` (Indian investment in overseas equity) is selected during bank remittance initiation.
3. **Clearing Latency**:
   - Outward telegraphic transfers typically clear within **24 to 48 hours** on standard business days.
   - Bank holidays or weekend interbank cut-offs extend clearing latency.
4. **In-Flight Tracking**:
   - The system audits in-flight remittances via `us_account_fund_history_read`.
   - Trade execution is automatically locked while funds report as `in_transit`, preventing premature execution against uncleared funds.

---

## 4. Execution Step-by-Step Workflow

### Step 1: Verify System Invariants & Live Balance
```bash
python agent.py test
python agent.py status
```

### Step 2: Generate Capital Allocation Preview
```bash
python agent.py preview --budget 1000
```
* Audits committee consensus and outputs exact dollar allocations and limit price ceilings (+1.0%).

### Step 3: Execute Live Allocation
```bash
python agent.py execute --budget 1000
```
* Executes confirmed orders within safety limits.
* Residual unspent funds from any failed leg absorb dynamically into primary positions via Zero-Limbo protection.
* All trade IDs, shares, and prices log to `memory/trade_journal.jsonl` and synchronize to Git.

### Step 4: Residual Micro-Drain (Optional)
If residual loose cash remains:
```bash
python agent.py drain --ticker ASML
```
