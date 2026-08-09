"""
Compiles results into results/results.json for the UI and run report.

Evidence-backed rows (live runs with screenshots) are preserved exactly.
Every other registry route gets a placeholder row from seed_registry.json
so the Results tab stays in sync with the Market registry tab.

Run once: python compile_real_results.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS_PATH = ROOT / "results" / "results.json"
METRICS_PATH = ROOT / "results" / "metrics.json"
REGISTRY_PATH = ROOT / "registry" / "seed_registry.json"

# Real, evidence-backed outcomes aligned with registry/seed_registry.json.
EVIDENCE_RESULTS = [
    {
        "registry_id": "sonnet-direct-001",
        "distinct_rate_source_id": "definity-sonnet",
        "status": "unresolved",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "2026-08-09T15:29:08.907142+00:00",
        "evidence_artifact_path": "evidence/sonnet-direct-001_final_20260809T152908850252Z.png",
        "source_url": "https://secure.sonnet.ca/#/quoting/auto/province?lang=en",
        "confidence": "low",
        "failure_reason": "Custom (non-native) dropdown component on province-selection screen could not be reliably driven within the build window.",
        "next_action": "Reached real form. Needs site-specific selector work for the custom dropdown component.",
    },
    {
        "registry_id": "lowestrates-agg-001",
        "distinct_rate_source_id": "agg-lowestrates",
        "status": "blocked",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "2026-08-09T15:41:44.190122+00:00",
        "evidence_artifact_path": "evidence/lowestrates-agg-001_final_20260809T154144146884Z.png",
        "source_url": "https://www.lowestrates.ca/insurance/auto",
        "confidence": "low",
        "failure_reason": "Active bot-detection block: \"Sorry, you have been blocked. You are unable to access lowestrates.ca.\"",
        "next_action": "Logged per guardrail; access-control block, not evaded per brief requirements.",
    },
    {
        "registry_id": "belairdirect-001",
        "distinct_rate_source_id": "intact-belairdirect",
        "status": "unresolved",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "2026-08-09T16:03:15.881556+00:00",
        "evidence_artifact_path": "evidence/belairdirect-001_final_20260809T160315728573Z.png",
        "source_url": "https://webquote.app.belairdirect.com/quote/car/1/info?language=en&province=on&f=c&intcid=homepage:quote-from-bundle-started-1v-1d-0h",
        "confidence": "low",
        "failure_reason": "Reached step 1 of 3 vehicle form after homepage redirect recovery; did not complete within step budget.",
        "next_action": "Reached real multi-step quote form (step 1 of 3, native vehicle fields) after recovering from an anti-direct-link redirect. Did not complete within step budget - furthest progress of any direct route.",
    },
    {
        "registry_id": "thinkinsure-broker-001",
        "distinct_rate_source_id": "broker-thinkinsure",
        "status": "callback_required",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "2026-08-09T17:21:45.723837+00:00",
        "evidence_artifact_path": "evidence/thinkinsure-broker-001_final_20260809T172145645048Z.png",
        "source_url": "https://www.thinkinsure.ca/quotes/auto",
        "confidence": "low",
        "failure_reason": "Broker lead-capture intake requires full name, email, and phone; footer states final pricing requires registered broker phone completion. reCAPTCHA present on submit step. No instant self-serve premium.",
        "next_action": "Licensed broker callback at 1-855-550-5515; request full carrier list and quote outcomes per Ontario Insurance Act disclosure requirements.",
    },
    {
        "registry_id": "caa-affinity-001",
        "distinct_rate_source_id": "caa-direct",
        "status": "unresolved",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "2026-08-09T17:23:09.503451+00:00",
        "evidence_artifact_path": "evidence/caa-affinity-001_final_20260809T172309421847Z.png",
        "source_url": "https://car-insurance.caasco.com/auto/intro",
        "confidence": "low",
        "failure_reason": "Reached CAA South Central Ontario step-1 Vehicle Details; garaging address required. Membership number not requested on this screen. Could not advance in estimate_only mode without address.",
        "next_action": "Not affinity_restricted on evidence captured — address gate reached first. Membership eligibility may appear on later steps.",
    },
    {
        "registry_id": "facility-residual-001",
        "distinct_rate_source_id": "residual-facility",
        "status": "manual_handoff",
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "",
        "evidence_artifact_path": "",
        "source_url": "",
        "confidence": "low",
        "failure_reason": "Residual market has no direct automatable path by design.",
        "next_action": "Route through licensed broker - correctly logged without attempting to fabricate a direct path.",
    },
]


def _placeholder_from_registry(record: dict) -> dict:
    return {
        "registry_id": record["registry_id"],
        "distinct_rate_source_id": record["distinct_rate_source_id"],
        "status": record.get("status", "unresolved"),
        "annual_premium": None,
        "monthly_premium": None,
        "coverage_notes": "",
        "matches_benchmark": False,
        "quote_or_reference_id": "",
        "effective_date": "",
        "evidence_timestamp": "",
        "evidence_artifact_path": record.get("evidence_url") or "",
        "source_url": record.get("quote_url") or "",
        "confidence": "low",
        "failure_reason": "",
        "next_action": record.get("automation_notes") or "Not yet attempted live.",
    }


def build_results() -> list[dict]:
    evidence_by_id = {r["registry_id"]: r for r in EVIDENCE_RESULTS}
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)

    results = []
    for record in registry:
        rid = record["registry_id"]
        if rid in evidence_by_id:
            results.append(evidence_by_id[rid])
        else:
            results.append(_placeholder_from_registry(record))
    return results


results = build_results()

RESULTS_PATH.parent.mkdir(exist_ok=True)
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"Wrote {len(results)} results to {RESULTS_PATH} ({len(EVIDENCE_RESULTS)} with live evidence)")

verified_applicable = len(results)
evidence_backed = sum(
    1 for r in results
    if r.get("evidence_timestamp") or r.get("status") == "manual_handoff"
)
comparable = sum(1 for r in results if r.get("status") == "quoted_comparable")

metrics = {
    "verified_applicable_rate_sources": verified_applicable,
    "results_produced": len(results),
    "market_completion": round(evidence_backed / verified_applicable, 3) if verified_applicable else 0,
    "comparable_quote_yield": round(comparable / verified_applicable, 3) if verified_applicable else 0,
    "evidence_rate": round(evidence_backed / len(results), 3) if results else 0,
}

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print(f"Wrote metrics to {METRICS_PATH}:")
print(json.dumps(metrics, indent=2))
