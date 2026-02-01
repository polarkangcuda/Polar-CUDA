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
# CUDA = Cryospheric Uncertainty–Driven Awareness
#
# POLAR CUDA – Arctic Ice Situational Awareness Gauge
#
# Human-in-the-loop:
# - Designed for decision awareness, not decision-making.
# - NOT a navigation/routing/feasibility product.
# - NOT an official ice service or ice chart.
# =========================================================

# ---------------------------
# Branding strings
# ---------------------------
CUDA_ACRONYM = "Cryospheric Uncertainty–Driven Awareness"
APP_TITLE = "POLAR CUDA – Arctic Ice Situational Awareness Gauge"
APP_SUBTITLE = (
    "Human-vision–aligned sea-ice sentiment gauge "
    "for decision awareness (not decision-making)."
)

DISCLAIMER_TEXT = """
### ⚠ Mandatory disclaimer (situational awareness only)

**POLAR CUDA** is a **situational awareness gauge**, not an operational tool.

- **NOT** navigation, routing, or feasibility advice  
- **NOT** an official ice chart / ice service  
- **NOT** forecasting or prediction  
- **NOT** legal, safety, or operational advice  

This gauge uses a **daily PNG visualization** and a **human-in-the-loop calibration (α)**.  
All operational decisions and legal responsibility remain with the **user/operator**.  
Always consult official ice services, ice charts, regulations, insurance/contract terms, and professional judgement.
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

# ---------------------------------------------------------
# Files
# ---------------------------------------------------------
ALPHA_HISTORY_FILE = "alpha_history.csv"

# ---------------------------------------------------------
# Fixed ROIs
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
# ✅ UPDATED REGIONAL GROUPS (as requested)
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
# Default alpha correction
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
# Pixel classifier
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"
    if b > r and b > g:
        return "water"
    return "ice"

# ---------------------------------------------------------
# Raw & hybrid ice calculations
# ---------------------------------------------------------
def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape

    for y in range(y1, min(y2, h), step):
        for x in range(x1, min(x2, w), step):
            c = classify_pixel(arr[y, x])
            if c == "land":
                continue
            if c == "ice":
                ice += 1
            else:
                water += 1

    if ice + water == 0:
        return None
    return (ice / (ice + water)) * 100.0

def clamp_0_100(v):
    return max(0.0, min(100.0, v))

def compute_hybrid_ice(arr, region, roi, correction, step=4):
    raw = compute_raw_ice(arr, roi, step)
    if raw is None:
        return None, None
    alpha = correction.get(region, 1.0)
    hybrid = clamp_0_100(raw * alpha)
    return round(raw, 1), round(hybrid, 1)

# ---------------------------------------------------------
# Gauge labels
# ---------------------------------------------------------
def friction_level(ice_pct, t1, t2, t3, t4):
    if ice_pct <= t1:
        return "🟢 Extreme Open", "Very low friction"
    if ice_pct <= t2:
        return "🟩 Open", "Low friction"
    if ice_pct <= t3:
        return "🟡 Neutral", "Moderate friction"
    if ice_pct <= t4:
        return "🟠 Constrained", "High friction"
    return "🔴 Extreme Constrained", "Very high friction"

# ---------------------------------------------------------
# Alpha history
# ---------------------------------------------------------
def save_alpha_history(correction, date_obj):
    date_str = str(date_obj)
    rows = [{"date": date_str, "region": r, "alpha": float(a)} for r, a in correction.items()]
    df_new = pd.DataFrame(rows)

    if os.path.exists(ALPHA_HISTORY_FILE):
        df_old = pd.read_csv(ALPHA_HISTORY_FILE)
        df_old = df_old[df_old["date"] != date_str]
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(ALPHA_HISTORY_FILE, index=False)

# =========================================================
# UI
# =========================================================

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)
st.info(f"**CUDA = {CUDA_ACRONYM}**")

with st.expander("⚠ Disclaimer & Scope", expanded=True):
    st.markdown(DISCLAIMER_TEXT)
    st.markdown(f"> *{PHILOSOPHY_ONE_LINER}*")

ack = st.checkbox("I understand. Show situational awareness outputs.", value=False)
if not ack:
    st.stop()

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
st.write(f"**Analysis date:** {today}")

if st.button("🔄 Refresh (clear cache)"):
    st.cache_data.clear()
    st.rerun()

# Settings
st.subheader("Sampling & Gauge Settings")
step = st.slider("Sampling step", 2, 12, 4, 1)

t1 = st.slider("Extreme Open ≤", 0, 40, 15)
t2 = st.slider("Open ≤", 10, 60, 35)
t3 = st.slider("Neutral ≤", 20, 80, 60)
t4 = st.slider("Constrained ≤", 40, 95, 85)

if not (t1 < t2 < t3 < t4):
    st.error("Thresholds must satisfy: Extreme Open < Open < Neutral < Constrained")
    st.stop()

# Alpha selection
use_custom_alpha = st.checkbox("Manually adjust α", value=False)
correction = DEFAULT_CORRECTION.copy()

# Save alpha history
save_alpha_history(correction, today)

# Compute
arr = load_image()
rows = []
hybrid_values = []

for region, roi in REGIONS.items():
    raw, hybrid = compute_hybrid_ice(arr, region, roi, correction, step)
    if hybrid is None:
        continue
    lvl, note = friction_level(hybrid, t1, t2, t3, t4)
    rows.append({"Region": region, "Hybrid Ice Area (%)": hybrid})
    hybrid_values.append(hybrid)

df = pd.DataFrame(rows)

# ---------------------------------------------------------
# GROUP AVERAGES (UPDATED)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("Regional group averages (situational buckets)")

cols = st.columns(len(REGION_GROUPS))
for i, (group, members) in enumerate(REGION_GROUPS.items()):
    vals = df[df["Region"].isin(members)]["Hybrid Ice Area (%)"]
    if not vals.empty:
        avg = round(vals.mean(), 1)
        lvl, _ = friction_level(avg, t1, t2, t3, t4)
        with cols[i]:
            st.metric(group, f"{avg}%")
            st.write(lvl)
            st.progress(int(avg))
    else:
        with cols[i]:
            st.metric(group, "N/A")
            st.write("⚪ No data")

st.markdown("---")
st.caption(
    f"CUDA = {CUDA_ACRONYM}. "
    "POLAR CUDA provides situational awareness only."
)
