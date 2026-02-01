import streamlit as st
import datetime
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Sea-Region Situation Viewer (Stable ROI Reference Model)
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
# Load reference ROI image (user-approved)
# ---------------------------------------------------------
@st.cache_data
def load_reference_image():
    return Image.open(REFERENCE_IMAGE_PATH).convert("RGB")

# ---------------------------------------------------------
# Load daily Bremen AMSR2 PNG
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_bremen_png():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Align Bremen image to reference image size
# ---------------------------------------------------------
def align_to_reference(bremen_img, ref_img):
    return bremen_img.resize(ref_img.size, Image.BILINEAR)

# ---------------------------------------------------------
# Pixel classification (robust & conservative)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # Land: bright green (Bremen land mask)
    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"

    # Open water: dark blue
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"

    # All remaining colors = sea ice
    return "ice"

# ---------------------------------------------------------
# Fixed ROIs (pixel coordinates on reference image)
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
        status = "🟠 ICE HEAVY (High Operational Risk)"
    elif ice_ratio > 0.2:
        status = "🟡 MIXED (Conditional)"
    else:
        status = "🟢 WATER DOMINANT (Relatively Open)"

    return status, ice_ratio, water_ratio

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Stable ROI Reference Model)")
st.caption(f"Analysis date: **{today}** (Bremen AMSR2 daily PNG)")

st.markdown("---")

# Load images
ref_img = load_reference_image()
bremen_img = load_bremen_png()
aligned_img = align_to_reference(bremen_img, ref_img)

# ---------------------------------------------------------
# Draw ROI boxes on aligned image
# ---------------------------------------------------------
overlay = aligned_img.copy()
draw = ImageDraw.Draw(overlay)

for roi in REGION_ROIS.values():
    draw.rectangle(roi, outline="yellow", width=3)

st.image(
    overlay,
    caption="Bremen AMSR2 Arctic Sea Ice (Daily) aligned to reference ROI",
    use_container_width=True
)

# ---------------------------------------------------------
# Regional assessment table
# ---------------------------------------------------------
st.markdown("## Regional Sea Ice Situation")

cols = st.columns(3)

for idx, (region, roi) in enumerate(REGION_ROIS.items()):
    with cols[idx % 3]:
        status, ice_r, water_r = assess_region(aligned_img, roi)
        st.markdown(f"### {region}")
        st.markdown(f"**Status:** {status}")
        st.markdown(f"- Ice-dominant: {ice_r*100:.1f}%")
        st.markdown(f"- Open water: {water_r*100:.1f}%")

# ---------------------------------------------------------
# Legal & methodological notice
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice information is derived from the publicly available daily AMSR2
sea-ice concentration imagery provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

Regional boxes shown here are **user-defined operational ROIs**
anchored to a fixed reference image for consistency.
They are **not official, legal, or navigational sea boundaries**.

This tool provides situational awareness only and must not replace
official ice services, navigational charts, or vessel master judgment.
"""
)
