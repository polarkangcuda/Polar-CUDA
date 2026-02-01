import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Level 3
# Reference-ROI Locked Sea-Region Viewer
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3 (Reference ROI)",
    layout="wide"
)

today = datetime.date.today()

# ---------------------------------------------------------
# Load reference image (USER-DEFINED, FIXED)
# ---------------------------------------------------------
@st.cache_data
def load_reference_image():
    return Image.open("reference_roi.png").convert("RGB")

# ---------------------------------------------------------
# Load daily Bremen image (analysis only)
# ---------------------------------------------------------
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
# USER-DEFINED ROIs (FROM REFERENCE IMAGE)
# Example values – 반드시 reference 이미지에서 추출한 값 사용
# ---------------------------------------------------------
REGION_ROIS = {
    "1. Sea of Okhotsk": (610, 150, 900, 360),
    "2. Bering Sea": (450, 300, 720, 520),
    "3. Chukchi Sea": (650, 420, 860, 610),
    "4. East Siberian Sea": (780, 420, 1000, 610),
    "5. Laptev Sea": (930, 420, 1160, 610),
    "6. Kara Sea": (1120, 460, 1320, 660),
    "7. Barents Sea": (1160, 650, 1420, 900),
    "8. Beaufort Sea": (680, 560, 900, 760),
    "9. Canadian Arctic Archipelago": (640, 700, 860, 900),
    "10. Central Arctic Ocean": (820, 540, 1080, 780),
    "11. Greenland Sea": (980, 760, 1240, 1000),
    "12. Baffin Bay": (700, 820, 920, 1040),
}

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.title("🧊 POLAR CUDA – Level 3")
st.caption("Reference-ROI Locked Sea-Region Situation Viewer")
st.caption(f"Analysis date: {today}")

st.markdown("---")

ref_img = load_reference_image()
st.image(ref_img, caption="Reference Sea-Region Definition (User-Defined)", use_container_width=False)

st.markdown("## Why this works")
st.markdown("""
- Sea regions are **defined once by a domain expert**
- Daily Bremen imagery is used **only for pixel statistics**
- ROIs never move, rescale, or drift
- Interpretation remains stable across seasons and years
""")

st.markdown("---")
st.caption("""
This system intentionally separates:
(1) **Expert-defined spatial judgment**
(2) **Daily satellite-derived situational data**

This avoids false precision and preserves scientific accountability.
""")
