# ==========================================
# Polar CUDA – Regional MVP (Safe Version)
# ==========================================

import streamlit as st
import datetime
import numpy as np
import pandas as pd

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Polar CUDA",
    layout="centered"
)

# -------------------------
# Date
# -------------------------
today = datetime.date.today()

# -------------------------
# Region selector
# -------------------------
region = st.selectbox(
    "Select Region",
    [
        "Entire Arctic (Pan-Arctic)",
        "Chukchi Sea",
        "Beaufort Sea",
        "East Siberian Sea"
    ]
)

# -------------------------
# Data source note (MVP-safe)
# -------------------------
DATA_NOTE = {
    "Entire Arctic (Pan-Arctic)": "NSIDC Sea Ice Index v4 (Pan-Arctic)",
    "Chukchi Sea": "Placeholder (regional grid-based data not yet connected)",
    "Beaufort Sea": "Placeholder (regional grid-based data not yet connected)",
    "East Siberian Sea": "Placeholder (regional grid-based data not yet connected)",
}

# -------------------------
# Risk values (safe MVP logic)
# -------------------------
if region == "Entire Arctic (Pan-Arctic)":
    risk_index = 47.6
    delta = +0.8
    status = "Moderate"
else:
    # Placeholder values (clearly marked)
    risk_index = np.nan
    delta = None
    status = "N/A (Coming Soon)"

# -------------------------
# Header
# -------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Date: {today.isoformat()}")

st.markdown("## Polar Risk Index")

# -------------------------
# Main metric
# -------------------------
if not np.isnan(risk_index):
    st.metric(
        label="Current Status",
        value=f"{risk_index:.1f} / 100",
        delta=f"{delta:+.1f}"
    )
    st.progress(int(risk_index))
    st.success(f"Status: {status}")
else:
    st.metric(
        label="Current Status",
        value="—",
        delta="—"
    )
    st.info("Regional risk indices will be available after grid-based data integration.")

# -------------------------
# Guidance
# -------------------------
if not np.isnan(risk_index):
    st.markdown(
        "**Guidance:** Conditions are generally manageable, "
        "but localized or short-term risks may be present."
    )
else:
    st.markdown(
        "**Guidance:** Regional guidance will be provided once "
        "NSIDC grid-based sea ice concentration data are connected."
    )

# -------------------------
# 7-day trend (Pan-Arctic only, simulated)
# -------------------------
st.markdown("### 7-day Risk Trend")

if region == "Entire Arctic (Pan-Arctic)":
    days = pd.date_range(end=today, periods=7)
    values = np.linspace(43, risk_index, 7)
    trend_df = pd.DataFrame({"Date": days, "Risk Index": values})
    st.line_chart(trend_df.set_index("Date"))
else:
    st.info("7-day regional trends will be enabled in the next development phase.")

# -------------------------
# Footer: data & disclaimer
# -------------------------
st.markdown("---")
st.caption(
    f"""
**Data source:** {DATA_NOTE[region]}

This index is provided for situational awareness only.  
It does not constitute operational, navigational, or safety guidance.
"""
)
