import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Public Edition (12 Regions)
# CUDA = Cryospheric Uncertainty–Driven Awareness
#
# Simple, readable, impactful.
# Situational awareness only.
# =========================================================

st.set_page_config(page_title="POLAR CUDA", layout="wide")

# ---------------------------------------------------------
# Branding
# ---------------------------------------------------------
st.title("🧊 POLAR CUDA")
st.subheader("Arctic Ice Situational Awareness Gauge")
st.caption(
    "A simple, human-readable gauge for today’s Arctic sea-ice situation.\n"
    "Designed for awareness — not for decision-making."
)

# ---------------------------------------------------------
# Short disclaimer (public-friendly)
# ---------------------------------------------------------
with st.expander("⚠️ Important notice", expanded=True):
    st.markdown(
        """
**POLAR CUDA is NOT an operational navigation tool.**

• Not a forecast  
• Not an official ice chart  
• Not a routing or safety service  

This gauge helps you **sense today’s situation**,  
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
# 12 Arctic sea regions (fixed ROIs)
# ---------------------------------------------------------
REGIONS = {
    "Sea of Okhotsk": (620, 90, 900, 330),
    "Bering Sea": (480, 300, 720, 520),
    "Chukchi Sea": (700, 420, 900, 580),
    "East Siberian Sea": (820, 380, 1030, 560),
    "Laptev Sea": (930, 370, 1150, 560),
    "Kara Sea": (1080, 420, 1280, 600),
    "Barents Sea": (1180, 520, 1420, 720),
    "Beaufort Sea": (650, 520, 850, 700),
    "Canadian Arctic Archipelago": (650, 650, 880, 860),
    "Central Arctic Ocean": (820, 500, 1050, 720),
    "Greenland Sea": (980, 650, 1180, 900),
    "Baffin Bay": (760, 740, 980, 980),
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

def compute_ice_ratio(arr, roi, step=5):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape

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
# Public-friendly gauge labels
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
st.subheader(f"🧭 Today’s Arctic Sea-Ice Situation ({today})")

# Display 12 regions in a 3 x 4 grid
region_items = list(REGIONS.items())
rows = [region_items[i:i+4] for i in range(0, 12, 4)]

for row in rows:
    cols = st.columns(4)
    for col, (region, roi) in zip(cols, row):
        pct = compute_ice_ratio(arr, roi)

        with col:
            st.markdown(f"### {region}")
            if pct is None:
                st.write("No data")
                continue

            label, note = gauge_label(pct)
            st.write(f"**Ice presence:** {pct}%")
            st.write(f"**Situation:** {label}")
            st.caption(note)
            st.progress(int(pct))

st.markdown("---")
st.caption(
    "POLAR CUDA does not tell you where to go.\n"
    "It helps you see whether today is a day for confidence — or for hesitation."
)
