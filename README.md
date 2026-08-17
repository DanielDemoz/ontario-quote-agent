# Ontario All-Quote Agent (Binder)

Personal Ontario auto insurance shopping agent that attempts real quotes across direct writers, brokers, aggregators, and residual-market routes from a single intake profile.

## Problem

Ontario drivers must shop many disconnected quote channels manually; each site has different forms, widgets, and stop points (CAPTCHA, declarations, payment).

## Approach

Built Binder—a Streamlit dashboard plus Playwright browser agent driven by Claude field mapping. Maintains a seed registry of 48 live-tested routes (69 in full registry), with guardrails that halt at CAPTCHA, declarations, or payment. Normalizes premiums for comparison, redacts PII before storage, and tracks confidence so the agent never submits unconfirmed answers to risk-relevant questions.

## Results

- 48 catalogued market routes in `registry/seed_registry.json`; full Appendix A-style merge to ~69 entities
- Evidence-backed outcomes per route: status, premium when available, timestamped screenshot, or explicit non-quote reason
- Unit-tested premium normalizer (`tests/test_normalizer.py`) and shared coverage metrics via `metrics_utils.py`

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

Personal-use prototype only—not deployed publicly. Real intake data stays in gitignored `intake_config.py`.

## Screenshot / demo

Run locally at http://localhost:8501 — no public deployment by design (Ontario All-Quote Agent Challenge prototype).

See `architecture_and_safety_note.md` and `results/run_report.md` for safety behavior and evidence format.
