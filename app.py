import streamlit as st
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Level 3
# Sea-Region Navigation Feasibility (Expert-Defined ROIs)
# =========================================================

st.set_page_config(layout="wide")
st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Navigation Feasibility (Expert-Defined, Image-Based)")
st.caption(f"Analysis date: {datetime.date.today()} (AMSR2 daily PNG)")

# ---------------------------------------------------------
# Load daily AMSR2 PNG (Bremen)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(AMSR2_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

img = load_image()
arr = np.array(img)
h, w, _ = arr.shape

st.image(img, caption="AMSR2 Arctic Sea Ice Concentration (Daily)", use_container_width=True)

# ---------------------------------------------------------
# 🔒 Expert-defined ROIs (PIXEL COORDINATES)
# These MUST match the yellow boxes provided by Dr. Kang
# Format: (x1, y1, x2, y2)
# ---------------------------------------------------------
REGIONS = {
    "1. Sea of Okhotsk": (620, 90, 900, 330),
    "2. Bering Sea": (480, 300, 720, 520),
    "3. Chukchi Sea": (700, 420, 900, 580),
    "4. East Siberian Sea": (820, 380, 1030, 560),
    "5. Laptev Sea": (930, 370, 1150, 560),
    "6. Kara Sea": (1080, 420, 1280, 600),
    "7. Barents Sea": (1180, 520, 1420, 720),
    "8. Beaufort Sea": (650, 520, 850, 700),
    "9. Canadian Arctic Archipelago": (650, 650, 880, 860),
    "10. Central Arctic Ocean": (820, 500, 1050, 720),
    "11. Greenland Sea": (980, 650, 1180, 900),
    "12. Baffin Bay": (760, 740, 980, 980),
}

# ---------------------------------------------------------
# Pixel classification (robust & conservative)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    # Land (bright green)
    if g > 160 and g > r * 1.1 and g > b * 1.1:
        return "land"
    # Open water (dark blue)
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "water"
    # Otherwise ice
    return "ice"

# ---------------------------------------------------------
# Assess navigation feasibility per region
# ---------------------------------------------------------
def assess_region(roi):
    x1, y1, x2, y2 = roi
    ice = water = ocean = 0

    for y in range(y1, min(y2, h), 3):
        for x in range(x1, min(x2, w), 3):
            cls = classify_pixel(arr[y, x])
            if cls == "land":
                continue
            ocean += 1
            if cls == "ice":
                ice += 1
            else:
                water += 1

    if ocean == 0:
        return "⚪ No data"

    ice_ratio = ice / ocean

    if ice_ratio > 0.75:
        return "🔴 Navigation NOT possible"
    elif ice_ratio > 0.45:
        return "🟠 Very high risk"
    elif ice_ratio > 0.20:
        return "🟡 Conditional"
    else:
        return "🟢 Relatively open"

# ---------------------------------------------------------
# Display results (Simple View)
# ---------------------------------------------------------
st.markdown("## Sea-Region Navigation Feasibility (Simple View)")

for region, roi in REGIONS.items():
    status = assess_region(roi)
    st.markdown(f"**{region} → {status}**")

# ---------------------------------------------------------
# Notice
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
Data source: University of Bremen AMSR2 daily sea-ice concentration PNG.  
Sea regions are **expert-defined operational sectors**, manually aligned to the
displayed image and **non-authoritative**.  

This tool provides **situational awareness only** and must not replace official
ice services, navigational charts, or operational decision systems.
"""
)
