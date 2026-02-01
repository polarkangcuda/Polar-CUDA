import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA v2.0
# Hybrid Ice Area Index
#
# Satellite color signal × Human visual correction
#
# “Designed for decision awareness, not decision-making”
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Hybrid Ice Area Index",
    layout="centered"
)

# ---------------------------------------------------------
# Data source
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# ---------------------------------------------------------
# Fixed ROIs (expert-defined)
# ---------------------------------------------------------
REGIONS = {
    "Sea of Okhotsk": (620, 90, 900, 330),
    "Bering Sea": (480, 300, 720, 520),
    "Chukchi Sea": (700, 420, 900, 580),
    "East Siberian Sea": (820, 380, 1030, 560),
    "Laptev Sea": (930, 370, 1150, 560),
    "Kara Sea": (1080, 420, 1280, 600),
    "Barents Sea": (1180, 520, 1420, 720),
    "Beaufort Sea": (650, 520, 850, 700),
    "Canadian Arctic Archipelago": (650, 650, 880, 860),
    "Central Arctic Ocean": (820, 500, 1050, 720),
    "Greenland Sea": (980, 650, 1180, 900),
    "Baffin Bay": (760, 740, 980, 980),
}

# ---------------------------------------------------------
# Human visual correction factors (α)
# Derived from Dr. Kang’s visual judgement
# ---------------------------------------------------------
CORRECTION = {
    "Sea of Okhotsk": 0.55,
    "Bering Sea": 0.45,
    "Chukchi Sea": 1.55,
    "East Siberian Sea": 1.00,
    "Laptev Sea": 1.00,
    "Kara Sea": 0.90,
    "Barents Sea": 0.35,
    "Beaufort Sea": 1.75,
    "Canadian Arctic Archipelago": 1.40,
    "Central Arctic Ocean": 1.00,
    "Greenland Sea": 0.75,
    "Baffin Bay": 0.80,
}

# ---------------------------------------------------------
# Load image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Pixel classifier (visual logic)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # LAND
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"

    # WATER (all blue-dominant tones)
    if b > r and b > g:
        return "water"

    # ICE
    return "ice"

# ---------------------------------------------------------
# Raw ice percentage (satellite signal)
# ---------------------------------------------------------
def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0

    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel(arr[y, x])
            if c == "land":
                continue
            if c == "ice":
                ice += 1
            else:
                water += 1

    if ice + water == 0:
        return None

    return (ice / (ice + water)) * 100

# ---------------------------------------------------------
# Hybrid ice area (human-corrected)
# ---------------------------------------------------------
def compute_hybrid_ice(arr, region, roi):
    raw = compute_raw_ice(arr, roi)
    if raw is None:
        return None, None

    alpha = CORRECTION.get(region, 1.0)
    corrected = raw * alpha

    # Clamp to 0–100
    corrected = max(0, min(100, corrected))

    return round(raw, 1), round(corrected, 1)

# ---------------------------------------------------------
# Label
# ---------------------------------------------------------
def label(val):
    if val >= 90:
        return "🔴 Ice-dominant"
    if val >= 70:
        return "🟠 High ice"
    if val >= 40:
        return "🟡 Mixed"
    return "🟢 More open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Hybrid Ice Area Index")
st.markdown(
    "**Satellite signal × Human judgement**  \n"
    "*Designed for decision awareness, not decision-making.*"
)

st.write(f"**Analysis date:** {datetime.date.today()}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

arr = load_image()

rows = []
final_values = []

for region, roi in REGIONS.items():
    raw, hybrid = compute_hybrid_ice(arr, region, roi)
    if hybrid is not None:
        final_values.append(hybrid)
        rows.append({
            "Region": region,
            "Raw (%)": raw,
            "Hybrid Ice Area (%)": hybrid,
            "Status": label(hybrid)
        })

df = pd.DataFrame(rows)

if final_values:
    overall = round(sum(final_values) / len(final_values), 1)
    st.metric("POLAR CUDA (Hybrid, overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Hybrid Ice Area (%)")

for _, r in df.iterrows():
    st.write(
        f"**{r['Region']}** → {r['Status']}  |  "
        f"Hybrid: {r['Hybrid Ice Area (%)']} % "
        f"(raw {r['Raw (%)']} %)"
    )

st.markdown("---")
st.caption(
    """
**POLAR CUDA v2.0**  
This hybrid index approximates **visual ice-covered area (%)**
by combining satellite color signals with expert human judgement.

⚠ Not for navigation or operational use.
"""
)
