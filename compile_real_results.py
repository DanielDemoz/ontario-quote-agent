"""
Compiles today's REAL results (captured during live testing against
production sites) into results/results.json, so generate_run_report.py
and the coverage metrics reflect actual evidence, not synthetic data.

Run once: python compile_real_results.py
"""

import json
from pathlib import Path

RESULTS_PATH = Path(__file__).parent / "results" / "results.json"
METRICS_PATH = Path(__file__).parent / "results" / "metrics.json"

# These are the real, evidence-backed outcomes from today's live runs.
# Evidence file paths reference actual screenshots captured during
# testing (see evidence/ folder).
results = [
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
        "failure_reason": "",
        "next_action": "Reached real multi-step quote form (step 1 of 3, native vehicle fields) after recovering from an anti-direct-link redirect. Did not complete within step budget - furthest progress of any route.",
    },
    {
        "registry_id": "thinkinsure-broker-001",
        "distinct_rate_source_id": "broker-thinkinsure",
        "status": "unresolved",
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
        "failure_reason": "Not yet attempted live within the build window.",
        "next_action": "Expected outcome is callback_required or manual_handoff per Ontario broker disclosure requirements - not yet verified live.",
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
        "evidence_timestamp": "",
        "evidence_artifact_path": "",
        "source_url": "",
        "confidence": "low",
        "failure_reason": "Not yet attempted live within the build window.",
        "next_action": "Expected to require CAA membership verification - not yet tested live.",
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

RESULTS_PATH.parent.mkdir(exist_ok=True)
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"Wrote {len(results)} real results to {RESULTS_PATH}")

# Compute the same metrics run_registry.py would, from this real data.
verified_applicable = len(results)
evidence_backed = sum(1 for r in results if r.get("evidence_timestamp") or r.get("status") == "manual_handoff")
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
