"""Tests for premium extraction and coverage comparability heuristics."""

import json
from pathlib import Path

from normalizer import extract_premium, assess_coverage_comparability, normalize_quote_result
from schema import Applicant, QuoteResult, Status, Confidence

FIXTURES = Path(__file__).parent / "fixtures" / "quote_pages.json"


def _applicant(**kwargs) -> Applicant:
    base = Applicant(
        liability_limit="2000000",
        dcpd_included=True,
        collision_deductible="1000",
        comprehensive_deductible="1000",
        opcf_44r=True,
    )
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


def test_extract_annual_premium_standard_wording():
    text = "Your estimated annual premium is $2,847.00 per year. Quote # QT-88291"
    ext = extract_premium(text)
    assert ext.annual_premium == 2847.0
    assert ext.quote_or_reference_id == "QT-88291"


def test_extract_monthly_premium():
    text = "Monthly payment: $237.25/month"
    ext = extract_premium(text)
    assert ext.monthly_premium == 237.25


def test_coverage_full_benchmark_match():
    text = """
    Liability $2,000,000
    Direct Compensation Property Damage included
    Collision deductible $1,000
    Comprehensive deductible $1,000
    OPCF 44R Family Protection endorsement
    Annual premium $1,500
    """
    assessment = assess_coverage_comparability(text, _applicant())
    assert assessment.matches_benchmark is True
    assert assessment.confidence == Confidence.HIGH


def test_coverage_partial_match_flags_gaps():
    text = "Annual premium $1,200. Liability $1,000,000."
    assessment = assess_coverage_comparability(text, _applicant())
    assert assessment.matches_benchmark is False
    assert len(assessment.gaps) >= 1


def test_normalize_sets_quoted_comparable():
    result = QuoteResult(
        registry_id="test-001",
        distinct_rate_source_id="test",
        status=Status.UNRESOLVED,
    )
    text = """
    Liability $2 million. DCPD included. Collision $1000 deductible.
    Comprehensive $1000. OPCF 44R family protection.
    Your annual premium is $2,100.00
    """
    out = normalize_quote_result(result, text, _applicant())
    assert out.status == Status.QUOTED_COMPARABLE
    assert out.annual_premium == 2100.0
    assert out.matches_benchmark is True


def test_marketing_page_does_not_extract_premium():
    text = """
    Car Insurance in Canada
    Postal code
    Get Quotes
    Average Cost $1,321 per year or $110 per month in Ontario
    """
    ext = extract_premium(text)
    assert ext.annual_premium is None
    assert ext.monthly_premium is None


def test_fixture_quote_pages():
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))
    app = _applicant()
    for case in cases:
        ext = extract_premium(case["text"])
        cov = assess_coverage_comparability(case["text"], app)
        if case["name"] == "partial_coverage":
            assert ext.monthly_premium == 987.0
            assert cov.matches_benchmark is False
        else:
            assert ext.annual_premium is not None
            assert cov.matches_benchmark is True
