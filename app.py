"""
Binder — Ontario auto insurance evidence dossier (Streamlit UI).

Run: streamlit run app.py
"""

import asyncio
import importlib
import json
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from formatting_utils import normalize_postal_code
from guardrails import validate_applicant_for_mode
from intake_writer import load_existing_applicant, stamp_consent, write_intake_config
from run_registry import run_all
from schema import Applicant
from ui_theme import (
    binder_hero,
    info_box,
    inject_theme,
    privacy_box,
    render_stamp_ledger,
    section_close,
    section_open,
    status_badge,
    warn_box,
)
from voice_input import listen_once, speech_recognition_available

ROOT = Path(__file__).parent
RESULTS_PATH = ROOT / "results" / "results.json"
METRICS_PATH = ROOT / "results" / "metrics.json"
REGISTRY_PATH = ROOT / "registry" / "seed_registry.json"
REPORT_PATH = ROOT / "results" / "run_report.md"

st.set_page_config(
    page_title="Binder",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text_safe(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def _resolve_artifact(path: str) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if p.is_absolute() and p.exists():
        return p
    candidate = ROOT / path
    return candidate if candidate.exists() else None


def _defaults() -> dict:
    existing = load_existing_applicant()
    if existing:
        return existing
    return {
        "mode": "estimate_only",
        "consent_timestamp": "",
        "legal_name": "",
        "date_of_birth": "",
        "licence_number": "",
        "licence_class": "G",
        "date_first_licensed": "",
        "email": "",
        "phone": "",
        "province": "Ontario",
        "street": "",
        "city": "Toronto",
        "postal_code": "",
        "residence_start_date": "",
        "vin": "",
        "model_year": "2020",
        "make": "Toyota",
        "model": "Corolla",
        "ownership": "owned",
        "annual_km": "12000",
        "commute_km_one_way": "10",
        "primary_use": "commute",
        "current_insurer": "",
        "years_continuously_insured": "0",
        "accidents_last_6y": "none",
        "convictions_last_3y": "none",
        "effective_date": date.today().isoformat(),
        "liability_limit": "2000000",
        "dcpd_included": True,
        "collision_deductible": "1000",
        "comprehensive_deductible": "1000",
        "opcf_44r": True,
        "telematics_opt_in": False,
    }


def _ensure_intake_state():
    if "intake_values" not in st.session_state:
        st.session_state.intake_values = _defaults()
    if "live_mode" not in st.session_state:
        st.session_state.live_mode = st.session_state.intake_values.get("mode") == "live"
    if "consent_given" not in st.session_state:
        st.session_state.consent_given = bool(st.session_state.intake_values.get("consent_timestamp"))


def _voice_enabled() -> bool:
    return st.session_state.get("input_mode") == "Speak your answers (microphone)"


def _dictate_field(field_key: str, label: str):
    """Mic button — updates session state and reruns."""
    if st.button("🎤", key=f"mic_{field_key}", help=f"Dictate: {label}", use_container_width=True):
        with st.spinner("Listening…"):
            heard, err = listen_once()
        if heard:
            st.session_state.intake_values[field_key] = heard
            st.session_state[f"heard_{field_key}"] = heard
            st.rerun()
        elif err:
            st.session_state["voice_error"] = err


def _text_field(
    field_key: str,
    label: str,
    *,
    disabled: bool = False,
    sensitive: bool = False,
    placeholder: str = "",
):
    """Text input with optional dictation column."""
    vals = st.session_state.intake_values
    voice = _voice_enabled() and not disabled
    sensitive_voice = voice and sensitive

    if voice:
        c_input, c_mic = st.columns([5, 1])
    else:
        c_input = st.container()
        c_mic = None

    with c_input:
        value = st.text_input(
            label,
            value=vals.get(field_key, ""),
            disabled=disabled,
            type="password" if sensitive else "default",
            placeholder=placeholder,
            key=f"field_{field_key}",
        )
        vals[field_key] = value
        if sensitive_voice:
            st.caption("Sensitive field — please type rather than dictate.")

    if voice and c_mic is not None and not sensitive:
        with c_mic:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            _dictate_field(field_key, label)

    heard = st.session_state.pop(f"heard_{field_key}", None)
    if heard:
        st.caption(f"Last dictation: {heard}")

    return vals.get(field_key, "")


def _build_payload(live: bool, consent: bool) -> dict:
    v = st.session_state.intake_values
    mode = "live" if live and consent else "estimate_only"
    return {
        "mode": mode,
        "consent_timestamp": stamp_consent() if mode == "live" else "",
        "legal_name": v.get("legal_name", "").strip(),
        "date_of_birth": v.get("date_of_birth", "").strip(),
        "licence_number": v.get("licence_number", "").strip(),
        "licence_class": v.get("licence_class", "G").strip() or "G",
        "date_first_licensed": v.get("date_first_licensed", "").strip(),
        "email": v.get("email", "").strip(),
        "phone": v.get("phone", "").strip(),
        "province": "Ontario",
        "street": v.get("street", "").strip(),
        "city": v.get("city", "").strip(),
        "postal_code": normalize_postal_code(v.get("postal_code", "").strip()) if v.get("postal_code", "").strip() else "",
        "residence_start_date": v.get("residence_start_date", "").strip(),
        "vin": v.get("vin", "").strip(),
        "model_year": v.get("model_year", "").strip(),
        "make": v.get("make", "").strip(),
        "model": v.get("model", "").strip(),
        "ownership": v.get("ownership", "owned"),
        "annual_km": v.get("annual_km", "").strip(),
        "commute_km_one_way": v.get("commute_km_one_way", "").strip(),
        "primary_use": v.get("primary_use", "commute"),
        "current_insurer": v.get("current_insurer", "").strip(),
        "years_continuously_insured": v.get("years_continuously_insured", "").strip(),
        "accidents_last_6y": v.get("accidents_last_6y", "none").strip() or "none",
        "convictions_last_3y": v.get("convictions_last_3y", "none").strip() or "none",
        "effective_date": v.get("effective_date", date.today().isoformat()).strip() or date.today().isoformat(),
        "liability_limit": v.get("liability_limit", "2000000"),
        "dcpd_included": True,
        "collision_deductible": "1000",
        "comprehensive_deductible": "1000",
        "opcf_44r": True,
        "telematics_opt_in": bool(v.get("telematics_opt_in", False)),
    }


def _applicant_from_payload(payload: dict) -> Applicant:
    return Applicant(
        mode=payload["mode"],
        consent_timestamp=payload["consent_timestamp"] or None,
        legal_name=payload["legal_name"],
        date_of_birth=payload["date_of_birth"],
        licence_number=payload["licence_number"],
        licence_class=payload["licence_class"],
        date_first_licensed=payload["date_first_licensed"],
        email=payload["email"],
        phone=payload["phone"],
        province=payload["province"],
        street=payload["street"],
        city=payload["city"],
        postal_code=payload["postal_code"],
        residence_start_date=payload["residence_start_date"],
        vin=payload["vin"],
        model_year=payload["model_year"],
        make=payload["make"],
        model=payload["model"],
        ownership=payload["ownership"],
        annual_km=payload["annual_km"],
        commute_km_one_way=payload["commute_km_one_way"],
        primary_use=payload["primary_use"],
        current_insurer=payload["current_insurer"],
        years_continuously_insured=payload["years_continuously_insured"],
        accidents_last_6y=payload["accidents_last_6y"],
        convictions_last_3y=payload["convictions_last_3y"],
        effective_date=payload["effective_date"],
        liability_limit=payload["liability_limit"],
        dcpd_included=payload["dcpd_included"],
        collision_deductible=payload["collision_deductible"],
        comprehensive_deductible=payload["comprehensive_deductible"],
        opcf_44r=payload["opcf_44r"],
        telematics_opt_in=payload["telematics_opt_in"],
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _current_mode() -> str:
    existing = load_existing_applicant()
    if existing:
        return existing.get("mode", "estimate_only")
    if "intake_values" in st.session_state:
        return st.session_state.intake_values.get("mode", "estimate_only")
    return "estimate_only"


def render_sidebar():
    st.sidebar.markdown('<p class="sidebar-brand">Binder</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="sidebar-sub">Ontario Auto Insurance Case File</p>',
        unsafe_allow_html=True,
    )

    existing = load_existing_applicant()
    if existing:
        mode = existing.get("mode", "estimate_only")
        st.sidebar.markdown(
            f"**Profile status**  \n"
            f"Mode: `{mode}`  \n"
            f"{'Live profile on disk (gitignored)' if mode == 'live' else 'Estimate-only profile'}"
        )
    else:
        st.sidebar.warning("No saved profile yet — complete Intake first.")

    st.sidebar.divider()
    st.sidebar.markdown("**Navigation**")
    st.sidebar.markdown(
        "- **Intake** — enter your profile  \n"
        "- **Results** — compare route outcomes  \n"
        "- **Registry** — market map  \n"
        "- **Run agent** — execute quote routes"
    )
    if st.sidebar.button("Reload dashboard", use_container_width=True):
        st.rerun()


# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------

def render_intake():
    _ensure_intake_state()
    v = st.session_state.intake_values

    section_open(
        "Your profile",
        "Enter information once. Saved locally to intake_config.py (gitignored, never committed).",
    )

    # Input mode
    st.markdown("**How would you like to enter your answers?**")
    modes = ["Type your answers", "Speak your answers (microphone)"]
    if not speech_recognition_available():
        modes = ["Type your answers"]
        st.caption("Voice mode requires: `pip install SpeechRecognition pyaudio`")

    st.session_state.input_mode = st.radio(
        "Input method",
        modes,
        horizontal=True,
        label_visibility="collapsed",
    )

    if _voice_enabled():
        warn_box(
            "<strong>Voice privacy notice:</strong> spoken answers are sent to Google's "
            "speech recognition service for transcription — this is not purely local. "
            "For licence numbers, addresses, and VIN, use the keyboard. "
            "Sensitive fields disable the microphone automatically."
        )
    else:
        info_box(
            "Type directly into each field below. Switch to <strong>Speak your answers</strong> "
            "to dictate non-sensitive fields using your microphone."
        )

    if "voice_error" in st.session_state:
        st.warning(st.session_state.pop("voice_error"))

    st.divider()

    live = st.toggle(
        "Live mode — submit my real information to quote routes",
        value=st.session_state.live_mode,
        help="Off keeps estimate-only mode (safe default).",
    )
    st.session_state.live_mode = live

    consent = False
    if live:
        warn_box(
            "Live mode uses <strong>your own</strong> accurate details on insurer websites. "
            "Guardrails still stop at declarations, payment, and CAPTCHA. "
            "Nothing is purchased automatically."
        )
        consent = st.checkbox(
            "I confirm this is my own information, I consent to submission on quote routes, "
            "and I understand no policy will be bound automatically.",
            value=st.session_state.consent_given,
        )
        st.session_state.consent_given = consent

    # --- Identity ---
    st.markdown("#### Identity")
    c1, c2 = st.columns(2)
    with c1:
        _text_field("legal_name", "Legal name (as on licence)", disabled=not live)
        _text_field("date_of_birth", "Date of birth (YYYY-MM-DD)", disabled=not live, placeholder="1990-01-15")
        _text_field("licence_class", "Licence class", placeholder="G")
    with c2:
        _text_field("licence_number", "Ontario licence number", disabled=not live, sensitive=True)
        _text_field("date_first_licensed", "Date first licensed (YYYY-MM-DD)", disabled=not live)

    # --- Contact ---
    st.markdown("#### Contact")
    c1, c2 = st.columns(2)
    with c1:
        _text_field("email", "Email address", disabled=not live)
    with c2:
        _text_field("phone", "Phone number", disabled=not live, sensitive=True)

    # --- Address ---
    st.markdown("#### Address")
    _text_field("street", "Street address", disabled=not live, sensitive=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        _text_field("city", "City", placeholder="Toronto")
    with c2:
        _text_field("postal_code", "Postal code", disabled=not live, sensitive=True, placeholder="M5H 2N2")
    with c3:
        _text_field("residence_start_date", "Residence start (YYYY-MM-DD)", disabled=not live)

    # --- Vehicle ---
    st.markdown("#### Vehicle")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _text_field("model_year", "Model year", placeholder="2020")
    with c2:
        _text_field("make", "Make", placeholder="Toyota")
    with c3:
        _text_field("model", "Model", placeholder="Corolla")
    with c4:
        _text_field("vin", "VIN (optional)", disabled=not live, sensitive=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        v["ownership"] = st.selectbox(
            "Ownership",
            ["owned", "leased"],
            index=0 if v.get("ownership", "owned") == "owned" else 1,
        )
    with c2:
        _text_field("annual_km", "Annual kilometres", placeholder="12000")
    with c3:
        _text_field("commute_km_one_way", "Commute km (one way)", placeholder="10")
    v["primary_use"] = st.selectbox(
        "Primary use",
        ["commute", "pleasure", "business"],
        index=["commute", "pleasure", "business"].index(v.get("primary_use", "commute")),
    )

    # --- History ---
    st.markdown("#### Insurance history")
    c1, c2 = st.columns(2)
    with c1:
        _text_field("current_insurer", "Current insurer (blank if none)")
        _text_field("years_continuously_insured", "Years continuously insured", placeholder="0")
    with c2:
        _text_field("accidents_last_6y", "Accidents / claims (last 6 years)", placeholder="none")
        _text_field("convictions_last_3y", "Convictions (last 3 years)", placeholder="none")

    # --- Coverage ---
    st.markdown("#### Coverage benchmark")
    c1, c2 = st.columns(2)
    with c1:
        _text_field("effective_date", "Coverage start date (YYYY-MM-DD)", placeholder=date.today().isoformat())
        v["liability_limit"] = st.selectbox(
            "Third-party liability limit",
            ["1000000", "2000000"],
            index=0 if v.get("liability_limit") == "1000000" else 1,
            format_func=lambda x: f"${int(x):,}",
        )
    with c2:
        v["telematics_opt_in"] = st.checkbox("Opt into telematics / usage-based insurance", value=v.get("telematics_opt_in", False))

    privacy_box("Your profile file stays on this computer only and is excluded from git commits.")

    st.divider()
    if st.button("Save profile", type="primary", use_container_width=True):
        if live and not consent:
            st.error("Live mode requires consent before saving.")
        else:
            payload = _build_payload(live, consent)
            try:
                applicant = _applicant_from_payload(payload)
                validate_applicant_for_mode(applicant)
                path = write_intake_config(payload)
                import intake_config
                importlib.reload(intake_config)
                st.session_state.intake_values = payload
                st.success(f"Profile saved · mode: **{applicant.mode}** · file: `{path.name}`")
            except Exception as exc:
                st.error(f"Could not save: {exc}")

    section_close()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def render_results():
    section_open("Quote comparison", "Evidence-backed outcomes across all market routes.")

    if not RESULTS_PATH.exists():
        st.warning("No results yet. Complete **Intake**, then run routes from the **Run agent** tab.")
        section_close()
        return

    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = {r["registry_id"]: r for r in json.load(f)}

    if METRICS_PATH.exists():
        with open(METRICS_PATH, encoding="utf-8") as f:
            metrics = json.load(f)
        cols = st.columns(len(metrics))
        for col, (k, val) in zip(cols, metrics.items()):
            with col:
                st.markdown(
                    f'<div class="metric-card"><div class="label">{k.replace("_", " ")}</div>'
                    f'<div class="value">{val}</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)
    df = pd.DataFrame(results)
    if df.empty:
        st.info("No route results recorded yet.")
        section_close()
        return

    df["brand"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("brand_or_program", rid))
    df["legal_underwriter"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("legal_underwriter", ""))
    df["insurer_group"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("insurer_group", ""))
    df["distribution_type"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("distribution_type", ""))
    df["attempted"] = df["evidence_timestamp"].fillna("").astype(str).str.len() > 0

    c1, c2 = st.columns(2)
    with c1:
        status_filter = st.multiselect(
            "Filter by status",
            sorted(df["status"].unique()),
            default=list(df["status"].unique()),
        )
    with c2:
        sort_col = st.selectbox("Sort by", ["annual_premium", "status", "brand"], index=1)
    show_not_attempted = st.checkbox("Include routes without evidence timestamps", value=True)

    filtered = df[df["status"].isin(status_filter)]
    if not show_not_attempted:
        filtered = filtered[filtered["attempted"]]
    filtered = filtered.sort_values(by=sort_col, na_position="last")

    st.markdown("#### Case ledger — stamped outcomes")
    ledger_rows = filtered.to_dict("records")
    st.markdown(render_stamp_ledger(ledger_rows), unsafe_allow_html=True)

    display_cols = [
        "brand", "legal_underwriter", "insurer_group", "distribution_type",
        "status", "annual_premium", "monthly_premium", "matches_benchmark",
        "confidence", "coverage_notes", "quote_or_reference_id",
        "evidence_timestamp", "failure_reason",
    ]
    st.markdown("#### Full comparison table")
    st.dataframe(
        filtered[[c for c in display_cols if c in filtered.columns]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Evidence detail")
    for _, row in filtered.iterrows():
        badge = status_badge(row["status"])
        with st.expander(
            f"{row.get('brand', row['registry_id'])}  ·  {row['status'].replace('_', ' ')}",
            expanded=False,
        ):
            st.markdown(badge, unsafe_allow_html=True)
            st.markdown(f"**Source URL**  \n{row.get('source_url') or '—'}")
            st.markdown(f"**Evidence timestamp**  \n{row.get('evidence_timestamp') or '—'}")
            artifact = _resolve_artifact(row.get("evidence_artifact_path", ""))
            if artifact:
                st.image(str(artifact), caption="Redacted evidence screenshot")
            elif row.get("evidence_artifact_path"):
                st.caption(f"Screenshot not found locally: `{row['evidence_artifact_path']}`")
            reason = row.get("failure_reason") or row.get("next_action")
            if reason:
                st.markdown(f"**Outcome notes**  \n{reason}")

    section_close()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def render_registry():
    section_open("Market registry", "All Appendix A insurer groups — direct, aggregator, broker, affinity, mutual, and residual routes.")
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    show = [
        "brand_or_program", "distribution_type", "status", "legal_underwriter",
        "insurer_group", "quote_url", "public_phone_route", "last_verified_at",
    ]
    st.dataframe(df[[c for c in show if c in df.columns]], use_container_width=True, hide_index=True)
    section_close()


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def render_run():
    section_open("Execute quote routes", "Runs Playwright against each registry route using your saved profile.")

    info_box(
        "A visible Chromium window opens for each route. "
        "Guardrails stop at CAPTCHA, application declarations, and payment — "
        "nothing is bound automatically."
    )

    try:
        from intake_config import build_applicant
        applicant = build_applicant()
        validate_applicant_for_mode(applicant)
        st.success(f"Profile validated · mode: **{applicant.mode}**")
    except Exception as exc:
        st.error(f"Complete and save your **Intake** profile first: {exc}")
        section_close()
        return

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run all registry routes", type="primary", use_container_width=True):
            with st.spinner("Running routes — watch the browser windows…"):
                try:
                    asyncio.run(run_all())
                    st.success("Run complete. Open the **Results** tab.")
                    st.balloons()
                except Exception as exc:
                    st.error(f"Run failed: {exc}")
    with c2:
        if st.button("Refresh reports", use_container_width=True):
            subprocess.run(["python", "compile_real_results.py"], cwd=ROOT, check=False)
            subprocess.run(["python", "generate_run_report.py"], cwd=ROOT, check=False)
            st.success("Reports regenerated.")

    if REPORT_PATH.exists():
        with st.expander("Run report (markdown)", expanded=False):
            st.markdown(_read_text_safe(REPORT_PATH))

    section_close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    inject_theme()
    render_sidebar()
    binder_hero(_current_mode())

    tab_intake, tab_results, tab_registry, tab_run = st.tabs(
        ["Intake", "Results", "Registry", "Run agent"]
    )
    with tab_intake:
        render_intake()
    with tab_results:
        render_results()
    with tab_registry:
        render_registry()
    with tab_run:
        render_run()


if __name__ == "__main__":
    main()
