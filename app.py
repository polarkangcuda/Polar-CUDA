import streamlit as st
import numpy as np
import datetime
import math
from PIL import Image
import requests
from io import BytesIO

# =====================================================
# POLAR CUDA – Level 3 (Bremen AMSR2 PNG Operational Proxy)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="centered"
)

today = datetime.date.today()

# -----------------------------------------------------
# Bremen AMSR2 fixed concentration palette (NIC-style)
# RGB -> concentration %
# -----------------------------------------------------
BREMEN_PALETTE = [
    ((0,   0, 128),   0),
    ((0,   0, 255),   0),
    ((0, 128, 255),  10),
    ((0, 255, 255),  20),
    ((0, 255, 128),  30),
    ((0, 255,   0),  40),
    ((128,255,  0),  50),
    ((255,255,  0),  60),
    ((255,200,  0),  70),
    ((255,128,  0),  80),
    ((255,  0,  0),  90),
    ((180,  0,180), 100),
]

def rgb_to_concentration(rgb):
    r, g, b = rgb
    best_d = 1e9
    best_v = 0
    for (pr, pg, pb), v in BREMEN_PALETTE:
        d = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if d < best_d:
            best_d = d
            best_v = v
    return float(best_v)

# -----------------------------------------------------
# Simple pixel classifiers
# -----------------------------------------------------
def is_land(rgb):
    r, g, b = rgb
    return r > 150 and g > 150 and b > 150

def is_ocean(rgb):
    r, g, b = rgb
    return b > 120 and r < 50 and g < 80

def is_annotation(rgb):
    r, g, b = rgb
    return abs(r-g) < 5 and abs(g-b) < 5 and r > 180

# -----------------------------------------------------
# Region sectors (polar stereographic, approximate)
# theta: degrees clockwise from north
# r: normalized radius (0 = pole, 1 = edge)
# -----------------------------------------------------
REGION_SECTORS = {
    "Entire Arctic (Pan-Arctic)": dict(theta=(0,360), r=(0.15,0.95)),
    "Laptev Sea": dict(theta=(90,140), r=(0.45,0.75)),
    "Kara Sea": dict(theta=(30,80), r=(0.45,0.75)),
    "Beaufort Sea": dict(theta=(200,260), r=(0.45,0.75)),
    "Chukchi Sea": dict(theta=(240,300), r=(0.45,0.75)),
}

# -----------------------------------------------------
# Bremen PNG loader
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_bremen_png():
    url = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# -----------------------------------------------------
# Sector metrics computation
# -----------------------------------------------------
def compute_sector_metrics(img, sector, stride=3):
    w, h = img.size
    px = img.load()
    cx, cy = w//2, h//2
    max_r = min(cx, cy)

    t1, t2 = sector["theta"]
    r1, r2 = sector["r"]

    values = []

    for y in range(0, h, stride):
        for x in range(0, w, stride):
            dx = x - cx
            dy = cy - y
            rr = math.sqrt(dx*dx + dy*dy)
            rn = rr / max_r
            if rn < r1 or rn > r2:
                continue

            ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            if t1 <= t2:
                if not (t1 <= ang <= t2):
                    continue
            else:
                if not (ang >= t1 or ang <= t2):
                    continue

            rgb = px[x, y]
            if is_land(rgb) or is_annotation(rgb):
                continue

            if is_ocean(rgb):
                conc = 0.0
            else:
                conc = rgb_to_concentration(rgb)

            values.append(conc)

    if len(values) < 500:
        return None

    arr = np.array(values)
    return {
        "mean": float(arr.mean()),
        "cov15": float((arr >= 15).mean()*100),
        "heavy70": float((arr >= 70).mean()*100),
        "n": len(arr),
        "conf": min(1.0, len(arr)/8000.0)
    }

# =====================================================
# UI
# =====================================================
st.title("🧊 POLAR CUDA – Level 3")
st.caption("Cryospheric Unified Decision Assistant (Operational Risk Proxy)")
st.caption(f"Today (local): {today}")

region = st.selectbox(
    "Region",
    list(REGION_SECTORS.keys()),
    index=0
)

st.markdown("---")

# Load Bremen image
try:
    img = load_bremen_png()
except Exception as e:
    st.error("Failed to load Bremen AMSR2 PNG.")
    st.caption(str(e))
    st.stop()

metrics = compute_sector_metrics(img, REGION_SECTORS[region])

if metrics is None:
    st.error("ROI sampling insufficient for this region.")
    st.stop()

# -----------------------------------------------------
# Risk index (operational proxy)
# -----------------------------------------------------
risk_index = round(
    0.4*metrics["mean"]
    + 0.4*metrics["cov15"]
    + 0.2*metrics["heavy70"],
    1
)

if risk_index < 30:
    status, color = "LOW", "🟢"
elif risk_index < 50:
    status, color = "MODERATE", "🟡"
elif risk_index < 70:
    status, color = "HIGH", "🟠"
else:
    status, color = "EXTREME", "🔴"

# -----------------------------------------------------
# Display
# -----------------------------------------------------
st.subheader("Regional Navigation Risk (Status-Based)")

st.markdown(
f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

st.progress(int(risk_index))

st.markdown(
f"""
**Drivers (proxy)**  
• Mean concentration: **{metrics['mean']:.1f}%**  
• Coverage ≥15%: **{metrics['cov15']:.1f}%**  
• Heavy ice ≥70%: **{metrics['heavy70']:.1f}%**  
• Data confidence: **{metrics['conf']*100:.0f}%**

**Operational Interpretation (Non-Directive)**  
This indicator represents an **image-derived regional risk proxy**
computed from Bremen AMSR2 daily sea-ice concentration imagery.
It supports **situational awareness**, not route command.

Final operational decisions remain with operators and vessel masters.
"""
)

st.markdown("---")
st.caption(
"""
**Data Source & Legal Notice**

Level 3 (Experimental): Bremen AMSR2 daily sea-ice concentration PNG
(image-derived proxy using fixed color-palette quantization).

This is **not** an authoritative gridded concentration product and must
not replace official ice services or navigational judgment.
"""
)
