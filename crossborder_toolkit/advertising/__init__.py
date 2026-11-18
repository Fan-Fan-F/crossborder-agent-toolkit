"""Advertising funnel diagnostic, metric optimization, and action planning module."""

from .models import AdRecord, AdMetrics, AdAction
from .bid_optimizer import BidOptimizer
from .diagnostic import (
    AdFunnelDiagnostic,
    SingleAdDiagnosis,
    FunnelDiagnosticSummary,
    STAGE_INSUFFICIENT_DATA,
    STAGE_PRE_CLICK,
    STAGE_DETAIL_PAGE,
    STAGE_DECISION_MAKING,
    STAGE_COST_INEFFICIENT,
    STAGE_HEALTHY,
)
from .action_planner import AdActionPlanner

__all__ = [
    "AdRecord",
    "AdMetrics",
    "AdAction",
    "BidOptimizer",
    "AdFunnelDiagnostic",
    "SingleAdDiagnosis",
    "FunnelDiagnosticSummary",
    "AdActionPlanner",
    "STAGE_INSUFFICIENT_DATA",
    "STAGE_PRE_CLICK",
    "STAGE_DETAIL_PAGE",
    "STAGE_DECISION_MAKING",
    "STAGE_COST_INEFFICIENT",
    "STAGE_HEALTHY",
]
