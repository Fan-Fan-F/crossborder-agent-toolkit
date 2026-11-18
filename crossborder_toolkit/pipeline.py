"""End-to-end operational pipeline connecting Pricing -> Listing QC -> Ad Diagnosis."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from .pricing import PricingCalculator, PricingResult
from .listing import ListingValidator, ListingValidationResult
from .advertising import (
    AdRecord,
    AdFunnelDiagnostic,
    AdActionPlanner,
    FunnelDiagnosticSummary,
    AdAction,
)


@dataclass
class PipelineRunResult:
    pricing_result: PricingResult
    listing_result: ListingValidationResult
    ad_summary: Optional[FunnelDiagnosticSummary]
    recommended_actions: List[AdAction]
    overall_health: str  # 'EXCELLENT', 'ACTION_REQUIRED', 'BLOCKED'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pricing": self.pricing_result.to_dict(),
            "listing": self.listing_result.to_dict(),
            "ad_summary": self.ad_summary.to_dict() if self.ad_summary else None,
            "recommended_actions": [a.to_dict() for a in self.recommended_actions],
            "overall_health": self.overall_health,
        }


class CrossborderPipeline:
    """Orchestrates the 3-step closed-loop ecommerce lifecycle:

    1. Price & Margin Setup (determines breakeven ROAS and voucher room)
    2. Listing Compliance & Spec Validation (ensures high search quality & no policy bans)
    3. Advertising Funnel Diagnosis (identifies drop-off bottlenecks and issues P0/P1/P2 actions)
    """

    def __init__(
        self,
        listing_validator: Optional[ListingValidator] = None,
        ad_diagnostic: Optional[AdFunnelDiagnostic] = None,
        ad_planner: Optional[AdActionPlanner] = None,
    ):
        self.listing_validator = listing_validator or ListingValidator()
        self.ad_diagnostic = ad_diagnostic or AdFunnelDiagnostic()
        self.ad_planner = ad_planner or AdActionPlanner()

    def run(
        self,
        # Pricing Inputs
        cost: float,
        platform: str = "shopee",
        shipping: float = 0.0,
        packaging: float = 0.0,
        target_margin: Optional[float] = None,
        target_price: Optional[float] = None,
        # Listing Inputs
        title: str = "",
        description: str = "",
        spec_table: Optional[Dict[str, Any]] = None,
        core_keywords: Optional[List[str]] = None,
        # Ad Data Inputs (optional)
        ad_records: Optional[List[Dict[str, Any]]] = None,
    ) -> PipelineRunResult:
        """Run the integrated cross-border operational pipeline."""
        # Step 1: Calculate Pricing and Breakeven ROAS
        pricing_res = PricingCalculator.calculate(
            cost=cost,
            shipping=shipping,
            packaging=packaging,
            platform=platform,
            target_margin=target_margin,
            target_price=target_price,
        )

        # Step 2: Validate Listing Content & Policy Compliance
        listing_res = self.listing_validator.validate(
            platform=platform,
            title=title,
            description=description,
            spec_table=spec_table,
            core_keywords=core_keywords,
        )

        # Step 3: Advertising Diagnosis using calculated Breakeven ROAS
        ad_summary = None
        actions: List[AdAction] = []
        if ad_records:
            records = [AdRecord.from_dict(r) for r in ad_records]
            ad_summary = self.ad_diagnostic.diagnose_batch(
                records=records,
                breakeven_roas=pricing_res.breakeven_roas,
            )
            actions = self.ad_planner.plan_actions(
                diagnoses=ad_summary.diagnoses,
                breakeven_roas=pricing_res.breakeven_roas,
            )

        # Determine overall pipeline health
        if not listing_res.passed:
            overall_health = "BLOCKED"
        elif any(a.priority == "P0_EMERGENCY" for a in actions) or listing_res.status == "WARN":
            overall_health = "ACTION_REQUIRED"
        else:
            overall_health = "EXCELLENT"

        return PipelineRunResult(
            pricing_result=pricing_res,
            listing_result=listing_res,
            ad_summary=ad_summary,
            recommended_actions=actions,
            overall_health=overall_health,
        )
