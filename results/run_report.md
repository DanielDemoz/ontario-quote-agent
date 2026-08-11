# Run Report: Ontario All-Quote Agent (Binder)

Generated: 2026-08-11T23:49:27.215968+00:00

## Summary
- **Live-tested routes with real evidence:** 10
- **Discovery-stage seed entries (not yet attempted):** 38
- **Total registry entries:** 48
- **Evidence-backed completion (all results):** 0.562

## Live-Tested Routes: Real Evidence

Every row below reflects an actual attempt against a live site, with a timestamp and evidence artifact (or documented rationale when no live path exists).

| Route | Channel | Status | Premium | Evidence | Timestamp |
|---|---|---|---|---|---|
| Sonnet | direct | **unresolved** | n/a | evidence/sonnet-direct-001_final_20260809T152908850252Z.png | 2026-08-09T15:29:08.907142+00:00 |
| belairdirect | direct | **unresolved** | n/a | evidence/belairdirect-001_final_20260809T160315728573Z.png | 2026-08-09T16:03:15.881556+00:00 |
| LowestRates.ca | aggregator | **blocked** | n/a | evidence/lowestrates-agg-001_final_20260809T154144146884Z.png | 2026-08-09T15:41:44.190122+00:00 |
| ThinkInsure | broker | **callback_required** | n/a | evidence/thinkinsure-broker-001_final_20260809T172145645048Z.png | 2026-08-09T17:21:45.723837+00:00 |
| CAA Insurance | affinity | **unresolved** | n/a | evidence/caa-affinity-001_final_20260809T172309421847Z.png | 2026-08-09T17:23:09.503451+00:00 |
| Facility Association | residual | **manual_handoff** | n/a | documented rationale (no live path exists) |  |
| Aviva Direct | direct | **unresolved** | n/a | evidence/aviva-direct-002_final_20260810T205245477223Z.png |  |
| Duuo by Co-operators | direct | **unresolved** | n/a | evidence/duuo-cooperators-001_final_20260810T205229184544Z.png |  |
| TD Insurance | direct | **unresolved** | n/a | evidence/td-direct-002_step4_20260810T205619804284Z.png |  |
| Square One Insurance | direct | **manual_handoff** | n/a | evidence/squareone-direct-002_blocked_20260810T205206919255Z.png |  |

## Discovery-Stage Seed Entries: Not Yet Attempted

These entries are seeded from the brief's Appendix A regulatory dataset for market-mapping purposes. **No live attempt has been made against any of these.** They are discovery leads, not results, and are excluded from the evidence-backed completion count above.

