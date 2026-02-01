import streamlit as st
import datetime
import numpy as np
from PIL import Image, ImageDraw
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
# Pixel classification
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # Land (very strong green dominance – Bremen land mask)
    if g > 170 and g > r * 1.25 and g > b * 1.25:
        return "land"

    # Open water (dark blue)
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"

    # Everything else = sea ice (all concentrations)
    return "ice"

# ---------------------------------------------------------
# Operational sea regions (12, non-authoritative ROIs)
# Relative coordinates (x1, y1, x2, y2)
# ---------------------------------------------------------
REGION_ROIS = {
    "1. Sea of Okhotsk": (0.18, 0.05, 0.40, 0.28),
    "2. Bering Sea": (0.05, 0.25, 0.25, 0.45),
    "3. Chukchi Sea": (0.22, 0.35, 0.40, 0.55),
    "4. East Siberian Sea": (0.32, 0.30, 0.48, 0.48),
    "5. Laptev Sea": (0.42, 0.30, 0.58, 0.48),
    "6. Kara Sea": (0.55, 0.35, 0.70, 0.50),
    "7. Barents Sea": (0.60, 0.45, 0.80, 0.65),
    "8. Beaufort Sea": (0.25, 0.45, 0.42, 0.65),
    "9. Canadian Arctic Archipelago": (0.20, 0.60, 0.40, 0.80),
    "10. Central Arctic Ocean": (0.35, 0.40, 0.55, 0.60),
    "11. Greenland Sea": (0.50, 0.55, 0.70, 0.80),
    "12. Baffin Bay": (0.35, 0.65, 0.55, 0.85),
}

# ---------------------------------------------------------
# Draw ROI boxes on image
# ---------------------------------------------------------
def draw_rois(img, rois):
    draw = ImageDraw.Draw(img)
    w, h = img.size

    for name, (x1, y1, x2, y2) in rois.items():
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)

        draw.rectangle([(px1, py1), (px2, py2)], outline="yellow", width=4)
        draw.text((px1 + 5, py1 + 5), name.split(".")[0], fill="white")

    return img

# ---------------------------------------------------------
# Region assessment
# ---------------------------------------------------------
def assess_region(img, roi):
    arr = np.array(img)
    h, w, _ = arr.shape

    x1, y1 = int(roi[0] * w), int(roi[1] * h)
    x2, y2 = int(roi[2] * w), int(roi[3] * h)

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

    if ocean < 150:
        return "⚪ INSUFFICIENT DATA", 0.0, 0.0

    ice_ratio = ice / ocean
    water_ratio = water / ocean

    if ice_ratio > 0.8:
        status = "🔴 ICE DOMINANT (Practically Closed)"
    elif ice_ratio > 0.5:
        status = "🟠 ICE HEAVY (High Risk)"
    elif ice_ratio > 0.2:
        status = "🟡 MIXED (Marginal)"
    else:
        status = "🟢 WATER DOMINANT (Relatively Open)"

    return status, ice_ratio, water_ratio

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Image-Based)")
st.caption(f"Bremen AMSR2 image reference date: **{today}**")

st.markdown("---")

img = load_bremen_png()
img_boxed = draw_rois(img.copy(), REGION_ROIS)

st.image(
    img_boxed,
    caption="Bremen AMSR2 Arctic Sea Ice Concentration with Operational Sea Regions (Yellow Boxes)",
    use_container_width=True
)

st.markdown("## Regional Sea Ice Situation (Daily Snapshot)")

cols = st.columns(3)

for idx, (region, roi) in enumerate(REGION_ROIS.items()):
    with cols[idx % 3]:
        status, ice_r, water_r = assess_region(img, roi)
        st.markdown(f"### {region}")
        st.markdown(f"**Status:** {status}")
        st.markdown(f"- Ice pixels: {ice_r*100:.1f}%")
        st.markdown(f"- Open water pixels: {water_r*100:.1f}%")

st.markdown("---")

st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice information is derived from the publicly available daily AMSR2
sea-ice concentration imagery provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

The yellow boxes represent **analytically defined, non-authoritative
operational sea regions**, created for situational awareness and research
discussion only.

They do **not** correspond to official navigational, legal, or IMO-defined
sea boundaries.

Image date corresponds to the daily Bremen update
(reference date: **{today}**, UTC-based publication).

This application provides situational awareness only and must not replace
official ice services, navigational charts, or operational decision systems.
"""
)
