"""
Generates the redacted run report required by Section 9 of the brief.

Run after run_registry.py has produced results/results.json:
    python generate_run_report.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from formatting_utils import sanitize_display_text
from guardrails import redact_for_storage
from metrics_utils import compute_metrics, split_live_tested_vs_seed
from report_utils import (
    REGISTRY_PATH,
    RESULTS_PATH,
    format_evidence_link,
    load_registry_and_results,
)

METRICS_PATH = Path(__file__).parent / "results" / "metrics.json"
OUTPUT_PATH = Path(__file__).parent / "results" / "run_report.md"


def generate_report() -> Path | None:
    if not RESULTS_PATH.exists():
        print("No results.json found. Run run_registry.py first.")
        return None

    registry, results = load_registry_and_results()
    metrics = compute_metrics(registry, results)
    live_tested, seed_only = split_live_tested_vs_seed(registry, results)

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("# Run Report: Ontario All-Quote Agent (Binder)")
    lines.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")

    lines.append("\n## Summary")
    lines.append(f"- **Live-tested routes with real evidence:** {len(live_tested)}")
    lines.append(f"- **Discovery-stage seed entries (not yet attempted):** {len(seed_only)}")
    lines.append(f"- **Total registry entries:** {len(registry)}")
    lines.append(f"- **Evidence-backed completion (all results):** {metrics.get('market_completion', 'n/a')}")
    lines.append(f"- **Evidence rate:** {metrics.get('evidence_rate', 'n/a')}")

    lines.append("\n## Live-Tested Routes: Real Evidence")
    lines.append(
        "\nEvery row below reflects an actual attempt against a live site, "
        "with a timestamp and evidence artifact (or documented rationale when "
        "no live path exists).\n"
    )
    lines.append("| Route | Channel | Status | Premium | Evidence | Timestamp |")
    lines.append("|---|---|---|---|---|---|")
    for entry in live_tested:
        entry = redact_for_storage(entry)
        premium = entry.get("annual_premium")
        if premium is None and entry.get("monthly_premium") is not None:
            premium = f"${entry['monthly_premium']}/mo"
        lines.append(
            f"| {entry.get('brand_or_program', entry['registry_id'])} "
            f"| {entry.get('distribution_type', 'n/a')} "
            f"| **{entry.get('status', 'n/a')}** "
            f"| {premium if premium is not None else 'n/a'} "
            f"| {format_evidence_link(entry)} "
            f"| {entry.get('evidence_timestamp', 'n/a')} |"
        )

    lines.append("\n## Discovery-Stage Seed Entries: Not Yet Attempted")
    lines.append(
        "\nThese entries are seeded from the brief's Appendix A regulatory "
        "dataset for market-mapping purposes. **No live attempt has been "
        "made against any of these.** They are discovery leads, not "
        "results, and are excluded from the evidence-backed completion "
        "count above.\n"
    )
    lines.append("| Route | Channel | Legal Underwriter | Notes |")
    lines.append("|---|---|---|---|")
    for entry in seed_only:
        notes = sanitize_display_text(entry.get("automation_notes", "") or "")[:150].replace("|", "/")
        lines.append(
            f"| {entry.get('brand_or_program', entry['registry_id'])} "
            f"| {entry.get('distribution_type', 'n/a')} "
            f"| {entry.get('legal_underwriter', 'n/a')} "
            f"| {notes} |"
        )

    lines.append("\n## Gaps and unresolved (live-tested only)\n")
    unresolved = [
        e for e in live_tested
        if e.get("status") in (
            "unresolved", "unreachable", "blocked", "manual_handoff", "callback_required"
        )
    ]
    if unresolved:
        for entry in unresolved:
            entry = redact_for_storage(entry)
            reason = sanitize_display_text(
                entry.get("failure_reason") or entry.get("next_action") or "no reason logged"
            )
            lines.append(
                f"- **{entry.get('brand_or_program', entry['registry_id'])}**: "
                f"{entry.get('status')}: {reason}"
            )
    else:
        lines.append("None. All live-tested routes reached a quoted or estimate outcome.")

    lines.append("\n## Errors\n")
    errors = [e for e in live_tested if e.get("status") == "unreachable"]
    if errors:
        for entry in errors:
            entry = redact_for_storage(entry)
            lines.append(
                f"- {entry.get('registry_id')}: {sanitize_display_text(entry.get('failure_reason'))}"
            )
    else:
        lines.append("No unhandled errors recorded.")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Report regenerated: {len(live_tested)} live-tested, "
        f"{len(seed_only)} seed-only -> {OUTPUT_PATH}"
    )
    return OUTPUT_PATH


def generate():
    return generate_report()


if __name__ == "__main__":
    generate_report()
