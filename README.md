# Ontario All-Quote Agent (Binder)

Personal Ontario auto insurance shopping agent that attempts real quotes across direct writers, brokers, aggregators, and residual-market routes from a single intake profile.

## Problem

Ontario drivers must shop many disconnected quote channels manually; each site has different forms, widgets, and stop points (CAPTCHA, declarations, payment).

## Approach

Built Binder, a Streamlit dashboard plus Playwright browser agent driven by Claude field mapping. Maintains a seed registry of 48 market routes, 22 of them live-tested (69 in the full registry), with guardrails that halt at CAPTCHA, declarations, or payment. Normalizes premiums for comparison, redacts PII before storage, and tracks confidence so the agent never submits unconfirmed answers to risk-relevant questions.

## Results

**Status:** a working agent that reaches real quote forms, but no comparable premium has been captured yet.

- 48 market routes in `registry/seed_registry.json` (about 69 in the full registry). 22 were tried against live sites in August 2026, each with a timestamp and a screenshot or a written reason.
- Outcomes across the 48: 18 manual handoff, 17 unresolved, 10 callback required, 2 unreachable, 1 blocked.
- Premiums captured: 0. Most routes stopped at custom form widgets, callback requirements or bot checks. See `results/run_report.md` and `known_limitations.md`.
- Unit-tested premium normalizer (`tests/test_normalizer.py`) and shared coverage metrics in `metrics_utils.py`.

## Responsible AI, following the Reliable AI Adoption Framework

1. **Business problem:** help one Ontario driver compare auto insurance quotes without filling in dozens of forms by hand.
2. **Data readiness:** the driver's own intake profile. Personal fields are redacted before anything is stored, and none are in this repository.
3. **Governance and risk:** the agent stops at CAPTCHAs, legal declarations and payment pages, and never answers a risk-relevant question it is not sure of. It acts only for the person whose details it holds.
4. **Technology and tools:** Playwright drives the browser and Claude maps form fields. Every result keeps its evidence, so a person can check it.
5. **People and adoption:** the driver reviews every result and finishes any quote by hand. A wrong answer on an insurance form can void a policy.
6. **Outcomes and monitoring:** track how many routes reach a real premium, and re-test routes when insurers change their sites.

## Tech stack

Python, Streamlit, Playwright, Anthropic Claude API, pytest

## How to run

```bash
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY=your_key_here
cp intake_config.example.py intake_config.py
streamlit run app.py
```

Additional commands: `python run_registry.py`, `python -m pytest tests/ -q`

Personal-use prototype only, not deployed publicly. Real intake data stays in gitignored `intake_config.py`.

## Screenshot / demo

Run locally at http://localhost:8501, no public deployment by design (Ontario All-Quote Agent Challenge prototype).

See `architecture_and_safety_note.md` and `results/run_report.md` for safety behavior and evidence format.
