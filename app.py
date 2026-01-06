import streamlit as st
import numpy as np
import datetime
from PIL import Image
import requests
from io import BytesIO
import math

# =====================================================
# POLAR CUDA – Level 3 (Experimental Bremen PNG Proxy)
# Cryospheric Unified Decision Assistant
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="centered"
)

today = datetime.date.today()

# -----------------------------------------------------
# Region definition (polar sector: angle [deg], radius)
# angle: clockwise from Greenwich meridian
# radius: fraction of image half-size (empirical)
# -----------------------------------------------------
REGION_SECTORS = {
    "Entire Arctic (Pan-Arctic)": dict(theta=(0, 360), r=(0.15, 0.95)),
    "Chukchi Sea": dict(theta=(210, 250), r=(0.45, 0.80)),
    "Beaufort Sea": dict(theta=(250, 300), r=(0.45, 0.80)),
    "Laptev Sea": dict(theta=(90, 140), r=(0.45, 0.80)),
    "East Siberian Sea": dict(theta=(140, 200), r=(0.45, 0.80)),
    "Kara Sea": dict(theta=(40, 80), r=(0.45, 0.80)),
    "Barents Sea": dict(theta=(330, 360), r=(0.45, 0.80)),
    "Greenland Sea": dict(theta=(300, 330), r=(0.45, 0.80)),
    "Baffin Bay": dict(theta=(280, 320), r=(0.50, 0.85)),
    "Lincoln Sea": dict(theta=(0, 40), r=(0.20, 0.45)),
}

# -----------------------------------------------------
# Bremen AMSR2 PNG loader
# -----------------------------------------------------
@st.cache_data(ttl=1800)
def load_bremen_png():
    url = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# -----------------------------------------------------
# Color → concentration (approximate, conservative)
# -----------------------------------------------------
def rgb_to_concentration(rgb):
    r, g, b = rgb
    if r < 50 and g < 50 and b < 50:
        return np.nan  # land / no data
    return max(0, min(100, (r + g + b) / 3 / 255 * 100))

# -----------------------------------------------------
# Sector-based ROI sampling
# -----------------------------------------------------
def compute_sector_mean(img, sector):
    w, h = img.size
    cx, cy = w // 2, h // 2
    max_r = min(cx, cy)

    theta1, theta2 = sector["theta"]
    r1, r2 = sector["r"]

    values = []

    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = cy - y
            r = math.sqrt(dx * dx + dy * dy)
            if r == 0:
                continue
            rn = r / max_r
            if not (r1 <= rn <= r2):
                continue
            ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            if theta1 <= ang <= theta2:
                values.append(rgb_to_concentration(img.getpixel((x, y))))

    arr = np.array(values)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return np.nan, np.nan

    return float(arr.mean()), float((arr >= 15).mean() * 100)

# -----------------------------------------------------
# SVG Gauge (instrument style)
# -----------------------------------------------------
def render_gauge(value):
    angle = -90 + (value / 100) * 180
    return f"""
<svg viewBox="0 0 200 120" width="100%">
  <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#2ecc71" stroke-width="12"/>
  <path d="M60 100 A40 40 0 0 1 140 100" fill="none" stroke="#f39c12" stroke-width="12"/>
  <path d="M90 100 A10 10 0 0 1 110 100" fill="none" stroke="#e74c3c" stroke-width="12"/>
  <line x1="100" y1="100" x2="{100 + 60 * math.cos(math.radians(angle))}"
        y2="{100 - 60 * math.sin(math.radians(angle))}"
        stroke="white" stroke-width="3"/>
  <circle cx="100" cy="100" r="4" fill="white"/>
</svg>
"""

# =====================================================
# UI
# =====================================================
st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Today (local): {today}")

region = st.selectbox("Region", list(REGION_SECTORS.keys()))
st.markdown("---")

# Load Level 3 data
try:
    img = load_bremen_png()
    mean_c, frac15 = compute_sector_mean(img, REGION_SECTORS[region])
    data_level = "Level 3 (Bremen AMSR2 PNG – Experimental)"
except Exception as e:
    st.error("Level 3 dataset unavailable.")
    st.stop()

# Risk logic (conservative)
risk_index = float(np.clip(mean_c * 1.1, 0, 100))

if risk_index < 30:
    status, dot = "LOW", "🟢"
elif risk_index < 50:
    status, dot = "MODERATE", "🟡"
elif risk_index < 70:
    status, dot = "HIGH", "🟠"
else:
    status, dot = "EXTREME", "🔴"

# -----------------------------------------------------
# Dashboard
# -----------------------------------------------------
st.subheader("Regional Navigation Risk (Status-Based)")
st.markdown(f"**Selected Region:** {region}")
st.markdown(f"**Data Level Used:** {data_level}")

st.markdown(f"### {dot} **{status}**")
st.markdown(f"**Risk Index:** {risk_index:.1f} / 100")

st.markdown(render_gauge(risk_index), unsafe_allow_html=True)

st.progress(int(risk_index))

st.markdown(
    f"""
**Derived metrics (proxy):**
- Mean concentration within ROI: **{mean_c:.1f}%**
- Area ≥15% concentration: **{frac15:.1f}%**

**Interpretation (Non-Directive)**  
This Level-3 indicator is an **image-derived experimental proxy** computed from
Bremen AMSR2 daily PNG imagery using a polar-sector ROI approximation.
It is intended **solely for situational awareness** and does not replace
official gridded products, ice services, or vessel-master judgment.
"""
)

st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): Derived from publicly accessible Bremen AMSR2 daily sea-ice
concentration PNG imagery via color-based quantization and polar-sector ROI approximation.

This application provides situational awareness only and does not constitute
navigational guidance or an authoritative ice product.
"""
)
