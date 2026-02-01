import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# POLAR CUDA Index
#
# “This index is designed for decision awareness,
#  not decision-making.”
#
# A daily situational awareness index
# for Arctic sea-ice conditions.
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Ice Risk Index",
    layout="centered"
)

# ---------------------------------------------------------
# Data source
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# Your fixed ROIs (pixel coordinates, stable)
# NOTE: (x1, y1, x2, y2)
# ---------------------------------------------------------
REGIONS = {
    "Sea of Okhotsk": (620, 90, 900, 330),
    "Bering Sea": (480, 300, 720, 520),
    "Chukchi Sea": (700, 420, 900, 580),
    "East Siberian Sea": (820, 380, 1030, 560),
    "Laptev Sea": (930, 370, 1150, 560),
    "Kara Sea": (1080, 420, 1280, 600),
    "Barents Sea": (1180, 520, 1420, 720),
    "Beaufort Sea": (650, 520, 850, 700),  # <- ONLY this one gets adaptive clustering
    "Canadian Arctic Archipelago": (650, 650, 880, 860),
    "Central Arctic Ocean": (820, 500, 1050, 720),
    "Greenland Sea": (980, 650, 1180, 900),
    "Baffin Bay": (760, 740, 980, 980),
}

# ---------------------------------------------------------
# Load AMSR2 image (safe & cached)
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image_safe():
    r = requests.get(AMSR2_URL, timeout=30)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Simple pixel classifier (keep your previous behavior)
# - BUT slightly safer "land" rule:
#   land is "green-dominant AND not cyan-ish" (b not too high)
#   -> reduces misclassifying low-ice cyan/green as land
# ---------------------------------------------------------
def classify_pixel_simple(rgb):
    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])

    # LAND: strong green, and blue is not high (avoid cyan sea-ice band)
    if (g > 150) and (g > r * 1.08) and (g > b * 1.05) and (b < 150):
        return "land"

    # WATER: blue-dominant
    if (b > 120) and (b > r * 1.10) and (b > g * 1.10):
        return "water"

    # everything else is treated as ICE (includes purple / yellow-red edge)
    return "ice"

# ---------------------------------------------------------
# Classic ice dominance index (0–100) : ice / (ice+water) excluding land
# ---------------------------------------------------------
def compute_index_simple(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    # clamp
    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)
    if x2 <= x1 + 5 or y2 <= y1 + 5:
        return None

    ice = 0
    sea = 0

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel_simple(arr[y, x])
            if c == "land":
                continue
            sea += 1
            if c == "ice":
                ice += 1

    if sea == 0:
        return None

    return round((ice / sea) * 100, 1)

# ---------------------------------------------------------
# Tiny k-means (no sklearn) for Beaufort-only adaptive clustering
# We cluster ROI pixels into 3 groups and map them to land/water/ice
# ---------------------------------------------------------
def kmeans_rgb(points, k=3, iters=12, seed=7):
    if len(points) < k:
        return None, None

    rng = np.random.default_rng(seed)
    idx = rng.choice(len(points), size=k, replace=False)
    centers = points[idx].copy()

    for _ in range(iters):
        d2 = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)  # (N,k)
        labels = d2.argmin(axis=1)

        new_centers = centers.copy()
        for i in range(k):
            m = labels == i
            if m.any():
                new_centers[i] = points[m].mean(axis=0)

        if np.allclose(new_centers, centers, atol=1.0):
            centers = new_centers
            break
        centers = new_centers

    return centers, labels

def pick_land_water_ice_clusters(centers):
    """
    Heuristic mapping:
      - land  : highest G
      - water : highest (B - 0.55*G)  (blue-ish, not green)
      - ice   : remaining
    """
    g = centers[:, 1]
    land = int(np.argmax(g))

    score_water = centers[:, 2] - 0.55 * centers[:, 1]
    water = int(np.argmax(score_water))
    if water == land:
        water = int(np.argsort(score_water)[-2])

    ice = [i for i in range(len(centers)) if i not in (land, water)]
    ice = int(ice[0]) if ice else int(np.argsort(score_water)[0])

    return land, water, ice

def compute_index_beaufort_adaptive(arr, roi, step=3):
    """
    Beaufort-only:
      - sample pixels in ROI
      - cluster into 3 groups (land/water/ice) adaptively
      - exclude land
      - index = ice / (ice+water)
    """
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    # clamp
    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)
    if x2 <= x1 + 5 or y2 <= y1 + 5:
        return None, None

    pixels = arr[y1:y2:step, x1:x2:step].reshape(-1, 3).astype(np.float32)
    # remove near-black gridline pixels to stabilize clustering
    # (gridlines can be dark and distort centers)
    keep = pixels.mean(axis=1) > 25
    pixels = pixels[keep]
    if pixels.shape[0] < 200:
        return None, None

    centers, labels = kmeans_rgb(pixels, k=3, iters=14, seed=7)
    if centers is None:
        return None, None

    land_c, water_c, ice_c = pick_land_water_ice_clusters(centers)

    land_n = int(np.sum(labels == land_c))
    water_n = int(np.sum(labels == water_c))
    ice_n = int(np.sum(labels == ice_c))
    sea_n = water_n + ice_n

    if sea_n <= 0:
        dbg = {"land": land_n, "water": water_n, "ice": ice_n, "sea": sea_n, "centers": centers}
        return None, dbg

    idx = round((ice_n / sea_n) * 100.0, 1)
    dbg = {"land": land_n, "water": water_n, "ice": ice_n, "sea": sea_n, "centers": centers}
    return idx, dbg

# ---------------------------------------------------------
# Index label (simple, intuitive)
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
# UI (Index only)
# =========================================================
st.title("🧊 POLAR CUDA – Ice Risk Index")
st.markdown(
    "**POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)**  \n"
    "“This index is designed for decision awareness, not decision-making.”  \n"
    "*A daily situational awareness index for Arctic sea-ice conditions.*"
)

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

col1, col2 = st.columns([1, 2])
with col1:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

with col2:
    show_debug = st.checkbox("Show Beaufort diagnostics (optional)", value=False)

arr = load_image_safe()

results = []
indices = []

for region, roi in REGIONS.items():
    if region == "Beaufort Sea":
        idx, dbg = compute_index_beaufort_adaptive(arr, roi, step=3)
        if show_debug and dbg is not None:
            total = dbg["land"] + dbg["water"] + dbg["ice"]
            if total > 0:
                st.caption(
                    f"[diag] Beaufort: land {dbg['land']/total:.1%}, "
                    f"water {dbg['water']/total:.1%}, ice {dbg['ice']/total:.1%} "
                    f"(sea-only ice = {dbg['ice']/max(dbg['sea'],1):.1%})"
                )
    else:
        idx = compute_index_simple(arr, roi, step=4)

    if idx is None:
        results.append({"Region": region, "Index": "N/A", "Status": "⚪ No data"})
        continue

    indices.append(idx)
    results.append({"Region": region, "Index": idx, "Status": label(idx)})

df = pd.DataFrame(results)

if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Risk (Simple View)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']}  |  Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects **relative sea-ice area dominance** within your fixed operational ROIs.
It is designed for **decision awareness**, similar to a market sentiment index.

⚠ This tool does **not** indicate navigability, routing feasibility,
or replace official ice services, ice charts, or operational decision systems.
"""
)
