import streamlit as st
import datetime

# =====================================================
# Polar CUDA – Fleet Operations Manager (Status Only)
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

# Yesterday (baseline for day-over-day logic)
yesterday_risk = risk_index - 0.8
delta = round(risk_index - yesterday_risk, 1)

# -----------------------------------------------------
# Status Classification (CORE LOGIC)
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
# Fleet Risk Overview (No Graphs / No Tables)
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
# Operational Guidance
# -----------------------------------------------------
st.markdown(
    f"""
**Operational Guidance**

Fleet-level risk remains **{status.lower()}** for **{selected_region}**.  
Localized escalation trends may occur depending on synoptic conditions.

**Operational review is recommended within 48–72 hours if the trend persists.**
"""
)

# -----------------------------------------------------
# Disclaimer (Policy / Legal Grade)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Operational Disclaimer**

This dashboard provides fleet-level situational awareness derived from
aggregated cryospheric and atmospheric indicators.

It does not replace onboard navigation systems, ice services, or the
professional judgment of vessel masters. Final operational decisions
remain the responsibility of the operating company and ship masters.
"""
)
