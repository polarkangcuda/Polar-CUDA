import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3 (Season-Aware Openability Proxy)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="centered"
)

today = datetime.date.today()
month = today.month

# ---------------------------------------------------------
# Season definition
# ---------------------------------------------------------
if month in [12, 1, 2, 3]:
    SEASON = "winter"
elif month in [4, 5]:
    SEASON = "spring"
elif month in [6, 7, 8, 9]:
    SEASON = "summer"
else:
    SEASON = "autumn"

# ---------------------------------------------------------
# Sea Regions (12)
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

# ---------------------------------------------------------
# Structurally winter-closed seas
# ---------------------------------------------------------
WINTER_CLOSED = {
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Beaufort Sea",
    "Central Arctic Ocean",
}

# ---------------------------------------------------------
# Seasonal risk modifiers
# ---------------------------------------------------------
SEASON_MODIFIER = {
    "winter": 1.00,
    "spring": 0.85,   # thawing, leads increase
    "summer": 0.65,   # open season
    "autumn": 1.15,   # freeze-up risk amplification
}

# ---------------------------------------------------------
# Bremen AMSR2 PNG (daily auto-update)
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
# Pixel classification (FIXED)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # Land: strong green dominance (coast/land mask)
    if g > 170 and g > r * 1.2 and g > b * 1.2:
        return "land"

    # Open water: dark/deep blue
    if b > 120 and b > r * 1.2 and b > g * 1.2:
        return "water"

    # Everything else = ice (all concentration colors)
    return "ice"

# ---------------------------------------------------------
# Compute openability proxy (conservative)
# ---------------------------------------------------------
def compute_openability(img):
    arr = np.array(img)
    h, w, _ = arr.shape

    ocean_pixels = 0
    open_water = 0

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
# Status classification
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
st.caption(f"Date (local): {today}")
st.caption(f"Season detected: **{SEASON.upper()}**")

region = st.selectbox("Select Sea Region", REGIONS)

st.markdown("---")

# ---------------------------------------------------------
# Core risk logic
# ---------------------------------------------------------
if SEASON == "winter" and region in WINTER_CLOSED:
    base_risk = 95.0
    reason = "Structural winter closure (openability effectively zero)."

else:
    img = load_bremen_png()
    if img is None:
        st.error("Unable to load Bremen AMSR2 imagery.")
        st.stop()

    open_ratio = compute_openability(img)
    if open_ratio is None:
        st.error("Unable to compute open water proxy.")
        st.stop()

    base_risk = (1.0 - open_ratio) * 100.0
    reason = f"Open water ratio (proxy): {open_ratio*100:.1f}%"

# ---------------------------------------------------------
# Seasonal adjustment
# ---------------------------------------------------------
risk_index = round(
    np.clip(base_risk * SEASON_MODIFIER[SEASON], 0, 100),
    1
)

status, color = classify_status(risk_index)

# ---------------------------------------------------------
# Display
# ---------------------------------------------------------
st.subheader("Regional Navigation Risk (Season-Aware)")

st.markdown(f"### {color} **{status}**")
st.markdown(f"**Risk Index:** {risk_index} / 100")
st.progress(int(risk_index))

st.markdown(
    f"""
**Operational Interpretation (Non-Directive)**

- Selected Region: **{region}**
- Season Logic Applied: **{SEASON.upper()}**
- Assessment Basis: **Openability proxy + seasonal modifier**
- Note: {reason}

This indicator expresses **relative operational risk** rather than
route availability.  
Seasonal dynamics (thawing, freeze-up) are explicitly incorporated.

Final operational decisions remain with operators and vessel masters.
"""
)

st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): Image-derived proxy from the publicly accessible
**Bremen AMSR2 daily sea-ice concentration PNG**.

This application provides **situational awareness only** and does not
replace official ice services, onboard navigation systems, or the
judgment of vessel masters.
"""
)
