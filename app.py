import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Sea-Region Situation Viewer (Image-Based, Daily Updated)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3 (Sea Regions)",
    layout="wide"
)

# ---------------------------------------------------------
# Date
# ---------------------------------------------------------
today = datetime.date.today()

# ---------------------------------------------------------
# Bremen AMSR2 daily PNG
# ---------------------------------------------------------
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_bremen_png():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Pixel classification (robust & conservative)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # Land (bright green)
    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"

    # Open water (dark blue)
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"

    # All remaining colors = sea ice (any concentration)
    return "ice"

# ---------------------------------------------------------
# Operational sea regions (non-authoritative ROIs)
# Relative ratios based on visual interpretation
# ---------------------------------------------------------
REGION_ROIS = {
    "Sea of Okhotsk": (0.18, 0.05, 0.40, 0.28),
    "Bering Sea": (0.05, 0.25, 0.25, 0.45),
    "Chukchi Sea": (0.22, 0.35, 0.40, 0.55),
    "East Siberian Sea": (0.32, 0.30, 0.48, 0.48),
    "Laptev Sea": (0.42, 0.30, 0.58, 0.48),
    "Kara Sea": (0.55, 0.35, 0.70, 0.50),
    "Barents Sea": (0.60, 0.45, 0.80, 0.65),
    "Beaufort Sea": (0.25, 0.45, 0.42, 0.65),
    "Canadian Arctic Archipelago": (0.20, 0.60, 0.40, 0.80),
    "Central Arctic Ocean": (0.35, 0.40, 0.55, 0.60),
    "Greenland Sea": (0.50, 0.55, 0.70, 0.80),
    "Baffin Bay": (0.35, 0.65, 0.55, 0.85),
}

# ---------------------------------------------------------
# Region situation assessment
# ---------------------------------------------------------
def assess_region(img, roi):
    arr = np.array(img)
    h, w, _ = arr.shape

    x1 = int(roi[0] * w)
    y1 = int(roi[1] * h)
    x2 = int(roi[2] * w)
    y2 = int(roi[3] * h)

    ocean = ice = water = 0

    for y in range(y1, y2, 4):
        for x in range(x1, x2, 4):
            cls = classify_pixel(arr[y, x])
            if cls == "land":
                continue
            ocean += 1
            if cls == "ice":
                ice += 1
            elif cls == "water":
                water += 1

    if ocean < 100:
        return "INSUFFICIENT DATA", 0, 0

    ice_ratio = ice / ocean
    water_ratio = water / ocean

    if ice_ratio > 0.8:
        status = "ICE DOMINANT (Practically Closed)"
        icon = "🔴"
    elif ice_ratio > 0.5:
        status = "ICE HEAVY (High Operational Risk)"
        icon = "🟠"
    elif ice_ratio > 0.2:
        status = "MIXED (Conditional / Marginal)"
        icon = "🟡"
    else:
        status = "WATER DOMINANT (Relatively Open)"
        icon = "🟢"

    return f"{icon} {status}", ice_ratio, water_ratio

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Image-Based)")
st.caption(f"Image reference date: **{today}** (Bremen AMSR2 daily update)")

st.markdown("---")

img = load_bremen_png()
st.image(img, caption="Bremen AMSR2 Arctic Sea Ice Concentration (Daily PNG)", use_container_width=True)

st.markdown("## Regional Sea Ice Situation")

cols = st.columns(3)

for idx, (region, roi) in enumerate(REGION_ROIS.items()):
    with cols[idx % 3]:
        status, ice_r, water_r = assess_region(img, roi)
        st.markdown(f"### {region}")
        st.markdown(f"**Status:** {status}")
        st.markdown(f"- Ice-dominant pixels: {ice_r*100:.1f}%")
        st.markdown(f"- Open-water pixels: {water_r*100:.1f}%")

st.markdown("---")

st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice information is derived from the publicly available daily AMSR2
sea-ice concentration imagery provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

This application uses **image-based color interpretation** within
**approximate, non-authoritative Arctic sea regions** defined for
situational awareness and analytical discussion.

The regional divisions shown here are **operational constructs** and do
not represent official, legal, or navigational boundaries.

This tool provides situational awareness only and must not replace
official ice services, navigational products, or operational decision systems.
"""
)
