"""
Orchestrator. Loads the market registry, runs each route through the
browser agent, writes normalized results, and computes the coverage
metrics defined in Section 7 of the brief.

Run: python run_registry.py
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from schema import MarketRecord, Applicant, Status, QuoteResult
from browser_agent import run_route
from guardrails import validate_applicant_for_mode

REGISTRY_PATH = Path(__file__).parent / "registry" / "seed_registry.json"
RESULTS_PATH = Path(__file__).parent / "results" / "results.json"

ROUTE_TIMEOUT_SECONDS = 120  # hard cutoff per route


async def run_route_isolated(record: MarketRecord, applicant: Applicant) -> QuoteResult:
    """Run one route with a hard timeout and full exception isolation.
    A crash or hang in this route must never propagate and must never
    block subsequent routes from running."""
    try:
        result = await asyncio.wait_for(
            run_route(record, applicant),
            timeout=ROUTE_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        print(f"[{record.registry_id}] TIMED OUT after {ROUTE_TIMEOUT_SECONDS}s — logging as unreachable")
        return QuoteResult(
            registry_id=record.registry_id,
            distinct_rate_source_id=record.distinct_rate_source_id,
            status=Status.UNREACHABLE,
            failure_reason=f"Route did not complete within {ROUTE_TIMEOUT_SECONDS}s hard timeout — likely a hang, not a normal stop.",
            next_action="Investigate whether this route needs a longer timeout or has a specific stuck step to fix.",
            evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        print(f"[{record.registry_id}] CRASHED: {type(e).__name__}: {e} — logging as unreachable, continuing to next route")
        return QuoteResult(
            registry_id=record.registry_id,
            distinct_rate_source_id=record.distinct_rate_source_id,
            status=Status.UNREACHABLE,
            failure_reason=f"Unhandled error: {type(e).__name__}: {e}",
            next_action="Fix the specific error before re-attempting this route.",
            evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        )


def load_registry() -> list[MarketRecord]:
    with open(REGISTRY_PATH) as f:
        raw = json.load(f)
    return [MarketRecord(**r) for r in raw]


def build_applicant() -> Applicant:
    # TODO at event: fill in your real or hypothetical profile here,
    # or load from a separate untracked config file (see intake_config.py).
    from intake_config import build_applicant as _build
    return _build()


async def run_all():
    registry = load_registry()
    applicant = build_applicant()
    validate_applicant_for_mode(applicant)

    results = []
    seen_rate_sources = set()

    for record in registry:
        # Deduplication: if we've already resolved this distinct rate
        # source through another brand/route, mark it duplicate instead
        # of re-running.
        if record.distinct_rate_source_id in seen_rate_sources:
            print(f"[{record.registry_id}] duplicate rate source, skipping live attempt")
            continue

        print(f"[{record.registry_id}] running route: {record.brand_or_program} ...")
        result = await run_route_isolated(record, applicant)
        results.append(asdict(result))
        seen_rate_sources.add(record.distinct_rate_source_id)
        print(f"[{record.registry_id}] -> {result.status}")

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)

    metrics = compute_metrics(registry, results)
    print("\n--- Coverage metrics ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    with open(Path(__file__).parent / "results" / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


def compute_metrics(registry: list[MarketRecord], results: list[dict]) -> dict:
    verified_applicable = len(registry)
    evidence_backed = sum(1 for r in results if r.get("evidence_timestamp") or r.get("status") == "manual_handoff")
    comparable = sum(1 for r in results if r.get("status") == "quoted_comparable")

    return {
        "verified_applicable_rate_sources": verified_applicable,
        "results_produced": len(results),
        "market_completion": round(evidence_backed / verified_applicable, 3) if verified_applicable else 0,
        "comparable_quote_yield": round(comparable / verified_applicable, 3) if verified_applicable else 0,
        "evidence_rate": round(evidence_backed / len(results), 3) if results else 0,
    }


if __name__ == "__main__":
    asyncio.run(run_all())
