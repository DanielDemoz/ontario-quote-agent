"""Binder — manila/ink field-dossier design system for Streamlit.

Global styles live in `.streamlit/style.css` (auto-loaded by Streamlit).
This module provides HTML component helpers only.
"""


def inject_theme():
    """No-op: Binder CSS is injected via .streamlit/style.css."""
    pass

def binder_hero(mode: str):
    import streamlit as st
    st.markdown(
        f"""
        <div class="binder-hero">
            <div class="case-number">CASE FILE — ONTARIO AUTO INSURANCE — MODE: {mode.upper()}</div>
            <h1>Binder</h1>
            <p style="font-family:'IBM Plex Sans',sans-serif; max-width:600px;">
                One intake. Every reachable rate. Evidence for every result.
                Guardrails enforced — nothing bound automatically. Local data only.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_open(title: str, subtitle: str = ""):
    import streamlit as st
    sub = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="section-card"><h3>{title}</h3>{sub}', unsafe_allow_html=True)


def section_close():
    import streamlit as st
    st.markdown("</div>", unsafe_allow_html=True)


def info_box(html: str):
    import streamlit as st
    st.markdown(f'<div class="info-panel">{html}</div>', unsafe_allow_html=True)


def warn_box(html: str):
    import streamlit as st
    st.markdown(f'<div class="warn-panel">{html}</div>', unsafe_allow_html=True)


def privacy_box(html: str):
    import streamlit as st
    st.markdown(f'<div class="privacy-panel">{html}</div>', unsafe_allow_html=True)


def render_stamp(status: str) -> str:
    """Render a status value as an ink-stamp badge."""
    color_map = {
        "quoted_comparable": "stamp-green",
        "quoted_non_comparable": "stamp-green",
        "estimate_only": "stamp-amber",
        "callback_required": "stamp-amber",
        "manual_handoff": "stamp-amber",
        "unresolved": "stamp-amber",
        "ineligible": "stamp-red",
        "affinity_restricted": "stamp-red",
        "blocked": "stamp-red",
        "unreachable": "stamp-red",
        "not_currently_writing": "stamp-red",
        "duplicate_rate_source": "stamp-amber",
        "specialty_only": "stamp-amber",
    }
    css_class = color_map.get(status, "stamp-amber")
    return f'<span class="stamp {css_class}">{status.replace("_", " ")}</span>'


def status_badge(status: str) -> str:
    """Alias for expander headers — uses ink stamps."""
    return render_stamp(status)


def render_stamp_ledger(rows: list[dict]) -> str:
    """HTML table: brand + underwriter + stamp for quick visual scan."""
    body = []
    for row in rows:
        brand = row.get("brand", row.get("registry_id", "—"))
        underwriter = row.get("legal_underwriter", "—") or "—"
        status = row.get("status", "unresolved")
        premium = row.get("annual_premium")
        premium_cell = f"${premium:,.0f}" if premium else "—"
        body.append(
            f"<tr>"
            f'<td class="route-name">{brand}</td>'
            f'<td class="mono">{underwriter[:48]}</td>'
            f"<td>{render_stamp(status)}</td>"
            f'<td class="mono">{premium_cell}</td>'
            f"</tr>"
        )
    return (
        '<table class="stamp-ledger">'
        "<thead><tr>"
        "<th>Route</th><th>Underwriter</th><th>Status</th><th>Premium</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )
