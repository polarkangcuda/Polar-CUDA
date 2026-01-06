import streamlit as st
import pandas as pd
import datetime
import numpy as np
import requests
from io import BytesIO
from PIL import Image, ImageDraw

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Level 3: Bremen AMSR2 PNG (Pixel-based Operational ROI)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Cryospheric Unified Decision Assistant",
    layout="centered"
)

today = datetime.date.today()

# -----------------------------------------------------
# Regions (Sea of Okhotsk intentionally excluded)
# -----------------------------------------------------
REGIONS = [
    "Entire Arctic (Pan-Arctic)",
    "Bering Sea",
    "Chukchi Sea",
    "Beaufort Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Kara Sea",
    "Barents Sea",
    "Greenland Sea",
    "Baffin Bay",
    "Lincoln Sea",
]

# -----------------------------------------------------
# Bremen AMSR2 PNG pixel-based ROIs (x0, y0, x1, y1)
# Values are relative ratios of image width/height
# -----------------------------------------------------
BREMEN_ROI = {
    "Entire Arctic (Pan-Arctic)": (0.00, 0.00, 1.00, 1.00),
    "Bering Sea": (0.00, 0.45, 0.18, 0.70),
    "Chukchi Sea": (0.10, 0.35, 0.30, 0.55),
    "Beaufort Sea": (0.22, 0.32, 0.42, 0.55),
    "East Siberian Sea": (0.42, 0.35, 0.62, 0.55),
    "Laptev Sea": (0.55, 0.30, 0.75, 0.50),
    "Kara Sea": (0.65, 0.40, 0.85, 0.60),
    "Barents Sea": (0.75, 0.48, 0.95, 0.65),
    "Greenland Sea": (0.12, 0.55, 0.30, 0.80),
    "Baffin Bay": (0.28, 0.60, 0.45, 0.85),
    "Lincoln Sea": (0.40, 0.15, 0.60, 0.30),
}

# -----------------------------------------------------
# Helper: status classification
# -----------------------------------------------------
def classify_status(idx):
    if idx < 30:
        return "LOW", "🟢"
    if idx < 50:
        return "MODERATE", "🟡"
    if idx < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

# -----------------------------------------------------
# Load Bremen AMSR2 PNG
# -----------------------------------------------------
@st.cache_data(ttl=1800)
def load_bremen_png():
    url = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# -----------------------------------------------------
# Quantize ice concentration from RGB (proxy)
# Very conservative: bright colors → higher ice
# -----------------------------------------------------
def ice_concentration_proxy(rgb):
    r, g, b = rgb
    # Simple brightness-based proxy
    brightness = (r + g + b) / 3.0
    return np.clip((brightness - 60) / 140 * 100, 0, 100)

# -----------------------------------------------------
# Compute regional proxy from ROI
# -----------------------------------------------------
def compute_region_proxy(img, region):
    if region not in BREMEN_ROI:
        return None, None

    w, h = img.size
    x0, y0, x1, y1 = BREMEN_ROI[region]
    px0, py0 = int(x0 * w), int(y0 * h)
    px1, py1 = int(x1 * w), int(y1 * h)

    pixels = img.crop((px0, py0, px1, py1)).load()
    values = []

    for x in range(px1 - px0):
        for y in range(py1 - py0):
            values.append(ice_concentration_proxy(pixels[x, y]))

    arr = np.array(values)
    mean_c = float(arr.mean())
    frac_15 = float((arr >= 15).sum() / arr.size * 100)

    return mean_c, frac_15

# -----------------------------------------------------
# Draw ROI box
# -----------------------------------------------------
def draw_roi(img, region):
    if region not in BREMEN_ROI:
        return img

    w, h = img.size
    x0, y0, x1, y1 = BREMEN_ROI[region]
    px0, py0 = int(x0 * w), int(y0 * h)
    px1, py1 = int(x1 * w), int(y1 * h)

    draw = ImageDraw.Draw(img)
    draw.rectangle([px0, py0, px1, py1], outline=(255, 215, 0), width=4)
    return img

# -----------------------------------------------------
# Sidebar (mobile-friendly)
# -----------------------------------------------------
st.sidebar.title("🧊 POLAR CUDA")
region = st.sidebar.selectbox("Region", REGIONS)
st.sidebar.markdown("**Data Level**")
use_level3 = st.sidebar.radio(
    "",
    ["Level 3 (Bremen AMSR2 PNG – Experimental)", "Level 2 (NSIDC Extent – Fallback)"],
    index=0,
)

# -----------------------------------------------------
# Main – Dashboard
# -----------------------------------------------------
st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Today (local): {today}")
st.markdown("---")

# -----------------------------------------------------
# Level 3 logic
# -----------------------------------------------------
if use_level3.startswith("Level 3"):
    try:
        img = load_bremen_png()
        mean_c, frac_15 = compute_region_proxy(img, region)

        if mean_c is None:
            raise RuntimeError("ROI not defined.")

        risk_index = round(mean_c, 1)
        status, color = classify_status(risk_index)

        img = draw_roi(img, region)
        st.image(img, caption="Bremen AMSR2 PNG (Operational ROI – yellow box)", use_container_width=True)

        st.subheader("Regional Navigation Risk (Status-Based)")
        st.markdown(
            f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100

- Bremen-derived mean concentration (proxy): **{mean_c:.1f}%**
- Ice coverage ≥15% within ROI (proxy): **{frac_15:.1f}%**
"""
        )
        st.progress(int(risk_index))

        st.markdown(
            """
**Operational Interpretation (Non-Directive)**

This indicator is derived from **pixel-level color quantization**
within an **operational ROI defined directly in the AMSR2 polar-projected image space**.

The ROI is **not a geographic boundary** and is used solely for
**situational awareness**, not tactical navigation or route planning.
"""
        )

    except Exception as e:
        st.warning("Level 3 dataset could not be processed. Please switch to Level 2 fallback.")
        st.caption(str(e))

# -----------------------------------------------------
# Footer
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): Regional proxy derived from the publicly accessible
**Bremen AMSR2 daily sea-ice concentration PNG** by image-based quantization
for situational awareness only.

Level 2 (Fallback): NOAA / NSIDC Sea Ice Index (G02135), Version 4,
distributed under NOAA open data principles.

This application does **not** replace official ice services, onboard navigation
systems, or the judgment of vessel masters.
"""
)
