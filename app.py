import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Public Ice Awareness Gauge
#
# CUDA = Cryospheric Uncertainty–Driven Awareness
#
# “This index is designed for awareness, not decisions.”
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Arctic Ice Gauge",
    layout="centered"
)

# ---------------------------------------------------------
# Data source (daily updated image)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# ---------------------------------------------------------
# Fixed sea regions (simple, stable)
# ---------------------------------------------------------
REGIONS = {
    "Sea of Okhotsk": (620, 90, 900, 330),
    "Bering Sea": (480, 300, 720, 520),
    "Chukchi Sea": (700, 420, 900, 580),
    "Laptev Sea": (930, 370, 1150, 560),
    "Barents Sea": (1180, 520, 1420, 720),
    "Beaufort Sea": (650, 520, 850, 700),
    "Greenland Sea": (980, 650, 1180, 900),
    "Baffin Bay": (760, 740, 980, 980),
}

# ---------------------------------------------------------
# Load image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Very simple "human-eye" pixel logic
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # LAND = strong green
    if g > 160 and g > r and g > b:
        return "land"

    # WATER = blue-dominant
    if b > r and b > g:
        return "water"

    # ICE = everything else you visually perceive as ice
    return "ice"

# ---------------------------------------------------------
# Ice area percentage in a box
# ---------------------------------------------------------
def ice_percentage(arr, roi, step=5):
    x1, y1, x2, y2 = roi
    ice = water = 0

    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
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
# Simple gauge language (public-friendly)
# ---------------------------------------------------------
def gauge_label(v):
    if v < 30:
        return "🟢 Mostly Open"
    if v < 55:
        return "🟡 Mixed"
    if v < 80:
        return "🟠 Mostly Ice"
    return "🔴 Ice Dominant"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA")
st.caption("Arctic Ice Awareness Gauge")

st.markdown(
    "**CUDA = Cryospheric Uncertainty–Driven Awareness**  \n"
    "*This gauge helps you understand today’s Arctic ice situation.*  \n"
    "*It does not tell you what to do.*"
)

today = datetime.date.today()
st.write(f"**Date:** {today}")

with st.expander("⚠️ Read before use", expanded=True):
    st.markdown(
        """
- This is **NOT** a navigation or routing tool  
- This is **NOT** an official ice chart  
- This is **NOT** advice  

It is a **daily awareness gauge**, similar to a market sentiment index.
"""
    )

# Load data
arr = load_image()

st.markdown("---")
st.subheader("Today’s Arctic Ice Gauge")

values = []

for region, roi in REGIONS.items():
    v = ice_percentage(arr, roi)

    if v is None:
        st.write(f"**{region}** → ⚪ No data")
        continue

    values.append(v)
    label = gauge_label(v)

    st.write(f"**{region}** → {label}  |  Ice: {v}%")
    st.progress(int(v))

# ---------------------------------------------------------
# Overall public index
# ---------------------------------------------------------
st.markdown("---")
st.subheader("Overall Polar CUDA Index")

if values:
    overall = round(sum(values) / len(values), 1)
    st.metric("Polar CUDA Index", f"{overall} / 100")
    st.progress(int(overall))

    st.caption(
        "Higher values mean **more ice dominance** across key Arctic seas."
    )
else:
    st.warning("No valid data today.")

st.markdown("---")
st.caption(
    "Data source: University of Bremen AMSR2 daily PNG.  \n"
    "POLAR CUDA provides situational awareness only."
)
