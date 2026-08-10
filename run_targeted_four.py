"""
Run the four targeted direct-writer routes (Tasks 21–24) and merge
results into results/results.json + update registry entries.
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from schema import MarketRecord, Status
from browser_agent import run_route
from guardrails import validate_applicant_for_mode
from run_registry import build_applicant, compute_metrics

ROOT = Path(__file__).parent
REGISTRY_PATH = ROOT / "registry" / "seed_registry.json"
RESULTS_PATH = ROOT / "results" / "results.json"
METRICS_PATH = ROOT / "results" / "metrics.json"

TARGET_IDS = [
    "squareone-direct-002",
    "duuo-cooperators-001",
    "aviva-direct-002",
    "td-direct-002",
]


def _status_str(result) -> str:
    s = result.status
    return s.value if isinstance(s, Status) else str(s)


async def main():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry_raw = json.load(f)
    by_id = {r["registry_id"]: r for r in registry_raw}

    applicant = build_applicant()
    validate_applicant_for_mode(applicant)
    print(f"Mode: {applicant.mode}")

    live_results = {}
    for rid in TARGET_IDS:
        if rid not in by_id:
            print(f"SKIP missing registry id: {rid}")
            continue
        rec = MarketRecord(**by_id[rid])
        print(f"\n=== {rid} ({rec.brand_or_program}) ===")
        result = await run_route(rec, applicant)
        d = asdict(result)
        d["status"] = _status_str(result)
        d["confidence"] = result.confidence.value if hasattr(result.confidence, "value") else "low"
        live_results[rid] = d
        print(f"-> {d['status']}")
        print(f"   url: {d.get('source_url', '')}")
        print(f"   evidence: {d.get('evidence_artifact_path', '')}")

    # Merge into results.json
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    merged = {r["registry_id"]: r for r in existing}
    for rid, d in live_results.items():
        merged[rid] = {
            "registry_id": rid,
            "distinct_rate_source_id": by_id[rid]["distinct_rate_source_id"],
            "status": d["status"],
            "annual_premium": d.get("annual_premium"),
            "monthly_premium": d.get("monthly_premium"),
            "coverage_notes": d.get("coverage_notes", ""),
            "matches_benchmark": d.get("matches_benchmark", False),
            "quote_or_reference_id": d.get("quote_or_reference_id", ""),
            "effective_date": d.get("effective_date", ""),
            "evidence_timestamp": d.get("evidence_timestamp", ""),
            "evidence_artifact_path": d.get("evidence_artifact_path", ""),
            "source_url": d.get("source_url", ""),
            "confidence": d.get("confidence", "low"),
            "failure_reason": d.get("failure_reason", ""),
            "next_action": d.get("next_action", ""),
        }

    # Ensure all registry routes have a row (preserve placeholders)
    for rec in registry_raw:
        rid = rec["registry_id"]
        if rid not in merged:
            merged[rid] = {
                "registry_id": rid,
                "distinct_rate_source_id": rec["distinct_rate_source_id"],
                "status": rec.get("status", "unresolved"),
                "annual_premium": None,
                "monthly_premium": None,
                "coverage_notes": "",
                "matches_benchmark": False,
                "quote_or_reference_id": "",
                "effective_date": "",
                "evidence_timestamp": "",
                "evidence_artifact_path": rec.get("evidence_url", ""),
                "source_url": rec.get("quote_url", ""),
                "confidence": "low",
                "failure_reason": "",
                "next_action": rec.get("automation_notes", ""),
            }

    ordered = [merged[r["registry_id"]] for r in registry_raw if r["registry_id"] in merged]
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2)

    # Update registry status / evidence for targeted routes
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for rec in registry_raw:
        rid = rec["registry_id"]
        if rid not in live_results:
            continue
        d = live_results[rid]
        rec["status"] = d["status"]
        rec["last_verified_at"] = now
        if d.get("evidence_artifact_path"):
            rec["evidence_url"] = d["evidence_artifact_path"]
        note = d.get("next_action") or d.get("failure_reason") or ""
        if note:
            rec["automation_notes"] = (
                rec.get("automation_notes", "").rstrip()
                + f" UPDATE ({now[:10]}): {note}"
            )

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry_raw, f, indent=2)

    registry = [MarketRecord(**r) for r in registry_raw]
    metrics = compute_metrics(registry, ordered)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n--- Metrics ---")
    print(json.dumps(metrics, indent=2))
    print(f"\nWrote {len(ordered)} results, updated {len(live_results)} registry entries.")


if __name__ == "__main__":
    asyncio.run(main())
