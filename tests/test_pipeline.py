"""Integration tests for CrossborderPipeline and CLI."""

import unittest
from crossborder_toolkit.pipeline import CrossborderPipeline


class TestPipeline(unittest.TestCase):
    def test_end_to_end_pipeline(self):
        pipe = CrossborderPipeline()
        res = pipe.run(
            cost=80.0,
            platform="shopee",
            shipping=10.0,
            packaging=2.0,
            target_margin=0.25,
            title="Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km",
            description="Patinete com motor 500W, bateria 10.4Ah e autonomia de 30km.",
            spec_table={"potencia": "500W", "bateria": "10.4Ah", "autonomia": "30km"},
            core_keywords=["Patinete Elétrico"],
            ad_records=[
                {
                    "ad_id": "kw_hero",
                    "impressions": 1000,
                    "clicks": 60,
                    "add_to_cart": 12,
                    "orders": 3,
                    "spend": 20.0,
                    "revenue": 150.0,
                },
                {
                    "ad_id": "kw_waste",
                    "impressions": 800,
                    "clicks": 45,
                    "add_to_cart": 2,
                    "orders": 0,
                    "spend": 45.0,
                    "revenue": 0.0,
                },
            ],
        )

        self.assertIsNotNone(res.pricing_result)
        self.assertGreater(res.pricing_result.target_price, 100.0)
        self.assertTrue(res.listing_result.passed)
        self.assertIsNotNone(res.ad_summary)
        self.assertEqual(len(res.recommended_actions), 2)
        # Check P0 emergency action exists for kw_waste
        p0_actions = [a for a in res.recommended_actions if a.priority == "P0_EMERGENCY"]
        self.assertEqual(len(p0_actions), 1)
        self.assertEqual(p0_actions[0].target_ad_id, "kw_waste")


if __name__ == "__main__":
    unittest.main()
