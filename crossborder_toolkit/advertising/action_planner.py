"""Action plan generator mapping funnel diagnostics into prioritized P0/P1/P2 operational tasks."""

from typing import List, Optional
from .models import AdAction, AdRecord
from .diagnostic import (
    SingleAdDiagnosis,
    STAGE_PRE_CLICK,
    STAGE_DETAIL_PAGE,
    STAGE_DECISION_MAKING,
    STAGE_COST_INEFFICIENT,
    STAGE_HEALTHY,
)
from .bid_optimizer import BidOptimizer


class AdActionPlanner:
    """Translates diagnostic bottlenecks into structured, prioritized P0/P1/P2 actions."""

    def __init__(
        self,
        high_spend_zero_order_threshold: float = 40.0,
        target_acos: float = 0.25,
    ):
        self.high_spend_zero_order_threshold = high_spend_zero_order_threshold
        self.target_acos = target_acos

    def plan_actions(
        self,
        diagnoses: List[SingleAdDiagnosis],
        breakeven_roas: float,
    ) -> List[AdAction]:
        """Generate categorized operational action list."""
        actions: List[AdAction] = []

        for diag in diagnoses:
            rec = diag.record
            m = diag.metrics

            # Priority 0: Immediate Bleeding Stop (Zero orders with significant spend)
            if rec.spend >= self.high_spend_zero_order_threshold and rec.orders == 0:
                actions.append(
                    AdAction(
                        priority="P0_EMERGENCY",
                        target_ad_id=rec.ad_id,
                        action_type="PAUSE_OR_NEGATIVE",
                        reason=f"花费已达 ${rec.spend:.2f} 但订单数为 0，构成持续无意义亏损。",
                        recommended_step=f"立即暂停推广词/广告组 '{rec.ad_id}'，或添加为精确否定词，切断无效耗资。",
                    )
                )
                continue

            # Priority 0: Severe loss (ROAS < 50% breakeven with notable spend)
            if rec.spend >= 30.0 and m.roas > 0 and m.roas < (breakeven_roas * 0.5):
                actions.append(
                    AdAction(
                        priority="P0_EMERGENCY",
                        target_ad_id=rec.ad_id,
                        action_type="SLASH_BID_OR_PAUSE",
                        reason=f"当前 ROAS 仅为 {m.roas:.2f}，不足保本线 ({breakeven_roas:.2f}) 的 50%。",
                        recommended_step=f"立即下调出价 40% 或将广告组 '{rec.ad_id}' 降级为观察组。",
                    )
                )
                continue

            # Priority 1: Funnel Bottlenecks
            if diag.funnel_stage == STAGE_PRE_CLICK:
                actions.append(
                    AdAction(
                        priority="P1_OPTIMIZATION",
                        target_ad_id=rec.ad_id,
                        action_type="FIX_CREATIVE",
                        reason=f"CTR 过低 ({m.ctr*100:.2f}%)，搜索流失严重。",
                        recommended_step="更换高对比度白底主图，提炼前 30 字符核心产品词，测试 3-5 天观察 CTR 是否回升至 3% 以上。",
                    )
                )
            elif diag.funnel_stage == STAGE_DETAIL_PAGE:
                actions.append(
                    AdAction(
                        priority="P1_OPTIMIZATION",
                        target_ad_id=rec.ad_id,
                        action_type="FIX_DETAIL_PAGE",
                        reason=f"加购率过低 ({m.cart_rate*100:.2f}%)，页面缺乏吸引力。",
                        recommended_step="重新梳理详情页前 3 段痛点文案，核查参数表完整性，并在图片中明确展示包装清单与配件。",
                    )
                )
            elif diag.funnel_stage == STAGE_DECISION_MAKING:
                actions.append(
                    AdAction(
                        priority="P1_OPTIMIZATION",
                        target_ad_id=rec.ad_id,
                        action_type="ADD_VOUCHER_OR_PROMOTION",
                        reason=f"加购率良好但转化率不足 ({m.cvr*100:.2f}%)，临门一脚犹豫。",
                        recommended_step="配置 5%-10% 店铺专属优惠券或开启多件打包减价，强化买家好评晒单置顶与官方质保承诺。",
                    )
                )
            elif diag.funnel_stage == STAGE_COST_INEFFICIENT:
                # Calculate optimal CPC ceiling
                aov = m.aov if m.aov > 0 else (rec.revenue / rec.orders if rec.orders > 0 else 50.0)
                cvr = m.cvr if m.cvr > 0 else 0.02
                suggested_max_cpc = BidOptimizer.calculate_max_cpc(aov, cvr, self.target_acos)
                actions.append(
                    AdAction(
                        priority="P1_OPTIMIZATION",
                        target_ad_id=rec.ad_id,
                        action_type="ADJUST_BID",
                        reason=f"转化漏斗正常但出价偏高 (当前 CPC ${m.cpc:.2f}，ROAS {m.roas:.2f} < 保本线 {breakeven_roas:.2f})。",
                        recommended_step=f"下调单次点击出价至建议上限 ${suggested_max_cpc:.2f}，或将广泛匹配收紧为词组/精准匹配。",
                    )
                )

            # Priority 2: Profitable scaling
            elif diag.funnel_stage == STAGE_HEALTHY:
                actions.append(
                    AdAction(
                        priority="P2_EXPANSION",
                        target_ad_id=rec.ad_id,
                        action_type="SCALE_BUDGET",
                        reason=f"广告表现优异 (ROAS {m.roas:.2f} >= 保本线 {breakeven_roas:.2f}，转化率 {m.cvr*100:.2f}%)。",
                        recommended_step=f"将日预算提升 15%-25%，持续拓展同类目精准搜索长尾词，扩大转化规模。",
                    )
                )

        # Sort actions: P0 first, then P1, then P2
        priority_rank = {"P0_EMERGENCY": 0, "P1_OPTIMIZATION": 1, "P2_EXPANSION": 2}
        actions.sort(key=lambda a: priority_rank.get(a.priority, 99))
        return actions
