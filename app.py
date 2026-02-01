import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
#
# “This index is designed for decision awareness,
#  not decision-making.”
#
# Human-vision–aligned daily situational awareness index
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
# (mentally corresponding to 1–12 Arctic sea regions)
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
# Load AMSR2 image (safe & cached)
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image_safe():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Pixel classifier (human-vision aligned)
#
# Rules:
#  - Bright green  → land (exclude)
#  - Deep blue     → open water (exclude)
#  - Any other color → ice (regardless of concentration)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # LAND (bright green)
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"

    # OPEN WATER (deep blue)
    if b > 140 and b > r * 1.2 and b > g * 1.2:
        return "open_water"

    # Everything else = ICE (visual interpretation)
    return "ice"

# ---------------------------------------------------------
# Ice area percentage (visual-rule based)
#
# Denominator:
#   pixels where ice could exist
#   (land + deep-blue open water excluded)
#
# Numerator:
#   pixels visually interpreted as ice
# ---------------------------------------------------------
def compute_ice_area_percent(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice_pixels = 0
    ice_possible = 0

    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel(arr[y, x])

            if c == "land":
                continue
            if c == "open_water":
                continue

            ice_possible += 1
            if c == "ice":
                ice_pixels += 1

    if ice_possible == 0:
        return None

    return round((ice_pixels / ice_possible) * 100, 1)

# ---------------------------------------------------------
# Index label (simple, intuitive)
# ---------------------------------------------------------
def label(idx):
    if idx >= 90:
        return "🔴 Ice-dominant"
    if idx >= 70:
        return "🟠 High ice"
    if idx >= 40:
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

today = datetime.date.today()
st.caption("Daily situational awareness for Arctic sea-ice conditions.")
st.write(f"**Analysis date:** {today}")

# Refresh
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# Compute indices
# ---------------------------------------------------------
arr = load_image_safe()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_area_percent(arr, roi)
    if idx is not None:
        indices.append(idx)
        results.append({
            "Region": region,
            "Ice Area (%)": idx,
            "Status": label(idx)
        })
    else:
        results.append({
            "Region": region,
            "Ice Area (%)": "N/A",
            "Status": "⚪ No data"
        })

df = pd.DataFrame(results)

# ---------------------------------------------------------
# Overall POLAR CUDA Index
# ---------------------------------------------------------
if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Status (Visual Interpretation)")

for _, r in df.iterrows():
    st.write(
        f"**{r['Region']}** → {r['Status']}  |  Ice area: {r['Ice Area (%)']} %"
    )

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects **human-vision–aligned ice dominance**
within expert-defined Arctic sea regions.

⚠ This tool does **not** indicate navigability, routing feasibility,
or replace official ice services, ice charts, or operational decision systems.
"""
)
