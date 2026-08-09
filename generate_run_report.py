"""
Generates the redacted run report required by Section 9 of the brief:
"include the coverage ledger, comparisons, gaps, errors and timestamps
without real licence numbers or other sensitive data."

Run after run_registry.py has produced results/results.json:
    python generate_run_report.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from guardrails import redact_for_storage

RESULTS_PATH = Path(__file__).parent / "results" / "results.json"
METRICS_PATH = Path(__file__).parent / "results" / "metrics.json"
REGISTRY_PATH = Path(__file__).parent / "registry" / "seed_registry.json"
OUTPUT_PATH = Path(__file__).parent / "results" / "run_report.md"


def generate():
    if not RESULTS_PATH.exists():
        print("No results.json found — run run_registry.py first.")
        return

    with open(RESULTS_PATH) as f:
        results = json.load(f)
    with open(REGISTRY_PATH) as f:
        registry = {r["registry_id"]: r for r in json.load(f)}

    metrics = {}
    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            metrics = json.load(f)

    lines = []
    lines.append("# Run Report — Ontario All-Quote Agent")
    lines.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("\n## Coverage metrics\n")
    for k, v in metrics.items():
        lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")

    lines.append("\n## Coverage ledger\n")
    lines.append("| Route | Channel | Status | Annual Premium | Confidence | Evidence Timestamp |")
    lines.append("|---|---|---|---|---|---|")
    for r in results:
        r = redact_for_storage(r)
        reg = registry.get(r.get("registry_id", ""), {})
        lines.append(
            f"| {reg.get('brand_or_program', r.get('registry_id'))} "
            f"| {reg.get('distribution_type', '—')} "
            f"| {r.get('status', '—')} "
            f"| {r.get('annual_premium', '—')} "
            f"| {r.get('confidence', '—')} "
            f"| {r.get('evidence_timestamp', '—')} |"
        )

    lines.append("\n## Gaps and unresolved routes\n")
    unresolved = [r for r in results if r.get("status") in
                  ("unresolved", "unreachable", "blocked", "manual_handoff", "callback_required")]
    if unresolved:
        for r in unresolved:
            r = redact_for_storage(r)
            reg = registry.get(r.get("registry_id", ""), {})
            reason = r.get("failure_reason") or r.get("next_action") or "no reason logged"
            lines.append(
                f"- **{reg.get('brand_or_program', r.get('registry_id'))}**: "
                f"{r.get('status')} — {reason}"
            )
    else:
        lines.append("None — all attempted routes reached a quoted or estimate outcome.")

    lines.append("\n## Errors\n")
    errors = [r for r in results if r.get("status") == "unreachable"]
    if errors:
        for r in errors:
            r = redact_for_storage(r)
            lines.append(f"- {r.get('registry_id')}: {r.get('failure_reason')}")
    else:
        lines.append("No unhandled errors recorded.")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Run report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
