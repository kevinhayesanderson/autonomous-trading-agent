"""
Autonomous Quantitative Trading Agent - Pydantic v2 Schema Registry
Defines strict, grammar-enforced schemas for Multi-Agent Deliberations,
Committee Consensus, Risk Audits, and MCP Tool payloads.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Graceful fallback base if running in raw stdlib minimal environment
    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__
        def model_dump(self):
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "model_dump"):
                    res[k] = v.model_dump()
                else:
                    res[k] = v
            return res
        def model_dump_json(self):
            import json
            return json.dumps(self.model_dump(), default=str)
    def Field(*args, **kwargs):
        return None

# =====================================================================
# 1. SPECIALIST AGENT REASONING SCHEMAS
# =====================================================================

class FundamentalVote(BaseModel):
    """Structured assessment from the Fundamental Analyst agent."""
    analyst: str = Field(default="Fundamental Analyst", description="Agent persona name")
    ticker: str = Field(..., description="Stock symbol (e.g. ASML, NVDA)")
    vote: Literal["BUY", "HOLD", "VETO"] = Field(..., description="Analyst voting decision")
    moat_score: float = Field(..., ge=0.0, le=10.0, description="Economic moat rating out of 10")
    net_margin_pct: float = Field(..., description="Net margin percentage")
    fwd_eps_growth_pct: float = Field(..., description="Consensus 1Y forward EPS growth %")
    thesis: str = Field(..., description="Core business conviction and pricing power rationale")
    primary_risks: List[str] = Field(default_factory=list, description="Top operational or valuation risks")

class TechnicalVote(BaseModel):
    """Structured assessment from the Technical Analyst agent."""
    analyst: str = Field(default="Technical Analyst", description="Agent persona name")
    ticker: str = Field(..., description="Stock symbol")
    vote: Literal["BUY", "HOLD", "VETO"] = Field(..., description="Analyst voting decision")
    ret_6m_pct: float = Field(..., description="6-month total return %")
    ret_1m_pct: float = Field(..., description="1-month total return %")
    rsi_14w: Optional[float] = Field(None, description="14-period weekly RSI")
    trend_status: str = Field(..., description="Price vs 50-day and 200-day moving averages")
    entry_timing: str = Field(..., description="Evaluation of entry pullback vs overextended momentum")

class RiskAuditVote(BaseModel):
    """Structured assessment from the Fiduciary Risk Manager agent."""
    analyst: str = Field(default="Fiduciary Risk Manager", description="Agent persona name")
    ticker: str = Field(..., description="Stock symbol")
    vote: Literal["BUY", "HOLD", "VETO"] = Field(..., description="Analyst voting decision")
    beta: float = Field(..., description="Calculated 3Y market beta")
    beta_collar_pass: bool = Field(..., description="Beta is within fiduciary collar [1.40, 2.80]")
    net_margin_pass: bool = Field(..., description="Net margin strictly > 0.0% (Anti-Cash-Burner)")
    earnings_blackout_pass: bool = Field(..., description="No earnings report scheduled within 48 hours")
    tenure_lock_compliant: bool = Field(True, description="Complies with 60-day anti-churn mandate")
    fiduciary_violation: Optional[str] = Field(None, description="Explanation of any fiduciary violation")
    ruin_prevention_memo: str = Field(..., description="Capital preservation and downside scenario analysis")

# =====================================================================
# 2. COMMITTEE DELIBERATION & EXTENDED REASONING
# =====================================================================

class CommitteeDeliberation(BaseModel):
    """
    Synthesized deliberation of the Multi-Agent Investment Committee.
    Enforces test-time reasoning traces and deterministic quorum rules.
    """
    ticker: str = Field(..., description="Stock ticker under deliberation")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="UTC timestamp")
    recommendation: Literal["BUY", "HOLD", "VETO"] = Field(..., description="Final committee consensus")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    buy_votes: int = Field(..., ge=0, le=3, description="Count of BUY votes from specialist agents")
    hold_votes: int = Field(..., ge=0, le=3, description="Count of HOLD votes from specialist agents")
    veto_votes: int = Field(..., ge=0, le=3, description="Count of VETO votes from specialist agents")
    fundamental: FundamentalVote = Field(..., description="Fundamental analyst evaluation")
    technical: TechnicalVote = Field(..., description="Technical analyst evaluation")
    risk: RiskAuditVote = Field(..., description="Fiduciary risk manager evaluation")
    thinking_trace: Optional[str] = Field(None, description="Test-time reasoning / chain-of-thought trace")
    synthesis_memo: str = Field(..., description="Final synthesis and capital allocation rationale")

# =====================================================================
# 3. PORTFOLIO & REBALANCE SCHEMAS
# =====================================================================

class HoldingItem(BaseModel):
    ticker: str
    shares: float
    invested_usd: float
    current_value_usd: float
    unrealized_pnl_usd: float
    unrealized_pnl_pct: float
    tenure_days: int
    tenure_locked: bool
    status: Literal["HEALTHY", "WARNING", "STOP_LOSS", "TAKE_PROFIT"]

class PortfolioStatus(BaseModel):
    cash_available_usd: float
    cash_withdrawable_usd: float
    holdings: List[HoldingItem]
    total_portfolio_value_usd: float
    in_flight_lrs_usd: float
    tenure_locked_count: int
    active_factor_model_version: str

class TargetAllocation(BaseModel):
    ticker: str
    target_weight_pct: float
    current_value_usd: float
    target_value_usd: float
    net_order_usd: float
    action: Literal["BUY", "SELL", "HOLD", "LOCKED"]
    reason: str

class RebalancePlan(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    withdrawable_cash_usd: float
    recyclable_capital_usd: float
    total_deployment_budget_usd: float
    allocations: List[TargetAllocation]
    fiduciary_compliance: bool
    ruin_check_passed: bool
    execution_orders: List[Dict[str, Any]]
