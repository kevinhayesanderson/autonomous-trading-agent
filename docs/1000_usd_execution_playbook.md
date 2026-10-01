# $1,000 USD Capital Deployment Playbook
**System**: Autonomous Quantitative Trading Agent (AQTA)  
**Target Capital**: $1,000.00 USD (~₹84,000 – ₹85,000 INR)  
**Execution Broker**: Tickertape / DriveWealth LLC  
**Optimal Execution Window**: 7:45 PM – 8:15 PM IST (10:15 AM – 10:45 AM EDT)  

---

## 1. Capital Scaling Economics & Target Rebalance

### Current Portfolio Baseline (Pre-$1,000 Inflow)
* `ASML`: 0.02511 shares (~$45.25 USD, 25.9% weight)
* `TSM`: 0.14380 shares (~$65.60 USD, 37.6% weight)
* `MRVL`: 0.24286 shares (~$64.40 USD, 36.5% weight)
* **Total Invested Equity**: **~$175.25 USD**
* **Cash**: **$2.12 USD**

### Post-$1,000 Allocation Targets
When the $1,000 USD remittance lands, the total portfolio equity expands to **~$1,177.37 USD**.  
Under the Fiduciary 3-Asset Concentration Cap (`MAX_PORTFOLIO_ASSETS = 3`), the target equal-weight allocation is **$392.45 USD per asset (33.3% each)**:

| Ticker | Company Name | Current Value | Target Weight | Required Buy Inflow | Post-Trade Value |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **ASML** | ASML Holding N.V. | $45.25 | 33.3% | **+$346.00 USD** | ~$391.25 |
| **TSM** | Taiwan Semiconductor Mfg | $65.60 | 33.3% | **+$326.00 USD** | ~$391.60 |
| **MRVL** | Marvell Technology Group | $64.40 | 33.3% | **+$326.00 USD** | ~$390.40 |
| **FEE CUSHION** | Brokerage & Buffer | — | — | **$2.00 USD** | — |
| **TOTAL** | — | **$175.25** | **100%** | **$1,000.00 USD** | **~$1,175.25** |

*Notice: ASML receives a slightly larger inflow ($346 vs $326) to mathematically equalize its previous underweight position.*

---

## 2. Navigating Tickertape's 50% Wallet-Drain Protection

Tickertape / DriveWealth blocks orders with `WALLET_DRAIN_LIMIT_EXCEEDED` if any single order or cumulative buy spend exceeds 50% of the active wallet balance within a 60-minute window.

### The 2-Tranche Staged Execution Strategy
To deploy the full $1,000 USD safely without hitting wallet drain rejections:

```
[Day of Execution - Initial Settled Cash: $1,000.00 USD]
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
  Tranche 1 (Immediate)                   Tranche 2 (T + 60m or Staggered)
  ─────────────────────                   ────────────────────────────────
  • Buy ASML: $346.00 (34.6% of wallet)   • Buy MRVL: $326.00
  • Buy TSM:  $326.00 (49.9% of remainder)• Remaining cash: ~$2.00 fee cushion
  • Total Deployed: $672.00 USD           • Total Deployed: $326.00 USD
  • Remaining Cash: $328.00 USD           • Wallet Drained: 99.8% deployed!
```

---

## 3. Indian Banking (RBI LRS) Readiness Checklist

1. **Amount & Limit**: ₹84,000–₹85,000 INR ($1,000 USD) falls comfortably within the annual ₹7,00,000 INR TCS-free LRS threshold (0% TCS).
2. **Form A2 Purpose Code**: Ensure `S0001` (Indian investment in overseas equity) is selected in HDFC NetBanking.
3. **Execution Timing**:
   * HDFC outward remittance cut-off is **1:00 PM IST** on bank working days.
   * **Do NOT initiate on Friday, Oct 2** (Gandhi Jayanti — Indian National Gazetted Bank Holiday; interbank desks closed).
   * Initiate on **Monday, Oct 5 before 11:00 AM IST** to ensure clearance into DriveWealth by Tuesday/Wednesday, Oct 6–7.
4. **In-Flight Tracking**:
   * Monitor clearance with:
     ```bash
     python agent.py status
     ```
   * Once status changes from `in_transit` to `completed` and `Available Funds` reflects **$1,000+ USD**, proceed to execution.

---

## 4. Execution Step-by-Step Command Workflow

### Step 1: Verify System Invariants & Live Pricing
```bash
python agent.py test
python agent.py status
```

### Step 2: Generate $1,000 Preview Plan
```bash
python agent.py preview --budget 1000
```
* Audits committee consensus and prints exact dollar allocations and limit price ceilings (+1.0%).

### Step 3: Execute Live $1,000 Allocation
```bash
python agent.py execute --budget 1000
```
* Executes the confirmed orders.
* Any unspent residual cash is absorbed via Zero-Limbo protection.
* All trade IDs, shares, and prices are logged to [`memory/trade_journal.jsonl`](../memory/trade_journal.jsonl) and pushed to GitHub.

### Step 4: Final Micro-Drain (Optional)
If any loose cash remains ($5–$15):
```bash
python agent.py drain --ticker ASML
```
* Drains the final cents into ASML, leaving the portfolio 100% deployed.
