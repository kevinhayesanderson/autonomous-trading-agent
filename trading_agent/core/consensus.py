"""
Multi-Agent Committee Consensus & Cross-Sectional Z-Score Engine
"""

import math
from typing import Dict, Any, List

def cross_sectional_z_score(values: List[float]) -> List[float]:
    """Computes sample z-scores for cross-sectional factor ranking."""
    if not values or len(values) < 2:
        return [0.0] * len(values)
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std = math.sqrt(variance) if variance > 1e-9 else 1e-9
    return [(x - mean) / std for x in values]

from .deliberation import deliberate_candidate

def multi_agent_committee_vote(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements multi-agent committee consensus (Fundamental, Technical, Risk)
    using the SOTA typed deliberation engine with test-time reasoning traces.
    """
    delib = deliberate_candidate(candidate)
    return {
        "fundamental": delib.fundamental.vote,
        "technical": delib.technical.vote,
        "risk": delib.risk.vote,
        "consensus": delib.recommendation == "BUY",
        "recommendation": delib.recommendation,
        "confidence": delib.confidence_score,
        "synthesis": delib.synthesis_memo,
        "thinking_trace": delib.thinking_trace
    }

def score_candidates_with_consensus(candidates: List[Dict[str, Any]], active_weights: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Synthesizes factor scores, Z-scores, committee votes, and technical adjustments into a final Consensus Q-Score."""
    if not candidates:
        return []

    w_6m = active_weights.get("weight_6m_return", 0.20)
    w_1m = active_weights.get("weight_1m_return", 0.15)
    w_beta = active_weights.get("weight_beta", 20.0)
    beta_max = active_weights.get("beta_clamp_max", 2.50)
    w_eps = active_weights.get("weight_fwd_eps", 0.15)
    eps_cap = active_weights.get("fwd_eps_cap", 250.0)
    w_upside = active_weights.get("weight_analyst_upside", 0.15)
    w_buy_pct = active_weights.get("weight_analyst_buy_pct", 0.15)
    rsi_ob_thresh = active_weights.get("rsi_overbought_threshold", 75.0)
    rsi_ob_pen = active_weights.get("rsi_overbought_penalty", -15.0)
    rsi_os_thresh = active_weights.get("rsi_oversold_threshold", 35.0)
    rsi_os_boost = active_weights.get("rsi_oversold_boost", 10.0)
    earn_pen = active_weights.get("earnings_proximity_penalty", -25.0)

    z_6m = cross_sectional_z_score([c["ret_6m"] for c in candidates])
    z_1m = cross_sectional_z_score([c["ret_1m"] for c in candidates])
    z_eps = cross_sectional_z_score([min(c["eps_fwd"], eps_cap) for c in candidates])
    z_upside = cross_sectional_z_score([max(c["upside"], -10.0) for c in candidates])

    for i, c in enumerate(candidates):
        beta_clamped = min(c["beta"], beta_max)
        raw_score = (
            (c["ret_6m"] * w_6m) +
            (c["ret_1m"] * w_1m) +
            (beta_clamped * w_beta) +
            (min(c["eps_fwd"], eps_cap) * w_eps) +
            (max(c["upside"], -10.0) * w_upside) +
            (c["buy_pct"] * w_buy_pct)
        )
        z_composite = (z_6m[i] * 0.35) + (z_1m[i] * 0.25) + (z_eps[i] * 0.20) + (z_upside[i] * 0.20)
        c["z_score"] = z_composite

        comm_vote = multi_agent_committee_vote(c)
        c["committee_vote"] = comm_vote
        comm_boost = 10.0 if comm_vote["consensus"] else -10.0

        rsi_adj = 0.0
        if c["rsi"] is not None:
            if c["rsi"] >= rsi_ob_thresh:
                rsi_adj = rsi_ob_pen
            elif c["rsi"] <= rsi_os_thresh:
                rsi_adj = rsi_os_boost

        earn_adj = earn_pen if c["has_earnings_risk"] else 0.0
        c["consensus_q"] = round((raw_score * 0.40) + ((z_composite * 15.0 + 50.0) * 0.60) + comm_boost + rsi_adj + earn_adj, 2)
        c["q_score"] = c["consensus_q"]

    candidates.sort(key=lambda x: x["consensus_q"], reverse=True)
    return candidates
