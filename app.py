import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA
# Cryospheric Uncertainty & Decision Awareness
# Visual Ice Awareness Index
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Awareness Index",
    layout="centered"
)

st.title("🧊 POLAR CUDA Index")
st.caption(
    "Cryospheric Uncertainty & Decision Awareness\n\n"
    "“This index is designed for decision awareness, not decision-making.”"
)

st.write(f"**Analysis date:** {datetime.date.today()}")

# ---------------------------------------------------------
# Data source (visual map – human-eye reference)
# ---------------------------------------------------------
IMAGE_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_visual.png"

# ---------------------------------------------------------
# Expert-defined ROIs (pixel coordinates)
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
# Load image
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(IMAGE_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

# ---------------------------------------------------------
# Ice detection based on visual whiteness
# ---------------------------------------------------------
def is_ice(pixel):
    r, g, b = pixel
    return (r > 200) and (g > 200) and (b > 200)

def compute_visual_index(arr, roi, step=3):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)

    ice = total = 0

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            total += 1
            if is_ice(arr[y, x]):
                ice += 1

    if total == 0:
        return None

    return round((ice / total) * 100, 1)

# ---------------------------------------------------------
# Refresh
# ---------------------------------------------------------
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# =========================================================
# Compute Index
# =========================================================

img = load_image()

records = []
values = []

for region, roi in REGIONS.items():
    idx = compute_visual_index(img, roi)
    if idx is not None:
        values.append(idx)
        records.append({"Region": region, "Index": idx})
    else:
        records.append({"Region": region, "Index": "N/A"})

df = pd.DataFrame(records)

# ---------------------------------------------------------
# Overall Index
# ---------------------------------------------------------
if values:
    overall = round(sum(values) / len(values), 1)
    st.metric("POLAR CUDA Index (Overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Awareness Index")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → Index: **{r['Index']}**")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 visual ice map.

This index reflects the **visible proportion of ice (white areas)** within
expert-defined Arctic sea regions.

It is intentionally simple and non-directive,
similar to a market sentiment index.

⚠ This tool does **not** indicate navigability,
routing feasibility, or operational safety.
"""
)
