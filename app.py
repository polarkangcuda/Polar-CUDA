# =========================================================
# Polar CUDA – Operational Risk Dashboard (Fleet Manager)
# NSIDC Sea Ice Index v4 (Read-only, public data)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Polar CUDA – Fleet Operations",
    layout="wide"
)

# ---------------------------------------------------------
# Sidebar – Region Selector
# ---------------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": "pan_arctic",
    "Beaufort Sea": "beaufort",
    "Chukchi Sea": "chukchi",
    "East Siberian Sea": "east_siberian"
}

st.sidebar.title("🧭 Operational Controls")
region_label = st.sidebar.selectbox("Select Region", list(REGIONS.keys()))
region_key = REGIONS[region_label]

# ---------------------------------------------------------
# Data source (NSIDC v4 – simplified operational proxy)
# NOTE:
# NSIDC v4 region-specific daily CSV is not always uniform.
# For MVP safety, we:
# 1) pull Pan-Arctic daily extent (official)
# 2) apply region scaling factors (documented proxy)
# ---------------------------------------------------------
NSIDC_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

REGION_SCALE = {
    "pan_arctic": 1.00,
    "beaufort": 0.18,
    "chukchi": 0.14,
    "east_siberian": 0.16
}

@st.cache_data(ttl=3600)
def load_nsidc_data():
    r = requests.get(NSIDC_URL, timeout=20)
    r.raise_for_status()
    df = pd.read_csv(NSIDC_URL, skiprows=1)
    df["date"] = pd.to_datetime(
        dict(year=df.Year, month=df.Month, day=df.Day)
    )
    return df[["date", "Extent"]]

df = load_nsidc_data()

# ---------------------------------------------------------
# Region-adjusted ice extent (operational proxy)
# ---------------------------------------------------------
df["region_extent"] = df["Extent"] * REGION_SCALE[region_key]

latest = df.iloc[-1]
yesterday = df.iloc[-2]

extent_today = latest["region_extent"]
extent_yesterday = yesterday["region_extent"]

delta_extent = extent_today - extent_yesterday

# ---------------------------------------------------------
# Risk Index (operational, explainable)
# ---------------------------------------------------------
def normalize(value, vmin, vmax):
    value = max(min(value, vmax), vmin)
    return 100 * (value - vmin) / (vmax - vmin)

ice_risk = normalize(15 - extent_today, 0, 15)

# Placeholder environmental components (safe MVP)
wind_risk = 45
drift_risk = 40

risk_index = round(
    0.5 * ice_risk + 0.3 * wind_risk + 0.2 * drift_risk, 1
)

# ---------------------------------------------------------
# Status logic
# ---------------------------------------------------------
if risk_index < 30:
    status = "Low"
elif risk_index < 50:
    status = "Moderate"
elif risk_index < 70:
    status = "High"
else:
    status = "Extreme"

arrow = "⬆️" if delta_extent < 0 else "⬇️"

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Region: **{region_label}**")
st.caption(f"Data date: {latest['date'].date()}")

# ---------------------------------------------------------
# KPI Row
# ---------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Polar Risk Index",
    f"{risk_index} / 100",
    status
)

c2.metric(
    "Sea Ice Extent (proxy, M km²)",
    f"{extent_today:.2f}",
    f"{arrow} {abs(delta_extent):.2f}"
)

c3.metric("Wind Risk", wind_risk)
c4.metric("Ice Drift Risk", drift_risk)

st.progress(int(risk_index))

# ---------------------------------------------------------
# Guidance
# ---------------------------------------------------------
st.subheader("Operational Guidance")

GUIDANCE = {
    "Low": "Normal operations possible. Maintain routine monitoring.",
    "Moderate": "Operations manageable. Enhanced watch recommended.",
    "High": "Conservative routing advised. Icebreaker support likely.",
    "Extreme": "Avoid operations. High probability of ice interference."
}

st.info(GUIDANCE[status])

# ---------------------------------------------------------
# 7-day Trend
# ---------------------------------------------------------
st.subheader("7-Day Risk Trend")

df_recent = df.tail(7).copy()
df_recent["risk"] = (
    0.5 * normalize(15 - df_recent["region_extent"], 0, 15)
    + 0.3 * wind_risk
    + 0.2 * drift_risk
)

st.line_chart(
    df_recent.set_index("date")["risk"]
)

# ---------------------------------------------------------
# Fleet Operations Panel
# ---------------------------------------------------------
st.subheader("Fleet & Schedule Monitoring")

fleet_df = pd.DataFrame({
    "Vessel": ["ARAON-1", "Polar Trader-7", "Arctic Supply-3"],
    "Status": ["En-route", "Standby", "Ice Escort"],
    "Region": [region_label, "Beaufort Sea", "Chukchi Sea"],
    "Risk Exposure": ["Moderate", "Low", "High"]
})

st.dataframe(fleet_df, use_container_width=True)

# ---------------------------------------------------------
# Footer – Policy wording
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data sources:**  
NOAA/NSIDC Sea Ice Index Version 4 (AMSR2), public operational release.

**Disclaimer:**  
This product is provided for situational awareness and planning support only.  
It does **not** constitute navigational advice, ice routing guidance, or safety certification.  
Final operational decisions remain the responsibility of vessel masters and operators.
"""
)
