import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# Ice Area Awareness Index
#
# "Designed for decision awareness, not decision-making."
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Area Index",
    layout="centered"
)

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# ---------------------------------------------------------
# Fixed ROIs (white boxes defined by user)
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
# Load image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

# ---------------------------------------------------------
# Human-eye-based pixel classification
# ---------------------------------------------------------
def is_land(rgb):
    r, g, b = rgb
    return g > 150 and g > r * 1.1 and g > b * 1.1

def is_ocean(rgb):
    r, g, b = rgb
    return b > 120 and b > r * 1.2 and b > g * 1.2

# ---------------------------------------------------------
# Ice area ratio (what the eye sees)
# ---------------------------------------------------------
def compute_ice_area_index(arr, roi, step=3):
    x1, y1, x2, y2 = roi
    ice_pixels = 0
    valid_pixels = 0

    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            rgb = arr[y, x]

            if is_land(rgb):
                continue

            valid_pixels += 1

            if not is_ocean(rgb):
                ice_pixels += 1

    if valid_pixels == 0:
        return None

    return round((ice_pixels / valid_pixels) * 100, 1)

# ---------------------------------------------------------
# Simple labels
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

st.title("🧊 POLAR CUDA – Ice Area Index")
st.caption(
    "POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)\n"
    "This index is designed for decision awareness, not decision-making."
)

st.write(f"**Analysis date:** {datetime.date.today()}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

arr = load_image()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_area_index(arr, roi)
    if idx is not None:
        indices.append(idx)
        results.append({
            "Region": region,
            "Index": idx,
            "Status": label(idx)
        })

df = pd.DataFrame(results)

if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Area (Human-eye based)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']} | Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index counts **visible ice-covered area only**, exactly as perceived by the human eye.
It does not interpret concentration values or physical thickness.

⚠ This tool provides situational awareness only and does not replace official ice services.
"""
)
