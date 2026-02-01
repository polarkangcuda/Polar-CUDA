import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

st.set_page_config(
    page_title="POLAR CUDA – Ice Risk Index",
    layout="centered"
)

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

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

@st.cache_data(ttl=CACHE_TTL)
def load_image_safe():
    try:
        r = requests.get(AMSR2_URL, timeout=15)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB")
        return np.array(img)
    except Exception as e:
        return None, str(e)

def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.1 and g > b * 1.1:
        return "land"
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "water"
    return "ice"

def compute_index(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = ocean = 0
    h, w, _ = arr.shape
    x2, y2 = min(x2, w), min(y2, h)

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel(arr[y, x])
            if c == "land":
                continue
            ocean += 1
            if c == "ice":
                ice += 1

    if ocean == 0:
        return None
    return round((ice / ocean) * 100, 1)

def label(idx):
    if idx >= 80: return "🔴 Ice-dominant"
    if idx >= 60: return "🟠 High ice"
    if idx >= 35: return "🟡 Mixed"
    return "🟢 More open"

# ================= UI =================

st.title("🧊 POLAR CUDA – Ice Risk Index")
st.caption("Daily Arctic sea-ice awareness index (non-directive)")
st.write(f"**Analysis date:** {datetime.date.today()}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.info("Cache cleared. Reloading latest data…")

with st.spinner("Loading latest AMSR2 sea-ice image…"):
    arr, err = load_image_safe()

if arr is None:
    st.error("❌ Failed to load AMSR2 image.")
    st.code(err)
    st.stop()

# 디버그용 (정상 확인 후 제거 가능)
st.caption(f"Image loaded successfully: shape = {arr.shape}")

results = []
indices = []

for region, roi in REGIONS.items():
    idx = compute_index(arr, roi)
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
    st.metric("Polar CUDA Index (overall)", f"{overall} / 100")

st.markdown("---")
st.subheader("Sea-Region Ice Risk (Simple View)")

for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {r['Status']}  |  Index: {r['Index']}")

st.markdown("---")
st.caption(
    """
Data source: University of Bremen AMSR2 daily sea-ice concentration PNG.

This index reflects relative ice dominance in expert-defined operational regions.
It provides situational awareness only and does not indicate navigability.
"""
)
