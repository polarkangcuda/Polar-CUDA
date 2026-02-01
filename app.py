import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# POLAR CUDA Index
#
# “This index is designed for decision awareness,
#  not decision-making.”
#
# A daily situational awareness index
# for Arctic sea-ice conditions.
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Risk Index",
    layout="centered"
)

# ---------------------------------------------------------
# Data source
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# Expert-defined fixed ROIs (pixel coordinates)
# (based on your white-box definition)
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
# Load AMSR2 image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Human-eye-based pixel perception
# ---------------------------------------------------------
def perceive_pixel(rgb):
    r, g, b = rgb
    brightness = r + g + b  # 0 ~ 765

    # --- Land (dark/vivid green only) ---
    if g > 140 and g > r * 1.2 and g > b * 1.2:
        return "land"

    # --- Open water: ONLY very dark navy ---
    if (b > 110) and (b > r + 30) and (b > g + 30) and (brightness < 260):
        return "water"

    # --- Everything else is visually ice ---
    return "ice"

# ---------------------------------------------------------
# Ice area index (human-eye based)
# ---------------------------------------------------------
def compute_ice_index(img, roi, step=3):
    x1, y1, x2, y2 = roi
    ice = water = 0

    h, w, _ = img.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            p = perceive_pixel(img[y, x])
            if p == "land":
                continue
            if p == "ice":
                ice += 1
            else:
                water += 1

    total = ice + water
    if total == 0:
        return None

    return round((ice / total) * 100, 1)

# ---------------------------------------------------------
# Simple, intuitive labels
# ---------------------------------------------------------
def label(idx):
    if idx >= 80:
        return "🔴 Ice-dominant"
    if idx >= 60:
        return "🟠 High ice"
    if idx >= 35:
        return "🟡 Mixed"
    return "🟢 More open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Ice Risk Index")
st.markdown(
    "**POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)**  \n"
    "*This index is designed for decision awareness, not decision-making.*"
)

st.caption(
    "A daily situational awareness index for Arctic sea-ice conditions."
)

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# Compute indices
# ---------------------------------------------------------
img = load_image()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_index(img, roi)
    if idx is not None:
        indices.append(idx)
        results.append({
            "Region": region,
            "Index": idx,
            "Status": label(idx)
        })
    else:
        results.append({
            "Region": region,
            "Index": "N/A",
            "Status": "⚪ No data"
        })

df = pd.DataFrame(results)

# ---------------------------------------------------------
# Overall Polar CUDA Index
# ---------------------------------------------------------
if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Area (Human-eye based)")

for _, r in df.iterrows():
    st.write(
        f"**{r['Region']}** → {r['Status']}  |  Index: {r['Index']}"
    )

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects **visually perceived sea-ice area**
within expert-defined Arctic sea regions.

It is designed for **decision awareness**, similar to a market sentiment index.

⚠ This tool does **not** indicate navigability, routing feasibility,
or replace official ice services or operational decision systems.
"""
)
