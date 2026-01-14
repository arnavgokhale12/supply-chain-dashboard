import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")
st.title("Supply Chain Dashboard")

st.markdown("""
Welcome! This dashboard helps you understand **how smoothly goods are moving** through the economy.

Think of it like a health checkup for shipping and inventory:
- **When supply chains are healthy**, products move efficiently from factories to stores
- **When supply chains are stressed**, you might see shipping delays, empty shelves, or higher prices

We combine three key indicators into one easy-to-read score.
""")

@st.cache_data(ttl=60)
def get_json(path: str):
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

def get_regime_display(regime: str) -> tuple[str, str, str]:
    """Returns (emoji, color, plain english description) for a regime."""
    regime_map = {
        "low": ("🟢", "green", "Better than normal - supply chains are running smoothly"),
        "normal": ("🟡", "orange", "Normal conditions - typical levels of activity"),
        "elevated": ("🟠", "orange", "Elevated stress - some delays or bottlenecks"),
        "crisis": ("🔴", "red", "High stress - significant disruptions likely"),
    }
    return regime_map.get(regime, ("⚪", "gray", "Unknown"))

def score_to_plain_english(score: float) -> str:
    """Convert a numeric score to plain English."""
    if score <= -1.0:
        return "Much better than usual"
    elif score <= -0.5:
        return "Better than usual"
    elif score <= 0.5:
        return "About average"
    elif score <= 1.0:
        return "Worse than usual"
    else:
        return "Much worse than usual"

col_refresh, _ = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

try:
    latest = get_json("/v1/composite/latest")
except Exception as e:
    st.error(f"Could not connect to data service: {e}")
    st.stop()

# ---- Main Status Banner ----
regime = latest["composite"]["regime"]
score = latest["composite"]["score"]
emoji, color, description = get_regime_display(regime)

st.markdown("---")
st.subheader("Current Supply Chain Status")

status_col1, status_col2 = st.columns([1, 2])
with status_col1:
    st.markdown(f"### {emoji} {regime.upper()}")
    st.metric("Overall Score", f"{score:.2f}", help="Negative = healthier, Positive = more stressed")

with status_col2:
    st.info(f"""
    **What this means:** {description}

    **Score interpretation:** {score_to_plain_english(score)}

    *Data as of {latest['month']}*
    """)

st.markdown("---")

# ---- Individual Indicators with Context ----
st.subheader("What's Driving This?")
st.markdown("We track three key indicators. Here's what each one is telling us:")

ind1, ind2, ind3 = st.columns(3)

# GSCPI
gscpi_emoji, _, gscpi_desc = get_regime_display(latest['gscpi']['regime'])
with ind1:
    st.markdown(f"#### {gscpi_emoji} Shipping & Logistics")
    st.metric(
        "Global Supply Chain Pressure",
        f"{latest['gscpi']['value']:.2f}",
        delta=f"{latest['gscpi']['z_score']:.2f} vs normal",
        delta_color="inverse"
    )
    with st.expander("What is this?"):
        st.markdown("""
        **Measures:** How congested shipping routes are, delivery delays, and transportation bottlenecks worldwide.

        **In plain terms:** When this is high, it's harder and slower to ship goods. Think of it like traffic on highways - higher means more gridlock.

        **Source:** Federal Reserve Bank of New York
        """)

# Retail IR/SA
retail_emoji, _, retail_desc = get_regime_display(latest['retailirsa']['regime'])
with ind2:
    st.markdown(f"#### {retail_emoji} Store Inventory Levels")
    st.metric(
        "Inventory-to-Sales Ratio",
        f"{latest['retailirsa']['value']:.2f}",
        delta=f"{latest['retailirsa']['z_score']:.2f} vs normal",
        delta_color="normal"
    )
    with st.expander("What is this?"):
        st.markdown("""
        **Measures:** How much inventory stores have compared to how much they're selling.

        **In plain terms:**
        - **High ratio** = stores have lots of stock sitting around (maybe demand is weak, or they over-ordered)
        - **Low ratio** = shelves are emptier than usual (maybe demand is strong, or supply can't keep up)

        **Source:** U.S. Census Bureau via FRED
        """)

# Cass Freight
cass_emoji, _, cass_desc = get_regime_display(latest['cass']['regime'])
with ind3:
    st.markdown(f"#### {cass_emoji} Freight Activity")
    st.metric(
        "Cass Freight Index",
        f"{latest['cass']['value']:.3f}",
        delta=f"{latest['cass']['z_score']:.2f} vs normal",
        delta_color="normal"
    )
    with st.expander("What is this?"):
        st.markdown("""
        **Measures:** Volume of freight shipments across North America.

        **In plain terms:** How much stuff is actually being shipped by trucks and rail. More shipments = more economic activity.
        - **High** = lots of goods moving (busy economy)
        - **Low** = fewer shipments (slower economy)

        **Source:** Cass Information Systems via FRED
        """)

st.markdown("---")

# ---- Historical Chart ----
st.subheader("How Has This Changed Over Time?")

history = get_json("/v1/composite/history?window=365")
df = pd.DataFrame(history)
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")

st.markdown("""
This chart shows the overall supply chain health score over time.
- **Line above zero (gray dashed):** Supply chains are under stress
- **Line below zero:** Supply chains are healthier than average
- **The further from zero, the more extreme conditions are**
""")

# Create a more informative chart
chart_df = df.set_index("month")[["composite"]].copy()
chart_df.columns = ["Supply Chain Stress Score"]
st.line_chart(chart_df)

# Add regime legend
st.markdown("""
**How to read the score:**
| Score Range | Status | What It Means |
|-------------|--------|---------------|
| Below -0.5 | 🟢 Low | Supply chains running smoothly, goods flowing freely |
| -0.5 to 0.5 | 🟡 Normal | Typical conditions, nothing unusual |
| 0.5 to 1.5 | 🟠 Elevated | Some stress - possible delays or shortages |
| Above 1.5 | 🔴 Crisis | Significant disruptions - expect delays and shortages |
""")

st.markdown("---")

# ---- Detailed Table (collapsed by default) ----
with st.expander("📊 View Detailed Monthly Data"):
    st.markdown("""
    This table shows the raw data for each month. The "z-score" columns show how far
    each indicator is from its historical average (0 = average, positive = above average stress).
    """)

    display_df = df.copy()
    display_df = display_df.rename(columns={
        "month": "Month",
        "gscpi_z": "Shipping Pressure",
        "retailirsa_z": "Inventory Level",
        "cass_z": "Freight Activity",
        "composite": "Overall Score",
        "regime": "Status"
    })
    display_df = display_df[["Month", "Overall Score", "Status", "Shipping Pressure", "Inventory Level", "Freight Activity"]]

    st.dataframe(
        display_df.tail(36).style.format({
            "Overall Score": "{:.2f}",
            "Shipping Pressure": "{:.2f}",
            "Inventory Level": "{:.2f}",
            "Freight Activity": "{:.2f}",
        }),
        use_container_width=True
    )

# ---- Footer ----
st.markdown("---")
st.caption("""
**About this dashboard:** Data is updated monthly. Sources include the Federal Reserve Bank of New York (GSCPI),
U.S. Census Bureau (Retail Inventories), and Cass Information Systems (Freight Index).
The composite score combines these indicators using statistical normalization to create a single, easy-to-interpret measure.
""")

# Technical details hidden in expander
with st.expander("🔧 Technical Details"):
    st.markdown(f"**API Endpoint:** `{API_BASE}`")
    st.markdown("**Raw API Response:**")
    st.json(latest)
