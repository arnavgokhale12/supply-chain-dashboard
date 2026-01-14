"""Supply Chain Dashboard with Market Overlays."""
import os

import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")


# ============================================================================
# Data Fetching
# ============================================================================

@st.cache_data(ttl=60)
def get_json(path: str):
    """Fetch JSON from API with caching."""
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def get_market_data():
    """Fetch market data with longer cache."""
    try:
        return get_json("/v1/market/current")
    except Exception:
        return None


# ============================================================================
# Helper Functions
# ============================================================================

def get_regime_display(regime: str) -> tuple[str, str, str]:
    """Returns (emoji, color, description) for a regime."""
    regime_map = {
        "low": ("🟢", "green", "Better than normal - supply chains are running smoothly"),
        "normal": ("🟡", "orange", "Normal conditions - typical levels of activity"),
        "elevated": ("🟠", "darkorange", "Elevated stress - some delays or bottlenecks"),
        "crisis": ("🔴", "red", "High stress - significant disruptions likely"),
    }
    return regime_map.get(regime, ("⚪", "gray", "Unknown"))


def score_to_plain_english(score: float) -> str:
    """Convert score to plain English."""
    if score <= -1.0:
        return "Much better than usual"
    elif score <= -0.5:
        return "Better than usual"
    elif score <= 0.5:
        return "About average"
    elif score <= 1.0:
        return "Worse than usual"
    return "Much worse than usual"


def format_return(ret: float | None) -> str:
    """Format return as percentage with color indicator."""
    if ret is None:
        return "N/A"
    sign = "+" if ret >= 0 else ""
    return f"{sign}{ret:.1f}%"


def get_return_color(ret: float | None) -> str:
    """Get color for return display."""
    if ret is None:
        return "gray"
    return "green" if ret >= 0 else "red"


INDICATOR_INFO = {
    "gscpi": {
        "name": "Shipping & Logistics (GSCPI)",
        "description": "Measures worldwide shipping congestion, delivery delays, and transportation bottlenecks.",
        "interpretation": "Higher = more shipping gridlock, like traffic on highways.",
    },
    "retailirsa": {
        "name": "Retail Inventories",
        "description": "Ratio of store inventory to sales volume.",
        "interpretation": "High = stores overstocked. Low = shelves emptier than usual.",
    },
    "cass": {
        "name": "Cass Freight Index",
        "description": "Volume of freight shipments across North America.",
        "interpretation": "Higher = more goods moving. Lower = slower economic activity.",
    },
    "baltic_dry": {
        "name": "Baltic Dry Index",
        "description": "Cost of shipping raw materials by sea globally.",
        "interpretation": "Higher = strong demand for shipping. Lower = weak demand.",
    },
    "ism_supplier": {
        "name": "Manufacturing Employment",
        "description": "Employment levels in manufacturing sector.",
        "interpretation": "Higher = more manufacturing activity and hiring.",
    },
    "mfg_new_orders": {
        "name": "Manufacturing New Orders",
        "description": "New orders received by manufacturers.",
        "interpretation": "Higher = strong demand for manufactured goods.",
    },
    "wholesale_ratio": {
        "name": "Wholesale Inventories/Sales",
        "description": "Ratio of wholesale inventory to sales.",
        "interpretation": "High = inventory buildup. Low = tight supplies.",
    },
}


# ============================================================================
# Main App
# ============================================================================

st.title("Supply Chain Dashboard")

st.markdown("""
Welcome! This dashboard helps you understand **how smoothly goods are moving** through the economy.

Think of it like a health checkup for shipping and inventory:
- **When supply chains are healthy**, products move efficiently from factories to stores
- **When supply chains are stressed**, you might see shipping delays, empty shelves, or higher prices

We combine multiple economic indicators into one easy-to-read score, and show how different market sectors historically perform under various supply chain conditions.
""")

# Refresh button
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Fetch data
try:
    composite = get_json("/v1/composite/latest")
except Exception as e:
    st.error(f"Could not connect to backend: {e}")
    st.info("Make sure the backend is running: `uvicorn backend.app.main:app --reload`")
    st.stop()

