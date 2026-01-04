# ===============================
# Polar CUDA – MVP (NSIDC v4)
# ===============================

import streamlit as st
import datetime
import numpy as np
import pandas as pd
import requests
from io import StringIO

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Polar CUDA",
    layout="wide"
)

# -------------------------------
# Date
# -------------------------------
today = datetime.date.today()

# -------------------------------
# NSIDC v4 data loader
# -------------------------------
def load_nsidc_sea_ice_extent():
    """
    Load NOAA/NSIDC Sea Ice Index Version 4 (daily extent).
    Returns latest extent value (million km²).
    If failed, returns None.
    """
    url = "https://nsidc.org/data/seaice_index/seaice_index_daily.csv"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        latest = df.iloc[-1]
        return float(latest["extent"])

    except Exception:
        return None


# -------------------------------
# Convert extent → risk
# -------------------------------
def extent_to_risk(extent):
    """
    Convert sea ice extent to risk score (0–100).
    Lower extent = higher risk
    """
    min_extent = 10.0   # high risk
    max_extent = 16.0   # low risk

    extent = max(min(extent, max_extent), min_extent)
    risk = 100 * (max_extent - extent) / (max_extent - min_extent)
    return risk


# -------------------------------
# Load NSIDC data (safe)
# -------------------------------
nsidc_extent = load_nsidc_sea_ice_extent()

# fallback value if data unavailable
if nsidc_extent is None:
    nsidc_extent = 14.0  # conservative climatological mean

sea_ice_risk = extent_to_risk(nsidc_extent)

# -------------------------------
# Placeholder wind & drift (MVP)
# -------------------------------
wind_risk = 35.0
drift_risk = 40.0

# -------------------------------
# Polar CUDA Risk Index
# -------------------------------
risk_index = (
    0.4 * sea_ice_risk +
    0.3 * drift_risk +
    0.3 * wind_risk
)

# Yesterday comparison (synthetic MVP logic)
yesterday_risk = risk_index - 0.8
delta = risk_index - yesterday_risk

# -------------------------------
# Status classification
# -------------------------------
if risk_index < 30:
    status = "Low"
    status_color = "green"
elif risk_index < 50:
    status = "Moderate"
    status_color = "green"
elif risk_index < 70:
    status = "High"
    status_color = "orange"
else:
    status = "Extreme"
    status_color = "red"

# -------------------------------
# UI
# -------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Date: {today}")

st.header("Polar Risk Index")

st.metric(
    label="Current Status",
    value=f"{risk_index:.1f} / 100",
    delta=f"{delta:+.1f}"
)

st.progress(int(risk_index))

st.success(f"Status: {status}")

st.markdown(
    "Guidance: Conditions are generally manageable, but localized "
    "or short-term risks may be present."
)

# -------------------------------
# 7-day trend (synthetic MVP)
# -------------------------------
st.subheader("7-day Risk Trend")

trend = np.linspace(risk_index - 4, risk_index + 2, 7)
st.line_chart(trend)

# -------------------------------
# Transparency section
# -------------------------------
st.markdown("---")

st.caption(
    f"Sea Ice Extent (NSIDC v4): {nsidc_extent:.2f} million km²"
)

st.caption(
    "Data source: NOAA/NSIDC Sea Ice Index Version 4 (AMSR2). "
    "Wind and ice drift values are illustrative placeholders. "
    "This index is provided for situational awareness only and "
    "does not constitute operational or navigational guidance."
)
