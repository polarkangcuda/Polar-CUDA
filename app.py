import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Public Edition
# CUDA = Cryospheric Uncertainty–Driven Awareness
#
# A simple situational awareness gauge
# for Arctic sea-ice conditions.
#
# Not a navigation tool.
# Not a forecast.
# =========================================================

st.set_page_config(page_title="POLAR CUDA", layout="centered")

# ---------------------------------------------------------
# Branding
# ---------------------------------------------------------
st.title("🧊 POLAR CUDA")
st.subheader("Arctic Ice Situational Awareness Gauge")
st.caption(
    "A human-vision–aligned gauge for understanding today’s Arctic sea-ice situation.\n"
    "Designed for awareness, not for decision-making."
)

# ---------------------------------------------------------
# Mandatory disclaimer (short & readable)
# ---------------------------------------------------------
with st.expander("⚠️ Important notice", expanded=True):
    st.markdown(
        """
**POLAR CUDA is NOT an operational navigation tool.**

• Not a forecast  
• Not an official ice chart  
• Not a routing or safety service  

This gauge helps you **sense the situation**,  
not decide what to do.
"""
    )

agree = st.checkbox("I understand. Show today’s situation.", value=False)
if not agree:
    st.stop()

# ---------------------------------------------------------
# Data source
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Simplified regions (grouped for public view)
# ---------------------------------------------------------
REGION_GROUPS = {
    "Pacific Arctic": [
        (620, 90, 900, 330),   # Okhotsk
        (480, 300, 720, 520), # Bering
        (700, 420, 900, 580), # Chukchi
        (650, 520, 850, 700), # Beaufort
    ],
    "Atlantic Arctic": [
        (1080, 420, 1280, 600), # Kara
        (1180, 520, 1420, 720), # Barents
        (980, 650, 1180, 900),  # Greenland
        (760, 740, 980, 980),   # Baffin
    ],
    "Central Arctic": [
        (820, 500, 1050, 720),  # Central Arctic Ocean
    ]
}

# ---------------------------------------------------------
# Very simple color classifier (public version)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r and g > b:
        return "land"
    if b > r and b > g:
        return "water"
    return "ice"

def compute_ice_ratio(arr, rois, step=5):
    ice = water = 0
    h, w, _ = arr.shape

    for roi in rois:
        x1, y1, x2, y2 = roi
        for y in range(y1, min(y2, h), step):
            for x in range(x1, min(x2, w), step):
                c = classify_pixel(arr[y, x])
                if c == "land":
                    continue
                if c == "ice":
                    ice += 1
                else:
                    water += 1

    if ice + water == 0:
        return None
    return round((ice / (ice + water)) * 100, 1)

# ---------------------------------------------------------
# Gauge interpretation (Fear & Greed style)
# ---------------------------------------------------------
def gauge_label(pct):
    if pct < 25:
        return "🟢 Mostly Open", "Low ice presence"
    if pct < 50:
        return "🟡 Mixed", "Ice and open water coexist"
    if pct < 75:
        return "🟠 Ice-dominant", "Ice conditions increasingly present"
    return "🔴 Heavily Ice-covered", "Ice dominates the region"

# ---------------------------------------------------------
# Compute & display
# ---------------------------------------------------------
arr = load_image()
today = datetime.date.today()

st.markdown("---")
st.subheader(f"🧭 Today’s Arctic Situation ({today})")

for region, rois in REGION_GROUPS.items():
    pct = compute_ice_ratio(arr, rois)
    if pct is None:
        st.write(f"**{region}**: No data")
        continue

    label, note = gauge_label(pct)

    st.markdown(f"### {region}")
    st.write(f"**Ice presence:** {pct}%")
    st.write(f"**Situation:** {label}")
    st.caption(note)
    st.progress(int(pct))

st.markdown("---")
st.caption(
    "POLAR CUDA does not tell you what to do.\n"
    "It helps you understand whether today is a day for confidence—or for hesitation."
)
