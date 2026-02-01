import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA – Public Edition (12 Regions)
# Robust masking:
# - ignores white margins / legend background
# - ignores gridlines/text (dark gray/black)
# - more stable water/land detection
# =========================================================

st.set_page_config(page_title="POLAR CUDA", layout="wide")

st.title("🧊 POLAR CUDA")
st.subheader("Arctic Ice Situational Awareness Gauge (12 Regions)")
st.caption("Public-friendly situational awareness only — not navigation, not forecast, not official ice chart.")

with st.expander("⚠️ Important notice", expanded=True):
    st.markdown(
        """
**POLAR CUDA is NOT an operational navigation tool.**

• Not a forecast  
• Not an official ice chart  
• Not a routing or safety service  

This gauge helps you **sense today’s situation**, not decide what to do.
"""
    )

agree = st.checkbox("I understand. Show today’s situation.", value=False)
if not agree:
    st.stop()

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# 12 ROIs (as you defined)
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

# -----------------------------
# Robust pixel masking rules
# -----------------------------
def build_masks(arr):
    """Return masks: white_margin, dark_grid, land, water.
    Everything else (non-masked, non-land, non-water) is treated as ice-like."""
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)

    # (A) white margin / legend background: near-white pixels
    white = (r > 245) & (g > 245) & (b > 245)

    # (B) dark gridlines / text: near-black or dark gray
    # - captures graticule lines and labels
    # - also handles dark blue? (we keep threshold conservative)
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    dark = (maxc < 65) | ((maxc < 90) & ((maxc - minc) < 12))

    # (C) land: bright green (Bremen land is very green)
    land = (g > 150) & (g > r + 40) & (g > b + 40)

    # (D) water: blue-ish & relatively dark (ocean background)
    # Use both "blue dominance" and "not too bright" constraints
    water = (b > 80) & (b > r + 15) & (b > g + 10) & (g < 140) & (r < 140)

    return white, dark, land, water

def compute_ice_presence(arr, roi, masks, step=4):
    """Ice presence (%) within ROI, excluding land, white margins, dark grid/text."""
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    x1 = max(0, x1); y1 = max(0, y1)
    x2 = min(w, x2); y2 = min(h, y2)

    white, dark, land, water = masks

    # sample grid
    ys = np.arange(y1, y2, step)
    xs = np.arange(x1, x2, step)
    if len(xs) == 0 or len(ys) == 0:
        return None

    yy, xx = np.meshgrid(ys, xs, indexing="ij")

    # valid = not land, not white, not dark (grid/text)
    valid = (~land[yy, xx]) & (~white[yy, xx]) & (~dark[yy, xx])

    if valid.sum() == 0:
        return None

    # among valid pixels: classify water vs ice-like
    # if not water -> count as ice-like (includes concentration colors)
    water_pix = water[yy, xx] & valid
    ice_like = valid & (~water_pix)

    total = valid.sum()
    ice_count = ice_like.sum()

    return round((ice_count / total) * 100.0, 1)

def gauge_label(pct):
    if pct < 25:
        return "🟢 Mostly Open", "Low ice presence"
    if pct < 50:
        return "🟡 Mixed", "Ice and open water coexist"
    if pct < 75:
        return "🟠 Ice-dominant", "Ice conditions increasingly present"
    return "🔴 Heavily Ice-covered", "Ice dominates the region"

# -----------------------------
# Run
# -----------------------------
arr = load_image()
masks = build_masks(arr)
today = datetime.date.today()

st.markdown("---")
st.subheader(f"🧭 Today’s Arctic Sea-Ice Situation ({today})")

# 12 cards in 3x4 grid
items = list(REGIONS.items())
rows = [items[i:i+4] for i in range(0, 12, 4)]

for row in rows:
    cols = st.columns(4)
    for col, (name, roi) in zip(cols, row):
        with col:
            st.markdown(f"### {name}")
            pct = compute_ice_presence(arr, roi, masks, step=4)

            if pct is None:
                st.write("Ice presence: N/A")
                st.write("Situation: ⚪ No data")
                continue

            label, note = gauge_label(pct)
            st.write(f"**Ice presence:** {pct}%")
            st.write(f"**Situation:** {label}")
            st.caption(note)
            st.progress(int(pct))

st.markdown("---")
st.caption("POLAR CUDA provides situational awareness only. It helps you sense when to hesitate — not what to do.")
