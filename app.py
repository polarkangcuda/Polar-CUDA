# =========================================================
# Polar CUDA – Operational Risk Dashboard (Stable Edition)
# No external visualization libraries (Plotly-free)
# =========================================================

import streamlit as st
import datetime
import pandas as pd
import numpy as np

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Polar CUDA – Fleet Risk Monitor",
    layout="wide"
)

# -----------------------------
# Sidebar: Region selection
# -----------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 47.6,
    "Beaufort Sea": 52.1,
    "Chukchi Sea": 49.3,
    "East Siberian Sea": 55.4,
    "Laptev Sea": 58.2,
    "Kara Sea": 50.7
}

selected_region = st.selectbox(
    "Select Region",
    list(REGIONS.keys())
)

# -----------------------------
# Date
# -----------------------------
today = datetime.date.today()
st.caption(f"Date: {today}")

# -----------------------------
# Risk values (placeholder → real data replaceable)
# -----------------------------
current_risk = REGIONS[selected_region]
yesterday_risk = current_risk - np.random.uniform(-1.5, 1.5)
delta = round(current_risk - yesterday_risk, 1)

# -----------------------------
# Status classification
# -----------------------------
def risk_status(value):
    if value < 30:
        return "Low", "🟢"
    elif value < 50:
        return "Moderate", "🟢"
    elif value < 70:
        return "High", "🟠"
    else:
        return "Extreme", "🔴"

status_text, status_icon = risk_status(current_risk)

# -----------------------------
# Header
# -----------------------------
st.title("🧊 Polar CUDA")
st.subheader("Polar Risk Index – Operational View")

# -----------------------------
# Main KPI
# -----------------------------
col1, col2 = st.columns([1, 3])

with col1:
    st.metric(
        label="Current Risk Index",
        value=f"{current_risk:.1f} / 100",
        delta=f"{delta:+.1f}"
    )
    st.markdown(f"**Status:** {status_icon} {status_text}")

with col2:
    st.progress(int(current_risk))

# -----------------------------
# Guidance
# -----------------------------
GUIDANCE = {
    "Low": "Conditions are generally favorable for operations.",
    "Moderate": "Conditions are manageable, but localized or short-term risks may be present.",
    "High": "Operational caution advised. Ice, wind, or drift may restrict maneuverability.",
    "Extreme": "Operations not recommended without icebreaker escort and contingency planning."
}

st.info(f"**Guidance:** {GUIDANCE[status_text]}")

# -----------------------------
# 7-day trend (synthetic but structured)
# -----------------------------
dates = pd.date_range(end=today, periods=7)
trend = np.linspace(current_risk - 3, current_risk, 7) + np.random.normal(0, 0.4, 7)

trend_df = pd.DataFrame({
    "Date": dates,
    "Risk Index": trend
})

st.markdown("### 7-day Risk Trend")
st.line_chart(trend_df.set_index("Date"))

# -----------------------------
# Operational interpretation (manager-focused)
# -----------------------------
st.markdown("### Operational Interpretation")
st.write(
    """
- **Trend direction** supports short-term planning decisions (next 3–7 days).
- **Region-specific view** enables fleet-level risk differentiation.
- **Daily delta** highlights rapidly deteriorating or improving conditions.
- Intended for **situational awareness**, not autonomous navigation.
"""
)

# -----------------------------
# Footer: Data policy & disclaimer
# -----------------------------
st.markdown("---")
st.caption(
    """
**Data sources (planned integration):**  
NOAA/NSIDC Sea Ice Index Version 4 (AMSR2), wind reanalysis products, ice drift datasets.

**Disclaimer:**  
This index is provided for situational awareness and planning support only.  
It does not constitute operational, navigational, or legal guidance.  
Final decisions remain the responsibility of vessel masters and operators.
"""
)