| Route | Channel | Legal Underwriter | Notes |
|---|---|---|---|
| Rates.ca | aggregator | TBD - returned by panel | Broad broker engine B per brief Section 4. Describes insurer API and industry-rater connectivity. Not yet attempted live; treat returned legal underwr |
| Surex | broker | TBD - returned by broker panel | Broad licensed brokerage per brief Section 4. Compensation disclosure names Aviva, Intact, Jevco, Wawanesa, CAA, Coachman, Definity/Economical, Gore,  |
| Onlia | broker | TBD - returned by broker | Digital brokerage with multiple carriers per brief Section 4. Capture actual returned underwriter, not brokerage brand. Not yet attempted live. |
| Allstate | direct | Allstate Insurance Company of Canada | Appendix A Allstate group. Legal entities: Allstate Insurance Company of Canada; Esurance Insurance Company of Canada; Pafco Insurance Company; Pembri |
| Pafco | broker | Pafco Insurance Company | Appendix A Allstate group: Pafco non-standard PPA via licensed broker only. No direct consumer quote URL seeded. Validate Esurance entity separately i |
| RBC Insurance | affinity | Aviva Insurance Company of Canada | Appendix A Aviva group: RBC affinity route with Aviva underwriting disclosure per brief. Capture returned legal underwriter on quote page. Not yet att |
| Co-operators | direct | Co-operators General Insurance Company | Appendix A Co-op group. Legal entities: COSECO Insurance Company; CUMIS General Insurance Company; Co-operators General Insurance Company; The Soverei |
| Desjardins Insurance | direct | Certas Direct Insurance Company | Appendix A Desjardins group. Legal entities: Certas Direct Insurance Company; Certas Home and Auto Insurance Company; The Personal Insurance Company.  |
| The Personal | affinity | The Personal Insurance Company | Appendix A Desjardins group: The Personal group/employer affinity route per brief citation [18]. Membership or group eligibility may restrict access.  |
| Definity / Economical broker | broker | Definity Insurance Company | Appendix A Definity group: Definity/Economical broker route distinct from Sonnet direct (definity-sonnet). Legal entities: Definity Insurance Company; |
| Economical | broker | Economical Mutual Insurance Company | Appendix A Economical group: broker route; map current legal entity/program. May overlap Definity group post-amalgamation: dedupe by returned underwri |
| Intact Insurance | broker | Intact Insurance Company | Appendix A Intact group: Intact broker route distinct from belairdirect direct. Legal entities include Intact Insurance Company; Jevco; Novex; Unifund |
| Jevco | broker | Jevco Insurance Company | Appendix A Intact group: Jevco non-standard PPA via licensed broker when profile fits. Not yet attempted live. |
| Echelon | broker | Echelon Insurance | Appendix A CAA group: Echelon broker and non-standard route distinct from CAA direct affinity. Not yet attempted live. |
| Wawanesa | mutual | The Wawanesa Mutual Insurance Company | Appendix A Wawanesa group: broker route primary per brief; public web quote path seeded for discovery. Not yet attempted live. |
| Gore Mutual | broker | Gore Mutual Insurance Company | Appendix A Gore group: broker route. Named on LowestRates panel. Not yet attempted live. |
| Travelers | broker | The Dominion of Canada General Insurance Company | Appendix A Travelers group: broker route. Named on LowestRates panel. Not yet attempted live. |
| Coachman | broker | Coachman Insurance Company | Appendix A SGI group. Legal entities: Coachman Insurance Company; SGI CANADA Insurance Services Ltd. Coachman non-standard via broker. Not yet attempt |
| SGI Canada | broker | SGI CANADA Insurance Services Ltd. | Appendix A SGI group: standard PPA broker route distinct from Coachman non-standard. Not yet attempted live. |
| Northbridge | broker | Northbridge General Insurance Corporation | Appendix A Northbridge group. Legal entities: Federated Insurance Company of Canada; Northbridge General Insurance Corporation; Verassure Insurance Co |
| Zenith | broker | Zenith Insurance Company | Appendix A Northbridge group: Zenith broker route; distinct rate source from Northbridge General if panel returns separately. Not yet attempted live. |
| Pembridge | broker | Pembridge Insurance Company | Appendix A Allstate group: Pembridge broker/non-standard route. Named on LowestRates panel. Not yet attempted live. |
| Beneva / Unica | broker | Unica Insurance Inc. | Appendix A Beneva group: broker route only. Not yet attempted live. |
| Optimum | broker | Optimum Insurance Company Inc. | Appendix A Optimum group: broker route. Not yet attempted live. |
| Portage Mutual | broker | The Portage la Prairie Mutual Insurance Company | Appendix A Portage group: broker route. Not yet attempted live. |
| Commonwell Mutual | mutual | The Commonwell Mutual Insurance Group | Appendix A Commonwell group: mutual and broker/agent route. Validate Ontario PPA availability and territory. Not yet attempted live. |
| Heartland Farm Mutual | mutual | Heartland Farm Mutual Inc. | Appendix A Heartland group: mutual/local agent or broker route. Not yet attempted live. |
| Peel Mutual | mutual | Peel Mutual Insurance Company | Appendix A Peel group: mutual/local agent or broker route. Not yet attempted live. |
| Ontario Mutuals | mutual | Farm Mutual Reinsurance Plan Inc. | Appendix A FMRe group: Ontario Mutuals locator and specific mutual validation per brief citation [12]. Not yet attempted live. |
| AIG | broker | AIG Insurance Company of Canada | Appendix A AIG group: specialty/commercial broker; validate PPA relevance for standard private-passenger profile. Not yet attempted live. |
| Chubb | broker | Chubb Insurance Company of Canada | Appendix A Chubb group: high-net-worth or specialty broker route. Not yet attempted live. |
| PURE | broker | PURE Insurance | Appendix A PURE group: high-net-worth broker route. Not yet attempted live. |
| Continental | broker | Continental Casualty Company | Appendix A Continental group: specialty/commercial broker; validate PPA relevance. Not yet attempted live. |
| Hartford | broker | Hartford Fire Insurance Company | Appendix A Hartford group: specialty/commercial broker; validate PPA relevance. Not yet attempted live. |
| Liberty Mutual | broker | Liberty Mutual Insurance Company | Appendix A Liberty group: specialty/commercial broker; validate PPA relevance. Not yet attempted live. |
| Sompo | broker | Sompo Japan Insurance Inc. | Appendix A Sompo group. Legal entities: Endurance Specialty Insurance Ltd.; Sompo Japan Insurance Inc. Specialty/commercial broker; validate PPA relev |
| Tokio Marine | broker | Tokio Marine and Nichido Fire Insurance Company Limited | Appendix A Tokio group: specialty/commercial broker; validate PPA relevance. Not yet attempted live. |
| XL Specialty | broker | XL Specialty Insurance Company | Appendix A XL group: specialty/commercial broker; validate PPA relevance. Not yet attempted live. |

