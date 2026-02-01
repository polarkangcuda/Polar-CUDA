import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)
# Sea-Region Ice Area Index (Human-eye based)
#
# “This index is designed for decision awareness,
#  not decision-making.”
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Sea-Region Ice Area",
    layout="centered"
)

# ---------------------------------------------------------
# Data source (visual NIC-style PNG)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

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
# Load image (safe & cached)
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Simple k-means (RGB only, no sklearn)
# ---------------------------------------------------------
def kmeans_rgb(pixels, k=3, iters=10, seed=0):
    rng = np.random.default_rng(seed)
    centers = pixels[rng.choice(len(pixels), k, replace=False)]

    for _ in range(iters):
        dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centers = []
        for i in range(k):
            if np.any(labels == i):
                new_centers.append(pixels[labels == i].mean(axis=0))
            else:
                new_centers.append(centers[i])
        new_centers = np.array(new_centers)
        if np.allclose(centers, new_centers, atol=2):
            break
        centers = new_centers

    return centers, labels

# ---------------------------------------------------------
# Identify land / water / ice clusters (human-eye logic)
# ---------------------------------------------------------
def classify_clusters(centers):
    # land: strong green
    land_idx = np.argmax(centers[:, 1])

    # water: strong blue
    water_idx = np.argmax(centers[:, 2])

    # ice: remaining cluster
    ice_idx = list({0, 1, 2} - {land_idx, water_idx})[0]

    return land_idx, water_idx, ice_idx

# ---------------------------------------------------------
# Human-eye based ice area index
# ---------------------------------------------------------
def compute_ice_index(arr, roi, step=3):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h, y2))

    pixels = arr[y1:y2:step, x1:x2:step].reshape(-1, 3).astype(np.float32)
    if len(pixels) < 300:
        return None

    centers, labels = kmeans_rgb(pixels, k=3, iters=12, seed=7)
    land_c, water_c, ice_c = classify_clusters(centers)

    land_n = np.sum(labels == land_c)
    water_n = np.sum(labels == water_c)
    ice_n = np.sum(labels == ice_c)

    total = land_n + water_n + ice_n
    sea = water_n + ice_n
    if sea == 0:
        return None

    ice_ratio_sea = ice_n / sea
    ice_ratio_total = ice_n / total

    # -------------------------------------------------
    # 🔑 HUMAN-EYE DOMINANCE OVERRIDE
    # -------------------------------------------------
    # 해빙이 "덩어리로 지배"하면 100%
    if ice_ratio_sea >= 0.6 and ice_ratio_total >= 0.5:
        return 100.0

    return round(ice_ratio_sea * 100, 1)

# ---------------------------------------------------------
# Label
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

st.title("🧊 POLAR CUDA – Sea-Region Ice Area")
st.markdown(
    "**POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)**  \n"
    "*Human-eye based sea-region ice dominance index*"
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
    idx = compute_ice_index(arr, roi)
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

# Overall index
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
**Data source**: University of Bremen AMSR2 daily NIC-style PNG.

This index reflects **human-eye based ice dominance**
within expert-defined sea regions.

⚠ Not for navigation, routing, or operational decision-making.
"""
)
