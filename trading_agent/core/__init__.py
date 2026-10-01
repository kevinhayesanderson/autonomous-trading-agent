"""
AQTA Core Module - Unified Quantitative Architecture
"""

from .config import (
    REPO_ROOT,
    MEMORY_DIR,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    MAX_PORTFOLIO_ASSETS,
    TURNOVER_SCORE_DELTA,
    SLIPPAGE_TOLERANCE_PCT
)
from .deliberation import deliberate_candidate, deliberate_ticker
from .schemas import CommitteeDeliberation, FundamentalVote, TechnicalVote, RiskAuditVote
from .intelligence import get_cached_fundamental_dossier
