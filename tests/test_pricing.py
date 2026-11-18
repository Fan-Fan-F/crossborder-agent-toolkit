"""Unit tests for pricing module."""

import unittest
from crossborder_toolkit.pricing import (
    PricingCalculator,
    SkuMatrixPlanner,
    SkuItem,
    get_platform_preset,
)


class TestPricingCalculator(unittest.TestCase):
    def test_shopee_pricing(self):
        # Cost: 100, Target margin: 25%, Shopee preset
        res = PricingCalculator.calculate(
            cost=100.0,
            shipping=15.0,
            packaging=5.0,
            platform="shopee",
            target_margin=0.25,
        )
        self.assertEqual(res.cost, 100.0)
        self.assertEqual(res.total_fixed_cost, 120.0)
        self.assertGreater(res.target_price, res.breakeven_price)
        self.assertGreater(res.net_profit, 0)
        self.assertAlmostEqual(res.net_margin, 0.25, places=2)
        self.assertGreater(res.breakeven_roas, 1.0)
        self.assertIn("keep_15%_margin", res.voucher_buffers)

    def test_fixed_price_back_calculation(self):
        # When target_price is given
        res = PricingCalculator.calculate(
            cost=50.0,
            shipping=10.0,
            platform="custom",
            commission_rate=0.10,
            ad_rate=0.05,
            return_rate=0.02,
            tax_rate=0.0,
            target_price=120.0,
        )
        self.assertEqual(res.target_price, 120.0)
        self.assertGreater(res.net_margin, 0.20)
        self.assertGreater(res.net_profit, 0)

    def test_invalid_negative_cost(self):
        with self.assertRaises(ValueError):
            PricingCalculator.calculate(cost=-10.0)

    def test_invalid_excessive_rates(self):
        # Commission 60% + Ad 50% = 110% >= 100%
        with self.assertRaises(ValueError):
            PricingCalculator.calculate(
                cost=50.0,
                commission_rate=0.60,
                ad_rate=0.50,
            )

    def test_sku_matrix_planning(self):
        planner = SkuMatrixPlanner(platform="shopee", default_margin=0.30)
        skus = [
            SkuItem(sku_name="Basic White", role="traffic", cost=30.0),
            SkuItem(sku_name="Standard 500W", role="hero", cost=70.0),
            SkuItem(sku_name="Pro 800W Plus", role="high_end", cost=120.0),
            SkuItem(sku_name="Bundle with Helmet", role="bundle", cost=85.0),
        ]
        report = planner.evaluate_matrix(skus)
        self.assertTrue(report.healthy)
        self.assertEqual(report.hero_sku, "Standard 500W")
        self.assertEqual(len(report.skus), 4)
        # Check price hierarchy: traffic < hero < high_end
        traffic_p = report.skus[0]["target_price"]
        hero_p = report.skus[1]["target_price"]
        high_p = report.skus[2]["target_price"]
        self.assertLess(traffic_p, hero_p)
        self.assertGreater(high_p, hero_p)

    def test_sku_matrix_unhealthy_hierarchy(self):
        # Traffic cost higher than hero -> traffic price >= hero price
        planner = SkuMatrixPlanner(platform="shopee")
        skus = [
            SkuItem(sku_name="Traffic Fake", role="traffic", cost=150.0),
            SkuItem(sku_name="Hero Regular", role="hero", cost=50.0),
        ]
        report = planner.evaluate_matrix(skus)
        self.assertFalse(report.healthy)
        self.assertTrue(any("Traffic SKU price" in w for w in report.structural_warnings))


if __name__ == "__main__":
    unittest.main()
