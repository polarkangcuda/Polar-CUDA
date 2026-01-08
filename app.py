import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3 (Winter-Aware Openability Proxy)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="centered"
)

today = datetime.date.today()
month = today.month

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
# Winter-closed core seas (structural EXTREME)
# ---------------------------------------------------------
WINTER_CLOSED = {
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Beaufort Sea",
    "Central Arctic Ocean",
}

# ---------------------------------------------------------
# Bremen AMSR2 PNG URL (daily, auto-updating)
# ---------------------------------------------------------
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

# ---------------------------------------------------------
# Load Bremen PNG (safe)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_bremen_png():
    try:
        r = requests.get(BREMEN_URL, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None

# ---------------------------------------------------------
# Simple color-based classification
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    # land (green)
    if g > 180 and r < 100:
        return "land"
    # open water (dark blue)
    if b > 120 and g < 100:
        return "water"
    # ice (everything else)
    return "ice"

# ---------------------------------------------------------
# Bremen proxy stats (very conservative)
# ---------------------------------------------------------
def compute_openability_proxy(img):
    arr = np.array(img)
    h, w, _ = arr.shape

    total = 0
    ice = 0
    water = 0

    for y in range(0, h, 4):
        for x in range(0, w, 4):
            cls = classify_pixel(arr[y, x])
            if cls == "land":
                continue
            total += 1
            if cls == "ice":
                ice += 1
            if cls == "water":
                water += 1

    if total == 0:
        return None

    ice_ratio = ice / total
    water_ratio = water / total

    return {
        "ice_ratio": ice_ratio,
        "water_ratio": water_ratio,
    }

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
st.caption("Cryospheric Unified Decision Assistant (Operational Risk Proxy)")
st.caption(f"Today (local): {today}")

region = st.selectbox("Select Sea Region", REGIONS)

st.markdown("---")

# ---------------------------------------------------------
# Winter override logic
# ---------------------------------------------------------
if month in [12, 1, 2, 3] and region in WINTER_CLOSED:
    risk_index = 95.0
    status, color = "EXTREME", "🔴"
    proxy_note = "Winter structural closure (openability = effectively zero)."

else:
    img = load_bremen_png()
    if img is None:
        st.error("Unable to load Bremen AMSR2 image.")
        st.stop()

    stats = compute_openability_proxy(img)
    if stats is None:
        st.error("Unable to compute proxy statistics.")
        st.stop()

    # Conservative mapping:
    # less open water → higher risk
    risk_index = round(
        np.clip((1.0 - stats["water_ratio"]) * 100.0, 0, 100),
        1
    )
    status, color = classify_status(risk_index)
    proxy_note = (
        f"Open water ratio (proxy): {stats['water_ratio']*100:.1f}%"
    )

# ---------------------------------------------------------
# Display
# ---------------------------------------------------------
st.subheader("Regional Navigation Risk (Status-Based)")
st.markdown(f"### {color} **{status}**")
st.markdown(f"**Risk Index:** {risk_index} / 100")
st.progress(int(risk_index))

st.markdown(
    f"""
**Operational Interpretation (Non-Directive)**

- Selected Region: **{region}**
- Assessment Mode: **Level 3 (Winter-aware image-derived proxy)**
- Note: {proxy_note}

This indicator represents **operational openability risk**, not an
“open/closed route” declaration.  
During Arctic winter, several seas are **structurally closed** regardless
of small-scale leads visible in satellite imagery.

Final operational decisions remain with operators and vessel masters.
"""
)

st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): Image-derived proxy from the publicly accessible
daily **Bremen AMSR2 sea-ice concentration PNG**.
This is **not** an authoritative gridded concentration product and must not
replace official ice services or navigational judgment.
"""
)
