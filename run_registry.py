"""
Orchestrator. Loads the market registry, runs each route through the
browser agent or voice agent, writes normalized results, and computes
coverage metrics.

Run:
  python run_registry.py
  python run_registry.py --scope full --live-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from schema import MarketRecord, Applicant, Status, QuoteResult
from browser_agent import run_route
from guardrails import validate_applicant_for_mode
from voice_agent import run_voice_route, should_use_voice_route

REGISTRY_DIR = Path(__file__).parent / "registry"
SEED_PATH = REGISTRY_DIR / "seed_registry.json"
FULL_PATH = REGISTRY_DIR / "full_registry.json"
RESULTS_PATH = Path(__file__).parent / "results" / "results.json"

ROUTE_TIMEOUT_SECONDS = 120  # hard cutoff per route


async def run_route_isolated(record: MarketRecord, applicant: Applicant) -> QuoteResult:
    """Run one route with a hard timeout and full exception isolation."""
    try:
        result = await asyncio.wait_for(
            run_route(record, applicant),
            timeout=ROUTE_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        print(f"[{record.registry_id}] TIMED OUT after {ROUTE_TIMEOUT_SECONDS}s. Logging as unreachable.")
        return QuoteResult(
            registry_id=record.registry_id,
            distinct_rate_source_id=record.distinct_rate_source_id,
            status=Status.UNREACHABLE,
            failure_reason=f"Route did not complete within {ROUTE_TIMEOUT_SECONDS}s hard timeout.",
            next_action="Investigate whether this route needs a longer timeout or has a stuck step.",
            evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        print(f"[{record.registry_id}] CRASHED: {type(e).__name__}: {e}")
        return QuoteResult(
            registry_id=record.registry_id,
            distinct_rate_source_id=record.distinct_rate_source_id,
            status=Status.UNREACHABLE,
            failure_reason=f"Unhandled error: {type(e).__name__}: {e}",
            next_action="Fix the specific error before re-attempting this route.",
            evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        )


def load_registry(scope: str = "seed") -> list[MarketRecord]:
    if scope == "full":
        if not FULL_PATH.exists():
            from build_registry import main as build_main
            import sys
            sys.argv = ["build_registry.py", "--merge"]
            build_main()
        path = FULL_PATH
    else:
        path = SEED_PATH

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [MarketRecord(**r) for r in raw]


def build_applicant() -> Applicant:
    from intake_config import build_applicant as _build
    return _build()


async def run_one(record: MarketRecord, applicant: Applicant, retry: bool = True) -> QuoteResult:
    if should_use_voice_route(record):
        return run_voice_route(record, applicant)

    result = await run_route_isolated(record, applicant)
    if retry and result.status == Status.UNREACHABLE:
        print(f"[{record.registry_id}] unreachable. One bounded retry.")
        result = await run_route_isolated(record, applicant)
    return result


async def run_all(scope: str = "seed", live_only: bool = False, limit: int | None = None):
    registry = load_registry(scope)
    if live_only:
        registry = [r for r in registry if r.quote_url.strip()]
    if limit:
        registry = registry[:limit]

    applicant = build_applicant()
    validate_applicant_for_mode(applicant)

    results = []
    seen_rate_sources = set()

    for record in registry:
        if record.distinct_rate_source_id in seen_rate_sources:
            print(f"[{record.registry_id}] duplicate rate source, skipping live attempt")
            results.append({
                "registry_id": record.registry_id,
                "distinct_rate_source_id": record.distinct_rate_source_id,
                "status": Status.DUPLICATE_RATE_SOURCE.value,
                "failure_reason": "Rate source already resolved via another brand/route.",
                "next_action": "See primary route result.",
            })
            continue

        print(f"[{record.registry_id}] running route: {record.brand_or_program} ...")
        result = await run_one(record, applicant)
        results.append(asdict(result))
        seen_rate_sources.add(record.distinct_rate_source_id)
        print(f"[{record.registry_id}] -> {result.status}")

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    metrics = compute_metrics(registry, results)
    print("\n--- Coverage metrics ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    metrics_path = Path(__file__).parent / "results" / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


def compute_metrics(registry: list[MarketRecord], results: list[dict]) -> dict:
    verified_applicable = len(registry)
    evidence_backed = sum(
        1 for r in results
        if r.get("evidence_timestamp") or r.get("status") in ("manual_handoff", "callback_required")
    )
    comparable = sum(1 for r in results if r.get("status") == "quoted_comparable")

    return {
        "verified_applicable_rate_sources": verified_applicable,
        "results_produced": len(results),
        "market_completion": round(evidence_backed / verified_applicable, 3) if verified_applicable else 0,
        "comparable_quote_yield": round(comparable / verified_applicable, 3) if verified_applicable else 0,
        "evidence_rate": round(evidence_backed / len(results), 3) if results else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["seed", "full"], default="seed")
    parser.add_argument("--live-only", action="store_true", help="Skip registry entries with no quote_url")
    parser.add_argument("--limit", type=int, default=None, help="Max routes to run (debug)")
    args = parser.parse_args()
    asyncio.run(run_all(scope=args.scope, live_only=args.live_only, limit=args.limit))


if __name__ == "__main__":
    main()
