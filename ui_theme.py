"""Shared HTML/CSS theming for the Streamlit frontend."""

BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Serif+Display&display=swap');

:root {
    --brand-navy: #0f2744;
    --brand-blue: #1e5a8a;
    --brand-teal: #0d9488;
    --brand-slate: #475569;
    --brand-bg: #f4f7fb;
    --brand-card: #ffffff;
    --brand-border: #e2e8f0;
    --brand-accent: #2563eb;
    --brand-success: #059669;
    --brand-warn: #d97706;
    --brand-danger: #dc2626;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

.hero {
    background: linear-gradient(135deg, var(--brand-navy) 0%, var(--brand-blue) 55%, var(--brand-teal) 100%);
    border-radius: 16px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.75rem;
    color: #fff;
    box-shadow: 0 12px 40px rgba(15, 39, 68, 0.18);
}
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.1rem;
    font-weight: 400;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
}
.hero p {
    margin: 0;
    opacity: 0.92;
    font-size: 1.02rem;
    line-height: 1.55;
    max-width: 720px;
}
.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1.25rem;
}
.badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}
.badge-light {
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.28);
    color: #fff;
}

.section-card {
    background: var(--brand-card);
    border: 1px solid var(--brand-border);
    border-radius: 14px;
    padding: 1.35rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 12px rgba(15, 39, 68, 0.04);
}
.section-card h3 {
    margin: 0 0 0.35rem 0;
    color: var(--brand-navy);
    font-size: 1.05rem;
    font-weight: 700;
}
.section-card .subtitle {
    color: var(--brand-slate);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

.info-panel {
    background: #eff6ff;
    border-left: 4px solid var(--brand-accent);
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.1rem;
    margin: 0.75rem 0 1.25rem 0;
    color: #1e3a5f;
    font-size: 0.92rem;
    line-height: 1.5;
}
.warn-panel {
    background: #fffbeb;
    border-left: 4px solid var(--brand-warn);
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.1rem;
    margin: 0.75rem 0 1.25rem 0;
    color: #78350f;
    font-size: 0.92rem;
    line-height: 1.5;
}
.privacy-panel {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-size: 0.88rem;
    color: #14532d;
    margin-bottom: 1rem;
}

.status-pill {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.status-quoted { background: #d1fae5; color: #065f46; }
.status-blocked { background: #fee2e2; color: #991b1b; }
.status-callback { background: #dbeafe; color: #1e40af; }
.status-unresolved { background: #fef3c7; color: #92400e; }
.status-handoff { background: #ede9fe; color: #5b21b6; }

.sidebar-brand {
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem;
    color: var(--brand-navy);
    margin-bottom: 0.25rem;
}
.metric-card {
    background: var(--brand-bg);
    border-radius: 10px;
    padding: 0.75rem;
    text-align: center;
}
.metric-card .label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--brand-slate);
}
.metric-card .value {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--brand-navy);
}

div[data-testid="stTabs"] button {
    font-weight: 600;
}
</style>
"""


def inject_theme():
    import streamlit as st
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, badges: list[str] | None = None):
    import streamlit as st
    badge_html = "".join(f'<span class="badge badge-light">{b}</span>' for b in (badges or []))
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="hero-badges">{badge_html}</div>
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


def status_badge(status: str) -> str:
    css = {
        "quoted_comparable": "status-quoted",
        "quoted_non_comparable": "status-quoted",
        "blocked": "status-blocked",
        "callback_required": "status-callback",
        "manual_handoff": "status-handoff",
        "affinity_restricted": "status-handoff",
    }.get(status, "status-unresolved")
    label = status.replace("_", " ")
    return f'<span class="status-pill {css}">{label}</span>'
