import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# Ice Risk Index
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Risk Index",
    layout="centered"
)

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# Expert-defined fixed ROIs (pixel coordinates, stable)
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
# Load AMSR2 image (safe)
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Pixel classifier
# land is COMPLETELY excluded from analysis
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.1 and g > b * 1.1:
        return "land"
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "water"
    return "ice"

# ---------------------------------------------------------
# Ice Risk Index (SEA-ONLY denominator)
# ---------------------------------------------------------
def compute_ice_risk(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0

    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            cls = classify_pixel(arr[y, x])
            if cls == "land":
                continue
            if cls == "ice":
                ice += 1
            elif cls == "water":
                water += 1

    sea_pixels = ice + water
    if sea_pixels == 0:
        return None

    return round((ice / sea_pixels) * 100, 1)

# ---------------------------------------------------------
# Labeling (intuitive, non-directive)
# ---------------------------------------------------------
def label(idx):
    if idx >= 85:
        return "🔴 Ice-dominant"
    if idx >= 65:
        return "🟠 High ice"
    if idx >= 40:
        return "🟡 Mixed"
    return "🟢 More open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Ice Risk Index")
st.caption("POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)")
st.caption("“This index is designed for decision awareness, not decision-making.”")

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# Load data
arr = load_image()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_risk(arr, roi)
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
            "Status": "⚪ No sea data"
        })

df = pd.DataFrame(results)

# Overall Polar CUDA Index
if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Risk (Simple View)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']}  |  Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects **relative ice dominance over sea surface only**
within expert-defined Arctic sea regions.

It is designed for **situational awareness**, similar to a market
sentiment index (e.g., Fear & Greed Index).

⚠ This tool does **not** indicate navigability, routing feasibility,
or replace official ice services or operational decision systems.
"""
)
