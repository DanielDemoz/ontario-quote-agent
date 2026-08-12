
# Binder - Ontario All-Quote Agent

A personal Ontario auto insurance shopping agent. One intake, then it attempts a real quote across every reachable channel: direct writers, brokers, aggregators, affinity programs, mutuals, and the residual market, and returns either a real result or an honest, evidence-backed reason it couldn't.

Built for the Ontario All-Quote Agent Challenge. Personal-use prototype only, per the challenge brief. Not deployed publicly.

## Setup

```
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY=your_key_here
```

## Run the dashboard locally

```
cp intake_config.example.py intake_config.py   # or fill in the Binder Intake tab
streamlit run app.py
```

This opens Binder in your browser at `localhost:8501`.

- **Intake**: enter your profile. Real data stays local only; `intake_config.py` is gitignored and never committed. Only `intake_config.example.py` (fake placeholder data) lives in this repo.
- **Registry**: the market map, legal underwriter, insurer group, brand, distributor, and status for every route.
- **Run agent**: execute routes against the registry. Opens a visible browser per route; stops safely at any CAPTCHA, declaration, or payment step.
- **Results**: evidence-backed outcomes, status, premium (if any), timestamped screenshot, and the specific reason for any non-quote outcome.

## Files

- `schema.py`: all data structures (Status enum, MarketRecord, Applicant, QuoteResult). Source of truth for field names.
- `guardrails.py`: hard stops. CAPTCHA/block detection, declaration/signature detection, payment detection, applicant mode validation, redaction before storage.
- `browser_agent.py`: Playwright driver plus Claude field mapping, custom widgets, site hooks, and normalizer integration.
- `normalizer.py`: premium extraction plus Section 6 benchmark comparability, unit-tested via `tests/test_normalizer.py`.
- `site_hooks.py`: per-route SPA/combobox hooks (Sonnet province modal, CAA/ThinkInsure CTAs).
- `voice_agent.py`: callback scripts for phone-first routes, disclosing automation up front per the brief's required pattern. Optional Twilio integration via `TWILIO_*` env vars.
- `voice_input.py`: optional microphone dictation in the Binder Streamlit intake UI.
- `metrics_utils.py`: single source of truth for coverage metrics, shared by the dashboard and the run report so they can never disagree.
- `report_utils.py`: shared logic for splitting registry entries into live-tested evidence vs. discovery-stage seed leads.
- `registry/seed_registry.json`: 48 live-tested / catalogued market routes.
- `registry/full_registry.json`: about 69 Appendix A-style entities (`python build_registry.py --merge`).
- `build_registry.py`: generates/merges the full market registry.
- `run_registry.py`: orchestrator with route isolation (a hard timeout and full exception handling per route, so one failure never blocks the rest), `--scope full`, `--live-only`, voice routing.
- `run_targeted_four.py`: run the four targeted direct-writer routes only.
- `app.py`: Binder Streamlit dashboard (intake, run controls, comparison table, evidence).
- `intake_config.example.py`: fake-data template. Copy to `intake_config.py` (gitignored) for your own profile.
- `interactive_intake.py` / `intake_writer.py`: CLI intake flow, text or voice input, with per-field confidence tracking so the agent never submits an unconfirmed answer to a risk-relevant question.
- `formatting_utils.py`: postal code normalization and other field-formatting helpers.
- `compile_real_results.py`: compiles real, evidence-backed results into `results/results.json`.
- `generate_run_report.py`: regenerates `results/run_report.md`, the redacted coverage ledger required for submission.

## Additional commands

```
python run_registry.py                          # all 48 seed routes
python run_registry.py --scope full --live-only  # Appendix A routes with quote URLs
python generate_run_report.py                    # regenerate results/run_report.md
python -m pytest tests/ -q                       # run the test suite
```

## Privacy and safety

- Real personal data lives only in `intake_config.py`, gitignored, never committed. `intake_config.example.py` (fake data) is the version in this repo.
- Every screenshot and log entry is masked via `guardrails.redact_for_storage()` and `mask_sensitive_before_screenshot()` before being saved, covering every sensitive field in the intake schema (identity, licence, address, employment, financing, and more).
- A confidence-tracking system means the agent never guesses on a question it hasn't been explicitly given an answer to. It stops and logs `manual_handoff` instead of submitting an unconfirmed default.
- Guardrails hard-stop the agent at any CAPTCHA, application declaration, or payment step. See `architecture_and_safety_note.md` for the full behavior.
- Before committing, search `results/` and `logs/` for any real licence number, full address, or payment data as a manual final check.

## Further reading

- `architecture_and_safety_note.md`: agent responsibilities, human checkpoints, consent flow, data handling.
- `known_limitations.md`: where the system depends on a human, licensed intermediary, or unavailable integration.
- `ground_truth_and_future_direction.md`: what was verified live, lessons drawn from travel-booking systems, and what a structured-API future could look like for this problem.


