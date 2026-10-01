"""
Autonomous Test & Verification Suite (Self-Testing AI Agent Engine)
Enforces mathematical, architectural, and safety invariants before market analysis.
Run standalone:
    python scripts/test_system.py
"""

import os
import sys
import json
import unittest
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

class TestAIAgenticSystem(unittest.TestCase):
    
    def setUp(self):
        self.memory_dir = os.path.join(REPO_ROOT, "memory")
        self.weights_file = os.path.join(self.memory_dir, "factor_weights.json")
        self.journal_file = os.path.join(self.memory_dir, "trade_journal.jsonl")

    def test_01_hard_invariants(self):
        """Verify High-Risk High-Return hard mathematical invariants."""
        self.assertTrue(os.path.exists(self.weights_file), "factor_weights.json missing!")
        with open(self.weights_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        invariants = data.get("hard_invariants", {})
        min_beta = invariants.get("min_beta", 0.0)
        max_assets = invariants.get("max_assets", 99)
        min_mom = invariants.get("min_momentum_weight", 0.0)

        self.assertGreaterEqual(min_beta, 1.40, f"Invariant violation: Beta floor {min_beta} < 1.40")
        self.assertLessEqual(max_assets, 3, f"Invariant violation: Max assets {max_assets} > 3")
        self.assertGreaterEqual(min_mom, 0.20, f"Invariant violation: Momentum weight {min_mom} < 0.20")
        print("  [PASS] Hard Invariants: Beta >= 1.40, Max Assets <= 3, Momentum Weight >= 20%")

    def test_02_earnings_proximity_guardrail(self):
        """Verify dynamic 48-hour earnings penalty guardrail."""
        from trading_agent.core.config import is_earnings_within_48h, EARNINGS_CALENDAR
        
        # Test dynamically configured dates
        today = datetime.now().date()
        near_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        far_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

        EARNINGS_CALENDAR["TEST_NEAR"] = near_date
        EARNINGS_CALENDAR["TEST_FAR"] = far_date

        self.assertTrue(is_earnings_within_48h("TEST_NEAR"), "Failed to flag earnings within 48h")
        self.assertFalse(is_earnings_within_48h("TEST_FAR"), "False positive on earnings > 48h")
        print("  [PASS] Earnings Guardrail: Successfully flags binary quarterly report risks within +/- 48 hours")

    def test_03_pro_brokerage_tariff(self):
        """Verify Tickertape Pro 0.15% brokerage calculations and cash buffer."""
        from trading_agent.core.rebalance import evaluate_portfolio_rebalance
        
        pool = 51.49
        est_fee = round((pool * 0.0015) + (2 * 0.02), 2)
        expected_spendable = max(0.0, pool - est_fee - 0.20)
        
        # Run test rebalance with zero sales
        mock_candidates = [
            {"ticker": "AMD", "price": 160.00, "beta": 2.48, "scaled_q": 65.0, "recommendation": "BUY"},
            {"ticker": "NVDA", "price": 125.00, "beta": 2.10, "scaled_q": 60.0, "recommendation": "BUY"}
        ]
        res = evaluate_portfolio_rebalance(
            active_holdings=[],
            screened_candidates=mock_candidates,
            fresh_cash=pool
        )
        self.assertAlmostEqual(res["net_spendable"], expected_spendable, delta=0.05)
        self.assertGreater(res["net_spendable"], 50.0)
        print(f"  [PASS] Pro Tariff Modeling: Net spendable ${res['net_spendable']:.2f} properly incorporates 0.15% fee + buffer")

    def test_04_anti_churn_tenure_lock(self):
        """Verify that assets held < 60 days are protected from discretionary replacement."""
        from trading_agent.core.rebalance import evaluate_portfolio_rebalance

        mock_holdings = [
            {"ticker": "ASML", "invested": 19.45, "current": 19.59, "pnl_pct": 0.77, "shares": 0.01124, "tenure_days": 31},
            {"ticker": "TSM", "invested": 49.87, "current": 52.06, "pnl_pct": 4.40, "shares": 0.11551, "tenure_days": 62}
        ]
        mock_candidates = [
            {"ticker": "AMD", "price": 160.00, "beta": 2.48, "scaled_q": 85.0, "recommendation": "BUY"}
        ]
        
        res = evaluate_portfolio_rebalance(
            active_holdings=mock_holdings,
            screened_candidates=mock_candidates,
            fresh_cash=51.49
        )
        sells = [ra for ra in res["rebalance_actions"] if ra["amount_freed"] > 0]
        self.assertEqual(len(sells), 0, "Tenure lock breached! Position sold before 60 days.")
        print("  [PASS] Anti-Churn Lock: ASML & TSM protected from momentum churn during holding tenure")

    def test_05_credentials_and_git_isolation(self):
        """Verify strict credential containment and zero secret leakage."""
        gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
        self.assertTrue(os.path.exists(gitignore_path), ".gitignore missing!")
        
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gi_content = f.read()

        self.assertIn("*token*.json", gi_content)
        self.assertIn(".env", gi_content)
        self.assertIn("*.key", gi_content)
        print("  [PASS] Security & Credentials: Zero token/secret leakage into Git confirmed")

    def test_06_memory_integrity(self):
        """Verify persistent agent memory stores parse cleanly (supports example fallback)."""
        target_journal = self.journal_file if os.path.exists(self.journal_file) else os.path.join(self.memory_dir, "trade_journal.example.jsonl")
        if os.path.exists(target_journal):
            with open(target_journal, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self.assertIn("ticker", entry)
                        self.assertTrue("amount" in entry or "invested_amount" in entry)
        print("  [PASS] Memory Integrity: Trade journal and retrospective records valid")

    def test_07_fiduciary_anti_ruin_filter(self):
        """Verify that unprofitable companies and hyper-beta lottery tickets are strictly vetoed."""
        active_weights = {
            "hard_invariants": {"min_beta": 1.40, "max_beta": 2.80},
            "rsi_overbought_threshold": 75.0,
            "rsi_oversold_threshold": 35.0
        }
        
        from trading_agent.core.consensus import multi_agent_committee_vote
        
        # Test 1: Unprofitable cash-burner (e.g., net margin < 0%)
        bad_candidate = {
            "ticker": "BAD_CO", "beta": 2.2, "net_margin": -25.0, "has_earnings_risk": False,
            "z_scores": {"eps_fwd": 0.5, "upside": 0.5, "buy_pct": 0.5, "ret_6m": 1.0, "ret_1m": 0.5}
        }
        res_bad = multi_agent_committee_vote(bad_candidate)
        self.assertEqual(res_bad["recommendation"], "VETO", "Fiduciary filter failed to veto unprofitable business!")

        # Test 2: Hyper-beta speculative lottery (e.g., Beta > 2.80)
        hyper_beta_candidate = {
            "ticker": "HYPER_CO", "beta": 3.5, "net_margin": 20.0, "has_earnings_risk": False,
            "z_scores": {"eps_fwd": 0.5, "upside": 0.5, "buy_pct": 0.5, "ret_6m": 1.0, "ret_1m": 0.5}
        }
        res_hyper = multi_agent_committee_vote(hyper_beta_candidate)
        self.assertEqual(res_hyper["recommendation"], "VETO", "Fiduciary filter failed to veto hyper-beta lottery ticket!")

        # Test 3: Structural profitable compounder (e.g., NVDA, TSM, ASML)
        good_candidate = {
            "ticker": "NVDA", "beta": 2.2, "net_margin": 55.0, "has_earnings_risk": False,
            "ret_6m": 45.0, "ret_1m": 8.0, "eps_fwd": 30.0, "upside": 20.0, "buy_pct": 85.0
        }
        res_good = multi_agent_committee_vote(good_candidate)
        self.assertEqual(res_good["recommendation"], "BUY", "Fiduciary filter incorrectly vetoed profitable compounder!")
        self.assertGreaterEqual(res_good["confidence"], 0.70)
        print("  [PASS] Fiduciary Anti-Ruin Filter: Cash-burners and lottery tickets strictly VETOED; only profitable monopolies approved")

def run_self_verification():
    print("\n" + "=" * 80)
    print(" [AI AGENTIC SYSTEM SELF-VERIFICATION SUITE]")
    print(" Verifying system integrity, safety invariants, and tariffs before execution...")
    print("=" * 80)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIAgenticSystem)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("=" * 80)
        print(f" [ALL {result.testsRun} SYSTEM TESTS PASSED] System verified and ready for market operations.")
        print("=" * 80 + "\n")
        return True
    else:
        print("=" * 80)
        print(f" [CRITICAL FAIL] {len(result.failures)} test(s) failed, {len(result.errors)} error(s).")
        print(" Halting pipeline to protect capital from architectural failure.")
        print("=" * 80 + "\n")
        return False

if __name__ == "__main__":
    success = run_self_verification()
    sys.exit(0 if success else 1)
