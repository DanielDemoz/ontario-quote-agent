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

if not RESULTS_PATH.exists():
    st.warning("No results yet. Run `python run_registry.py` first.")
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

df["brand"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("brand_or_program", rid))
df["distribution_type"] = df["registry_id"].map(lambda rid: registry.get(rid, {}).get("distribution_type", ""))

status_filter = st.multiselect(
    "Filter by status",
    options=sorted(df["status"].unique()),
    default=list(df["status"].unique()),
)
filtered = df[df["status"].isin(status_filter)]

show_estimates = st.checkbox("Show estimate-only results", value=True)
if not show_estimates:
    filtered = filtered[filtered["status"] != "estimate_only"]

sort_col = st.selectbox("Sort by", ["annual_premium", "status", "brand"], index=0)
filtered = filtered.sort_values(by=sort_col, na_position="last")

display_cols = [
    "brand", "distribution_type", "status", "annual_premium",
    "matches_benchmark", "confidence", "quote_or_reference_id",
    "evidence_timestamp", "failure_reason",
]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

st.divider()
st.subheader("Evidence")
for _, row in filtered.iterrows():
    with st.expander(f"{row.get('brand', row['registry_id'])} — {row['status']}"):
        st.write(f"Source: {row.get('source_url', '—')}")
        st.write(f"Evidence timestamp: {row.get('evidence_timestamp', '—')}")
        artifact = row.get("evidence_artifact_path", "")
        if artifact and Path(artifact).exists():
            st.image(artifact, caption="Redacted evidence screenshot")
        if row.get("failure_reason"):
            st.write(f"Reason: {row['failure_reason']}")
        if row.get("next_action"):
            st.write(f"Next action: {row['next_action']}")
