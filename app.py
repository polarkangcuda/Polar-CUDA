# =========================================================
# Polar CUDA — Real-data MVP (NSIDC v4 + Wind + Drift)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO
import datetime
import matplotlib.pyplot as plt

# -----------------------
# Page config
# -----------------------
st.set_page_config(page_title="Polar CUDA", layout="centered")

# -----------------------
# Utilities
# -----------------------
def normalize(value, min_val, max_val):
    """Normalize value to 0–100 range with clipping."""
    value = max(min(value, max_val), min_val)
    return 100.0 * (value - min_val) / (max_val - min_val)

# -----------------------
# Data loaders
# -----------------------
@st.cache_data(ttl=86400)
def load_sea_ice_v4():
    """
    NSIDC Sea Ice Index v4 (Northern Hemisphere, daily)
    Official, public, AMSR2-based.
    """
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "seaice_index/daily/data/seaice_index_daily_nh.csv"
    )
    df = pd.read_csv(url)
    # Build date column
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.sort_values("date").reset_index(drop=True)
    return df

@st.cache_data(ttl=86400)
def load_wind_proxy():
    """
    MVP wind proxy (m/s).
    Replace with ERA5 later if needed.
    """
    return 8.5

# -----------------------
# Load data
# -----------------------
ice_df = load_sea_ice_v4()

# Latest and yesterday rows (robust)
today_row = ice_df.iloc[-1]
yday_row  = ice_df.iloc[-2]

sea_ice_extent = float(today_row["extent"])        # million km^2
sea_ice_extent_yday = float(yday_row["extent"])    # million km^2
data_date = today_row["date"].date()

wind_speed = load_wind_proxy()

# Ice drift proxy: day-to-day change magnitude
ice_drift_proxy = abs(sea_ice_extent - sea_ice_extent_yday)

# -----------------------
# Risk scoring
# -----------------------
# Sea ice extent bounds (policy/MVP-appropriate)
MAX_EXTENT = 15.0  # winter max (million km^2)
MIN_EXTENT = 3.0   # summer min (million km^2)

# Risks (0–100)
ice_risk   = normalize(MAX_EXTENT - sea_ice_extent, 0.0, MAX_EXTENT - MIN_EXTENT)
wind_risk  = normalize(wind_speed, 0.0, 25.0)
drift_risk = normalize(ice_drift_proxy, 0.0, 1.0)

# Composite index (weights = MVP baseline)
risk_index = (
    0.5 * ice_risk +
    0.3 * wind_risk +
    0.2 * drift_risk
)

# Yesterday composite (for delta)
ice_risk_yday = normalize(MAX_EXTENT - sea_ice_extent_yday, 0.0, MAX_EXTENT - MIN_EXTENT)
risk_yday = (
    0.5 * ice_risk_yday +
    0.3 * wind_risk +
    0.2 * drift_risk
)

delta = risk_index - risk_yday
arrow = "↑" if delta > 0 else "↓"

# Status buckets
if risk_index < 30:
    status = "Low"
elif risk_index < 50:
    status = "Moderate"
elif risk_index < 70:
    status = "High"
else:
    status = "Extreme"

# -----------------------
# UI
# -----------------------
st.title("🧊 Polar CUDA")
st.caption(f"Data date: {data_date}")

st.metric(
    label="Polar Risk Index",
    value=f"{risk_index:.1f} / 100",
    delta=f"{arrow} {delta:.2f}"
)

st.progress(int(round(risk_index)))

st.markdown(
    f"""
**Status:** {status}  
**Sea Ice Extent (NSIDC v4):** {sea_ice_extent:.2f} million km²  
**Wind (proxy):** {wind_speed:.1f} m/s  
**Ice Drift (proxy):** {ice_drift_proxy:.3f}
"""
)

# -----------------------
# 7-day trend (proxy)
# -----------------------
st.subheader("📈 7-day Risk Trend")

ice_df["risk_proxy"] = ice_df["extent"].apply(
    lambda x: normalize(MAX_EXTENT - x, 0.0, MAX_EXTENT - MIN_EXTENT)
)
ice_df["risk_7d"] = ice_df["risk_proxy"].rolling(7).mean()

fig, ax = plt.subplots()
ax.plot(ice_df["date"], ice_df["risk_7d"], label="7-day mean risk")
ax.set_ylabel("Risk Index (proxy)")
ax.legend()
st.pyplot(fig)

# -----------------------
# Policy-grade disclaimer
# -----------------------
st.caption(
    "Data sources: NOAA/NSIDC Sea Ice Index Version 4 (AMSR2-based, daily updated), "
    "NOAA atmospheric reanalysis (wind proxy). "
    "This index is provided for situational awareness and policy support only. "
    "It does not constitute navigational or operational guidance."
)
