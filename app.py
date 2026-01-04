import streamlit as st
import datetime
import numpy as np

# -----------------------
# Polar CUDA - MVP (Web)
# -----------------------

today = datetime.date.today()

# (임시) 대표값
sea_ice_concentration = 65
ice_drift_speed = 12
wind_speed = 8

def normalize(value, min_val, max_val):
    value = max(min(value, max_val), min_val)
    return 100 * (value - min_val) / (max_val - min_val)

sic_norm   = normalize(sea_ice_concentration, 0, 100)
drift_norm = normalize(ice_drift_speed, 0, 30)
wind_norm  = normalize(wind_speed, 0, 25)

risk_index = 0.4*sic_norm + 0.3*drift_norm + 0.3*wind_norm

if risk_index < 30:
    status = "Low Risk"
elif risk_index < 50:
    status = "Moderate"
elif risk_index < 70:
    status = "High Risk"
else:
    status = "Extreme Risk"

if status == "Low Risk":
    message = "Current conditions indicate low operational risk."
elif status == "Moderate":
    message = ("Conditions are generally manageable, "
               "but localized or short-term risks may be present.")
elif status == "High Risk":
    message = ("Elevated risk detected. "
               "Conservative operational decisions are recommended.")
else:
    message = ("Extreme risk conditions detected. "
               "Operational avoidance is strongly advised.")

# ---- UI ----
st.set_page_config(page_title="Polar CUDA", layout="centered")

st.title("🧊 Polar CUDA")
st.caption(f"Date: {today}")

st.markdown("### Polar Risk Index")
st.metric(label="Current Status", value=f"{risk_index:.1f} / 100", delta=status)
st.progress(int(risk_index))

st.markdown(f"**Guidance:** {message}")

st.markdown("---")
st.caption(
    "This index is provided for situational awareness only. "
    "It does not constitute operational or navigational guidance."
)
