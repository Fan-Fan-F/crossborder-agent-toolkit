"""Cross-border Ecommerce Agent Toolkit — Executable operational workflows for pricing, listing, and ads."""

__version__ = "1.0.0"

from .pricing import (
    PricingCalculator,
    PricingResult,
    SkuMatrixPlanner,
    SkuItem,
    SkuMatrixReport,
    get_platform_preset,
)
from .listing import (
    ListingValidator,
    ListingValidationResult,
    ComplianceGuard,
    ComplianceViolation,
    SpecConsistencyChecker,
    SpecTraceabilityReport,
    get_listing_rule,
)
from .advertising import (
    AdRecord,
    AdMetrics,
    AdAction,
    BidOptimizer,
    AdFunnelDiagnostic,
    SingleAdDiagnosis,
    FunnelDiagnosticSummary,
    AdActionPlanner,
)
from .pipeline import CrossborderPipeline, PipelineRunResult

__all__ = [
    "__version__",
    "PricingCalculator",
    "PricingResult",
    "SkuMatrixPlanner",
    "SkuItem",
    "SkuMatrixReport",
    "get_platform_preset",
    "ListingValidator",
    "ListingValidationResult",
    "ComplianceGuard",
    "ComplianceViolation",
    "SpecConsistencyChecker",
    "SpecTraceabilityReport",
    "get_listing_rule",
    "AdRecord",
    "AdMetrics",
    "AdAction",
    "BidOptimizer",
    "AdFunnelDiagnostic",
    "SingleAdDiagnosis",
    "FunnelDiagnosticSummary",
    "AdActionPlanner",
    "CrossborderPipeline",
    "PipelineRunResult",
]
