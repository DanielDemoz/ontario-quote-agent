# Run Report — Ontario All-Quote Agent

Generated: 2026-08-10T20:57:34.204472+00:00

## Coverage metrics

- **Verified Applicable Rate Sources**: 48
- **Results Produced**: 48
- **Market Completion**: 0.625
- **Comparable Quote Yield**: 0.0
- **Evidence Rate**: 0.625

## Coverage ledger

| Route | Channel | Status | Annual Premium | Confidence | Evidence Timestamp |
|---|---|---|---|---|---|
| Sonnet | direct | unresolved | None | low | 2026-08-09T15:29:08.907142+00:00 |
| belairdirect | direct | unresolved | None | low | 2026-08-09T16:03:15.881556+00:00 |
| LowestRates.ca | aggregator | blocked | None | low | 2026-08-09T15:41:44.190122+00:00 |
| ThinkInsure | broker | callback_required | None | low | 2026-08-09T17:21:45.723837+00:00 |
| CAA Insurance | affinity | unresolved | None | low | 2026-08-09T17:23:09.503451+00:00 |
| Facility Association | residual | manual_handoff | None | low |  |
| Rates.ca | aggregator | unresolved | None | low |  |
| Surex | broker | unresolved | None | low |  |
| Onlia | broker | unresolved | None | low |  |
| Allstate | direct | unresolved | None | low |  |
| Pafco | broker | manual_handoff | None | low |  |
| Aviva Direct | direct | unresolved | None | low | 2026-08-10T20:52:45.646556+00:00 |
| RBC Insurance | affinity | unresolved | None | low |  |
| Co-operators | direct | unresolved | None | low |  |
| Duuo by Co-operators | direct | unresolved | None | low | 2026-08-10T20:52:29.350831+00:00 |
| Desjardins Insurance | direct | unresolved | None | low |  |
| The Personal | affinity | unresolved | None | low |  |
| TD Insurance | direct | unresolved | None | low | 2026-08-10T20:56:22.495235+00:00 |
| Square One Insurance | direct | manual_handoff | None | low | 2026-08-10T20:52:06.911907+00:00 |
| Definity / Economical broker | broker | manual_handoff | None | low |  |
| Economical | broker | manual_handoff | None | low |  |
| Intact Insurance | broker | manual_handoff | None | low |  |
| Jevco | broker | manual_handoff | None | low |  |
| Echelon | broker | manual_handoff | None | low |  |
| Wawanesa | mutual | unresolved | None | low |  |
| Gore Mutual | broker | manual_handoff | None | low |  |
| Travelers | broker | manual_handoff | None | low |  |
| Coachman | broker | manual_handoff | None | low |  |
| SGI Canada | broker | manual_handoff | None | low |  |
| Northbridge | broker | manual_handoff | None | low |  |
| Zenith | broker | manual_handoff | None | low |  |
| Pembridge | broker | manual_handoff | None | low |  |
| Beneva / Unica | broker | manual_handoff | None | low |  |
| Optimum | broker | manual_handoff | None | low |  |
| Portage Mutual | broker | manual_handoff | None | low |  |
| Commonwell Mutual | mutual | manual_handoff | None | low |  |
| Heartland Farm Mutual | mutual | manual_handoff | None | low |  |
| Peel Mutual | mutual | manual_handoff | None | low |  |
| Ontario Mutuals | mutual | manual_handoff | None | low |  |
| AIG | broker | specialty_only | None | low |  |
| Chubb | broker | specialty_only | None | low |  |
| PURE | broker | specialty_only | None | low |  |
| Continental | broker | specialty_only | None | low |  |
| Hartford | broker | specialty_only | None | low |  |
| Liberty Mutual | broker | specialty_only | None | low |  |
| Sompo | broker | specialty_only | None | low |  |
| Tokio Marine | broker | specialty_only | None | low |  |
| XL Specialty | broker | specialty_only | None | low |  |

## Gaps and unresolved routes

