import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# Human-eye based Ice Area Index
#
# “This index is designed for decision awareness,
#  not decision-making.”
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Area Index (Human-eye)",
    layout="centered"
)

# ---------------------------------------------------------
# Data source (visual PNG – human-eye reference)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# User-defined sea regions (white boxes)
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
# Load image safely
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

# ---------------------------------------------------------
# Human-eye pixel classification
# ---------------------------------------------------------
def classify_pixel_human_eye(rgb):
    r, g, b = rgb

    # Land: green-dominant
    if g > 150 and g > r * 1.1 and g > b * 1.1:
        return "land"

    # Ocean: blue-dominant
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "ocean"

    # Everything else looks like ice to human eyes
    return "ice"

# ---------------------------------------------------------
# Ice area index (human-eye based)
# ---------------------------------------------------------
def compute_ice_area_index(arr, roi, step=3):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)

    ice = valid = 0

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel_human_eye(arr[y, x])
            if c in ["land", "ocean"]:
                continue
            valid += 1
            if c == "ice":
                ice += 1

    if valid == 0:
        return None

    return round((ice / valid) * 100, 1)

# ---------------------------------------------------------
# Simple label
# ---------------------------------------------------------
def label(idx):
    if idx >= 80:
        return "🔴 Ice-dominant"
    if idx >= 60:
        return "🟠 High ice"
    if idx >= 35:
        return "🟡 Mixed"
    return "🟢 More open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Ice Area Index (Human-eye based)")
st.markdown(
    "**POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)**  \n"
    "*This index reflects visually dominant ice-covered area only.*"
)

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

arr = load_image()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_area_index(arr, roi)
    if idx is not None:
        indices.append(idx)
        results.append({
            "Region": region,
            "Index": idx,
            "Status": label(idx)
        })
    else:
        results.append({
            "Region": region,
            "Index": "N/A",
            "Status": "⚪ No data"
        })

df = pd.DataFrame(results)

if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Area (Human-eye based)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']} | Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily visual PNG.

This index represents **visually perceived ice-covered area only**,
based on simple human-eye classification within user-defined regions.

⚠ This tool is for **decision awareness only**.
It does **not** represent physical ice concentration,
navigability, or operational guidance.
"""
)
