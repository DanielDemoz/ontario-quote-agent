# Architecture and Safety Note

## System overview

The system follows the recommended flow from the brief: consent-aware
intake, a market registry, route agents, an evidence store, a
normalizer, and a coverage ledger with comparison.

Scope for this build: six market routes chosen to cover direct,
aggregator, broker, affinity, and residual channels, rather than
attempting all sixty entities in the regulator's seed dataset. The
brief states explicitly that a smaller set of trustworthy,
evidence-backed results is stronger than a large set of duplicated or
unverifiable ones; this build follows that principle.

## Components

**Intake (`intake_config.py`, `schema.py`)**
A single `Applicant` object holds the profile. It runs in
`estimate_only` mode by default, which means no real licence number or
legal name is ever populated, and the system enforces this in code via
`validate_applicant_for_mode()` rather than relying on the operator to
remember.

**Market registry (`registry/seed_registry.json`)**
Six routes, each recording the distinction between legal underwriter,
insurer group, brand, distributor, and rate source, per the layering
the brief requires. One route (Facility Association, the residual
market) is recorded as `manual_handoff` by design, since no direct
automatable quote path exists for that market.

**Route agent (`browser_agent.py`)**
Rather than hardcoding CSS selectors per site, the agent extracts
every visible form field on the page, sends the field labels to Claude
to map them against the intake schema, and only fills fields with a
confident, non-sensitive match. Signature, payment, and identity
-verification-only fields are excluded from mapping by explicit
instruction to the model, and a hardcoded denylist provides a second
layer of protection independent of the model's judgment.

**Guardrails (`guardrails.py`)**
Every page load is checked against a pattern list for CAPTCHA/bot
-detection language, application declaration or signature language,
and payment/bind language, before any further automated action is
taken. A match raises an exception that stops the route immediately
and logs the correct terminal status (`blocked` or `manual_handoff`).
This check runs independently of whatever the form-mapping step
decided, so a mapping error cannot bypass it.

**Evidence store (`evidence/`, `logs/`)**
Screenshots are captured after masking any input whose name, id, or
placeholder matches a sensitive-field pattern (licence, VIN, date of
birth, postal code, address, phone, email). Log entries pass through
`redact_for_storage()` before being written to disk.

**Normalizer and comparison (`run_registry.py`, `app.py`)**
Results are deduplicated by `distinct_rate_source_id` so that the same
underlying rate source reached through two different brands is not
double-counted. The Streamlit app displays results sorted and
filterable by status, with evidence available per result.

## Quote normalization pipeline

Every route's output passes through the same explicit stages before
it can be compared against another route's result:

1. **Extraction** - raw form fields and page text captured from the
   live site (`extract_visible_fields()`, page text via
   `safe_inner_text()`).
2. **Mapping** - Claude maps each extracted field to the canonical
   intake schema (`map_fields_with_claude()`), never inventing a
   value not present in the applicant's confirmed profile.
3. **Normalization** - results are recorded against the common
   `QuoteResult` schema (`schema.py`), so every route's outcome uses
   identical field names and the same status enum, regardless of how
   differently each insurer's site is built.
4. **Comparison** - the Streamlit dashboard and run report read this
   normalized data uniformly, allowing routes to be filtered, sorted,
   and compared without any route-specific logic in the display
   layer.

This separation is what allows a new route to be added to the
registry and immediately participate in comparison, without needing
any change to the normalization or comparison code.

## Human checkpoints

Per the brief's required-behaviour table:

- Identity/database lookup: not reached in `estimate_only` mode, since
  no real identity data is present to submit.
- Application declaration: detected by `guardrails.py` and stops the
  route before any click.
- Coverage advice: the system presents returned coverage details; it
  does not recommend suitability.
- CAPTCHA/access restriction: detected and logged as `blocked`, never
  bypassed.
- Quote-to-purchase transition: detected as payment/bind language and
  stops the route.

## Consent and data handling

In `estimate_only` mode, no personal identifying information is
collected or transmitted, so no third-party consent question arises.
If a future run uses `live` mode with the participant's real
information, `validate_applicant_for_mode()` requires a
`consent_timestamp` to be set before any route executes.

## Known limitations

See `known_limitations.md`.
