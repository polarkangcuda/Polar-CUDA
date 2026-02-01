import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Expert-Defined Sea-Region Simple Viewer
# =========================================================

st.set_page_config(layout="wide")

today = datetime.date.today()

BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Pixel classification (simple & robust)
# ---------------------------------------------------------
def classify(rgb):
    r, g, b = rgb
    if g > 170 and g > r*1.2 and g > b*1.2:
        return "land"
    if b > 120 and b > r*1.2 and b > g*1.2:
        return "water"
    return "ice"

# ---------------------------------------------------------
# ⚠️ EXPERT-DEFINED ROIs (PIXEL COORDINATES)
# 아래 값은 강박사님 그림에 맞게 한 번만 조정
# (x1, y1, x2, y2)
# ---------------------------------------------------------
SEA_ROIS = {
    "1. Sea of Okhotsk": (900, 150, 1200, 450),
    "2. Bering Sea": (700, 350, 1000, 650),
    "3. Chukchi Sea": (850, 550, 1150, 850),
    "4. East Siberian Sea": (950, 550, 1250, 850),
    "5. Laptev Sea": (1050, 550, 1350, 850),
    "6. Kara Sea": (1250, 600, 1550, 850),
    "7. Barents Sea": (1350, 650, 1650, 950),
    "8. Beaufort Sea": (750, 750, 1050, 1050),
    "9. Canadian Arctic Archipelago": (700, 900, 1000, 1200),
    "10. Central Arctic Ocean": (900, 650, 1250, 1000),
    "11. Greenland Sea": (1100, 900, 1350, 1200),
    "12. Baffin Bay": (850, 1000, 1150, 1350),
}

# ---------------------------------------------------------
# Region assessment
# ---------------------------------------------------------
def assess(img, roi):
    arr = np.array(img)
    x1,y1,x2,y2 = roi
    ice = water = ocean = 0

    for y in range(y1, y2, 3):
        for x in range(x1, x2, 3):
            c = classify(arr[y,x])
            if c == "land": continue
            ocean += 1
            if c == "ice": ice += 1
            if c == "water": water += 1

    if ocean < 100:
        return "⚪ Data insufficient"

    ratio = ice / ocean

    if ratio >= 0.8: return "🔴 Navigation NOT possible"
    if ratio >= 0.5: return "🟠 Very high risk"
    if ratio >= 0.2: return "🟡 Conditional"
    return "🟢 Relatively open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption(f"Analysis date: {today} (Bremen AMSR2 daily PNG)")

img = load_image()
st.image(img, use_container_width=True)

st.markdown("## Sea-Region Navigation Feasibility (Simple View)")

for name, roi in SEA_ROIS.items():
    status = assess(img, roi)
    st.markdown(f"**{name}** → {status}")

st.caption(
    """
Data source: University of Bremen AMSR2 daily sea-ice concentration PNG.  
Regions are expert-defined operational sectors (non-authoritative).  
This view provides situational awareness only.
"""
)
