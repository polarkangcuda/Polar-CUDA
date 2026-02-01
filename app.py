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

# ---------------------------------------------------------
# Date
# ---------------------------------------------------------
today = datetime.date.today()

# ---------------------------------------------------------
# URLs (NO local files)
# ---------------------------------------------------------
# 1) Reference image with expert-defined yellow ROIs
REFERENCE_ROI_IMAGE_URL = (
    "https://raw.githubusercontent.com/USERNAME/REPO/main/reference_roi.png"
)

# 2) Bremen AMSR2 daily sea-ice PNG (auto-updated)
BREMEN_AMSR2_URL = (
    "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
)

# ---------------------------------------------------------
# Image loaders (NO caching to avoid freeze)
# ---------------------------------------------------------
def load_image_from_url(url, label):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        st.error(f"❌ Failed to load {label}.")
        st.stop()

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Situation Viewer (Stable Expert-Defined Model)")
st.caption(f"Analysis date: **{today}**")

st.markdown("---")

# ---------------------------------------------------------
# Reference region definition (expert judgement)
# ---------------------------------------------------------
st.subheader("① Reference Sea-Region Definition (Fixed)")

st.markdown(
    """
This reference image defines **12 Arctic sea regions** using
**expert judgement**.  
These yellow boxes are **fixed, non-authoritative operational sectors**
and **do not change over time**.
"""
)

ref_img = load_image_from_url(
    REFERENCE_ROI_IMAGE_URL,
    "Reference ROI image"
)

st.image(
    ref_img,
    caption="Expert-defined Arctic sea regions (fixed reference)",
    use_container_width=True
)

st.markdown("---")

# ---------------------------------------------------------
# Daily sea-ice situation (Bremen AMSR2)
# ---------------------------------------------------------
st.subheader("② Daily Sea-Ice Situation (Bremen AMSR2)")

st.markdown(
    """
This image shows the **daily AMSR2 sea-ice concentration** provided by
the University of Bremen.  
It is **automatically updated** and reflects **current conditions**.
"""
)

bremen_img = load_image_from_url(
    BREMEN_AMSR2_URL,
    "Bremen AMSR2 daily sea-ice image"
)

st.image(
    bremen_img,
    caption="Bremen AMSR2 Arctic Sea-Ice Concentration (daily PNG)",
    use_container_width=True
)

st.markdown("---")

# ---------------------------------------------------------
# Interpretation guidance (NO automation)
# ---------------------------------------------------------
st.subheader("③ How to Read This View")

st.markdown(
    """
**How this Level-3 view should be used**

- Yellow boxes = **fixed sea regions** (defined once by experts)
- Color map = **today’s observed ice concentration**
- Interpretation is **comparative and contextual**, not algorithmic

**What this view intentionally does NOT do**

- ❌ No automatic route availability
- ❌ No pixel-level legal classification
- ❌ No navigational instruction
- ❌ No false precision from reprojection

This design ensures:
**stability · transparency · explainability**
"""
)

st.markdown("---")

# ---------------------------------------------------------
# Legal & methodological notice
# ---------------------------------------------------------
st.caption(
    f"""
**Data Source & Legal Notice**

Sea-ice imagery is obtained from the publicly accessible AMSR2 daily
sea-ice concentration product provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

The reference sea-region boundaries are **expert-defined operational
constructs** and do **not** represent official, legal, or navigational
boundaries.

This application provides **situational awareness only** and must not
replace official ice services, navigational charts, or the judgement of
vessel masters.

Image reference date: **{today}** (based on daily Bremen update).
"""
)
