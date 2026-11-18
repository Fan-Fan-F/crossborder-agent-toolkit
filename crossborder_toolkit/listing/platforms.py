"""Platform-specific listing content limitations and guidelines."""

from typing import Dict, Any


PLATFORM_LISTING_RULES: Dict[str, Dict[str, Any]] = {
    "shopee": {
        "name": "Shopee",
        "max_title_chars": 120,
        "recommended_min_title_chars": 40,
        "front_weight_chars": 30,  # Characters given highest search weighting
        "max_images": 9,
        "description_min_chars": 50,
        "description_max_chars": 3000,
    },
    "mercadolivre": {
        "name": "Mercado Livre",
        "max_title_chars": 60,
        "recommended_min_title_chars": 25,
        "front_weight_chars": 20,
        "max_images": 10,
        "description_min_chars": 30,
        "description_max_chars": 5000,
    },
    "amazon": {
        "name": "Amazon",
        "max_title_chars": 200,
        "recommended_min_title_chars": 60,
        "front_weight_chars": 50,
        "max_images": 9,
        "description_min_chars": 100,
        "description_max_chars": 2000,
    },
}


def get_listing_rule(platform: str) -> Dict[str, Any]:
    """Retrieve listing rule specification for the given platform key."""
    key = platform.lower().replace(" ", "").replace("-", "").replace("_", "")
    for p_key, rule in PLATFORM_LISTING_RULES.items():
        if p_key == key or key in p_key:
            return dict(rule)
    # Default fallback
    return {
        "name": f"Generic ({platform})",
        "max_title_chars": 120,
        "recommended_min_title_chars": 30,
        "front_weight_chars": 30,
        "max_images": 9,
        "description_min_chars": 50,
        "description_max_chars": 3000,
    }
