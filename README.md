# Ontario All-Quote Agent — Hackathon Build

## Setup on your laptop (run this first, NOT in a sandboxed container)

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY=your_key_here
```

## Files

- `schema.py` — all data structures (Status enum, MarketRecord, Applicant, QuoteResult). Source of truth for field names.
- `guardrails.py` — hard stops: CAPTCHA/block detection, declaration/signature detection, payment detection, applicant mode validation, redaction before storage. TESTED, working.
- `registry/seed_registry.json` — your 6 scoped target routes (Sonnet direct, belairdirect, LowestRates aggregator, ThinkInsure broker, CAA affinity, Facility Association residual).
- `intake_config.py` — YOUR profile. Gitignored. Starts in `estimate_only` mode (safe default, no real licence/name).
- `browser_agent.py` — Playwright driver + Claude fallback for form-field mapping. Has a TODO where you add real selectors per site — this has to be done live against each actual page, since I can't preview real site DOM from here.
- `run_registry.py` — orchestrator, runs every route, computes coverage metrics, writes `results/results.json` and `results/metrics.json`.
- `app.py` — Streamlit comparison table. Run: `streamlit run app.py`

## What to do first at the venue

1. `python -c "from guardrails import check_page_text; check_page_text('test')"` — confirm imports work in your real environment.
2. Open Sonnet's quote page manually in a browser, walk through it yourself once, note the actual form field selectors (id/name attributes) for each step.
3. Fill those selectors into `browser_agent.py` in the `run_route()` function where the TODO comment is, for your first route.
4. Run `python run_registry.py` — even a single working route end to end proves the architecture.
5. Add routes one at a time, testing after each.
6. `streamlit run app.py` to see the comparison table update as results.json fills in.

## Guardrail check before every submission

Search results/ and logs/ for any of: real licence number, full street address,
payment info, unredacted phone/email. `guardrails.redact_for_storage()` should
have caught these, but verify manually before committing.

## Additional scripts

- `generate_run_report.py` — run after `run_registry.py` to produce `results/run_report.md`, the redacted coverage ledger / gaps / errors document required for submission. Tested end to end with synthetic data; works correctly against real results.json output.

## Submission checklist (Section 9 of the brief)

- [ ] GitHub repo + setup instructions — this repo, push it
- [ ] 3-5 min Loom walkthrough
- [ ] Machine-readable market registry — `registry/seed_registry.json`, update `status`/`last_verified_at` as you go
- [ ] Redacted run report — `python generate_run_report.py` after your run
- [ ] Architecture and safety note — `architecture_and_safety_note.md` (drafted, review before submitting)
- [ ] Known limitations — `known_limitations.md` (drafted, update with anything new you discover)
