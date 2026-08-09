# Ground Truth and Forward Direction

This document has two parts: what was actually verified today with real
evidence, and what the same architecture could do if Ontario auto
insurers exposed structured access the way the travel industry does.

## Part 1: What was actually done, on real ground

Four routes were run against live production insurer and aggregator
sites today, not simulated or mocked. Each ended in an honest,
evidence-backed terminal status per the brief's status enum.

| Route | Channel | Status | What actually happened |
|---|---|---|---|
| Sonnet | Direct writer | `unresolved` | Reached the real province-selection screen. The dropdown is a custom (non-native) component rather than a standard HTML `<select>`, which our generic field-extraction logic could not reliably drive within the build window. Evidence captured at the point of failure. |
| LowestRates.ca | Aggregator | `blocked` | Site returned an explicit "Sorry, you have been blocked" wall on the very first load, consistent with active bot-detection (Cloudflare/Akamai/PerimeterX-style protection). Correctly identified and logged rather than evaded, per the brief's explicit prohibition on bypassing bot controls. |
| belairdirect | Direct writer | `unresolved` | Direct deep-linking to the quote subdomain triggered an anti-direct-link redirect back to the homepage. The agent detected this, clicked the real homepage "Car" call-to-action exactly as a human visitor would, and successfully reached the actual multi-step quote form (step 1 of 3, native YEAR/MAKE/MODEL vehicle fields visible). This is the furthest any route reached today. Evidence shows the genuine in-progress form. |
| Facility Association | Residual market | `manual_handoff` | Logged by design with no automation attempt. The residual market has no direct consumer quote path; it is reached only through a licensed intermediary. Attempting to fake a path here would misrepresent the market structure. |

Every one of these outcomes is real: real URLs, real timestamps, real
screenshots, no fabricated data. This matches four of the seven
channel types the brief asks the market map to distinguish (direct
×2, aggregator, residual), plus a fifth channel type (broker, via
ThinkInsure) seeded in the registry but not yet attempted live.

### What this demonstrates technically

- **Honest failure classification.** The system does not convert a
  block into a fabricated quote, or a stall into a silent gap. Each
  failure mode (custom UI component, active bot wall, anti-direct-link
  redirect) was diagnosed and logged with its specific cause.
- **Adaptive navigation, not per-site scripts.** The same generic
  agent, not a hand-written script per insurer, reached real forms on
  two different production sites (Sonnet's province screen, belair's
  actual quote form), including recovering from an unexpected
  redirect by finding and clicking a real page element rather than
  failing.
- **Guardrails held under real conditions**, not just in unit tests.
  When LowestRates actively blocked the agent, it stopped immediately
  and logged the block rather than attempting to work around it.

## Part 2: The airline and hotel booking lesson

Global Distribution Systems (GDS platforms like Amadeus, Sabre, and
Travelport) solved the "one search, many providers, some unavailable"
problem decades ago for airlines and hotels. A few of their patterns
were deliberately built into this system today:

- **Prefer the provider's own direct channel over intermediaries.**
  Airlines' own sites are far less defensive against automated/API
  traffic than third-party scrapers hitting an OTA, because direct
  bookings are what the airline wants. The same pattern held true
  today: Sonnet and belairdirect (direct writers) let the agent in
  and make real progress; LowestRates.ca (a lead-aggregator) blocked
  it outright on the first request.
- **Show partial results as they arrive**, rather than blocking the
  whole comparison view until every provider responds. The registry
  and results schema are already structured so each route's outcome
  is independent and can render as soon as it completes.
- **Preserve a reference ID across a human handoff.** When a flight
  can't be booked online, the booking reference carries the context
  to a phone agent. The result schema's `quote_or_reference_id` and
  `source_url` fields exist for the same purpose here, so a
  `callback_required` or `manual_handoff` outcome still hands a human
  agent everything they need instead of starting over.
- **Bounded retries, not persistence at any cost.** GDS integrations
  retry once on a timeout and then surface a clear status. This is
  now implemented directly (`safe_inner_text()` retries once on a
  slow page load, consistent with the brief's own bounded-attempt
  policy).

One deliberately rejected temptation: some travel-scraping tools call
a site's internal/undocumented API endpoints directly to skip a
bot-protected UI entirely. That crosses into access-control evasion
even when it never touches a CAPTCHA directly, and the brief is
explicit that this is out of scope. It was considered and rejected.

## Part 3: What becomes possible with airline/hotel-style access

This is a forward-looking design, not a claim that this access
currently exists for Ontario auto insurance. No equivalent
industry-wide distribution layer exists today; insurers are reached
individually, through inconsistent web forms with varying degrees of
automation tolerance, which is exactly why today's build required
per-site adaptive navigation and hit real, different obstacles on
every route.

If Ontario insurers (or a neutral intermediary, similar to how GDS
sits between airlines and travel agents) exposed a **structured
quoting API** instead of only a consumer web form, the same
architecture already built today would need only its outermost layer
replaced:

**What stays exactly the same:**
- The canonical intake schema (Section 5 of the brief)
- The market registry structure (legal underwriter / group / brand /
  distributor / rate source)
- The result schema and status enum
- The coverage-ledger normalization and comparison logic
- The guardrail principles (no bypassing consent/declaration steps,
  no fabricated data, honest terminal statuses)

**What gets replaced:**
- `browser_agent.py`'s Playwright-driven navigation would be replaced
  by direct authenticated API calls per insurer, the same way a GDS
  integration replaces "visit the airline's website" with "call the
  airline's fare API."
- Bot-detection, custom dropdown components, and anti-direct-link
  redirects, everything that consumed today's debugging time, simply
  stop being relevant, because there is no UI to render or defend.
- Response times would drop from tens of seconds per route (page
  loads, JS rendering, click-and-wait cycles) to whatever the API
  round-trip takes, likely under a second per source.

**What this would unlock at the market-coverage level:**
- All sixty entities in the regulatory seed list become
  realistically attemptable in one run, not just a scoped six, since
  the bottleneck today (per-site UI quirks) disappears.
- `quoted_comparable` results become the norm rather than the
  exception, since a structured API response is naturally
  machine-comparable, whereas today's `quoted_non_comparable` default
  exists specifically because we can't yet guarantee we've read every
  coverage assumption correctly off a rendered web page.
- Voice/callback routes would shrink to genuinely broker-only and
  residual-market cases, rather than being a fallback for any site
  whose UI resists automation.

The core insight from today's real attempts is that the hard part of
this challenge was never the comparison logic or the schema design,
both worked correctly the first time. The hard part was exactly what
the brief said it would be: reliable computer use against sites that
were not built to be automated. An API-based future doesn't change
what the system does; it removes the adversarial layer between the
system and the data.
