"""Four-stage reverse funnel diagnostic engine for ecommerce ads."""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from .models import AdRecord, AdMetrics
from .bid_optimizer import BidOptimizer


STAGE_INSUFFICIENT_DATA = "STAGE_0_INSUFFICIENT_DATA"
STAGE_PRE_CLICK = "STAGE_1_PRE_CLICK"
STAGE_DETAIL_PAGE = "STAGE_2_DETAIL_PAGE"
STAGE_DECISION_MAKING = "STAGE_3_DECISION_MAKING"
STAGE_COST_INEFFICIENT = "STAGE_4_COST_INEFFICIENT"
STAGE_HEALTHY = "STAGE_5_HEALTHY"


@dataclass
class SingleAdDiagnosis:
    ad_id: str
    campaign_name: str
    record: AdRecord
    metrics: AdMetrics
    funnel_stage: str
    stage_name_cn: str
    primary_bottleneck: str
    diagnostic_detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ad_id": self.ad_id,
            "campaign_name": self.campaign_name,
            "record": asdict(self.record),
            "metrics": self.metrics.to_dict(),
            "funnel_stage": self.funnel_stage,
            "stage_name_cn": self.stage_name_cn,
            "primary_bottleneck": self.primary_bottleneck,
            "diagnostic_detail": self.diagnostic_detail,
        }


@dataclass
class FunnelDiagnosticSummary:
    total_spend: float
    total_revenue: float
    total_impressions: int
    total_clicks: int
    total_orders: int
    overall_ctr: float
    overall_cart_rate: float
    overall_cvr: float
    overall_roas: float
    breakeven_roas: float
    profitable: bool
    stage_counts: Dict[str, int]
    diagnoses: List[SingleAdDiagnosis]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_spend": self.total_spend,
            "total_revenue": self.total_revenue,
            "total_impressions": self.total_impressions,
            "total_clicks": self.total_clicks,
            "total_orders": self.total_orders,
            "overall_ctr": self.overall_ctr,
            "overall_cart_rate": self.overall_cart_rate,
            "overall_cvr": self.overall_cvr,
            "overall_roas": self.overall_roas,
            "breakeven_roas": self.breakeven_roas,
            "profitable": self.profitable,
            "stage_counts": self.stage_counts,
            "diagnoses": [d.to_dict() for d in self.diagnoses],
        }


