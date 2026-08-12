"""
Single source of truth for coverage metrics. Both app.py (dashboard
cards) and generate_run_report.py MUST import and call this - do not
let either file compute its own version, that's what caused the
dashboard and report to show contradictory numbers on the same page.
"""


def is_evidence_backed(result: dict, registry_by_id: dict) -> bool:
    """A result counts as evidence-backed only if it has a real
    evidence timestamp, OR it's a manual_handoff whose registry notes
    EXPLICITLY confirm no automatable path exists by design (the
    Facility Association case) - never just because quote_url happens
    to be empty, since that can also mean 'nobody has researched this
    URL yet', which is a completely different, unverified situation."""
    if result.get("evidence_timestamp"):
        return True
    if result.get("status") == "manual_handoff":
        reg_entry = registry_by_id.get(result.get("registry_id"), {})
        notes = (reg_entry.get("automation_notes", "") or "").lower()
        genuinely_no_path = (
            "no automatable path" in notes
            or ("no direct" in notes and "path exists" in notes)
        )
        never_attempted = "not yet attempted" in notes
        return genuinely_no_path and not never_attempted
    return False


def compute_metrics(registry: list, results: list) -> dict:
    registry_by_id = {r["registry_id"]: r for r in registry}
    total = len(results)
    backed = sum(1 for r in results if is_evidence_backed(r, registry_by_id))
    comparable = sum(1 for r in results if r.get("status") == "quoted_comparable")

    return {
        "verified_applicable_rate_sources": total,
        "results_produced": total,
        "market_completion": round(backed / total, 3) if total else 0,
        "comparable_quote_yield": round(comparable / total, 3) if total else 0,
        "evidence_rate": round(backed / total, 3) if total else 0,
    }


def split_live_tested_vs_seed(registry: list, results: list) -> tuple:
    """Same live-tested vs discovery-stage split used in the run
    report — also centralized here so app.py's dashboard view uses
    the identical split, not its own separately-written logic."""
    registry_by_id = {r["registry_id"]: r for r in registry}
    results_by_id = {r["registry_id"]: r for r in results}
    live_tested, seed_only = [], []

    for reg in registry:
        rid = reg["registry_id"]
        res = results_by_id.get(rid, {})
        entry = {**reg, **res}
        if is_evidence_backed(res, registry_by_id) or is_evidence_backed(reg, registry_by_id):
            live_tested.append(entry)
        else:
            seed_only.append(entry)

    return live_tested, seed_only
