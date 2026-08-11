"""
Premium extraction and coverage-benchmark comparability checks.

Separates parsing/normalization from browser navigation so extraction
logic can be unit-tested against fixture quote-page text without live
site access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from schema import Applicant, Confidence, QuoteResult, Status


@dataclass
class PremiumExtraction:
    annual_premium: float | None = None
    monthly_premium: float | None = None
    quote_or_reference_id: str = ""
    matched_pattern: str = ""


@dataclass
class CoverageAssessment:
    matches_benchmark: bool
    coverage_notes: str
    confidence: Confidence
    gaps: list[str]


def _parse_money(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


# Ordered most-specific first. Patterns tuned against common Ontario
# insurer results-page wording (annual/monthly, premium/price/rate).
ANNUAL_PREMIUM_PATTERNS = [
    r"(?:your\s+)?(?:estimated\s+)?(?:annual|yearly)\s+(?:premium|price|rate)[^\$]{0,40}\$\s?([\d,]+(?:\.\d{2})?)(?!\s*(?:/month|per month))",
    r"(?:total\s+)?(?:annual|yearly)\s+(?:premium|cost)[^\$]{0,40}\$\s?([\d,]+(?:\.\d{2})?)(?!\s*(?:/month|per month))",
    r"(?:your\s+)?(?:estimated\s+)?(?:annual|yearly)\s+(?:premium|price|rate)\s*(?:is|:)?\s*\$\s?([\d,]+(?:\.\d{2})?)",
    r"(?:total price per year|price per year|total premium)[^\$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)",
    r"\$\s?([\d,]+(?:\.\d{2})?)\s?(?:/year|per year|annually|a year)(?!\s*(?:or|/))",
]

MONTHLY_PREMIUM_PATTERNS = [
    r"(?:your\s+)?(?:estimated\s+)?monthly\s+(?:premium|payment|price)[^\$]{0,40}\$\s?([\d,]+(?:\.\d{2})?)",
    r"(?:your\s+)?(?:estimated\s+)?(?:monthly\s+)?(?:premium|payment)\s*(?:is|:)?\s*\$\s?([\d,]+(?:\.\d{2})?)\s?(?:/month|per month)",
]

QUOTE_ID_PATTERNS = [
    r"(?:quote|reference|confirmation)\s*(?:#|number|id)\s*:?\s*([A-Z0-9-]{6,})",
    r"\b(QT[A-Z0-9-]{4,})\b",
]

QUOTE_ID_BLOCKLIST = {
    "related", "details", "copyright", "seeker", "policy", "number",
    "insurance", "reference", "confirmation",
}

# Landing/funnel pages often mention dollar amounts in marketing copy.
FUNNEL_PAGE_SIGNALS = re.compile(
    r"postal code|get quotes|get started|invalid postal|select your province|"
    r"welcome to sonnet|compare rates from|average cost|save \$|"
    r"everything you need to know about|not recognized",
    re.IGNORECASE,
)

QUOTE_RESULT_SIGNALS = re.compile(
    r"your (?:estimated )?(?:quote|premium|rate|price)|quote summary|"
    r"total price per year|your car insurance quote|reference #",
    re.IGNORECASE,
)


def is_funnel_page(text: str) -> bool:
    return bool(FUNNEL_PAGE_SIGNALS.search(text))


def is_quote_results_page(text: str) -> bool:
    return bool(QUOTE_RESULT_SIGNALS.search(text))


def extract_premium(text: str) -> PremiumExtraction:
    """Best-effort premium and reference-id extraction from visible page text."""
    result = PremiumExtraction()

    # Ignore marketing averages on postal-code landing pages.
    if is_funnel_page(text) and not is_quote_results_page(text):
        return result

    for pat in ANNUAL_PREMIUM_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = _parse_money(m.group(1))
            if val and val >= 300:  # reject tiny marketing amounts
                result.annual_premium = val
                result.matched_pattern = pat
            break

    for pat in MONTHLY_PREMIUM_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = _parse_money(m.group(1))
            if val and val >= 35:
                result.monthly_premium = val
                if not result.matched_pattern:
                    result.matched_pattern = pat
            break

    for pat in QUOTE_ID_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            qid = m.group(1).strip()
            if qid.lower() not in QUOTE_ID_BLOCKLIST and re.search(r"\d", qid):
                result.quote_or_reference_id = qid
            break

    return result


def _liability_matches(text: str, applicant: Applicant) -> bool:
    target = re.sub(r"\D", "", applicant.liability_limit or "")
    if not target:
        return True
    # Accept $2M, 2,000,000, 2 million, etc.
    if target == "2000000":
        return bool(re.search(r"(?:2[\s,]?000[\s,]?000|2\s*million|\$2\s*m\b|2m\b)", text, re.I))
    return target in re.sub(r"\D", "", text)


def _deductible_matches(text: str, deductible: str) -> bool:
    if not deductible:
        return True
    d = int(re.sub(r"\D", "", deductible))
    formatted = f"{d:,}"  # e.g. 1,000
    patterns = [
        rf"\$\s*{re.escape(formatted)}\b",
        rf"\$\s*{d}\b",
        rf"deductible[^\$]{{0,40}}\$\s*{re.escape(formatted)}",
        rf"deductible[^\$]{{0,40}}\$\s*{d}\b",
    ]
    return any(re.search(p, text, re.I) for p in patterns)


def assess_coverage_comparability(text: str, applicant: Applicant) -> CoverageAssessment:
    """
    Heuristic check that a quote page mentions the Section 6 benchmark
    coverage assumptions. Returns matches_benchmark=False with explicit
    gaps when anything required is missing from the visible text.
    """
    gaps: list[str] = []
    lower = text.lower()

    if not _liability_matches(text, applicant):
        gaps.append(f"liability limit {applicant.liability_limit} not confirmed on page")

    if applicant.dcpd_included and not re.search(
        r"(direct compensation|dcpd|property damage)", lower
    ):
        gaps.append("DCPD / direct compensation not mentioned")

    if applicant.collision_deductible and not _deductible_matches(
        text, applicant.collision_deductible
    ):
        gaps.append(f"collision deductible {applicant.collision_deductible} not confirmed")

    if applicant.comprehensive_deductible and not _deductible_matches(
        text, applicant.comprehensive_deductible
    ):
        gaps.append(
            f"comprehensive deductible {applicant.comprehensive_deductible} not confirmed"
        )

    if applicant.opcf_44r and not re.search(
        r"(opcf\s*44|family protection|44r)", lower
    ):
        gaps.append("OPCF 44R / family protection endorsement not mentioned")

    matches = len(gaps) == 0
    if matches:
        notes = "All benchmark coverage elements detected in quote page text."
        confidence = Confidence.HIGH
    elif len(gaps) <= 2:
        notes = "Partial benchmark match — manual verification recommended. Gaps: " + "; ".join(gaps)
        confidence = Confidence.MEDIUM
    else:
        notes = "Coverage assumptions differ from benchmark or could not be read from page. Gaps: " + "; ".join(gaps)
        confidence = Confidence.LOW

    return CoverageAssessment(
        matches_benchmark=matches,
        coverage_notes=notes,
        confidence=confidence,
        gaps=gaps,
    )


def normalize_quote_result(
    result: QuoteResult,
    page_text: str,
    applicant: Applicant,
) -> QuoteResult:
    """
    Enrich a QuoteResult with extracted premium, reference id, and
    benchmark comparability. Sets quoted_comparable when both a premium
    and full benchmark match are found.
    """
    premium = extract_premium(page_text)
    coverage = assess_coverage_comparability(page_text, applicant)

    if premium.annual_premium is not None:
        result.annual_premium = premium.annual_premium
    if premium.monthly_premium is not None:
        result.monthly_premium = premium.monthly_premium
    if premium.quote_or_reference_id:
        result.quote_or_reference_id = premium.quote_or_reference_id

    result.matches_benchmark = coverage.matches_benchmark
    result.coverage_notes = coverage.coverage_notes
    result.confidence = coverage.confidence

    if (result.annual_premium or result.monthly_premium) and is_funnel_page(page_text) and not is_quote_results_page(page_text):
        result.annual_premium = None
        result.monthly_premium = None
        result.quote_or_reference_id = ""
        result.status = Status.UNRESOLVED
        result.next_action = "Reached funnel/landing page — premium figures are marketing copy, not a live quote."
        return result

    if result.annual_premium or result.monthly_premium:
        if coverage.matches_benchmark:
            result.status = Status.QUOTED_COMPARABLE
            result.next_action = "Premium and benchmark coverage detected — spot-check evidence before binding."
        else:
            result.status = Status.QUOTED_NON_COMPARABLE
            result.next_action = (
                "Premium found but coverage may differ from benchmark — "
                + (coverage.gaps[0] if coverage.gaps else "verify manually")
            )
    elif result.status == Status.UNRESOLVED:
        result.next_action = result.next_action or "No premium detected on final page — review evidence manually."

    return result
