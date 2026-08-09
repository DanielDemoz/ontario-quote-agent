# Run Report — Ontario All-Quote Agent

Generated: 2026-08-09T17:24:56.136997+00:00

## Coverage metrics

- **Verified Applicable Rate Sources**: 6
- **Results Produced**: 6
- **Market Completion**: 1.0
- **Comparable Quote Yield**: 0.0
- **Evidence Rate**: 1.0

## Coverage ledger

| Route | Channel | Status | Annual Premium | Confidence | Evidence Timestamp |
|---|---|---|---|---|---|
| Sonnet | direct | unresolved | None | low | 2026-08-09T15:29:08.907142+00:00 |
| LowestRates.ca | aggregator | blocked | None | low | 2026-08-09T15:41:44.190122+00:00 |
| belairdirect | direct | unresolved | None | low | 2026-08-09T16:03:15.881556+00:00 |
| ThinkInsure | broker | callback_required | None | low | 2026-08-09T17:21:45.723837+00:00 |
| CAA Insurance | affinity | unresolved | None | low | 2026-08-09T17:23:09.503451+00:00 |
| Facility Association | residual | manual_handoff | None | low |  |

## Gaps and unresolved routes

- **Sonnet**: unresolved — Custom (non-native) dropdown component on province-selection screen could not be reliably driven within the build window.
- **LowestRates.ca**: blocked — Active bot-detection block: "Sorry, you have been blocked. You are unable to access lowestrates.ca."
- **belairdirect**: unresolved — 
- **ThinkInsure**: callback_required — Broker lead-capture intake requires full name, email, and phone; footer states final pricing requires registered broker phone completion. reCAPTCHA present on submit step. No instant self-serve premium.
- **CAA Insurance**: unresolved — Reached CAA South Central Ontario step-1 Vehicle Details; garaging address required. Membership number not requested on this screen. Could not advance in estimate_only mode without address.
- **Facility Association**: manual_handoff — Residual market has no direct automatable path by design.

## Errors

No unhandled errors recorded.