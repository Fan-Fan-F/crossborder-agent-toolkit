"""Unit tests for listing validation module."""

import unittest
from crossborder_toolkit.listing import (
    ListingValidator,
    ComplianceGuard,
    SpecConsistencyChecker,
)


class TestListingValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ListingValidator()

    def test_shopee_valid_listing(self):
        title = "Patinete Elétrico Dobrável 500W Bateria 10.4Ah Autonomia 30km Preto"
        desc = "Patinete elétrico com motor potente de 500W e bateria de 10.4Ah com alcance de 30km e peso máximo 120kg."
        specs = {
            "potencia": "500W",
            "bateria": "10.4Ah",
            "autonomia": "30km",
            "peso_maximo": "120kg",
        }
        res = self.validator.validate(
            platform="shopee",
            title=title,
            description=desc,
            spec_table=specs,
            core_keywords=["Patinete Elétrico"],
        )
        self.assertTrue(res.passed)
        self.assertEqual(res.status, "PASS")
        self.assertGreaterEqual(res.score, 85)
        self.assertIn("Patinete Elétrico", res.core_keywords_in_front)
        self.assertTrue(res.spec_report.is_fully_traceable)

    def test_mercadolivre_title_length_exceeded(self):
        long_title = (
            "Patinete Elétrico Profissional Dobrável com Luz LED Potente 500W Bateria Longa Duração para Adultos Cidade"
        )
        # Length is > 60 chars
        res = self.validator.validate(
            platform="mercadolivre",
            title=long_title,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, "FAIL")
        self.assertFalse(res.is_title_length_valid)
        self.assertIn("Title exceeds Mercado Livre limit", res.actionable_feedback[0])

    def test_compliance_brand_and_exaggerated_claims(self):
        title = "Fone de Ouvido Bluetooth estilo Apple iPhone 100% original melhor do mercado"
        res = self.validator.validate(
            platform="shopee",
            title=title,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, "FAIL")
        matched_words = [v.matched_word for v in res.compliance_violations]
        self.assertIn("apple", matched_words)
        self.assertIn("iphone", matched_words)
        self.assertIn("100% original", matched_words)

    def test_spec_consistency_unverified(self):
        desc = "Patinete super rápido que atinge 80km/h com motor de 1500W e peso suportado de 200kg."
        specs = {
            "potencia": "500W",
            "velocidade_max": "25km/h",
        }
        report = SpecConsistencyChecker.verify(desc, specs)
        self.assertFalse(report.is_fully_traceable)
        self.assertTrue(len(report.unverified_specs) > 0)
        self.assertIn("1500w", report.unverified_specs)
        self.assertIn("80km/h", report.unverified_specs)


if __name__ == "__main__":
    unittest.main()
