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
- `guardrails.py` — hard stops: CAPTCHA/block detection, declaration/signature detection, payment detection, applicant mode validation, redaction before storage.
- `browser_agent.py` — Playwright driver + Claude field mapping, custom widgets, site hooks, and normalizer integration.
- `normalizer.py` — premium extraction + Section 6 benchmark comparability; unit-tested via `tests/test_normalizer.py`.
- `site_hooks.py` — per-route SPA/combobox hooks (Sonnet province modal, CAA/ThinkInsure CTAs).
- `voice_agent.py` — callback scripts for phone-first routes; optional Twilio via `TWILIO_*` env vars.
- `voice_input.py` — optional microphone dictation in the Binder Streamlit intake UI.
- `registry/seed_registry.json` — 48 live-tested / catalogued market routes.
- `registry/full_registry.json` — ~69 Appendix A-style entities (`python build_registry.py --merge`).
- `build_registry.py` — generates/merges the full market registry.
- `run_registry.py` — orchestrator with route isolation, `--scope full`, `--live-only`, voice routing.
- `run_targeted_four.py` — run the four targeted direct-writer routes only.
- `app.py` — **Binder** Streamlit dossier (intake, run controls, comparison table, evidence). Run: `streamlit run app.py`
- `intake_config.example.py` — copy to `intake_config.py` (gitignored) for your profile.

## Quick start

```bash
cp intake_config.example.py intake_config.py   # or use the Binder intake tab
python run_registry.py                         # all 48 seed routes
python run_registry.py --scope full --live-only  # Appendix A routes with quote URLs
python generate_run_report.py
streamlit run app.py
python -m pytest tests/ -q
```

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
