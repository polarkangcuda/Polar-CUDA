import streamlit as st
import datetime
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import os

# =========================================================
# POLAR CUDA – Level 3
# Sea-Region Situation Viewer (Fail-Safe ROI Model)
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
# Paths & URLs
# ---------------------------------------------------------
REFERENCE_IMAGE_PATH = "reference_roi.png"
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

# ---------------------------------------------------------
# Load Bremen AMSR2 image
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_bremen_png():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Load reference image (fail-safe)
# ---------------------------------------------------------
def load_reference_image_or_fallback(bremen_img):
    if os.path.exists(REFERENCE_IMAGE_PATH):
        ref = Image.open(REFERENCE_IMAGE_PATH).convert("RGB")
        source = "User-provided fixed reference image"
    else:
        ref = bremen_img.copy()
        source = "Daily Bremen image (automatic fallback reference)"
    return ref, source

# ---------------------------------------------------------
# Pixel classification
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"
    return "ice"

# ---------------------------------------------------------
# Fixed ROIs (pixel coordinates)
# ---------------------------------------------------------
REGION_ROIS = {
    "1. Sea of Okhotsk": (620, 110, 910, 330),
    "2. Bering Sea": (450, 300, 720, 500),
    "3. Chukchi Sea": (620, 420, 850, 620),
    "4. East Siberian Sea": (780, 420, 1010, 620),
    "5. Laptev Sea": (950, 420, 1180, 620),
    "6. Kara Sea": (1120, 460, 1320, 660),
    "7. Barents Sea": (1160, 640, 1440, 900),
    "8. Beaufort Sea": (680, 560, 900, 760),
    "9. Canadian Arctic Archipelago": (640, 700, 860, 900),
    "10. Central Arctic Ocean": (820, 540, 1080, 780),
    "11. Greenland Sea": (980, 760, 1240, 1000),
    "12. Baffin Bay": (700, 820, 920, 1040),
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
        return "⚪ INSUFFICIENT DATA", 0.0, 0.0

    ice_ratio = ice / ocean
    water_ratio = water / ocean

    if ice_ratio > 0.8:
        status = "🔴 ICE DOMINANT (Practically Closed)"
    elif ice_ratio > 0.5:
        status = "🟠 ICE HEAVY (High Risk)"
    elif ice_ratio > 0.2:
        status = "🟡 MIXED (Conditional)"
    else:
        status = "🟢 WATER DOMINANT"

    return status, ice_ratio, water_ratio

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Fail-Safe Reference Model)")
st.caption(f"Analysis date: **{today}** (Bremen AMSR2 daily PNG)")

st.markdown("---")

bremen_img = load_bremen_png()
ref_img, ref_source = load_reference_image_or_fallback(bremen_img)

# Align daily image to reference
aligned_img = bremen_img.resize(ref_img.size, Image.BILINEAR)

# Draw ROIs
overlay = aligned_img.copy()
draw = ImageDraw.Draw(overlay)
for roi in REGION_ROIS.values():
    draw.rectangle(roi, outline="yellow", width=3)

st.image(
    overlay,
    caption=f"Reference-aligned AMSR2 image | Reference source: {ref_source}",
    use_container_width=True
)

# ---------------------------------------------------------
# Regional table
# ---------------------------------------------------------
st.markdown("## Regional Sea Ice Situation")

cols = st.columns(3)

for i, (region, roi) in enumerate(REGION_ROIS.items()):
    with cols[i % 3]:
        status, ice_r, water_r = assess_region(aligned_img, roi)
        st.markdown(f"### {region}")
        st.markdown(f"**Status:** {status}")
        st.markdown(f"- Ice: {ice_r*100:.1f}%")
        st.markdown(f"- Open water: {water_r*100:.1f}%")

# ---------------------------------------------------------
# Legal notice
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea-ice information is derived from the publicly available daily AMSR2
sea-ice concentration imagery provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

Regional boxes are **user-defined operational ROIs** for situational awareness.
They are not official navigational or legal boundaries.

This tool supports analysis and discussion only and must not replace
official ice services or operational decision authority.
"""
)
