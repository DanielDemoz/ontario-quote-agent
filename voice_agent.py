"""
Callback / phone-route handler for markets with no automatable web path.

When TWILIO_* credentials are configured, can initiate an outbound call
stub. Without Twilio, produces a RIBO-aware callback script and logs
callback_required with the phone route as evidence.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from schema import Applicant, MarketRecord, QuoteResult, Status, Confidence, DistributionType

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def build_callback_script(record: MarketRecord, applicant: Applicant) -> str:
    """Opening script aligned with the brief's suggested call pattern.
    Must disclose automation up front - this is non-negotiable per
    the brief's Section 2 voice-agent requirements."""
    name = applicant.legal_name or "the applicant"
    vehicle = " ".join(
        p for p in [applicant.model_year, applicant.make, applicant.model] if p
    ) or "their vehicle"
    try:
        liability = int(applicant.liability_limit)
    except (TypeError, ValueError):
        liability = 2_000_000
    return (
        f"Hello, I am an automated assistant acting for {name} to request an "
        f"Ontario private-passenger auto insurance quote. Is it okay to "
        f"continue with an automated assistant? The applicant is available "
        f"if you need verification or consent. "
        f"I am looking for standard personal-use coverage for a {vehicle}, "
        f"comparable to ${liability:,} liability, "
        f"DCPD included, collision/comprehensive "
        f"${applicant.collision_deductible} deductibles"
        f"{', with OPCF 44R' if applicant.opcf_44r else ''}. "
        f"Could you provide a quote or reference number I can document? "
        f"I am not authorizing bind or payment on this call."
    )


def prepare_callback(record: MarketRecord, applicant: Applicant) -> QuoteResult:
    """
    Handle phone-only or requires_human routes without fabricating a web quote.
    """
    phone = (record.public_phone_route or "").strip()
    script = build_callback_script(record, applicant)

    result = QuoteResult(
        registry_id=record.registry_id,
        distinct_rate_source_id=record.distinct_rate_source_id,
        status=Status.CALLBACK_REQUIRED,
        confidence=Confidence.LOW,
        coverage_notes=f"Callback script prepared. Phone route: {phone or 'see registry'}.",
        failure_reason=record.automation_notes or "No automatable web quote path.",
        next_action="Place outbound call using script in logs; document quote reference if obtained.",
        evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        source_url=phone or record.quote_url,
    )

    log_path = LOGS_DIR / f"{record.registry_id}_callback.jsonl"
    entry = {
        "timestamp": result.evidence_timestamp,
        "registry_id": record.registry_id,
        "phone_route": phone,
        "script": script,
        "status": result.status.value,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return result


def maybe_place_call(record: MarketRecord, applicant: Applicant) -> QuoteResult | None:
    """
    Optional Twilio integration. Returns None if Twilio is not configured,
    letting the caller fall back to prepare_callback().
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    to_number = (record.public_phone_route or os.environ.get("TWILIO_CALLBACK_TO", "")).strip()

    if not all([account_sid, auth_token, from_number, to_number]):
        return None

    try:
        from twilio.rest import Client  # optional dependency
    except ImportError:
        return None

    script = build_callback_script(record, applicant)
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=f'<Response><Say voice="alice">{script[:1200]}</Say></Response>',
    )

    result = QuoteResult(
        registry_id=record.registry_id,
        distinct_rate_source_id=record.distinct_rate_source_id,
        status=Status.CALLBACK_REQUIRED,
        confidence=Confidence.LOW,
        quote_or_reference_id=call.sid,
        coverage_notes="Twilio outbound call initiated; human must complete quote on line.",
        evidence_timestamp=datetime.now(timezone.utc).isoformat(),
        source_url=to_number,
        next_action="Monitor call outcome and update result with premium if obtained.",
    )
    return result


def run_voice_route(record: MarketRecord, applicant: Applicant) -> QuoteResult:
    """Entry point: Twilio if configured, otherwise script + callback_required."""
    twilio_result = maybe_place_call(record, applicant)
    if twilio_result:
        return twilio_result
    return prepare_callback(record, applicant)


def should_use_voice_route(record: MarketRecord) -> bool:
    """True for phone-first routes; residual/manual_handoff stay out of voice."""
    if record.distribution_type == DistributionType.RESIDUAL:
        return False
    if not record.quote_url and record.status == Status.MANUAL_HANDOFF:
        return False
    if record.public_phone_route and not record.quote_url:
        return True
    if record.requires_human and not record.quote_url:
        return True
    return False