class AdFunnelDiagnostic:
    """Diagnoses ad campaigns strictly through sequential funnel stages (CTR -> Cart -> CVR -> ROAS)."""

    def __init__(
        self,
        min_ctr: float = 0.03,
        min_cart_rate: float = 0.08,
        min_cvr: float = 0.01,
        min_clicks_for_analysis: int = 20,
    ):
        self.min_ctr = min_ctr
        self.min_cart_rate = min_cart_rate
        self.min_cvr = min_cvr
        self.min_clicks_for_analysis = min_clicks_for_analysis

    def diagnose_record(self, record: AdRecord, breakeven_roas: float) -> SingleAdDiagnosis:
        """Diagnose a single ad record through the 4 funnel gates."""
        m = BidOptimizer.calculate_metrics(record)

        # Insufficient data check
        if record.clicks < self.min_clicks_for_analysis and record.impressions < 300:
            return SingleAdDiagnosis(
                ad_id=record.ad_id,
                campaign_name=record.campaign_name,
                record=record,
                metrics=m,
                funnel_stage=STAGE_INSUFFICIENT_DATA,
                stage_name_cn="样本量积累中",
                primary_bottleneck="数据积累期 (曝光 < 300 或 点击 < 20)",
                diagnostic_detail="当前样本量偏少，建议保持当前出价继续跑满 3-7 天测试周期。",
            )

        # Gate 1: Pre-Click funnel (CTR check)
        if m.ctr < self.min_ctr:
            return SingleAdDiagnosis(
                ad_id=record.ad_id,
                campaign_name=record.campaign_name,
                record=record,
                metrics=m,
                funnel_stage=STAGE_PRE_CLICK,
                stage_name_cn="有曝光无点击 (点击前环节故障)",
                primary_bottleneck="主图吸引力不足 / 标题核心词不精准 / 搜索展示价缺乏优势",
                diagnostic_detail=(
                    f"CTR 为 {m.ctr*100:.2f}% (低于健康线 {self.min_ctr*100:.1f}%)。"
                    "买家在搜索结果页未发生点击。病因在点击前环节，请勿盲目调价或动详情页，优先更换差异化主图并微调前 30 字符标题。"
                ),
            )

        # Gate 2: Detail Page funnel (Cart Rate check)
        if m.cart_rate < self.min_cart_rate:
            return SingleAdDiagnosis(
                ad_id=record.ad_id,
                campaign_name=record.campaign_name,
                record=record,
                metrics=m,
                funnel_stage=STAGE_DETAIL_PAGE,
                stage_name_cn="有点击无加购 (详情页环节故障)",
                primary_bottleneck="详情页卖点未打中痛点 / SKU 规格混乱 / 描述缺乏信任感",
                diagnostic_detail=(
                    f"CTR 达标 ({m.ctr*100:.2f}%)，但加购率仅为 {m.cart_rate*100:.2f}% (低于健康线 {self.min_cart_rate*100:.1f}%)。"
                    "买家已点击进入页面但未加购，说明主图引导有效但详情页承接转化不足。重点优化详情页 7 段结构与规格参数清晰度。"
                ),
            )

        # Gate 3: Decision Making funnel (Conversion Rate check)
        if m.cvr < self.min_cvr:
            return SingleAdDiagnosis(
                ad_id=record.ad_id,
                campaign_name=record.campaign_name,
                record=record,
                metrics=m,
                funnel_stage=STAGE_DECISION_MAKING,
                stage_name_cn="有加购无转化 (最终决策环节故障)",
                primary_bottleneck="价格与运费顾虑 / 缺乏促销刺激 / 评价与信任背书不足",
                diagnostic_detail=(
                    f"CTR 与加购率均达标，但转化率仅为 {m.cvr*100:.2f}% (低于健康线 {self.min_cvr*100:.1f}%)。"
                    "买家有强烈购买意向但在付款决策前流失。建议发放限时店铺满减优惠券、优化买家真实晒图评价、明确发货履约时效。"
                ),
            )

        # Gate 4: Cost Efficiency check (ROAS vs Breakeven)
        if m.roas < breakeven_roas:
            return SingleAdDiagnosis(
                ad_id=record.ad_id,
                campaign_name=record.campaign_name,
                record=record,
                metrics=m,
                funnel_stage=STAGE_COST_INEFFICIENT,
                stage_name_cn="高花费低 ROI (成本溢价环节)",
                primary_bottleneck="平均出价 (CPC) 过高 / 关键词过于宽泛引发无效消耗",
                diagnostic_detail=(
                    f"各转化漏斗指标均健康，但当前 ROAS 为 {m.roas:.2f} (低于保本线 {breakeven_roas:.2f})。"
                    f"当前 CPC 为 {m.cpc:.2f}，导致广告成本吞噬毛利。建议对该词进行出价回调 15%-20% 或收紧匹配方式。"
                ),
            )

        # Gate 5: Healthy and Profitable
        return SingleAdDiagnosis(
            ad_id=record.ad_id,
            campaign_name=record.campaign_name,
            record=record,
            metrics=m,
            funnel_stage=STAGE_HEALTHY,
            stage_name_cn="健康放量环节",
            primary_bottleneck="无瓶颈 (ROI 优秀)",
            diagnostic_detail=(
                f"漏斗全链路健康，ROAS ({m.roas:.2f}) 稳定高于保本线 ({breakeven_roas:.2f})。"
                "具备放量基础，可逐步提高 10%-20% 日预算或拓展相似长尾词抢占搜索前列。"
            ),
        )

    def diagnose_batch(
        self, records: List[AdRecord], breakeven_roas: float
    ) -> FunnelDiagnosticSummary:
        """Diagnose a collection of ad records and return aggregated insights."""
        diagnoses = [self.diagnose_record(r, breakeven_roas) for r in records]

        tot_spend = sum(r.spend for r in records)
        tot_rev = sum(r.revenue for r in records)
        tot_impr = sum(r.impressions for r in records)
        tot_clicks = sum(r.clicks for r in records)
        tot_orders = sum(r.orders for r in records)

        overall_ctr = round(tot_clicks / tot_impr, 4) if tot_impr > 0 else 0.0
        tot_carts = sum(r.add_to_cart for r in records)
        overall_cart_rate = round(tot_carts / tot_clicks, 4) if tot_clicks > 0 else 0.0
        overall_cvr = round(tot_orders / tot_clicks, 4) if tot_clicks > 0 else 0.0
        overall_roas = round(tot_rev / tot_spend, 2) if tot_spend > 0 else 0.0

        stage_counts = {}
        for d in diagnoses:
            stage_counts[d.funnel_stage] = stage_counts.get(d.funnel_stage, 0) + 1

        return FunnelDiagnosticSummary(
            total_spend=round(tot_spend, 2),
            total_revenue=round(tot_rev, 2),
            total_impressions=tot_impr,
            total_clicks=tot_clicks,
            total_orders=tot_orders,
            overall_ctr=overall_ctr,
            overall_cart_rate=overall_cart_rate,
            overall_cvr=overall_cvr,
            overall_roas=overall_roas,
            breakeven_roas=breakeven_roas,
            profitable=(overall_roas >= breakeven_roas),
            stage_counts=stage_counts,
            diagnoses=diagnoses,
        )
