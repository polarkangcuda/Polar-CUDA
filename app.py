import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd
import os

# =========================================================
# POLAR CUDA (v2.3)
# =========================================================
CUDA_ACRONYM = "Cryospheric Uncertainty–Driven Awareness"
APP_TITLE = "POLAR CUDA – Arctic Ice Situational Awareness Gauge"
APP_SUBTITLE = (
    "Human-vision–aligned sea-ice sentiment gauge "
    "for decision awareness (not decision-making)."
)

DISCLAIMER_TEXT = """
### ⚠ Mandatory disclaimer (situational awareness only)

**POLAR CUDA** is a **situational awareness gauge**, not an operational tool.
- NOT navigation, routing, feasibility, or forecasting
- NOT an official ice service
- NOT operational or legal advice
"""

PHILOSOPHY_ONE_LINER = (
    "POLAR CUDA does not tell you what to do — "
    "it helps you recognize when not to decide yet."
)

st.set_page_config(page_title=APP_TITLE, layout="centered")

# ---------------------------------------------------------
# Data source
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600
ALPHA_HISTORY_FILE = "alpha_history.csv"

# ---------------------------------------------------------
# Regions (ROIs)
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
# ✅ UPDATED REGION GROUPS (요청 반영)
# ---------------------------------------------------------
REGION_GROUPS = {
    "Pacific Arctic (situational bucket)": [
        "Bering Sea",
        "Chukchi Sea",
        "Beaufort Sea",
        "East Siberian Sea",
    ],
    "Atlantic Arctic (situational bucket)": [
        "Kara Sea",
        "Barents Sea",
        "Greenland Sea",
        "Baffin Bay",
    ],
}

# ---------------------------------------------------------
# Alpha correction
# ---------------------------------------------------------
DEFAULT_CORRECTION = {
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

@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"
    if b > r and b > g:
        return "water"
    return "ice"

def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape
    for y in range(max(0, y1), min(h, y2), step):
        for x in range(max(0, x1), min(w, x2), step):
            c = classify_pixel(arr[y, x])
            if c == "ice":
                ice += 1
            elif c == "water":
                water += 1
    if ice + water == 0:
        return None
    return (ice / (ice + water)) * 100

def clamp(v):
    return max(0, min(100, v))

def friction_level(v, t1, t2, t3, t4):
    if v <= t1: return "🟢 Extreme Open"
    if v <= t2: return "🟩 Open"
    if v <= t3: return "🟡 Neutral"
    if v <= t4: return "🟠 Constrained"
    return "🔴 Extreme Constrained"

# =========================================================
# UI
# =========================================================
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)
st.info(f"**CUDA = {CUDA_ACRONYM}**")

with st.expander("⚠ Disclaimer", expanded=True):
    st.markdown(DISCLAIMER_TEXT)
    st.markdown(f"> *{PHILOSOPHY_ONE_LINER}*")

if not st.checkbox("I understand and wish to continue"):
    st.stop()

step = st.slider("Sampling step", 2, 12, 4)
t1, t2, t3, t4 = 15, 35, 60, 85

arr = load_image()
rows = []

for r, roi in REGIONS.items():
    raw = compute_raw_ice(arr, roi, step)
    if raw is None:
        continue
    hybrid = clamp(raw * DEFAULT_CORRECTION.get(r, 1.0))
    rows.append({"Region": r, "Hybrid": round(hybrid, 1)})

df = pd.DataFrame(rows)

# =========================================================
# GROUP AVERAGES
# =========================================================
st.markdown("---")
st.subheader("Regional group averages (situational buckets)")

cols = st.columns(2)
for i, (g, members) in enumerate(REGION_GROUPS.items()):
    vals = df[df["Region"].isin(members)]["Hybrid"]
    with cols[i]:
        avg = round(vals.mean(), 1)
        st.metric(g, f"{avg}%")
        st.write(friction_level(avg, t1, t2, t3, t4))
        st.progress(int(avg))

# =========================================================
# INDIVIDUAL REGIONS
# =========================================================
st.markdown("---")
st.subheader("Sea-region situational gauges")

for _, r in df.iterrows():
    lvl = friction_level(r["Hybrid"], t1, t2, t3, t4)
    st.write(f"**{r['Region']}** → {lvl}  |  {r['Hybrid']}%")
    st.progress(int(r["Hybrid"]))

# =========================================================
# FOOTER / DATA SOURCE
# =========================================================
st.markdown("---")

st.caption(
    f"CUDA = {CUDA_ACRONYM}. "
    "Data source: University of Bremen AMSR2 daily PNG. "
    "POLAR CUDA provides situational awareness only."
)


