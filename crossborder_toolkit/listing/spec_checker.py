"""Specification consistency checker to prevent AI hallucination and spec exaggeration."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SpecTraceabilityReport:
    extracted_specs: List[str]
    verified_specs: List[str]
    unverified_specs: List[str]
    is_fully_traceable: bool
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extracted_specs": self.extracted_specs,
            "verified_specs": self.verified_specs,
            "unverified_specs": self.unverified_specs,
            "is_fully_traceable": self.is_fully_traceable,
            "warnings": self.warnings,
        }


# Regular expressions for technical/physical specs with units
SPEC_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(w|kw|v|kv|ah|mah|wh|kwh|kg|g|lb|km/h|mph|km|m|cm|mm|l|ml|db|rpm|hz|khz|mhz)\b",
    re.IGNORECASE,
)


class SpecConsistencyChecker:
    """Verifies that all technical numbers and units in text originate from an authentic spec table."""

    @staticmethod
    def extract_specs(text: str) -> List[str]:
        """Extract all technical specifications (number + unit) from text."""
        if not text:
            return []
        matches = SPEC_PATTERN.findall(text)
        found = []
        for val, unit in matches:
            formatted = f"{val}{unit.lower()}"
            if formatted not in found:
                found.append(formatted)
        return found

    @staticmethod
    def _normalize_spec_value(val: str) -> str:
        """Strip spaces and lowercase a spec string."""
        return re.sub(r"\s+", "", str(val)).lower()

    @classmethod
    def verify(
        cls,
        text: str,
        spec_table: Optional[Dict[str, Any]] = None,
    ) -> SpecTraceabilityReport:
        """Cross-check extracted specs from text against the truth spec table."""
        extracted = cls.extract_specs(text)
        if not spec_table:
            # If no spec table provided, report all extracted specs as unverified
            return SpecTraceabilityReport(
                extracted_specs=extracted,
                verified_specs=[],
                unverified_specs=extracted,
                is_fully_traceable=len(extracted) == 0,
                warnings=[
                    "No specification table provided. All technical numbers in text are unverified and at risk of hallucination."
                ]
                if extracted
                else [],
            )

        # Build normalized pool of allowed spec values and exact extracted spec tokens from the table
        allowed_spec_set = set()
        for k, v in spec_table.items():
            # Extract any structured specs inside the table values and keys
            table_specs = cls.extract_specs(str(v)) + cls.extract_specs(str(k))
            for ts in table_specs:
                allowed_spec_set.add(cls._normalize_spec_value(ts))
            # Also add exact normalized string value if it resembles a spec
            norm_v = cls._normalize_spec_value(v)
            allowed_spec_set.add(norm_v)

        verified = []
        unverified = []
        warnings = []

        for spec in extracted:
            spec_norm = cls._normalize_spec_value(spec)
            # Must strictly match an allowed spec token (avoid false substring match like '500w' inside '1500w')
            if spec_norm in allowed_spec_set:
                verified.append(spec)
            else:
                unverified.append(spec)
                warnings.append(
                    f"Spec '{spec}' found in content cannot be traced back to product spec sheet. "
                    "Possible hallucinated parameter."
                )

        return SpecTraceabilityReport(
            extracted_specs=extracted,
            verified_specs=verified,
            unverified_specs=unverified,
            is_fully_traceable=len(unverified) == 0,
            warnings=warnings,
        )