## Gaps and unresolved (live-tested only)

- **Sonnet**: unresolved: Custom (non-native) dropdown component on province-selection screen could not be reliably driven within the build window.
- **belairdirect**: unresolved: Reached step 1 of 3 vehicle form after homepage redirect recovery; did not complete within step budget.
- **LowestRates.ca**: blocked: Active bot-detection block: "Sorry, you have been blocked. You are unable to access lowestrates.ca."
- **ThinkInsure**: callback_required: Broker lead-capture intake requires full name, email, and phone; footer states final pricing requires registered broker phone completion. reCAPTCHA present on submit step. No instant self-serve premium.
- **CAA Insurance**: unresolved: Reached CAA South Central Ontario step-1 Vehicle Details; garaging address required. Membership number not requested on this screen. Could not advance in estimate_only mode without address.
- **Facility Association**: manual_handoff: Residual market has no direct automatable path by design.
- **Aviva Direct**: unresolved: Appendix A Aviva group. Legal entities: Aviva General Insurance Company; Aviva Insurance Company of Canada; S&Y Insurance Company; Scottish & York Insurance Co. Limited; Traders General Insurance Company. Starting route: Aviva Direct. Deduplicate legacy entities against broker/RBC returns when live. Not yet attempted live. Entry point has an embedded postal code field, not a separate quote-start page. Confirmed required fields upfront: driver name(s), DOB, licence class + G1/G2/G dates, driving history; vehicle year/make/model, owner details, purchase/lease date, use type. Hard limit: max 2 vehicles/2 drivers online. A language/province selection gate appears on entry: same pattern as Sonnet's province modal, handle with existing find_dropdown_trigger/find_homepage_cta logic. LIVE (2026-08-10): Stuck on language/province modal + cookie banner; postal-code field not reached.
- **Duuo by Co-operators**: unresolved: Confirmed live: Duuo offers real self-serve online auto insurance purchase in Ontario (explicitly listed as an eligible province), underwritten by Co-operators General Insurance Company. This is a genuinely direct digital flow, distinct from the parent cooperators.ca site which is agent-network-first. Not yet attempted live. LIVE (2026-08-10): Reached Duuo welcome SPA; stalled on Start your quote CTA.
- **TD Insurance**: unresolved: Appendix A TD group. Legal entities: Primmum Insurance Company; Security National Insurance Company; TD General Insurance Company. TD online, phone and affinity routes per brief. Not yet attempted live. Confirmed 3-step flow disclosed directly on the page: (1) Your vehicle, (2) Savings, (3) Driver details. Offers a VIN-prefill option as an alternative to manual vehicle entry: if VIN is available in the applicant profile, try the VIN path first as it may reduce the number of fields needed. Vehicle year field appears to be a genuine native HTML dropdown (explicit year list visible in page content), which is good news: try native select_option() before falling back to custom-dropdown handling. LIVE (2026-08-10): Reached step 1/3 vehicle year dropdown; browser closed before fill completed.
- **Square One Insurance**: manual_handoff: Appendix A Zurich group. Square One direct for Ontario car per brief citation [8]. Specialty Zurich broker routes may differ: validate underwriter on returned quote. Not yet attempted live. Confirmed 4-step flow per live page content: (1) drivers, (2) vehicle, (3) limits/deductibles/coverage, (4) premium. Cookie-consent modal appears on entry, similar pattern to Sonnet's: handle via existing find_homepage_cta or a dedicated cookie-consent click. Legal underwriter confirmed as Zurich Insurance Company Ltd (Canadian Branch) for Ontario auto: matches existing registry insurer_group 'Zurich'. LIVE (2026-08-10): Guardrail stopped on cookie/legal page containing declaration before CONFIRM or CAR QUOTE; never entered quote flow.

## Errors

No unhandled errors recorded.