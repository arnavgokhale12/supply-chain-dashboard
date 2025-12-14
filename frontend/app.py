import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")
st.title("Supply Chain Dashboard")

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
    st.write("- /composite/latest")
    st.write("- /series/{sid}/latest")

try:
    latest = get_json("/composite/latest")
except Exception as e:
    st.error(f"Backend error: {e}")
    st.stop()

# ---- KPIs ----
k1, k2, k3, k4 = st.columns(4)
k1.metric("Composite score", f"{latest['composite']['score']:.3f}")
k2.metric("Composite regime", latest["composite"]["regime"])
k3.metric("GSCPI", f"{latest['gscpi']['value']:.3f}", help=f"z={latest['gscpi']['z_score']:.3f} • {latest['gscpi']['date']}")
k4.metric("Retail IR/SA", f"{latest['retailirsa']['value']:.3f}", help=f"z={latest['retailirsa']['z_score']:.3f} • {latest['retailirsa']['date']}")

st.divider()

# ---- Chart ----
history = get_json("/composite/history")
df = pd.DataFrame(history)
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values("month")

left, right = st.columns([2,1])

with left:
    st.subheader("Composite over time")
    st.line_chart(df.set_index("month")[["composite"]])

with right:
    st.subheader("Latest snapshot")
    st.json(latest)

st.divider()

st.subheader("Recent months (table)")
st.dataframe(df.tail(36), use_container_width=True)
