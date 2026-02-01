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
# A daily situational awareness index for Arctic sea-ice conditions.
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Ice Risk Index", layout="centered")

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600  # seconds

# ---------------------------------------------------------
# Fixed ROIs (pixel coordinates)
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
# Load AMSR2 image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image_safe():
    r = requests.get(AMSR2_URL, timeout=30)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Minimal k-means (RGB, no sklearn)
# ---------------------------------------------------------
def kmeans_rgb(points, k=3, iters=12, seed=7):
    if len(points) < k:
        return None, None

    rng = np.random.default_rng(seed)
    centers = points[rng.choice(len(points), size=k, replace=False)].copy()

    for _ in range(iters):
        d2 = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = d2.argmin(axis=1)

        new_centers = centers.copy()
        for i in range(k):
            mask = labels == i
            if mask.any():
                new_centers[i] = points[mask].mean(axis=0)

        if np.allclose(new_centers, centers, atol=1.0):
            break
        centers = new_centers

    return centers, labels

def pick_land_water_ice_clusters(centers):
    g = centers[:, 1]
    land = int(np.argmax(g))

    score_water = centers[:, 2] - 0.6 * centers[:, 1]
    water = int(np.argmax(score_water))
    if water == land:
        water = int(np.argsort(score_water)[-2])

    ice = [i for i in range(3) if i not in (land, water)][0]
    return land, water, ice

# ---------------------------------------------------------
# Human-eye based ice area index
# (Beaufort Sea only: local correction)
# ---------------------------------------------------------
def compute_ice_area_index(arr, roi, region_name, step=3):
    x1, y1, x2, y2 = roi
    h, w, _ = arr.shape

    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h, y2))

    if x2 <= x1 + 5 or y2 <= y1 + 5:
        return None

    pts = arr[y1:y2:step, x1:x2:step].reshape(-1, 3).astype(np.float32)
    if pts.shape[0] < 100:
        return None

    centers, labels = kmeans_rgb(pts)
    if centers is None:
        return None

    land_c, water_c, ice_c = pick_land_water_ice_clusters(centers)

    water_n = np.sum(labels == water_c)
    ice_n = np.sum(labels == ice_c)
    sea_n = water_n + ice_n

    if sea_n == 0:
        return None

    ice_ratio = ice_n / sea_n
    idx = round(ice_ratio * 100.0, 1)

    # 🔧 Beaufort Sea ONLY – human-eye correction
    if region_name == "Beaufort Sea" and ice_ratio >= 0.5:
        idx = 100.0

    return idx

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

st.title("🧊 POLAR CUDA – Ice Risk Index")
st.markdown(
    "**POLAR CUDA (Cryospheric Uncertainty & Decision Awareness)**  \n"
    "“This index is designed for decision awareness, not decision-making.”  \n"
    "*Daily situational awareness for Arctic sea-ice conditions*"
)

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

arr = load_image_safe()

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_ice_area_index(arr, roi, region)
    if idx is None:
        results.append({"Region": region, "Index": "N/A", "Status": "⚪ No data"})
    else:
        indices.append(idx)
        results.append({"Region": region, "Index": idx, "Status": label(idx)})

df = pd.DataFrame(results)

if indices:
    overall = round(sum(indices) / len(indices), 1)
    st.metric("POLAR CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Risk (Human-eye based)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']}  |  Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects **human-eye-equivalent sea-ice area dominance**
within your fixed operational ROIs.

⚠ This tool provides **decision awareness only**.
It does **not** indicate navigability, routing feasibility,
or replace official ice charts or operational decision systems.
"""
)
