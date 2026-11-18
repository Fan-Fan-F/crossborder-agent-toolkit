"""Pricing strategy and multi-SKU margin analysis module."""

from .platforms import PLATFORM_PRESETS, get_platform_preset
from .calculator import PricingCalculator, PricingResult
from .sku_matrix import SkuMatrixPlanner, SkuItem, SkuMatrixReport

__all__ = [
    "PLATFORM_PRESETS",
    "get_platform_preset",
    "PricingCalculator",
    "PricingResult",
    "SkuMatrixPlanner",
    "SkuItem",
    "SkuMatrixReport",
]
