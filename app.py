import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# Ice Risk Index – VISUAL ICE (White-based)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Risk Index",
    layout="centered"
)

# ---------------------------------------------------------
# Data source (VISUAL ICE – white = ice)
# ---------------------------------------------------------
AMSR2_VISUAL_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_visual.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# Expert-defined fixed ROIs (pixel coordinates)
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
# Load image safely
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_VISUAL_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

# ---------------------------------------------------------
# VISUAL ICE classifier
# White pixels = sea ice
# ---------------------------------------------------------
def is_white_ice(rgb):
    r, g, b = rgb
    return (r > 200 and g > 200 and b > 200)

def is_land(rgb):
    r, g, b = rgb
    return (g > 120 and g > r and g > b)

# ---------------------------------------------------------
# Ice dominance index (white ratio)
# ---------------------------------------------------------
def compute_ice_index(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    ice = ocean = 0

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            rgb = arr[y, x]
            if is_land(rgb):
                continue
            ocean += 1
            if is_white_ice(rgb):
                ice += 1

    if ocean == 0:
        return None

    return round((ice / ocean) * 100, 1)

# ---------------------------------------------------------
# Human-friendly label (Fear / Greed style)
# ---------------------------------------------------------
def label(idx):
    if idx >= 85:
        return "🔴 Ice-dominant"
    if idx >= 65:
        return "🟠 High ice"
    if idx >= 35:
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

# ---------------------------------------------------------
# Core computation
# ---------------------------------------------------------
arr = load_image()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_index(arr, roi)
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
# Overall POLAR CUDA Index
# ---------------------------------------------------------
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
**Data source**: University of Bremen AMSR2 daily *visual* sea-ice imagery.

This index reflects **relative ice dominance (white ice coverage)** within
expert-defined Arctic sea regions.

It is intentionally designed as a **situational awareness index**,
similar to a market sentiment indicator.

⚠ This tool does **not** indicate navigability, routing feasibility,
or replace official ice services or operational decision systems.
"""
)
