import streamlit as st
import plotly.graph_objects as go
import datetime

# ==============================
# Polar CUDA – Operations Gauge
# ==============================

st.set_page_config(
    page_title="Polar CUDA – Operations Monitor",
    layout="centered"
)

# ------------------------------
# Header (minimal, professional)
# ------------------------------
today = datetime.date.today()
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:14px;">
        <span style="font-size:40px;">🧊</span>
        <div>
            <div style="font-size:34px; font-weight:700;">Polar CUDA</div>
            <div style="font-size:14px; color:#AAAAAA;">Date: {today}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# Region selector (fleet-ready)
# ------------------------------
region = st.selectbox(
    "Select Region",
    [
        "Entire Arctic (Pan-Arctic)",
        "Beaufort Sea",
        "Chukchi Sea",
        "East Siberian Sea",
        "Laptev Sea",
        "Kara Sea"
    ]
)

# ------------------------------
# Example risk values
# (→ later replaced by NSIDC v4)
# ------------------------------
region_risk = {
    "Entire Arctic (Pan-Arctic)": 47.6,
    "Beaufort Sea": 52.3,
    "Chukchi Sea": 44.1,
    "East Siberian Sea": 58.7,
    "Laptev Sea": 61.9,
    "Kara Sea": 39.8
}

risk_index = region_risk[region]

# ------------------------------
# Status label
# ------------------------------
if risk_index < 30:
    status_label = "LOW"
elif risk_index < 50:
    status_label = "MODERATE"
elif risk_index < 70:
    status_label = "HIGH"
else:
    status_label = "EXTREME"

# ------------------------------
# Plotly Gauge (Fear & Greed style)
# ------------------------------
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=risk_index,
    number={
        "font": {"size": 64},
        "suffix": ""
    },
    title={
        "text": f"<b>{status_label}</b>",
        "font": {"size": 20}
    },
    gauge={
        "axis": {
            "range": [0, 100],
            "tickwidth": 1,
            "tickcolor": "white"
        },
        "bar": {
            "color": "#3498DB",
            "thickness": 0.25
        },
        "steps": [
            {"range": [0, 30], "color": "#1ABC9C"},    # SAFE
            {"range": [30, 50], "color": "#F1C40F"},  # MODERATE
            {"range": [50, 70], "color": "#E67E22"},  # HIGH
            {"range": [70, 100], "color": "#E74C3C"}  # EXTREME
        ],
        "threshold": {
            "line": {"color": "black", "width": 4},
            "thickness": 0.8,
            "value": risk_index
        }
    }
))

fig.update_layout(
    height=450,
    margin=dict(l=20, r=20, t=40, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white")
)

# ------------------------------
# Display (visual-first)
# ------------------------------
st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# Minimal guidance bar
# ------------------------------
st.markdown(
    f"""
    <div style="
        margin-top:10px;
        padding:14px;
        border-radius:8px;
        background-color:rgba(46, 204, 113, 0.15);
        font-size:15px;
    ">
        <b>Operational Guidance:</b>
        Conditions are generally manageable, but localized or short-term risks may be present.
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# Footer (policy-safe)
# ------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="font-size:12px; color:#888888;">
    Data sources (planned): NOAA/NSIDC Sea Ice Index v4 (AMSR2), wind reanalysis, ice drift products.<br>
    This display is for situational awareness only and does not constitute operational or navigational guidance.
    </div>
    """,
    unsafe_allow_html=True
)
