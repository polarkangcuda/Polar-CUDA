import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3
# Image-Derived Operational Risk Proxy (Bremen AMSR2 PNG)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="centered"
)

# ---------------------------------------------------------
# Date & season
# ---------------------------------------------------------
today = datetime.date.today()
month = today.month

if month in [12, 1, 2, 3]:
    SEASON = "winter"
elif month in [4, 5]:
    SEASON = "spring"
elif month in [6, 7, 8, 9]:
    SEASON = "summer"
else:
    SEASON = "autumn"

# ---------------------------------------------------------
# Operational Sea Sectors (12, non-authoritative)
# ---------------------------------------------------------
REGIONS = [
    "Sea of Okhotsk",
    "Bering Sea",
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Kara Sea",
    "Barents Sea",
    "Beaufort Sea",
    "Canadian Arctic Archipelago",
    "Central Arctic Ocean",
    "Greenland Sea",
    "Baffin Bay",
]

# Structurally winter-closed seas
WINTER_CLOSED = {
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Beaufort Sea",
    "Central Arctic Ocean",
}

# Seasonal modifier (conservative)
SEASON_MODIFIER = {
    "winter": 1.00,
    "spring": 0.85,
    "summer": 0.65,
    "autumn": 1.15,
}

# ---------------------------------------------------------
# Bremen AMSR2 daily PNG
# ---------------------------------------------------------
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_bremen_png():
    try:
        r = requests.get(BREMEN_URL, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None

# ---------------------------------------------------------
# Pixel classification
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # Land (bright green on Bremen map)
    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"

    # Open water (dark blue)
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"

    # All remaining colors represent sea ice (any concentration)
    return "ice"

# ---------------------------------------------------------
# Openability proxy (image-based, conservative)
# ---------------------------------------------------------
def compute_openability(img):
    arr = np.array(img)
    h, w, _ = arr.shape

    ocean_pixels = 0
    open_water = 0

    # Subsample to reduce noise and cost
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            cls = classify_pixel(arr[y, x])
            if cls == "land":
                continue
            ocean_pixels += 1
            if cls == "water":
                open_water += 1

    if ocean_pixels == 0:
        return None

    return open_water / ocean_pixels

# ---------------------------------------------------------
# Risk status
# ---------------------------------------------------------
def classify_status(risk):
    if risk < 30:
        return "LOW", "🟢"
    if risk < 50:
        return "MODERATE", "🟡"
    if risk < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Analysis date (local): {today}")
st.caption(f"Season detected: **{SEASON.upper()}**")

region = st.selectbox("Select Operational Sea Sector", REGIONS)

st.markdown("---")

# ---------------------------------------------------------
# Core logic
# ---------------------------------------------------------
if SEASON == "winter" and region in WINTER_CLOSED:
    base_risk = 95.0
    reason = "Structural winter closure: regional openability effectively zero."

else:
    img = load_bremen_png()
    if img is None:
        st.error("Unable to load Bremen AMSR2 daily imagery.")
        st.stop()

    open_ratio = compute_openability(img)
    if open_ratio is None:
        st.error("Unable to compute image-based openability proxy.")
        st.stop()

    base_risk = (1.0 - open_ratio) * 100.0
    reason = f"Image-derived open water ratio (proxy): {open_ratio*100:.1f}%"

risk_index = round(
    np.clip(base_risk * SEASON_MODIFIER[SEASON], 0, 100),
    1
)

status, color = classify_status(risk_index)

# ---------------------------------------------------------
# Display
# ---------------------------------------------------------
st.subheader("Regional Navigation Risk (Image-Based, Season-Aware)")

st.markdown(f"### {color} **{status}**")
st.markdown(f"**Risk Index:** {risk_index} / 100")
st.progress(int(risk_index))

st.markdown(
    f"""
**Operational Interpretation (Non-Directive)**

- Selected Sector: **{region}**
- Assessment Basis: **Bremen AMSR2 image-derived proxy**
- Season Logic Applied: **{SEASON.upper()}**
- Diagnostic Note: {reason}

This indicator represents **relative operational risk**, not route availability.
It is designed to support situational awareness and risk reasoning only.

Final operational decisions remain the responsibility of operators and vessel masters.
"""
)

# ---------------------------------------------------------
# Legal & methodological notice
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    f"""
**Data Source & Methodology Notice**

Sea-ice information is derived from the publicly available daily AMSR2 sea-ice
concentration imagery provided by the University of Bremen:
https://data.seaice.uni-bremen.de/amsr2/

This Level 3 analysis does **not** use authoritative gridded concentration products
or official regional masks. Instead, it applies an image-based color-quantization
proxy within approximate, analytically defined Arctic subregions for situational
awareness purposes.

The regional sectors used here are **operational constructs**, not legally defined
or authoritative sea region boundaries.

Analysis date of the imagery: **{today}** (UTC reference, based on daily Bremen update).

This application provides situational awareness only and must not replace official
ice services, navigational charts, or operational decision systems.
"""
)