# Check for error in composite
if "error" in composite:
    st.warning(f"Composite calculation issue: {composite.get('error')}")
    st.info("Run the seed and ingestion scripts to populate data.")
    st.stop()

market_data = get_market_data()
current_regime = composite.get("composite", {}).get("regime", "normal")

# ============================================================================
# Status Banner
# ============================================================================

regime = composite.get("composite", {}).get("regime", "normal")
score = composite.get("composite", {}).get("score", 0)
month = composite.get("month", "")
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

    *Data as of {month}*
    """)

st.markdown("---")

# ============================================================================
# Main Layout: Left (60%) and Right (40%)
# ============================================================================

left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📈 What's Driving This?")
    st.markdown("We track multiple key indicators. Here's what each one is telling us:")

    # Individual indicators in a grid
    indicator_cols = st.columns(2)

    idx = 0
    for key, data in composite.items():
        if key in ["month", "composite", "meta"]:
            continue
        if isinstance(data, dict) and "value" in data:
            info = INDICATOR_INFO.get(key, {"name": key, "description": "", "interpretation": ""})
            ind_emoji, _, _ = get_regime_display(data.get("regime", "normal"))
            z_score = data.get("z_score", 0)

            with indicator_cols[idx % 2]:
                st.markdown(f"#### {ind_emoji} {info['name']}")
                st.metric(
                    "Current Value",
                    f"{data.get('value', 0):.2f}",
                    delta=f"{z_score:+.2f} vs normal",
                    delta_color="inverse"
                )
                with st.expander("What is this?"):
                    st.markdown(f"""
                    **Measures:** {info['description']}

                    **In plain terms:** {info['interpretation']}

                    **Current status:** {get_regime_display(data.get('regime', 'normal'))[2]}
                    """)
            idx += 1

    # Historical chart
    st.markdown("---")
    st.subheader("📉 How Has This Changed Over Time?")

    try:
        history = get_json("/v1/composite/history")
        if history and isinstance(history, list):
            df = pd.DataFrame(history)
            df["month"] = pd.to_datetime(df["month"])
            df = df.sort_values("month")

            st.markdown("""
            This chart shows the overall supply chain health score over time.
            - **Line above zero:** Supply chains are under stress
            - **Line below zero:** Supply chains are healthier than average
            - **The further from zero, the more extreme conditions are**
            """)

            chart_df = df.set_index("month")[["composite"]].copy()
            chart_df.columns = ["Supply Chain Stress Score"]
            st.line_chart(chart_df)

            # Score guide
            st.markdown("""
            **How to read the score:**
            | Score Range | Status | What It Means |
            |-------------|--------|---------------|
            | Below -0.5 | 🟢 Low | Supply chains running smoothly |
            | -0.5 to 0.5 | 🟡 Normal | Typical conditions |
            | 0.5 to 1.5 | 🟠 Elevated | Some stress - possible delays |
            | Above 1.5 | 🔴 Crisis | Significant disruptions |
            """)
    except Exception as e:
        st.warning(f"Could not load history: {e}")

with right_col:
    st.subheader("📊 Market Impact")

    if not market_data or not market_data.get("symbols"):
        st.warning("**Market data not yet available**")
        st.markdown("""
        To enable market data and see how stocks perform during different supply chain conditions:

        1. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
        2. Add to your `.env` file:
           ```
           ALPHA_VANTAGE_API_KEY=your_key
           ```
        3. Run the ingestion:
           ```bash
           python -m backend.app.services.ingest_market_data
           python -m backend.app.services.regime_analyzer
           ```
        """)

        st.markdown("---")
        st.markdown(f"""
        **What you'll see once enabled:**

        Based on the current **{regime.upper()}** regime, we'll show:
        - How S&P 500 and sector ETFs historically perform
        - Which stocks (semiconductors, retail, logistics) tend to do well or poorly
        - Color-coded performance indicators
        """)
    else:
        # Regime context
        context = market_data.get("regime_context", {})
        sector_perf = context.get("sector_performance", {})

        st.markdown(f"""
        **Current Regime:** {current_regime.upper()}

        *Historical sector performance in {current_regime} conditions:*
        """)

        # Sector performance
        if sector_perf:
            for theme, stats in sector_perf.items():
                avg_ret = stats.get("avg_monthly_return", 0)
                color = "green" if avg_ret > 0 else "red"
                st.markdown(f"- **{theme.title()}**: <span style='color: {color};'>{avg_ret:+.1f}%/mo</span>", unsafe_allow_html=True)
        else:
            st.info("Run regime analyzer to compute historical performance.")

        st.divider()

        # Current market snapshot
        st.markdown("**Latest Prices:**")
        symbols = market_data.get("symbols", [])

        indices = [s for s in symbols if s.get("type") == "index"]
        etfs = [s for s in symbols if s.get("type") == "etf"]

        for symbol in indices + etfs:
            daily_ret = symbol.get("daily_return_pct")
            regime_avg = symbol.get("regime_avg_return_pct")
            ret_str = format_return(daily_ret)
            ret_color = get_return_color(daily_ret)

            comparison = ""
            if regime_avg is not None and daily_ret is not None:
                if daily_ret > regime_avg:
                    comparison = " ↑"
                elif daily_ret < regime_avg:
                    comparison = " ↓"

            st.markdown(f"**{symbol['symbol']}**: <span style='color: {ret_color};'>{ret_str}{comparison}</span>", unsafe_allow_html=True)

# ============================================================================
# Key Stocks Widget
# ============================================================================

st.markdown("---")
st.subheader("🎯 Key Stocks by Theme")

if not market_data or not market_data.get("symbols"):
    st.info("""
    **Coming soon:** Once market data is ingested, you'll see key stocks grouped by theme:
    - **🔲 Semiconductors** (NVDA, TSM, AVGO) - Highly exposed to global supply chains
    - **🛒 Retail** (COST, WMT) - Sensitive to inventory and freight costs
    - **📦 Logistics** (AMZN) - Affected by shipping and fulfillment costs

    Each stock will show its current performance color-coded based on how it compares to historical averages for the current supply chain regime.
    """)
else:
    symbols = market_data.get("symbols", [])
    stocks = [s for s in symbols if s.get("type") == "stock"]

    if stocks:
        # Group by theme
        themes: dict[str, list] = {}
        for stock in stocks:
            theme = stock.get("theme") or "other"
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(stock)

        theme_order = ["chips", "retail", "logistics", "other"]
        visible_themes = [t for t in theme_order if t in themes]

        theme_labels = {
            "chips": "🔲 Semiconductors",
            "retail": "🛒 Retail",
            "logistics": "📦 Logistics",
            "other": "📋 Other",
        }

        theme_descriptions = {
            "chips": "Highly exposed to complex global supply chains",
            "retail": "Sensitive to freight costs and inventory levels",
            "logistics": "Directly affected by shipping and fulfillment",
        }

        if visible_themes:
            cols = st.columns(len(visible_themes))

            for col, theme in zip(cols, visible_themes):
                with col:
                    st.markdown(f"**{theme_labels.get(theme, theme.title())}**")
                    st.caption(theme_descriptions.get(theme, ""))

                    for stock in themes[theme]:
                        daily_ret = stock.get("daily_return_pct")
                        regime_avg = stock.get("regime_avg_return_pct")
                        ret_str = format_return(daily_ret)
                        ret_color = get_return_color(daily_ret)

                        st.markdown(f"""
                        **{stock['symbol']}** - {stock['name'][:15]}...
                        <span style='color: {ret_color}; font-size: 1.2em;'>{ret_str}</span>
                        """, unsafe_allow_html=True)
    else:
        st.info("No stock data available yet.")

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.caption("""
**About this dashboard:** Data is updated monthly for supply chain indicators and daily for market data.
Sources include the Federal Reserve Bank of New York (GSCPI), FRED (economic indicators), and Alpha Vantage (market data).
The composite score combines indicators using z-score normalization with a 36-month rolling window.
""")

# Technical details (collapsed)
with st.expander("🔧 Technical Details"):
    st.markdown(f"**API Endpoint:** `{API_BASE}`")
    st.markdown("**Raw API Response:**")
    st.json(composite)

    if market_data:
        st.markdown("**Market API Response:**")
        st.json(market_data)
