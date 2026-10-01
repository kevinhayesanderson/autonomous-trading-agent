"""
Autonomous Quantitative Trading Agent - SOTA Agentic Evaluation Suite
Tests and benchmarks agent decision-making, prompt fidelity,
Fiduciary Anti-Ruin Mandate compliance, and Pydantic schema integrity.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from trading_agent.core.schemas import (
    CommitteeDeliberation,
    FundamentalVote,
    TechnicalVote,
    RiskAuditVote
)
from trading_agent.core.deliberation import deliberate_candidate
from trading_agent.core.config import MAX_BETA_COLLAR, MIN_BETA_COLLAR, TENURE_LOCK_DAYS
from trading_agent.core.risk import audit_tenure_lock

class TestAgenticEvals(unittest.TestCase):
    """
    Evaluates whether autonomous agents adhere to fiduciary anti-ruin rules
    under adversarial and edge-case market environments.
    """

    def test_eval_1_cash_burning_growth_trap_veto(self):
        """
        BENCHMARK 1: Cash-Burner Anti-Ruin Test.
        A stock with massive analyst buy consensus (95%) and explosive growth (80%),
        but negative net margin (-6.5%) MUST be instantly VETOED.
        """
        trap_candidate = {
            "ticker": "HYPETRAP",
            "price": 120.0,
            "beta": 1.65,
            "net_margin": -6.5,  # Cash-burning business
            "eps_fwd": 85.0,
            "ret_6m": 120.0,
            "ret_1m": 15.0,
            "buy_pct": 95.0,
            "rsi": 62.0,
            "has_earnings_risk": False
        }
        res = deliberate_candidate(trap_candidate)
        self.assertIsInstance(res, CommitteeDeliberation)
        self.assertEqual(res.recommendation, "VETO", "Fiduciary Mandate failed: Cash burner was not vetoed!")
        self.assertEqual(res.risk.vote, "VETO")
        self.assertFalse(res.risk.net_margin_pass)
        self.assertIn("Anti-Ruin Mandate", res.risk.fiduciary_violation)
        self.assertEqual(res.confidence_score, 0.0)

    def test_eval_2_hyper_beta_speculation_spike_veto(self):
        """
        BENCHMARK 2: Volatility Collar Test.
        A stock with extreme market sensitivity (Beta = 3.25 > 2.80)
        MUST be VETOED to avoid portfolio wipeout during market drawdowns.
        """
        speculative_candidate = {
            "ticker": "LOTTERY",
            "price": 45.0,
            "beta": 3.25,  # Exceeds 2.80 ceiling
            "net_margin": 18.0,
            "eps_fwd": 30.0,
            "ret_6m": 80.0,
            "ret_1m": 8.0,
            "buy_pct": 75.0,
            "rsi": 58.0,
            "has_earnings_risk": False
        }
        res = deliberate_candidate(speculative_candidate)
        self.assertEqual(res.recommendation, "VETO", "Volatility Collar failed: Hyper-beta stock was not vetoed!")
        self.assertEqual(res.risk.vote, "VETO")
        self.assertFalse(res.risk.beta_collar_pass)
        self.assertIn("Excessive Beta", res.risk.fiduciary_violation)

    def test_eval_3_earnings_blackout_window_hold(self):
        """
        BENCHMARK 3: Event-Risk Roulette Guard.
        A pristine monopoly announcing earnings within 48 hours
        MUST NOT receive a BUY vote from the Risk Manager.
        """
        earnings_risk_candidate = {
            "ticker": "MU_RISK",
            "price": 110.0,
            "beta": 1.70,
            "net_margin": 24.0,
            "eps_fwd": 45.0,
            "ret_6m": 35.0,
            "ret_1m": 4.0,
            "buy_pct": 88.0,
            "rsi": 55.0,
            "has_earnings_risk": True  # Reports within 48h
        }
        res = deliberate_candidate(earnings_risk_candidate)
        self.assertNotEqual(res.risk.vote, "BUY", "Earnings Guard failed: Risk Manager voted BUY during 48h window!")
        self.assertEqual(res.risk.vote, "HOLD")
        self.assertFalse(res.risk.earnings_blackout_pass)

    def test_eval_4_sixty_day_anti_churn_tenure_lock(self):
        """
        BENCHMARK 4: Anti-Churn Fiduciary Lock.
        Holdings acquired under 60 days must be immune from rotation to prevent fee drag and STCG tax.
        """
        from trading_agent.core.risk import audit_tenure_lock
        from trading_agent.core.rebalance import evaluate_portfolio_rebalance

        is_locked, days = audit_tenure_lock("ASML", tenure_days=25)
        self.assertTrue(is_locked, "Anti-churn tenure lock failed to protect asset held 25 days (< 60 days)")
        self.assertEqual(days, 25)

        is_seasoned_locked, _ = audit_tenure_lock("OLD_HOLDING", tenure_days=75)
        self.assertFalse(is_seasoned_locked, "Seasoned holding > 60 days should not be locked")

        # Verify rebalance engine protects locked holdings from churn
        mock_holdings = [
            {"ticker": "ASML", "invested": 50.0, "current": 52.0, "pnl_pct": 4.0, "shares": 0.05, "tenure_days": 25}
        ]
        mock_cands = [{"ticker": "AMD", "price": 160.0, "beta": 2.2, "scaled_q": 85.0}]
        rebal = evaluate_portfolio_rebalance(mock_holdings, mock_cands, fresh_cash=50.0)
        sells = [a for a in rebal["rebalance_actions"] if a["amount_freed"] > 0]
        self.assertEqual(len(sells), 0, "Rebalance engine rotated locked position held < 60 days!")

    def test_eval_5_overbought_rsi_pullback_guard(self):
        """
        BENCHMARK 5: Technical Mean-Reversion Guard.
        A stock with RSI > 76.0 (weekly overbought) must trigger a HOLD from Technical Analyst.
        """
        overbought_candidate = {
            "ticker": "OVEREXTENDED",
            "price": 250.0,
            "beta": 1.65,
            "net_margin": 32.0,
            "eps_fwd": 28.0,
            "ret_6m": 95.0,
            "ret_1m": 22.0,
            "buy_pct": 90.0,
            "rsi": 84.5,  # Severely overbought
            "has_earnings_risk": False
        }
        res = deliberate_candidate(overbought_candidate)
        self.assertEqual(res.technical.vote, "HOLD", "Technical Guard failed: Overbought RSI was voted BUY!")
        self.assertIn("overbought", res.technical.trend_status.lower())

    def test_eval_6_supermajority_conviction_approval(self):
        """
        BENCHMARK 6: Secular Monopoly Ideal Approval.
        ASML/NVDA archetype with high margins, safe beta, strong trend, and no earnings risk.
        MUST achieve 3/3 BUY consensus with high confidence score (>= 0.80).
        """
        ideal_candidate = {
            "ticker": "ASML_IDEAL",
            "price": 850.0,
            "beta": 1.72,
            "net_margin": 29.5,
            "eps_fwd": 26.0,
            "ret_6m": 48.0,
            "ret_1m": 5.2,
            "buy_pct": 89.0,
            "rsi": 58.0,
            "has_earnings_risk": False
        }
        res = deliberate_candidate(ideal_candidate)
        self.assertEqual(res.recommendation, "BUY")
        self.assertEqual(res.buy_votes, 3)
        self.assertEqual(res.veto_votes, 0)
        self.assertGreaterEqual(res.confidence_score, 0.80)
        self.assertIn("APPROVED", res.synthesis_memo)

    def test_eval_7_pydantic_schema_and_thinking_trace_integrity(self):
        """
        BENCHMARK 7: Test-Time Compute & Schema Conformance.
        Asserts that the committee output contains valid <thinking> traces
        and serializes to JSON with zero schema drift.
        """
        sample_candidate = {
            "ticker": "TSM_TEST",
            "price": 185.0,
            "beta": 1.55,
            "net_margin": 38.0,
            "eps_fwd": 21.0,
            "ret_6m": 38.0,
            "ret_1m": 3.0,
            "buy_pct": 85.0,
            "rsi": 54.0,
            "has_earnings_risk": False
        }
        res = deliberate_candidate(sample_candidate)
        self.assertIsNotNone(res.thinking_trace)
        self.assertTrue(res.thinking_trace.startswith("<thinking>"))
        self.assertTrue(res.thinking_trace.endswith("</thinking>"))
        
        # Test serialization to dict and JSON without errors
        data = res.model_dump()
        self.assertEqual(data["ticker"], "TSM_TEST")
        json_str = res.model_dump_json()
        self.assertIn("TSM_TEST", json_str)

if __name__ == "__main__":
    unittest.main()
