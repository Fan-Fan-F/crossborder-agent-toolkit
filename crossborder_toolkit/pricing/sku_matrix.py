"""Multi-SKU matrix strategy and tier structural health validator."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .calculator import PricingCalculator, PricingResult


VALID_ROLES = {"traffic", "hero", "high_end", "bundle"}


@dataclass
class SkuItem:
    sku_name: str
    role: str  # traffic, hero, high_end, bundle
    cost: float
    shipping: float = 0.0
    packaging: float = 0.0
    target_price: Optional[float] = None
    target_margin: Optional[float] = None


@dataclass
class SkuMatrixReport:
    skus: List[Dict[str, Any]]
    hero_sku: Optional[str]
    has_traffic_sku: bool
    structural_warnings: List[str] = field(default_factory=list)
    healthy: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skus": self.skus,
            "hero_sku": self.hero_sku,
            "has_traffic_sku": self.has_traffic_sku,
            "structural_warnings": self.structural_warnings,
            "healthy": self.healthy,
        }


class SkuMatrixPlanner:
    """Plans and evaluates a 4-role ecommerce SKU portfolio (Traffic, Hero, High-End, Bundle)."""

    def __init__(self, platform: str = "custom", default_margin: float = 0.28):
        self.platform = platform
        self.default_margin = default_margin

    def evaluate_matrix(
        self,
        sku_items: List[SkuItem],
        commission_rate: Optional[float] = None,
        ad_rate: Optional[float] = None,
        return_rate: Optional[float] = None,
        tax_rate: Optional[float] = None,
    ) -> SkuMatrixReport:
        """Evaluate multi-SKU list, calculate pricing for each, and validate hierarchy."""
        if not sku_items:
            raise ValueError("sku_items list cannot be empty")

        evaluated_skus = []
        role_map: Dict[str, List[Dict[str, Any]]] = {r: [] for r in VALID_ROLES}
        warnings = []

        for item in sku_items:
            if item.role not in VALID_ROLES:
                raise ValueError(
                    f"Invalid SKU role '{item.role}'. Allowed roles are: {', '.join(sorted(VALID_ROLES))}"
                )

            # Assign default margin expectation according to role if not specified
            assigned_margin = item.target_margin
            if assigned_margin is None and item.target_price is None:
                if item.role == "traffic":
                    assigned_margin = max(0.10, self.default_margin - 0.12)
                elif item.role == "hero":
                    assigned_margin = self.default_margin
                elif item.role == "high_end":
                    assigned_margin = self.default_margin + 0.08
                elif item.role == "bundle":
                    assigned_margin = self.default_margin + 0.05

            result: PricingResult = PricingCalculator.calculate(
                cost=item.cost,
                shipping=item.shipping,
                packaging=item.packaging,
                platform=self.platform,
                commission_rate=commission_rate,
                ad_rate=ad_rate,
                return_rate=return_rate,
                tax_rate=tax_rate,
                target_margin=assigned_margin,
                target_price=item.target_price,
            )

            res_dict = result.to_dict()
            res_dict["sku_name"] = item.sku_name
            res_dict["role"] = item.role
            evaluated_skus.append(res_dict)
            role_map[item.role].append(res_dict)

        # Structural health analysis
        hero_skus = role_map["hero"]
        traffic_skus = role_map["traffic"]
        high_end_skus = role_map["high_end"]

        hero_name = hero_skus[0]["sku_name"] if hero_skus else None

        if not hero_skus:
            warnings.append("Missing 'hero' (main conversion) SKU. Every listing should have 1 hero SKU.")

        if traffic_skus and hero_skus:
            min_traffic_price = min(s["target_price"] for s in traffic_skus)
            hero_price = hero_skus[0]["target_price"]
            if min_traffic_price >= hero_price:
                warnings.append(
                    f"Traffic SKU price ({min_traffic_price}) is >= Hero SKU price ({hero_price}). "
                    "Traffic SKU must have a distinctly lower entry price to attract initial clicks."
                )

        if high_end_skus and hero_skus:
            max_high_price = max(s["target_price"] for s in high_end_skus)
            hero_price = hero_skus[0]["target_price"]
            if max_high_price <= hero_price:
                warnings.append(
                    f"High-end SKU price ({max_high_price}) is <= Hero SKU price ({hero_price}). "
                    "High-end SKU should be positioned with higher specs and premium pricing."
                )

        # Check for dangerously negative or low margins on traffic SKUs
        for t_sku in traffic_skus:
            if t_sku["net_margin"] < -0.05:
                warnings.append(
                    f"Traffic SKU '{t_sku['sku_name']}' has severely negative margin ({t_sku['net_margin']*100:.1f}%). "
                    "Loss-leader SKU should cap maximum monthly order volume to protect cash flow."
                )

        return SkuMatrixReport(
            skus=evaluated_skus,
            hero_sku=hero_name,
            has_traffic_sku=bool(traffic_skus),
            structural_warnings=warnings,
            healthy=len(warnings) == 0,
        )
