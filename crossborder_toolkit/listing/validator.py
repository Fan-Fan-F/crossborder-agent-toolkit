"""Listing validation engine: character limits, front-weight analysis, and compliance."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .platforms import get_listing_rule
from .compliance import ComplianceGuard, ComplianceViolation
from .spec_checker import SpecConsistencyChecker, SpecTraceabilityReport


@dataclass
class ListingValidationResult:
    platform: str
    title: str
    title_char_count: int
    max_title_chars: int
    is_title_length_valid: bool
    front_weight_chars: int
    front_weight_text: str
    core_keywords_in_front: List[str]
    core_keywords_in_total: List[str]
    missing_core_keywords: List[str]
    compliance_violations: List[ComplianceViolation]
    spec_report: SpecTraceabilityReport
    score: int  # 0 to 100
    status: str  # 'PASS', 'WARN', 'FAIL'
    passed: bool
    actionable_feedback: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "title": self.title,
            "title_char_count": self.title_char_count,
            "max_title_chars": self.max_title_chars,
            "is_title_length_valid": self.is_title_length_valid,
            "front_weight_chars": self.front_weight_chars,
            "front_weight_text": self.front_weight_text,
            "core_keywords_in_front": self.core_keywords_in_front,
            "core_keywords_in_total": self.core_keywords_in_total,
            "missing_core_keywords": self.missing_core_keywords,
            "compliance_violations": [v.to_dict() for v in self.compliance_violations],
            "spec_report": self.spec_report.to_dict(),
            "score": self.score,
            "status": self.status,
            "passed": self.passed,
            "actionable_feedback": self.actionable_feedback,
        }


class ListingValidator:
    """End-to-end Listing quality, policy compliance, and spec consistency validator."""

    def __init__(
        self,
        compliance_guard: Optional[ComplianceGuard] = None,
    ):
        self.compliance_guard = compliance_guard or ComplianceGuard()

    def validate(
        self,
        platform: str,
        title: str,
        description: str = "",
        spec_table: Optional[Dict[str, Any]] = None,
        core_keywords: Optional[List[str]] = None,
    ) -> ListingValidationResult:
        """Validate title and description against platform rules, compliance guards, and specs."""
        title_clean = (title or "").strip()
        desc_clean = (description or "").strip()
        rule = get_listing_rule(platform)
        max_chars = rule["max_title_chars"]
        front_chars_len = rule["front_weight_chars"]

        # Exact Unicode character count
        title_length = len(title_clean)
        is_length_valid = title_length <= max_chars and title_length >= rule.get("recommended_min_title_chars", 10)

        # Front-weight analysis
        front_text = title_clean[:front_chars_len]
        core_in_front: List[str] = []
        core_in_total: List[str] = []
        missing_core: List[str] = []

        keywords = core_keywords or []
        for kw in keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue
            if kw_clean in front_text.lower():
                core_in_front.append(kw)
            if kw_clean in title_clean.lower():
                core_in_total.append(kw)
            else:
                missing_core.append(kw)

        # Compliance scan across title + description
        combined_text = f"{title_clean}\n{desc_clean}"
        violations = self.compliance_guard.scan(combined_text)

        # Spec traceability cross-check
        spec_report = SpecConsistencyChecker.verify(combined_text, spec_table)

        # Score calculation and actionable feedback
        score = 100
        feedback: List[str] = []

        # Length evaluation
        if title_length > max_chars:
            score -= 35
            feedback.append(
                f"Title exceeds {rule['name']} limit: {title_length}/{max_chars} chars. Cut {title_length - max_chars} chars."
            )
        elif title_length < rule.get("recommended_min_title_chars", 10):
            score -= 15
            feedback.append(
                f"Title is too short ({title_length} chars). Recommend at least {rule.get('recommended_min_title_chars')} chars to cover keywords."
            )

        # Front keywords weighting
        if keywords and not core_in_front:
            score -= 15
            feedback.append(
                f"No core search keyword found within the first {front_chars_len} characters. "
                "Move the primary product noun to the very beginning of the title."
            )
        if missing_core:
            score -= min(20, len(missing_core) * 5)
            feedback.append(f"Missing core keywords in title: {', '.join(missing_core)}.")

        # Violations evaluation
        has_error = False
        for v in violations:
            if v.severity == "ERROR":
                has_error = True
                score -= 30
                feedback.append(f"[BLOCKER] {v.recommendation}")
            else:
                score -= 10
                feedback.append(f"[WARNING] {v.recommendation}")

        # Spec traceability evaluation
        if spec_report.unverified_specs:
            score -= min(25, len(spec_report.unverified_specs) * 8)
            feedback.extend(spec_report.warnings)

        score = max(0, min(100, score))

        # Overall status determination
        if has_error or title_length > max_chars:
            status = "FAIL"
            passed = False
        elif score < 75 or violations or spec_report.unverified_specs:
            status = "WARN"
            passed = True  # Can proceed with caution
        else:
            status = "PASS"
            passed = True

        return ListingValidationResult(
            platform=platform,
            title=title_clean,
            title_char_count=title_length,
            max_title_chars=max_chars,
            is_title_length_valid=(title_length <= max_chars),
            front_weight_chars=front_chars_len,
            front_weight_text=front_text,
            core_keywords_in_front=core_in_front,
            core_keywords_in_total=core_in_total,
            missing_core_keywords=missing_core,
            compliance_violations=violations,
            spec_report=spec_report,
            score=score,
            status=status,
            passed=passed,
            actionable_feedback=feedback,
        )
