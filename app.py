import streamlit as st
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Polar CUDA – Operational Risk Monitor",
    layout="wide",
)

# --------------------------------------------------
# Header
# --------------------------------------------------
today = datetime.date.today()

st.markdown("## 🧊 Polar CUDA")
st.caption(f"Date: {today}")

# --------------------------------------------------
# Region selector (operational view)
# --------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 47.6,
    "Chukchi Sea": 52.3,
    "Beaufort Sea": 44.8,
    "East Siberian Sea": 58.1,
    "Laptev Sea": 61.5,
}

region = st.selectbox("Select Region", list(REGIONS.keys()))
risk_index = REGIONS[region]

# Dummy yesterday value (placeholder for real data)
yesterday_risk = risk_index - 0.8
delta = risk_index - yesterday_risk

# --------------------------------------------------
# Risk category
# --------------------------------------------------
def risk_category(value):
    if value < 30:
        return "Low", "🟢"
    elif value < 60:
        return "Moderate", "🟡"
    else:
        return "High", "🔴"

status, icon = risk_category(risk_index)

# --------------------------------------------------
# Gauge (visual only – professional style)
# --------------------------------------------------
fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=risk_index,
        number={"suffix": " / 100"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4da6ff"},
            "steps": [
                {"range": [0, 30], "color": "#1f3d2b"},
                {"range": [30, 60], "color": "#2f4f4f"},
                {"range": [60, 100], "color": "#4f2f2f"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 4},
                "thickness": 0.75,
                "value": risk_index,
            },
        },
    )
)

fig.update_layout(
    height=360,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="#0e1117",
    font={"color": "white"},
)

# --------------------------------------------------
# Layout
# --------------------------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Polar Risk Index")
    st.markdown(f"### {risk_index:.1f} / 100")
    st.markdown(
        f"{icon} **{status}**  "
        f"{'▲' if delta > 0 else '▼'} {abs(delta):.1f} vs yesterday"
    )

with col2:
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Guidance
# --------------------------------------------------
if status == "Low":
    guidance = "Conditions are favorable for navigation with routine monitoring."
elif status == "Moderate":
    guidance = "Conditions are generally manageable, but localized or short-term risks may be present."
else:
    guidance = "Elevated operational risk. Enhanced ice navigation and contingency planning recommended."

st.info(f"**Guidance:** {guidance}")

# --------------------------------------------------
# 7-day trend (placeholder → real data 연결 예정)
# --------------------------------------------------
st.subheader("7-day Risk Trend")

dates = pd.date_range(end=today, periods=7)
trend = np.linspace(risk_index - 5, risk_index, 7)

trend_df = pd.DataFrame({"Date": dates, "Risk Index": trend})

st.line_chart(trend_df.set_index("Date"))

# --------------------------------------------------
# Footer – policy-grade disclaimer
# --------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data sources (planned):** NOAA/NSIDC Sea Ice Index v4 (AMSR2), atmospheric reanalysis winds,
sea-ice drift products.  
**Notice:** This index is provided for situational awareness and fleet-level risk monitoring only.
It does not constitute operational, navigational, or legal guidance.
"""
)
