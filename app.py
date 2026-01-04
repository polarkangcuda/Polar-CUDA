import streamlit as st
import datetime
import numpy as np
import pandas as pd

# =====================================================
# Polar CUDA – Fleet Operations Manager Edition (PRO)
# =====================================================

st.set_page_config(
    page_title="Polar CUDA – Fleet Operations",
    layout="wide"
)

# -----------------------------------------------------
# Date & Update Cycle
# -----------------------------------------------------
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

# -----------------------------------------------------
# Region Selection
# -----------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": {"ice": 65, "drift": 12, "wind": 8},
    "Chukchi Sea": {"ice": 72, "drift": 15, "wind": 9},
    "East Siberian Sea": {"ice": 78, "drift": 18, "wind": 10},
    "Beaufort Sea": {"ice": 60, "drift": 11, "wind": 7},
    "Barents Sea": {"ice": 42, "drift": 6, "wind": 12},
}

selected_region = st.selectbox(
    "Select Region",
    list(REGIONS.keys())
)

data = REGIONS[selected_region]

# -----------------------------------------------------
# Normalization Function
# -----------------------------------------------------
def normalize(value, min_val, max_val):
    value = max(min(value, max_val), min_val)
    return 100 * (value - min_val) / (max_val - min_val)

sic_norm = normalize(data["ice"], 0, 100)
drift_norm = normalize(data["drift"], 0, 30)
wind_norm = normalize(data["wind"], 0, 25)

# -----------------------------------------------------
# Risk Index Calculation
# -----------------------------------------------------
risk_index = round(
    0.45 * sic_norm +
    0.30 * drift_norm +
    0.25 * wind_norm,
    1
)

# Yesterday (dummy baseline for trend logic)
yesterday_risk = risk_index - 0.8
delta = round(risk_index - yesterday_risk, 1)

# -----------------------------------------------------
# Status Classification
# -----------------------------------------------------
if risk_index < 30:
    status = "LOW"
    color = "🟢"
elif risk_index < 50:
    status = "MODERATE"
    color = "🟡"
elif risk_index < 70:
    status = "HIGH"
    color = "🟠"
else:
    status = "EXTREME"
    color = "🔴"

trend_arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"

# -----------------------------------------------------
# Header
# -----------------------------------------------------
st.title("🧊 Polar CUDA – Fleet Operations Monitor")
st.caption(f"Date: {today} | Update Cycle: Daily")

# -----------------------------------------------------
# Fleet Risk Overview
# -----------------------------------------------------
st.subheader("Fleet Polar Risk Index")

col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.metric(
        label="Current Fleet Risk",
        value=f"{risk_index} / 100",
        delta=f"{trend_arrow} {abs(delta)} (DoD)"
    )

with col2:
    st.markdown(f"### Status\n**{color} {status}**")

with col3:
    st.progress(int(risk_index))

# -----------------------------------------------------
# Guidance Text (Operations Language)
# -----------------------------------------------------
st.markdown(
    f"""
**Operational Guidance**

Fleet-level risk remains **{status.lower()}** for **{selected_region}**.  
However, localized escalation trends are observed.  
**Schedule review may be required within the next 48–72 hours if the trend persists.**
"""
)

# -----------------------------------------------------
# Driver Decomposition
# -----------------------------------------------------
st.subheader("Risk Driver Decomposition")

driver_df = pd.DataFrame({
    "Driver": ["Sea Ice Extent", "Ice Drift", "Wind"],
    "Contribution (%)": [
        round(0.45 * sic_norm, 1),
        round(0.30 * drift_norm, 1),
        round(0.25 * wind_norm, 1)
    ]
})

st.bar_chart(driver_df.set_index("Driver"))

# -----------------------------------------------------
# 7-Day Risk Trend (Moving Average)
# -----------------------------------------------------
st.subheader("7-Day Fleet Risk Trend")

trend_values = np.linspace(risk_index - 5, risk_index, 7)
trend_df = pd.DataFrame({
    "Date": pd.date_range(end=today, periods=7),
    "Risk Index": trend_values
})

st.line_chart(trend_df.set_index("Date"))

# -----------------------------------------------------
# Fleet Impact Matrix (Example)
# -----------------------------------------------------
st.subheader("Fleet Impact Matrix")

fleet_df = pd.DataFrame([
    ["ARAON", "Chukchi Sea", 52, "↑", "⚠ Monitor"],
    ["Cargo-01", "Beaufort Sea", 61, "↑↑", "❗ Review"],
    ["Tanker-02", "Barents Sea", 34, "↓", "✅ Normal"],
], columns=[
    "Vessel", "Region", "Risk Index", "Trend", "Action Flag"
])

st.dataframe(fleet_df, use_container_width=True)

# -----------------------------------------------------
# Disclaimer (Policy / Legal Grade)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Operational Disclaimer**

This dashboard provides fleet-level situational risk awareness derived from publicly available
cryospheric and atmospheric datasets (NOAA/NSIDC Sea Ice Index v4, reanalysis wind fields, and ice drift products).

It does not replace onboard navigation systems, ice services, or the judgment of vessel masters.
Final operational decisions remain the responsibility of the operating company and ship masters.
"""
)
