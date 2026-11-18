"""Data models and enums for advertising performance and diagnostic funnel."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class AdRecord:
    ad_id: str
    campaign_name: str
    impressions: int
    clicks: int
    add_to_cart: int
    orders: int
    spend: float
    revenue: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdRecord":
        return cls(
            ad_id=str(data.get("ad_id") or data.get("id") or data.get("keyword") or "unknown"),
            campaign_name=str(data.get("campaign_name") or data.get("name") or data.get("ad_id") or "default"),
            impressions=int(data.get("impressions") or data.get("impr") or 0),
            clicks=int(data.get("clicks") or 0),
            add_to_cart=int(data.get("add_to_cart") or data.get("cart") or 0),
            orders=int(data.get("orders") or data.get("conversions") or 0),
            spend=float(data.get("spend") or data.get("cost") or 0.0),
            revenue=float(data.get("revenue") or data.get("gmv") or data.get("sales") or 0.0),
        )


@dataclass
class AdMetrics:
    ctr: float
    cart_rate: float  # add_to_cart / clicks
    cvr: float        # orders / clicks
    cart_to_order_rate: float  # orders / add_to_cart
    cpc: float
    cpa: float        # spend / orders
    roas: float       # revenue / spend
    acos: float       # spend / revenue
    aov: float        # revenue / orders

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdAction:
    priority: str     # 'P0_EMERGENCY', 'P1_OPTIMIZATION', 'P2_EXPANSION'
    target_ad_id: str
    action_type: str  # 'PAUSE', 'ADJUST_BID', 'FIX_CREATIVE', 'ADD_VOUCHER', 'SCALE_BUDGET'
    reason: str
    recommended_step: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
