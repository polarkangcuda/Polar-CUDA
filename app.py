import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="Polar CUDA – Operational Risk Monitor",
    layout="wide"
)

# =========================================================
# Title
# =========================================================
st.title("🧊 Polar CUDA")
st.caption("Operational Risk Monitor for Arctic Navigation")

# =========================================================
# Sidebar – Operational controls
# =========================================================
st.sidebar.header("⚙️ Operational Controls")

region = st.sidebar.selectbox(
    "Select Region",
    [
        "Entire Arctic (Pan-Arctic)",
        "Beaufort Sea",
        "Chukchi Sea",
        "East Siberian Sea"
    ]
)

# =========================================================
# Load NSIDC v4 data (SAFE)
# =========================================================
@st.cache_data(ttl=3600)
def load_nsidc_data():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df["date"] = pd.to_datetime(df[["Year", "Month", "Day"]])

    df = df[["date", "Extent"]].dropna()
    return df


df = load_nsidc_data()

# =========================================================
# Region weighting (operational approximation)
# =========================================================
REGION_WEIGHT = {
    "Entire Arctic (Pan-Arctic)": 1.00,
    "Beaufort Sea": 1.08,
    "Chukchi Sea": 1.12,
    "East Siberian Sea": 1.15
}

weight = REGION_WEIGHT[region]

# =========================================================
# Risk index calculation
# =========================================================
def calculate_risk(extent):
    # Normalization (lower ice = higher risk)
    norm = np.clip((12 - extent) / 12, 0, 1)
    return round(norm * 100 * weight, 1)


df["risk"] = df["Extent"].apply(calculate_risk)

latest = df.iloc[-1]
previous = df.iloc[-2]

risk_today = latest["risk"]
risk_yesterday = previous["risk"]
delta = round(risk_today - risk_yesterday, 1)

# =========================================================
# Status classification
# =========================================================
if risk_today < 30:
    status = "Low"
    color = "🟢"
elif risk_today < 55:
    status = "Moderate"
    color = "🟡"
elif risk_today < 75:
    status = "High"
    color = "🟠"
else:
    status = "Extreme"
    color = "🔴"

# =========================================================
# Main display
# =========================================================
st.subheader("📍 Region")
st.markdown(f"**{region}**")

st.subheader("📊 Polar Risk Index")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Current Risk",
        value=f"{risk_today} / 100",
        delta=f"{delta:+}"
    )

with col2:
    st.markdown("**Status**")
    st.markdown(f"{color} **{status}**")

with col3:
    st.markdown("**Data Date**")
    st.markdown(latest["date"].strftime("%Y-%m-%d"))

st.progress(int(min(risk_today, 100)))

# =========================================================
# Guidance
# =========================================================
st.markdown("### 🧭 Operational Guidance")

if status == "Low":
    guidance = "Normal operations acceptable."
elif status == "Moderate":
    guidance = "Heightened awareness advised. Monitor regional changes."
elif status == "High":
    guidance = "Conservative routing and ice support recommended."
else:
    guidance = "Avoid operations. Severe ice risk conditions."

st.info(guidance)

# =========================================================
# 7-day trend
# =========================================================
st.markdown("### 📈 7-day Risk Trend")

trend = df.tail(7).copy()
trend = trend.set_index("date")

st.line_chart(trend["risk"])

# =========================================================
# Footer – policy safe wording
# =========================================================
st.markdown("---")
st.caption(
    "Data source: NOAA/NSIDC Sea Ice Index v4 (AMSR2). "
    "This index is provided for situational awareness only. "
    "It does not constitute navigational, legal, or operational authority."
)
