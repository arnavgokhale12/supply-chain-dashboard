import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")
st.title("Supply Chain Dashboard")

st.markdown("""
**What this dashboard shows**

This dashboard tracks **overall supply-chain stress** using a composite index built from
multiple macroeconomic indicators related to logistics, inventories, and delivery delays.

Each indicator is standardized (z-scored) and combined into a single monthly measure:
- **Positive values** indicate above-normal supply-chain stress
- **Negative values** indicate below-normal stress

The goal is to summarize complex supply-chain conditions into **one interpretable signal**
that can be tracked over time.
""")

@st.cache_data(ttl=60)
def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

colA, colB, colC = st.columns([1,1,1])
with colA:
    st.caption("API base")
    st.code(API_BASE)
with colB:
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()
with colC:
    st.caption("Endpoints")
    st.write("- /v1/composite/latest")
    st.write("- /series/{sid}/latest")

try:
    latest = get_json("/v1/composite/latest")
except Exception as e:
    st.error(f"Backend error: {e}")
    st.stop()

# ---- KPIs ----
st.caption("Composite score summarizes overall supply-chain stress. Individual indicators below show their latest values and standardized deviations.")
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Composite score",
    f"{latest['composite']['score']:.3f}",
    help=(
        "Overall supply-chain stress index. "
        "Positive values indicate above-normal stress; "
        "negative values indicate below-normal conditions. "
        "Magnitude reflects severity."
    ),
)

k2.metric(
    "Composite regime",
    latest["composite"]["regime"],
    help=(
        "Qualitative classification of supply-chain conditions "
        "based on the composite score (e.g., low, normal, high stress)."
    ),
)

k3.metric(
    "GSCPI",
    f"{latest['gscpi']['value']:.3f}",
    help=(
        "Global Supply Chain Pressure Index (New York Fed). "
        "Measures logistics congestion, delivery delays, and transportation bottlenecks. "
        "Shown as a standardized deviation from historical norms."
    ),
)

k4.metric(
    "Retail IR/SA",
    f"{latest['retailirsa']['value']:.3f}",
    help=(
        "Retail inventories-to-sales ratio. "
        "Higher values suggest inventory buildup relative to demand; "
        "lower values indicate tighter inventories."
    ),
)

st.divider()

# ---- Chart ----
history = get_json("/v1/composite/history?window=365")
df = pd.DataFrame(history)
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")

left, right = st.columns([2,1])

with left:
    st.markdown("""
    **Composite over time**

This chart shows the **composite supply-chain stress index**, a standardized measure that
summarizes conditions across multiple supply-chain indicators.

- Values **above zero** indicate above-average supply-chain stress  
- Values **below zero** indicate below-average stress  
- Larger magnitudes reflect more extreme conditions

The index is normalized so that zero represents typical historical conditions.

    """)
    st.subheader("Composite over time")
    st.line_chart(df.set_index("month")[["composite"]])

with right:
    st.subheader("Latest snapshot")
    st.json(latest)

st.divider()

st.markdown("""
**Recent monthly values**

This table shows the most recent composite values by month, allowing closer inspection
of short-term trends.
""")
st.subheader("Recent months (table)")

st.caption(
    "**Table guide:** "
    "`month` = observation month. "
    "`gscpi_z` = standardized (z-score) GSCPI value; positive means higher-than-normal logistics pressure. "
    "`retailirsa_z` = standardized (z-score) retail inventories-to-sales ratio; positive suggests inventory buildup vs demand. "
    "`composite` = combined stress index (weighted average of z-scores). "
    "`regime` = qualitative bucket derived from the composite score."
)

display_df = df.rename(columns={
    "month": "Month",
    "gscpi_z": "GSCPI (z-score)",
    "retailirsa_z": "Retail IR/SA (z-score)",
    "composite": "Composite score",
    "regime": "Regime"
})

st.dataframe(display_df.tail(36), width="stretch")
