import streamlit as st
import datetime
import requests
from PIL import Image
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Stable Sea-Region Situation Viewer
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="wide"
)

today = datetime.date.today()

REFERENCE_ROI_IMAGE_URL = (
    "https://raw.githubusercontent.com/your-id/polar-cuda/main/reference_roi.png"
)

BREMEN_AMSR2_URL = (
    "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
)

def try_load_image(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Stable Expert-Defined Model)")
st.caption(f"Analysis date: **{today}**")

st.markdown("---")

# ---------------------------------------------------------
# Reference Sea-Region Definition
# ---------------------------------------------------------
st.subheader("① Reference Sea-Region Definition (Fixed)")

ref_img = try_load_image(REFERENCE_ROI_IMAGE_URL)

if ref_img is None:
    st.warning(
        "Reference ROI image not available.\n\n"
        "Please upload the expert-defined region image to GitHub "
        "and update `REFERENCE_ROI_IMAGE_URL`."
    )
else:
    st.image(
        ref_img,
        caption="Expert-defined Arctic sea regions (fixed reference)",
        use_container_width=True
    )

st.markdown("---")

# ---------------------------------------------------------
# Daily AMSR2 Image
# ---------------------------------------------------------
st.subheader("② Daily Sea-Ice Situation (Bremen AMSR2)")

bremen_img = try_load_image(BREMEN_AMSR2_URL)

if bremen_img is None:
    st.error("Failed to load Bremen AMSR2 daily image.")
else:
    st.image(
        bremen_img,
        caption="Bremen AMSR2 Arctic Sea-Ice Concentration (Daily PNG)",
        use_container_width=True
    )

st.markdown("---")

st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice imagery is provided by the University of Bremen (AMSR2 daily PNG):
https://data.seaice.uni-bremen.de/amsr2/

Sea-region boundaries are expert-defined operational constructs and do not
represent official or legal boundaries.

Situational awareness only. Not for navigation.
Image reference date: **{today}**.
"""
)
