"""Listing compliance, brand infringement prevention, and exaggerated claims filtering."""

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set


@dataclass
class ComplianceViolation:
    severity: str  # 'ERROR' or 'WARNING'
    category: str  # 'BRAND_INFRINGE', 'EXAGGERATED_CLAIM', 'PROMOTIONAL_SPAM'
    matched_word: str
    context: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Default brand database of common protected trademarks in cross-border commerce
DEFAULT_PROTECTED_BRANDS: Set[str] = {
    "apple", "iphone", "ipad", "airpods", "magsafe",
    "samsung", "galaxy", "xiaomi", "redmi", "huawei",
    "sony", "dyson", "nike", "adidas", "puma",
    "jbl", "bose", "gopro", "philips", "rolex", "stanley"
}

# Portuguese & English exaggerated, deceptive, or restricted claims
DEFAULT_EXAGGERATED_CLAIMS: Dict[str, Dict[str, str]] = {
    # Portuguese terms
    "melhor do mercado": {"severity": "WARNING", "category": "EXAGGERATED_CLAIM", "rec": "Replace superlative claim with factual performance metrics."},
    "100% original": {"severity": "ERROR", "category": "EXAGGERATED_CLAIM", "rec": "Avoid '100% original' unless you hold verified brand authorization certs."},
    "cura milagrosa": {"severity": "ERROR", "category": "EXAGGERATED_CLAIM", "rec": "Remove medical efficacy claims; platforms immediately suspend such listings."},
    "garantia vitalicia": {"severity": "WARNING", "category": "EXAGGERATED_CLAIM", "rec": "Specify exact warranty period (e.g., 90 dias / 1 ano)."},
    "gratis": {"severity": "WARNING", "category": "PROMOTIONAL_SPAM", "rec": "Avoid putting 'gratis' directly in titles on Shopee/Mercado Livre."},
    "de graca": {"severity": "WARNING", "category": "PROMOTIONAL_SPAM", "rec": "Remove spam promotional keywords from product titles."},

    # English & Universal terms
    "best seller": {"severity": "WARNING", "category": "EXAGGERATED_CLAIM", "rec": "Platforms forbid self-declaring 'Best Seller' in titles."},
    "#1": {"severity": "WARNING", "category": "EXAGGERATED_CLAIM", "rec": "Remove '#1' ranking claims."},
    "100% guarantee": {"severity": "WARNING", "category": "EXAGGERATED_CLAIM", "rec": "Specify exact platform return policy rather than blanket guarantees."},
    "miracle cure": {"severity": "ERROR", "category": "EXAGGERATED_CLAIM", "rec": "Strictly prohibited health claim."},
    "free gift": {"severity": "WARNING", "category": "PROMOTIONAL_SPAM", "rec": "Gift keywords trigger title spam filtering on several marketplaces."},
}


class ComplianceGuard:
    """Scans product titles and descriptions for policy infringements and restricted words."""

    def __init__(
        self,
        custom_brands: Optional[List[str]] = None,
        custom_forbidden: Optional[List[str]] = None,
        whitelist_brands: Optional[List[str]] = None,
    ):
        self.protected_brands = set(DEFAULT_PROTECTED_BRANDS)
        if custom_brands:
            self.protected_brands.update(b.strip().lower() for b in custom_brands if b.strip())

        self.whitelist_brands = set(b.strip().lower() for b in (whitelist_brands or []))
        self.claims_db = dict(DEFAULT_EXAGGERATED_CLAIMS)

        if custom_forbidden:
            for word in custom_forbidden:
                w_clean = word.strip().lower()
                if w_clean:
                    self.claims_db[w_clean] = {
                        "severity": "ERROR",
                        "category": "CUSTOM_RESTRICTED",
                        "rec": f"Word '{w_clean}' is listed in merchant custom restricted keyword list.",
                    }

    def scan(self, text: str) -> List[ComplianceViolation]:
        """Scan input text and return a list of compliance violations."""
        if not text or not text.strip():
            return []

        violations: List[ComplianceViolation] = []
        lower_text = text.lower()

        # Check brands
        for brand in sorted(self.protected_brands, key=len, reverse=True):
            if brand in self.whitelist_brands:
                continue
            # Match word boundary
            pattern = rf"\b{re.escape(brand)}\b"
            match = re.search(pattern, lower_text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end].strip()
                violations.append(
                    ComplianceViolation(
                        severity="ERROR",
                        category="BRAND_INFRINGE",
                        matched_word=brand,
                        context=f"...{snippet}...",
                        recommendation=(
                            f"Protected trademark '{brand}' detected. Do not use unauthorized brand names; "
                            "if compatible, use 'compatível com' or 'compatible with' where platform allows."
                        ),
                    )
                )

        # Check exaggerated claims and spam phrases
        for phrase, meta in self.claims_db.items():
            pattern = rf"\b{re.escape(phrase)}\b" if " " in phrase else rf"\b{re.escape(phrase)}\b"
            match = re.search(pattern, lower_text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end].strip()
                violations.append(
                    ComplianceViolation(
                        severity=meta["severity"],
                        category=meta["category"],
                        matched_word=phrase,
                        context=f"...{snippet}...",
                        recommendation=meta["rec"],
                    )
                )

        return violations
