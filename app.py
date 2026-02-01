import streamlit as st
import datetime
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Sea-Region Situation Viewer (Pixel-Accurate ROIs)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3 (Sea Regions)",
    layout="wide"
)

today = datetime.date.today()

BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_bremen_png():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Pixel classifier
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"
    return "ice"

# ---------------------------------------------------------
# Pixel-based ROIs (hand-aligned to provided reference map)
# (x1, y1, x2, y2)
# ---------------------------------------------------------
REGION_ROIS = {
    "1. Sea of Okhotsk": (760, 140, 1040, 360),
    "2. Bering Sea": (560, 320, 820, 520),
    "3. Chukchi Sea": (760, 420, 980, 600),
    "4. East Siberian Sea": (900, 420, 1120, 600),
    "5. Laptev Sea": (1040, 420, 1260, 600),
    "6. Kara Sea": (1180, 460, 1380, 640),
    "7. Barents Sea": (1220, 620, 1480, 860),
    "8. Beaufort Sea": (820, 560, 1040, 760),
    "9. Canadian Arctic Archipelago": (760, 700, 980, 900),
    "10. Central Arctic Ocean": (900, 540, 1160, 760),
    "11. Greenland Sea": (1080, 760, 1320, 980),
    "12. Baffin Bay": (820, 820, 1040, 1020),
}

# ---------------------------------------------------------
# Region assessment
# ---------------------------------------------------------
def assess_region(img, roi):
    arr = np.array(img)
    x1, y1, x2, y2 = roi

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

    if ocean < 200:
        return "INSUFFICIENT DATA", 0, 0

    ice_ratio = ice / ocean
    water_ratio = water / ocean

    if ice_ratio > 0.8:
        status = "🔴 ICE DOMINANT (Closed)"
    elif ice_ratio > 0.5:
        status = "🟠 ICE HEAVY"
    elif ice_ratio > 0.2:
        status = "🟡 MIXED"
    else:
        status = "🟢 WATER DOMINANT"

    return status, ice_ratio, water_ratio

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Pixel-Aligned)")
st.caption(f"Bremen AMSR2 image date: **{today}**")

img = load_bremen_png()

# Draw ROI boxes
overlay = img.copy()
draw = ImageDraw.Draw(overlay)
for roi in REGION_ROIS.values():
    draw.rectangle(roi, outline="yellow", width=3)

st.image(
    overlay,
    caption="Bremen AMSR2 Arctic Sea Ice Concentration with Operational Sea Regions",
    use_container_width=True
)

st.markdown("## Regional Situation Summary")

cols = st.columns(3)
for i, (region, roi) in enumerate(REGION_ROIS.items()):
    with cols[i % 3]:
        status, ice_r, water_r = assess_region(img, roi)
        st.markdown(f"### {region}")
        st.markdown(f"**Status:** {status}")
        st.markdown(f"- Ice pixels: {ice_r*100:.1f}%")
        st.markdown(f"- Open water: {water_r*100:.1f}%")

st.markdown("---")
st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice information is derived from the publicly available daily AMSR2
sea-ice concentration PNG provided by the University of Bremen  
https://data.seaice.uni-bremen.de/amsr2/

The yellow boxes represent **operational, non-authoritative sea regions**
defined manually in pixel space to match the reference map provided by the user.

These regions are **not official geographic boundaries** and are used solely
for situational awareness and analytical discussion.

Image reference date: **{today}** (UTC, based on Bremen daily update).

This tool does **not** replace official ice services, navigational charts,
or operational decision systems.
"""
)
