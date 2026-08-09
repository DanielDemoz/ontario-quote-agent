"""
Comparison UI. Run: streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

RESULTS_PATH = Path(__file__).parent / "results" / "results.json"
METRICS_PATH = Path(__file__).parent / "results" / "metrics.json"
REGISTRY_PATH = Path(__file__).parent / "registry" / "seed_registry.json"

st.set_page_config(page_title="Ontario All-Quote Agent", layout="wide")
st.title("Ontario All-Quote Agent — Comparison")
st.caption("Personal-use prototype. Local run only — see README for setup.")

if not RESULTS_PATH.exists():
    st.warning("No results yet. Run `python compile_real_results.py` or `python run_registry.py` first.")
    st.stop()

with open(RESULTS_PATH) as f:
    results = json.load(f)
with open(REGISTRY_PATH) as f:
    registry = {r["registry_id"]: r for r in json.load(f)}

if METRICS_PATH.exists():
    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    cols = st.columns(len(metrics))
    for col, (k, v) in zip(cols, metrics.items()):
        col.metric(k.replace("_", " ").title(), v)

st.divider()

df = pd.DataFrame(results)
if df.empty:
    st.info("No route results recorded yet.")
    st.stop()

# Market-layer breakdown — the brief specifically requires the registry
# to distinguish legal underwriter, group, brand, and distributor, so
# surface those directly rather than only the consumer-facing brand.
df["brand"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("brand_or_program", rid))
df["legal_underwriter"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("legal_underwriter", ""))
df["insurer_group"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("insurer_group", ""))
df["distribution_type"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("distribution_type", ""))

# Distinguish "attempted, no result yet" from "not attempted at all" -
# the latter has no evidence_timestamp AND an unresolved status with
# the specific not-attempted failure reason.
df["attempted"] = df["evidence_timestamp"].fillna("").astype(str).str.len() > 0

status_filter = st.multiselect(
    "Filter by status",
    options=sorted(df["status"].unique()),
    default=list(df["status"].unique()),
)
filtered = df[df["status"].isin(status_filter)]

show_not_attempted = st.checkbox("Show not-yet-attempted routes", value=True)
if not show_not_attempted:
    filtered = filtered[filtered["attempted"]]

sort_col = st.selectbox("Sort by", ["annual_premium", "status", "brand"], index=0)
filtered = filtered.sort_values(by=sort_col, na_position="last")

display_cols = [
    "brand", "legal_underwriter", "insurer_group", "distribution_type",
    "status", "annual_premium", "matches_benchmark", "confidence",
    "quote_or_reference_id", "evidence_timestamp", "failure_reason",
]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(filtered[display_cols], width="stretch", hide_index=True)

st.divider()
st.subheader("Evidence")
for _, row in filtered.iterrows():
    with st.expander(f"{row.get('brand', row['registry_id'])} — {row['status']}"):
        if not row.get("attempted", True) and row.get("status") != "manual_handoff":
            st.info("Not yet attempted live within the build window.")
        st.write(f"Source: {row.get('source_url') or '—'}")
        st.write(f"Evidence timestamp: {row.get('evidence_timestamp') or '—'}")
        artifact = row.get("evidence_artifact_path", "")
        if artifact and Path(artifact).exists():
            st.image(artifact, caption="Redacted evidence screenshot")
        if row.get("failure_reason"):
            st.write(f"Reason: {row['failure_reason']}")
        if row.get("next_action"):
            st.write(f"Next action: {row['next_action']}")
