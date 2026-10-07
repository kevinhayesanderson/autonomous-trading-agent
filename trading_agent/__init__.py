"""
Autonomous Quantitative Trading Agent (AQTA)
Institutional Multi-Agent Quantitative Trading Platform for US & Indian Equities
"""

from .core.schemas import (
    CommitteeDeliberation,
    FundamentalVote,
    TechnicalVote,
    RiskAuditVote,
)
from .core.deliberation import deliberate_candidate, deliberate_ticker
from .core.config import (
    REPO_ROOT,
    MAX_BETA_COLLAR,
    MIN_BETA_COLLAR,
    TENURE_LOCK_DAYS,
)

__version__ = "2.2.0"
__author__ = "Kevin Hayes Anderson"
__all__ = [
    "__version__",
    "__author__",
    "CommitteeDeliberation",
    "FundamentalVote",
    "TechnicalVote",
    "RiskAuditVote",
    "deliberate_candidate",
    "deliberate_ticker",
    "REPO_ROOT",
    "MAX_BETA_COLLAR",
    "MIN_BETA_COLLAR",
    "TENURE_LOCK_DAYS",
]
