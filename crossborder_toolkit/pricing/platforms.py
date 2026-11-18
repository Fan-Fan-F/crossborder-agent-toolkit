"""Platform-specific fee schedules and presets for cross-border ecommerce."""

from typing import Dict, Any


PLATFORM_PRESETS: Dict[str, Dict[str, Any]] = {
    "shopee": {
        "name": "Shopee (Brazil / LatAm)",
        "commission_rate": 0.14,
        "ad_rate": 0.05,
        "return_rate": 0.02,
        "tax_rate": 0.04,  # Estimated local tax / nota fiscal buffer
        "currency": "BRL",
        "description": "Standard cross-border fee structure for Shopee Brazil.",
    },
    "mercadolivre": {
        "name": "Mercado Livre (Brazil / Clásico-Premium)",
        "commission_rate": 0.16,
        "ad_rate": 0.06,
        "return_rate": 0.02,
        "tax_rate": 0.04,
        "currency": "BRL",
        "description": "Standard commission structure for Mercado Livre Brazil Clásico/Premium.",
    },
    "amazon": {
        "name": "Amazon Global Selling",
        "commission_rate": 0.15,
        "ad_rate": 0.08,
        "return_rate": 0.03,
        "tax_rate": 0.0,
        "currency": "USD",
        "description": "Standard referral fee schedule for Amazon cross-border marketplace.",
    },
    "custom": {
        "name": "Custom Platform",
        "commission_rate": 0.10,
        "ad_rate": 0.05,
        "return_rate": 0.02,
        "tax_rate": 0.0,
        "currency": "USD",
        "description": "User-defined fee rates.",
    },
}


def get_platform_preset(platform_name: str) -> Dict[str, Any]:
    """Retrieve fee preset for the given platform key (case-insensitive)."""
    key = platform_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    for p_key, data in PLATFORM_PRESETS.items():
        if p_key == key or key in p_key:
            return dict(data)
    # Default to custom
    preset = dict(PLATFORM_PRESETS["custom"])
    preset["name"] = f"Custom ({platform_name})"
    return preset
