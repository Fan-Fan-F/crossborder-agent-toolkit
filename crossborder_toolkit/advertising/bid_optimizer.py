"""Advertising performance metrics calculation and bid optimization formulas."""

from .models import AdRecord, AdMetrics


class BidOptimizer:
    """Calculates granular ad performance metrics and maximum allowable bid ceilings."""

    @staticmethod
    def calculate_metrics(record: AdRecord) -> AdMetrics:
        """Compute standard ecommerce advertising conversion and efficiency metrics with zero protection."""
        impr = max(0, record.impressions)
        clicks = max(0, record.clicks)
        carts = max(0, record.add_to_cart)
        orders = max(0, record.orders)
        spend = max(0.0, record.spend)
        revenue = max(0.0, record.revenue)

        ctr = round(clicks / impr, 4) if impr > 0 else 0.0
        cart_rate = round(carts / clicks, 4) if clicks > 0 else 0.0
        cvr = round(orders / clicks, 4) if clicks > 0 else 0.0
        cart_to_order_rate = round(orders / carts, 4) if carts > 0 else 0.0

        cpc = round(spend / clicks, 2) if clicks > 0 else 0.0
        cpa = round(spend / orders, 2) if orders > 0 else (round(spend, 2) if spend > 0 else 0.0)
        roas = round(revenue / spend, 2) if spend > 0 else 0.0
        acos = round(spend / revenue, 4) if revenue > 0 else (9.99 if spend > 0 else 0.0)
        aov = round(revenue / orders, 2) if orders > 0 else 0.0

        return AdMetrics(
            ctr=ctr,
            cart_rate=cart_rate,
            cvr=cvr,
            cart_to_order_rate=cart_to_order_rate,
            cpc=cpc,
            cpa=cpa,
            roas=roas,
            acos=acos,
            aov=aov,
        )

    @staticmethod
    def calculate_breakeven_roas(profit_margin: float) -> float:
        """Compute breakeven ROAS given product profit margin before ads.

        ROAS_breakeven = 1.0 / profit_margin
        """
        if profit_margin <= 0:
            raise ValueError(f"Profit margin must be positive to compute breakeven ROAS, got {profit_margin}")
        return round(1.0 / profit_margin, 2)

    @staticmethod
    def calculate_max_cpc(aov: float, cvr: float, target_acos: float) -> float:
        """Calculate maximum allowable CPC to stay within target ACOS.

        Formula: Max_CPC = Average Order Value (AOV) * Conversion Rate (CVR) * Target ACOS
        """
        if aov < 0 or cvr < 0 or target_acos < 0:
            raise ValueError("AOV, CVR, and target ACOS must be non-negative.")
        return round(aov * cvr * target_acos, 2)
