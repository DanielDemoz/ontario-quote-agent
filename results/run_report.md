# Run Report — Ontario All-Quote Agent

Generated: 2026-08-10T21:08:43.773137+00:00

## Coverage metrics

- **Verified Applicable Rate Sources**: 48
- **Results Produced**: 48
- **Market Completion**: 0.562
- **Comparable Quote Yield**: 0.0
- **Evidence Rate**: 0.562

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
| Aviva Direct | direct | unresolved | None | low |  |
| RBC Insurance | affinity | unresolved | None | low |  |
| Co-operators | direct | unresolved | None | low |  |
| Duuo by Co-operators | direct | unresolved | None | low |  |
| Desjardins Insurance | direct | unresolved | None | low |  |
| The Personal | affinity | unresolved | None | low |  |
| TD Insurance | direct | unresolved | None | low |  |
| Square One Insurance | direct | manual_handoff | None | low |  |
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
- **Aviva Direct**: unresolved — Appendix A Aviva group. Legal entities: Aviva General Insurance Company; Aviva Insurance Company of Canada; S&Y Insurance Company; Scottish & York Insurance Co. Limited; Traders General Insurance Company. Starting route: Aviva Direct. Deduplicate legacy entities against broker/RBC returns when live. Not yet attempted live. Entry point has an embedded postal code field, not a separate quote-start page. Confirmed required fields upfront: driver name(s), DOB, licence class + G1/G2/G dates, driving history; vehicle year/make/model, owner details, purchase/lease date, use type. Hard limit: max 2 vehicles/2 drivers online. A language/province selection gate appears on entry — same pattern as Sonnet's province modal, handle with existing find_dropdown_trigger/find_homepage_cta logic. LIVE (2026-08-10): Stuck on language/province modal + cookie banner; postal-code field not reached.
- **RBC Insurance**: unresolved — Appendix A Aviva group — RBC affinity route with Aviva underwriting disclosure per brief. Capture returned legal underwriter on quote page. Not yet attempted live.
- **Co-operators**: unresolved — Appendix A Co-op group. Legal entities: COSECO Insurance Company; CUMIS General Insurance Company; Co-operators General Insurance Company; The Sovereign General Insurance Company. Starting route: Co-operators web/agent. Affinity and specialty entities need validation. Not yet attempted live. Main cooperators.ca site is agent-network-first ('connect with a financial representative'), not a confirmed self-serve instant-quote flow. Prefer the separate Duuo (duuo-cooperators-001) entry for a genuine direct online attempt.
- **Duuo by Co-operators**: unresolved — Confirmed live: Duuo offers real self-serve online auto insurance purchase in Ontario (explicitly listed as an eligible province), underwritten by Co-operators General Insurance Company. This is a genuinely direct digital flow, distinct from the parent cooperators.ca site which is agent-network-first. Not yet attempted live. LIVE (2026-08-10): Reached Duuo welcome SPA; stalled on Start your quote CTA.
- **Desjardins Insurance**: unresolved — Appendix A Desjardins group. Legal entities: Certas Direct Insurance Company; Certas Home and Auto Insurance Company; The Personal Insurance Company. Desjardins web/agent route. The Personal is separate affinity entry. Not yet attempted live.
- **The Personal**: unresolved — Appendix A Desjardins group — The Personal group/employer affinity route per brief citation [18]. Membership or group eligibility may restrict access. Not yet attempted live.
- **TD Insurance**: unresolved — Appendix A TD group. Legal entities: Primmum Insurance Company; Security National Insurance Company; TD General Insurance Company. TD online, phone and affinity routes per brief. Not yet attempted live. Confirmed 3-step flow disclosed directly on the page: (1) Your vehicle, (2) Savings, (3) Driver details. Offers a VIN-prefill option as an alternative to manual vehicle entry — if VIN is available in the applicant profile, try the VIN path first as it may reduce the number of fields needed. Vehicle year field appears to be a genuine native HTML dropdown (explicit year list visible in page content), which is good news — try native select_option() before falling back to custom-dropdown handling. LIVE (2026-08-10): Reached step 1/3 vehicle year dropdown; browser closed before fill completed.
- **Square One Insurance**: manual_handoff — Appendix A Zurich group. Square One direct for Ontario car per brief citation [8]. Specialty Zurich broker routes may differ — validate underwriter on returned quote. Not yet attempted live. Confirmed 4-step flow per live page content: (1) drivers, (2) vehicle, (3) limits/deductibles/coverage, (4) premium. Cookie-consent modal appears on entry, similar pattern to Sonnet's — handle via existing find_homepage_cta or a dedicated cookie-consent click. Legal underwriter confirmed as Zurich Insurance Company Ltd (Canadian Branch) for Ontario auto — matches existing registry insurer_group 'Zurich'. LIVE (2026-08-10): Guardrail stopped on cookie/legal page containing declaration before CONFIRM or CAR QUOTE; never entered quote flow.
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