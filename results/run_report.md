# Run Report: Ontario All-Quote Agent (Binder)

Generated: 2026-08-12T00:45:20.869290+00:00

## Summary
- **Live-tested routes with real evidence:** 22
- **Discovery-stage seed entries (not yet attempted):** 26
- **Total registry entries:** 48
- **Evidence-backed completion (all results):** 0.458
- **Evidence rate:** 0.458

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
| Pafco | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Definity / Economical broker | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Economical | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Intact Insurance | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Jevco | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Echelon | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Gore Mutual | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Travelers | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Coachman | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| SGI Canada | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Northbridge | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Zenith | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Pembridge | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Beneva / Unica | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Optimum | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |
| Portage Mutual | broker | **manual_handoff** | n/a | see outcome notes in dashboard |  |

## Discovery-Stage Seed Entries: Not Yet Attempted

These entries are seeded from the brief's Appendix A regulatory dataset for market-mapping purposes. **No live attempt has been made against any of these.** They are discovery leads, not results, and are excluded from the evidence-backed completion count above.

| Route | Channel | Legal Underwriter | Notes |
|---|---|---|---|
| Rates.ca | aggregator | TBD - returned by panel | Broad broker engine B per brief Section 4. Describes insurer API and industry-rater connectivity. Not yet attempted live; treat returned legal underwr |
| Surex | broker | TBD - returned by broker panel | Broad licensed brokerage per brief Section 4. Compensation disclosure names Aviva, Intact, Jevco, Wawanesa, CAA, Coachman, Definity/Economical, Gore,  |
| Onlia | broker | TBD - returned by broker | Digital brokerage with multiple carriers per brief Section 4. Capture actual returned underwriter, not brokerage brand. Not yet attempted live. |
| Allstate | direct | Allstate Insurance Company of Canada | Appendix A Allstate group. Legal entities: Allstate Insurance Company of Canada; Esurance Insurance Company of Canada; Pafco Insurance Company; Pembri |
| Aviva Direct | direct | S&Y Insurance Company | Appendix A Aviva group. Legal entities: Aviva General Insurance Company; Aviva Insurance Company of Canada; S&Y Insurance Company; Scottish & York Ins |
| RBC Insurance | affinity | Aviva Insurance Company of Canada | Appendix A Aviva group: RBC affinity route with Aviva underwriting disclosure per brief. Capture returned legal underwriter on quote page. Not yet att |
| Co-operators | direct | Co-operators General Insurance Company | Appendix A Co-op group. Legal entities: COSECO Insurance Company; CUMIS General Insurance Company; Co-operators General Insurance Company; The Soverei |
| Duuo by Co-operators | direct | Co-operators General Insurance Company | Confirmed live: Duuo offers real self-serve online auto insurance purchase in Ontario (explicitly listed as an eligible province), underwritten by Co- |
| Desjardins Insurance | direct | Certas Direct Insurance Company | Appendix A Desjardins group. Legal entities: Certas Direct Insurance Company; Certas Home and Auto Insurance Company; The Personal Insurance Company.  |
| The Personal | affinity | The Personal Insurance Company | Appendix A Desjardins group: The Personal group/employer affinity route per brief citation [18]. Membership or group eligibility may restrict access.  |
| TD Insurance | direct | TD General Insurance Company | Appendix A TD group. Legal entities: Primmum Insurance Company; Security National Insurance Company; TD General Insurance Company. TD online, phone an |
| Square One Insurance | direct | Zurich Insurance Company | Appendix A Zurich group. Square One direct for Ontario car per brief citation [8]. Specialty Zurich broker routes may differ: validate underwriter on  |
| Wawanesa | mutual | The Wawanesa Mutual Insurance Company | Appendix A Wawanesa group: broker route primary per brief; public web quote path seeded for discovery. Not yet attempted live. |
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
- **Pafco**: manual_handoff: Appendix A Allstate group: Pafco non-standard PPA via licensed broker only. No direct consumer quote URL seeded. Validate Esurance entity separately if profile fits.
- **Definity / Economical broker**: manual_handoff: Appendix A Definity group: Definity/Economical broker route distinct from Sonnet direct (definity-sonnet). Legal entities: Definity Insurance Company; Sonnet Insurance Company. Map current legal entity/program at quote time. Not yet attempted live.
- **Economical**: manual_handoff: Appendix A Economical group: broker route; map current legal entity/program. May overlap Definity group post-amalgamation: dedupe by returned underwriter. Not yet attempted live.
- **Intact Insurance**: manual_handoff: Appendix A Intact group: Intact broker route distinct from belairdirect direct. Legal entities include Intact Insurance Company; Jevco; Novex; Unifund; Western Assurance; Royal & SunAlliance; The Guarantee Company of North America. Validate legacy/affinity entities. Not yet attempted live.
- **Jevco**: manual_handoff: Appendix A Intact group: Jevco non-standard PPA via licensed broker when profile fits. Not yet attempted live.
- **Echelon**: manual_handoff: Appendix A CAA group: Echelon broker and non-standard route distinct from CAA direct affinity. Not yet attempted live.
- **Gore Mutual**: manual_handoff: Appendix A Gore group: broker route. Named on LowestRates panel. Not yet attempted live.
- **Travelers**: manual_handoff: Appendix A Travelers group: broker route. Named on LowestRates panel. Not yet attempted live.
- **Coachman**: manual_handoff: Appendix A SGI group. Legal entities: Coachman Insurance Company; SGI CANADA Insurance Services Ltd. Coachman non-standard via broker. Not yet attempted live.
- **SGI Canada**: manual_handoff: Appendix A SGI group: standard PPA broker route distinct from Coachman non-standard. Not yet attempted live.
- **Northbridge**: manual_handoff: Appendix A Northbridge group. Legal entities: Federated Insurance Company of Canada; Northbridge General Insurance Corporation; Verassure Insurance Company; Zenith Insurance Company. Zenith named on LowestRates panel. Validate Federated/Verassure scope. Not yet attempted live.
- **Zenith**: manual_handoff: Appendix A Northbridge group: Zenith broker route; distinct rate source from Northbridge General if panel returns separately. Not yet attempted live.
- **Pembridge**: manual_handoff: Appendix A Allstate group: Pembridge broker/non-standard route. Named on LowestRates panel. Not yet attempted live.
- **Beneva / Unica**: manual_handoff: Appendix A Beneva group: broker route only. Not yet attempted live.
- **Optimum**: manual_handoff: Appendix A Optimum group: broker route. Not yet attempted live.
- **Portage Mutual**: manual_handoff: Appendix A Portage group: broker route. Not yet attempted live.

## Errors

No unhandled errors recorded.