import streamlit as st
import datetime
import pandas as pd
import numpy as np

# =========================
# Polar CUDA – Daily Risk Index (Prototype v2)
# =========================

st.set_page_config(page_title="Polar CUDA", layout="wide")

# --- Date ---
today = datetime.date.today()
st.markdown("### Polar CUDA")
st.caption(f"Date: {today}")

# --- Sample daily data (to be replaced by NSIDC v4 fetch) ---
data = {
    "date": pd.date_range(end=today, periods=7),
    "risk": [42.1, 43.0, 44.5, 45.2, 46.0, 46.8, 47.6],
}
df = pd.DataFrame(data)

today_risk = df.iloc[-1]["risk"]
yesterday_risk = df.iloc[-2]["risk"]
delta = today_risk - yesterday_risk

# --- Status ---
if today_risk < 30:
    status = "Low"
elif today_risk < 60:
    status = "Moderate"
else:
    status = "High"

# --- Main Display ---
st.markdown("## Polar Risk Index")
st.metric(
    label="Current Status",
    value=f"{today_risk:.1f} / 100",
    delta=f"{delta:+.1f}",
)

st.progress(int(today_risk))

st.success(f"Status: {status}")

st.markdown(
    "Guidance: Conditions are generally manageable, but localized or short-term risks may be present."
)

# --- 7-day trend ---
st.markdown("### 7-day Risk Trend")
st.line_chart(df.set_index("date")["risk"])

# --- Footer ---
st.divider()
st.caption(
    "Data sources (planned): NOAA/NSIDC Sea Ice Index v4 (AMSR2), wind reanalysis, ice drift products. "
    "This index is provided for situational awareness only and does not constitute operational or navigational guidance."
)
Update app.py with daily trend and change indicator
