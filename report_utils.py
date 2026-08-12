"""
Shared logic for splitting registry entries into live-tested evidence
vs discovery-stage seed-only leads. Used by generate_run_report.py and
the Binder Streamlit Results tab.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
REGISTRY_PATH = ROOT / "registry" / "seed_registry.json"
RESULTS_PATH = ROOT / "results" / "results.json"


def load_registry_and_results(
    registry_path: Path | None = None,
    results_path: Path | None = None,
) -> tuple[list[dict], list[dict]]:
    registry_path = registry_path or REGISTRY_PATH
    results_path = results_path or RESULTS_PATH
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
    if not results_path.exists():
        return registry, []
    with open(results_path, encoding="utf-8") as f:
        results = json.load(f)
    return registry, results


def _genuinely_no_path(notes: str) -> bool:
    lower = (notes or "").lower()
    return "no automatable path" in lower or "no direct quote path" in lower


def _never_attempted(notes: str) -> bool:
    return "not yet attempted live" in (notes or "").lower()


def classify_routes(
    registry: list[dict],
    results: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Return (live_tested, seed_only) merged registry+result entries."""
    from metrics_utils import split_live_tested_vs_seed
    return split_live_tested_vs_seed(registry, results)


def format_evidence_link(entry: dict) -> str:
    """Human-readable evidence reference for tables and reports."""
    path = (entry.get("evidence_artifact_path") or entry.get("evidence_url") or "").strip()
    if path:
        p = Path(path)
        try:
            rel = p.relative_to(ROOT)
            return str(rel).replace("\\", "/")
        except ValueError:
            return str(p).replace("\\", "/")

    notes = entry.get("automation_notes", "") or ""
    if entry.get("status") == "manual_handoff" and _genuinely_no_path(notes):
        return "documented rationale (no live path exists)"

    if entry.get("failure_reason") or entry.get("next_action"):
        return "see outcome notes in dashboard"

    return "n/a"