- **Sonnet**: unresolved — Custom (non-native) dropdown component on province-selection screen could not be reliably driven within the build window.
- **belairdirect**: unresolved — Reached step 1 of 3 vehicle form after homepage redirect recovery; did not complete within step budget.
- **LowestRates.ca**: blocked — Active bot-detection block: "Sorry, you have been blocked. You are unable to access lowestrates.ca."
- **ThinkInsure**: callback_required — Broker lead-capture intake requires full name, email, and phone; footer states final pricing requires registered broker phone completion. reCAPTCHA present on submit step. No instant self-serve premium.
- **CAA Insurance**: unresolved — Reached CAA South Central Ontario step-1 Vehicle Details; garaging address required. Membership number not requested on this screen. Could not advance in estimate_only mode without address.
- **Facility Association**: manual_handoff — Residual market has no direct automatable path by design.
- **Rates.ca**: unresolved — Broad broker engine B per brief Section 4. Describes insurer API and industry-rater connectivity. Not yet attempted live; treat returned legal underwriter separately from aggregator brand.
- **Surex**: unresolved — Broad licensed brokerage per brief Section 4. Compensation disclosure names Aviva, Intact, Jevco, Wawanesa, CAA, Coachman, Definity/Economical, Gore, Pafco, Pembridge, SGI, Travelers. Not yet attempted live.
- **Onlia**: unresolved — Digital brokerage with multiple carriers per brief Section 4. Capture actual returned underwriter, not brokerage brand. Not yet attempted live.
- **Allstate**: unresolved — Appendix A Allstate group. Legal entities: Allstate Insurance Company of Canada; Esurance Insurance Company of Canada; Pafco Insurance Company; Pembridge Insurance Company. Starting route: Allstate direct/agent. Pafco and Pembridge are broker/non-standard paths — separate registry entries. Not yet attempted live.
- **Pafco**: manual_handoff — Appendix A Allstate group — Pafco non-standard PPA via licensed broker only. No direct consumer quote URL seeded. Validate Esurance entity separately if profile fits.
- **Aviva Direct**: unresolved — Stuck on entry gate: language/province modal (English/Ontario) and cookie-consent banner both visible; did not reach embedded postal-code quote field within step budget.
- **RBC Insurance**: unresolved — Appendix A Aviva group — RBC affinity route with Aviva underwriting disclosure per brief. Capture returned legal underwriter on quote page. Not yet attempted live.
- **Co-operators**: unresolved — Appendix A Co-op group. Legal entities: COSECO Insurance Company; CUMIS General Insurance Company; Co-operators General Insurance Company; The Sovereign General Insurance Company. Starting route: Co-operators web/agent. Affinity and specialty entities need validation. Not yet attempted live.
- **Duuo by Co-operators**: unresolved — Launch URL redirected to Duuo auto SPA welcome screen with Start your quote CTA; agent did not click through to driver/vehicle form within step budget.
- **Desjardins Insurance**: unresolved — Appendix A Desjardins group. Legal entities: Certas Direct Insurance Company; Certas Home and Auto Insurance Company; The Personal Insurance Company. Desjardins web/agent route. The Personal is separate affinity entry. Not yet attempted live.
- **The Personal**: unresolved — Appendix A Desjardins group — The Personal group/employer affinity route per brief citation [18]. Membership or group eligibility may restrict access. Not yet attempted live.
- **TD Insurance**: unresolved — Reached step 1/3 (Your vehicle) with Manual Input selected and native Vehicle year dropdown visible; run ended with transient browser crash before year could be filled.
- **Square One Insurance**: manual_handoff — Guardrail stopped on cookie/legal page text containing 'declaration' before CONFIRM or CAR QUOTE could be clicked; never entered 4-step quote flow.
- **Definity / Economical broker**: manual_handoff — Appendix A Definity group — Definity/Economical broker route distinct from Sonnet direct (definity-sonnet). Legal entities: Definity Insurance Company; Sonnet Insurance Company. Map current legal entity/program at quote time. Not yet attempted live.
- **Economical**: manual_handoff — Appendix A Economical group — broker route; map current legal entity/program. May overlap Definity group post-amalgamation — dedupe by returned underwriter. Not yet attempted live.
- **Intact Insurance**: manual_handoff — Appendix A Intact group — Intact broker route distinct from belairdirect direct. Legal entities include Intact Insurance Company; Jevco; Novex; Unifund; Western Assurance; Royal & SunAlliance; The Guarantee Company of North America. Validate legacy/affinity entities. Not yet attempted live.
- **Jevco**: manual_handoff — Appendix A Intact group — Jevco non-standard PPA via licensed broker when profile fits. Not yet attempted live.
- **Echelon**: manual_handoff — Appendix A CAA group — Echelon broker and non-standard route distinct from CAA direct affinity. Not yet attempted live.
- **Wawanesa**: unresolved — Appendix A Wawanesa group — broker route primary per brief; public web quote path seeded for discovery. Not yet attempted live.
- **Gore Mutual**: manual_handoff — Appendix A Gore group — broker route. Named on LowestRates panel. Not yet attempted live.
- **Travelers**: manual_handoff — Appendix A Travelers group — broker route. Named on LowestRates panel. Not yet attempted live.
- **Coachman**: manual_handoff — Appendix A SGI group. Legal entities: Coachman Insurance Company; SGI CANADA Insurance Services Ltd. Coachman non-standard via broker. Not yet attempted live.
- **SGI Canada**: manual_handoff — Appendix A SGI group — standard PPA broker route distinct from Coachman non-standard. Not yet attempted live.
- **Northbridge**: manual_handoff — Appendix A Northbridge group. Legal entities: Federated Insurance Company of Canada; Northbridge General Insurance Corporation; Verassure Insurance Company; Zenith Insurance Company. Zenith named on LowestRates panel. Validate Federated/Verassure scope. Not yet attempted live.
- **Zenith**: manual_handoff — Appendix A Northbridge group — Zenith broker route; distinct rate source from Northbridge General if panel returns separately. Not yet attempted live.
- **Pembridge**: manual_handoff — Appendix A Allstate group — Pembridge broker/non-standard route. Named on LowestRates panel. Not yet attempted live.
- **Beneva / Unica**: manual_handoff — Appendix A Beneva group — broker route only. Not yet attempted live.
- **Optimum**: manual_handoff — Appendix A Optimum group — broker route. Not yet attempted live.
- **Portage Mutual**: manual_handoff — Appendix A Portage group — broker route. Not yet attempted live.
- **Commonwell Mutual**: manual_handoff — Appendix A Commonwell group — mutual and broker/agent route. Validate Ontario PPA availability and territory. Not yet attempted live.
- **Heartland Farm Mutual**: manual_handoff — Appendix A Heartland group — mutual/local agent or broker route. Not yet attempted live.
- **Peel Mutual**: manual_handoff — Appendix A Peel group — mutual/local agent or broker route. Not yet attempted live.
- **Ontario Mutuals**: manual_handoff — Appendix A FMRe group — Ontario Mutuals locator and specific mutual validation per brief citation [12]. Not yet attempted live.

## Errors

No unhandled errors recorded.