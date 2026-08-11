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
    section_close,
    section_open,
    status_badge,
    warn_box,
)
from voice_input import listen_once, speech_recognition_available
from report_utils import classify_routes, format_evidence_link, load_registry_and_results

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
    voice = _voice_enabled() and speech_recognition_available() and not disabled
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
            st.caption("Sensitive field. Please type rather than dictate.")

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
        st.sidebar.warning("No saved profile yet. Complete Intake first.")

    st.sidebar.divider()
    st.sidebar.markdown("**Navigation**")
    st.sidebar.markdown("Intake\n\nResults\n\nRegistry\n\nRun agent")
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
        "Enter your details once. They stay on this device.",
    )

    # Input mode
    st.markdown("**How would you like to enter your answers?**")
    st.session_state.input_mode = st.radio(
        "Input method",
        ["Type your answers", "Speak your answers (microphone)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if _voice_enabled() and not speech_recognition_available():
        st.caption("Voice input is not available in this environment.")
    elif _voice_enabled():
        warn_box(
            "<strong>Voice privacy notice:</strong> spoken answers are sent to Google's "
            "speech recognition service for transcription. This is not purely local. "
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
        "Live mode: submit my real information to quote routes",
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

    registry_list, results = load_registry_and_results(results_path=RESULTS_PATH)
    registry = {r["registry_id"]: r for r in registry_list}
    live_tested, seed_only = classify_routes(registry_list, results)

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
    c1, c2, c3 = st.columns(3)
    c1.metric("Live-tested (evidence)", len(live_tested))
    c2.metric("Discovery seed (not attempted)", len(seed_only))
    c3.metric("Total registry", len(registry_list))

    st.markdown("#### Live-tested routes: real evidence")
    st.caption(
        "Routes with an evidence timestamp, screenshot path, or documented "
        "rationale when no live path exists."
    )

    if live_tested:
        live_df = pd.DataFrame(live_tested)
        live_df["brand"] = live_df["registry_id"].map(
            lambda rid: registry.get(rid, {}).get("brand_or_program", rid)
        )
        live_df["evidence"] = live_df.apply(format_evidence_link, axis=1)
        live_display = [
            "brand", "distribution_type", "status", "annual_premium",
            "evidence", "evidence_timestamp", "failure_reason",
        ]
        st.dataframe(
            live_df[[c for c in live_display if c in live_df.columns]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("##### Evidence detail (live-tested)")
        for entry in live_tested:
            badge = status_badge(entry.get("status", ""))
            with st.expander(
                f"{entry.get('brand_or_program', entry['registry_id'])}  ·  "
                f"{str(entry.get('status', '')).replace('_', ' ')}",
                expanded=False,
            ):
                st.markdown(badge, unsafe_allow_html=True)
                st.markdown(f"**Evidence**  \n`{format_evidence_link(entry)}`")
                st.markdown(f"**Source URL**  \n{entry.get('source_url') or 'n/a'}")
                st.markdown(f"**Evidence timestamp**  \n{entry.get('evidence_timestamp') or 'n/a'}")
                artifact = _resolve_artifact(entry.get("evidence_artifact_path", "") or entry.get("evidence_url", ""))
                if artifact:
                    st.image(str(artifact), caption="Redacted evidence screenshot")
                elif entry.get("evidence_artifact_path") or entry.get("evidence_url"):
                    st.caption("Screenshot not found locally. Path recorded in report.")
                reason = entry.get("failure_reason") or entry.get("next_action")
                if reason:
                    st.markdown(f"**Outcome notes**  \n{reason}")
    else:
        st.info("No live-tested routes with evidence yet.")

    with st.expander(
        f"Discovery-stage seed entries (not yet attempted) ({len(seed_only)})",
        expanded=False,
    ):
        st.caption(
            "Appendix A market-mapping leads. No live attempt. Excluded from "
            "evidence-backed completion counts."
        )
        if seed_only:
            seed_df = pd.DataFrame(seed_only)
            seed_display = [
                "brand_or_program", "distribution_type", "legal_underwriter", "automation_notes",
            ]
            st.dataframe(
                seed_df[[c for c in seed_display if c in seed_df.columns]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("All registry entries have live evidence.")

    section_close()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def render_registry():
    section_open(
        "Market registry",
        "All Appendix A insurer groups: direct, aggregator, broker, affinity, mutual, and residual routes.",
    )
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
    section_open(
        "Execute quote routes",
        "Attempts every route in your registry and records what actually happens.",
    )

    st.caption(
        "Opens a live browser for each route. Stops safely at any CAPTCHA, "
        "declaration, or payment step."
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
            with st.spinner("Running routes. Watch the browser windows…"):
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
