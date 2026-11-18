"""Core pricing calculator and margin analysis for cross-border ecommerce."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from .platforms import get_platform_preset


@dataclass
class PricingResult:
    cost: float
    shipping: float
    packaging: float
    total_fixed_cost: float
    platform: str
    commission_rate: float
    ad_rate: float
    return_rate: float
    tax_rate: float
    total_variable_rate: float
    target_price: float
    breakeven_price: float
    net_profit: float
    net_margin: float
    breakeven_roas: float
    target_margin: float
    voucher_buffers: Dict[str, Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PricingCalculator:
    """Calculates pricing, breakeven thresholds, and margin matrices for ecommerce SKUs."""

    @staticmethod
    def calculate(
        cost: float,
        shipping: float = 0.0,
        packaging: float = 0.0,
        platform: str = "custom",
        commission_rate: Optional[float] = None,
        ad_rate: Optional[float] = None,
        return_rate: Optional[float] = None,
        tax_rate: Optional[float] = None,
        target_margin: Optional[float] = None,
        target_price: Optional[float] = None,
    ) -> PricingResult:
        """Calculate target selling price, breakeven price, and margin structures.

        Args:
            cost: Base unit procurement cost (must be > 0).
            shipping: Domestic + international freight per unit (must be >= 0).
            packaging: Packaging, labeling, warehouse handling fee (must be >= 0).
            platform: Preset platform key ('shopee', 'mercadolivre', 'amazon', 'custom').
            commission_rate: Marketplace commission rate (0.0 to 1.0).
            ad_rate: Estimated ad spend ratio of revenue (0.0 to 1.0).
            return_rate: Return/damage loss ratio of revenue (0.0 to 1.0).
            tax_rate: Applicable sales/invoice tax ratio (0.0 to 1.0).
            target_margin: Desired net profit margin (0.0 to 1.0).
            target_price: Given test selling price (to back-calculate net margin).

        Raises:
            ValueError: If inputs violate boundary conditions or rates exceed 100%.
        """
        if cost <= 0:
            raise ValueError(f"Procurement cost must be strictly positive, got {cost}")
        if shipping < 0:
            raise ValueError(f"Shipping cost cannot be negative, got {shipping}")
        if packaging < 0:
            raise ValueError(f"Packaging cost cannot be negative, got {packaging}")

        # Fill defaults from platform presets if omitted
        preset = get_platform_preset(platform)
        c_rate = commission_rate if commission_rate is not None else preset["commission_rate"]
        a_rate = ad_rate if ad_rate is not None else preset["ad_rate"]
        r_rate = return_rate if return_rate is not None else preset["return_rate"]
        t_rate = tax_rate if tax_rate is not None else preset["tax_rate"]

        for name, r in [
            ("commission_rate", c_rate),
            ("ad_rate", a_rate),
            ("return_rate", r_rate),
            ("tax_rate", t_rate),
        ]:
            if r < 0 or r >= 1.0:
                raise ValueError(f"{name} must be within [0.0, 1.0), got {r}")

        total_variable_rate = c_rate + a_rate + r_rate + t_rate
        if total_variable_rate >= 1.0:
            raise ValueError(
                f"Combined fee rates ({total_variable_rate * 100:.2f}%) exceed or reach 100%. "
                "Pricing is mathematically impossible."
            )

        total_fixed_cost = cost + shipping + packaging
        breakeven_price = round(total_fixed_cost / (1.0 - total_variable_rate), 2)

        # Decide mode: target_margin or target_price
        if target_margin is not None:
            if target_margin < 0 or target_margin >= 1.0:
                raise ValueError(f"target_margin must be within [0.0, 1.0), got {target_margin}")
            combined_rate = total_variable_rate + target_margin
            if combined_rate >= 1.0:
                raise ValueError(
                    f"Combined fees ({total_variable_rate * 100:.2f}%) + target margin "
                    f"({target_margin * 100:.2f}%) = {combined_rate * 100:.2f}%, which is >= 100%. "
                    "Cannot price with this margin target."
                )
            calc_price = round(total_fixed_cost / (1.0 - combined_rate), 2)
            final_target_price = calc_price
            effective_margin = target_margin
        elif target_price is not None:
            if target_price <= 0:
                raise ValueError(f"target_price must be strictly positive, got {target_price}")
            final_target_price = round(target_price, 2)
            # Net margin = 1 - total_variable_rate - (fixed_cost / price)
            effective_margin = round(1.0 - total_variable_rate - (total_fixed_cost / final_target_price), 4)
            target_margin = effective_margin
        else:
            # Default to 25% target margin for standard ecommerce products
            default_margin = 0.25
            if total_variable_rate + default_margin >= 1.0:
                default_margin = max(0.05, round((1.0 - total_variable_rate) / 2.0, 2))
            final_target_price = round(total_fixed_cost / (1.0 - (total_variable_rate + default_margin)), 2)
            effective_margin = default_margin
            target_margin = effective_margin

        net_profit = round(final_target_price * effective_margin, 2)

        # Breakeven ROAS: reciprocal of (gross margin before ads)
        # Gross margin before ads = 1 - commission - return - tax - (cost/price)
        cost_ratio = total_fixed_cost / final_target_price if final_target_price > 0 else 1.0
        gross_margin_before_ads = 1.0 - (c_rate + r_rate + t_rate) - cost_ratio
        if gross_margin_before_ads > 0:
            breakeven_roas = round(1.0 / gross_margin_before_ads, 2)
        else:
            breakeven_roas = 999.0  # Cannot break even even with infinite ROAS

        # Calculate voucher buffer: how much discount/coupon can be provided
        # while preserving minimum net margins (e.g., preserving 15%, 10%, 5% net margin)
        voucher_buffers = {}
        for floor_margin in [0.15, 0.10, 0.05, 0.0]:
            if effective_margin > floor_margin:
                max_discount_ratio = round((effective_margin - floor_margin) / (1.0 - c_rate), 4)
                max_discount_amount = round(final_target_price * max_discount_ratio, 2)
                voucher_buffers[f"keep_{int(floor_margin * 100)}%_margin"] = {
                    "max_discount_pct": round(max_discount_ratio * 100, 2),
                    "max_discount_amount": max_discount_amount,
                    "discounted_price": round(final_target_price - max_discount_amount, 2),
                }
            else:
                voucher_buffers[f"keep_{int(floor_margin * 100)}%_margin"] = {
                    "max_discount_pct": 0.0,
                    "max_discount_amount": 0.0,
                    "discounted_price": final_target_price,
                }

        return PricingResult(
            cost=cost,
            shipping=shipping,
            packaging=packaging,
            total_fixed_cost=total_fixed_cost,
            platform=platform,
            commission_rate=c_rate,
            ad_rate=a_rate,
            return_rate=r_rate,
            tax_rate=t_rate,
            total_variable_rate=round(total_variable_rate, 4),
            target_price=final_target_price,
            breakeven_price=breakeven_price,
            net_profit=net_profit,
            net_margin=round(effective_margin, 4),
            breakeven_roas=breakeven_roas,
            target_margin=round(target_margin, 4),
            voucher_buffers=voucher_buffers,
        )
