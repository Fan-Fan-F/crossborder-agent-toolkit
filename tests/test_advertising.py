"""Unit tests for advertising diagnostic and action planner module."""

import unittest
from crossborder_toolkit.advertising import (
    AdRecord,
    BidOptimizer,
    AdFunnelDiagnostic,
    AdActionPlanner,
    STAGE_PRE_CLICK,
    STAGE_DETAIL_PAGE,
    STAGE_DECISION_MAKING,
    STAGE_COST_INEFFICIENT,
    STAGE_HEALTHY,
)


class TestAdvertisingDiagnostic(unittest.TestCase):
    def setUp(self):
        self.diagnostic = AdFunnelDiagnostic(
            min_ctr=0.03,
            min_cart_rate=0.08,
            min_cvr=0.01,
            min_clicks_for_analysis=10,
        )
        self.planner = AdActionPlanner(high_spend_zero_order_threshold=30.0)
        self.breakeven_roas = 2.5

    def test_metrics_calculation(self):
        rec = AdRecord(
            ad_id="kw_1",
            campaign_name="scooter_exact",
            impressions=1000,
            clicks=50,
            add_to_cart=10,
            orders=2,
            spend=25.0,
            revenue=100.0,
        )
        m = BidOptimizer.calculate_metrics(rec)
        self.assertEqual(m.ctr, 0.05)
        self.assertEqual(m.cart_rate, 0.20)
        self.assertEqual(m.cvr, 0.04)
        self.assertEqual(m.cpc, 0.50)
        self.assertEqual(m.roas, 4.0)
        self.assertEqual(m.acos, 0.25)
        self.assertEqual(m.aov, 50.0)

    def test_stage_1_pre_click(self):
        # CTR < 3%
        rec = AdRecord(
            ad_id="kw_low_ctr",
            campaign_name="broad_campaign",
            impressions=2000,
            clicks=20,  # CTR = 1%
            add_to_cart=5,
            orders=1,
            spend=15.0,
            revenue=40.0,
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        self.assertEqual(diag.funnel_stage, STAGE_PRE_CLICK)
        self.assertIn("点击前环节故障", diag.stage_name_cn)

    def test_stage_2_detail_page(self):
        # CTR >= 3%, but Cart Rate < 8%
        rec = AdRecord(
            ad_id="kw_low_cart",
            campaign_name="exact_campaign",
            impressions=1000,
            clicks=50,  # CTR = 5%
            add_to_cart=2,  # Cart rate = 4% < 8%
            orders=1,
            spend=25.0,
            revenue=50.0,
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        self.assertEqual(diag.funnel_stage, STAGE_DETAIL_PAGE)
        self.assertIn("详情页环节故障", diag.stage_name_cn)

    def test_stage_3_decision_making(self):
        # CTR >= 3%, Cart Rate >= 8%, but CVR < 1%
        rec = AdRecord(
            ad_id="kw_low_cvr",
            campaign_name="exact_campaign",
            impressions=1000,
            clicks=100,  # CTR = 10%
            add_to_cart=15,  # Cart rate = 15%
            orders=0,  # CVR = 0% < 1%
            spend=35.0,
            revenue=0.0,
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        self.assertEqual(diag.funnel_stage, STAGE_DECISION_MAKING)

    def test_stage_4_cost_inefficient(self):
        # All conversion rates good, but ROAS < breakeven (2.5)
        rec = AdRecord(
            ad_id="kw_high_bid",
            campaign_name="exact_campaign",
            impressions=1000,
            clicks=50,  # CTR = 5%
            add_to_cart=10,  # Cart rate = 20%
            orders=3,  # CVR = 6%
            spend=60.0,  # High CPC = 1.20
            revenue=100.0,  # ROAS = 1.67 < 2.5
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        self.assertEqual(diag.funnel_stage, STAGE_COST_INEFFICIENT)

    def test_stage_5_healthy(self):
        # Healthy ROAS >= breakeven
        rec = AdRecord(
            ad_id="kw_champion",
            campaign_name="exact_campaign",
            impressions=1000,
            clicks=50,
            add_to_cart=10,
            orders=4,
            spend=20.0,
            revenue=120.0,  # ROAS = 6.0
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        self.assertEqual(diag.funnel_stage, STAGE_HEALTHY)

    def test_p0_action_generation(self):
        # Record with high spend and 0 orders should trigger P0_EMERGENCY
        rec = AdRecord(
            ad_id="kw_money_pit",
            campaign_name="phrase_campaign",
            impressions=1000,
            clicks=60,
            add_to_cart=8,
            orders=0,
            spend=55.0,
            revenue=0.0,
        )
        diag = self.diagnostic.diagnose_record(rec, self.breakeven_roas)
        actions = self.planner.plan_actions([diag], self.breakeven_roas)
        self.assertTrue(len(actions) > 0)
        self.assertEqual(actions[0].priority, "P0_EMERGENCY")
        self.assertEqual(actions[0].action_type, "PAUSE_OR_NEGATIVE")


if __name__ == "__main__":
    unittest.main()
