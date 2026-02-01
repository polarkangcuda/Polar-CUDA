import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA – Level 3
# "Ice Risk Index" (Fear/Greed style, non-directive)
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Ice Risk Index", layout="wide")

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL_SEC = 3600  # 1 hour

# ---------------------------------------------------------
# Expert-defined fixed ROIs (pixel coordinates on the PNG)
# Format: (x1, y1, x2, y2)
# ---------------------------------------------------------
REGIONS = {
    "1. Sea of Okhotsk": (620, 90, 900, 330),
    "2. Bering Sea": (480, 300, 720, 520),
    "3. Chukchi Sea": (700, 420, 900, 580),
    "4. East Siberian Sea": (820, 380, 1030, 560),
    "5. Laptev Sea": (930, 370, 1150, 560),
    "6. Kara Sea": (1080, 420, 1280, 600),
    "7. Barents Sea": (1180, 520, 1420, 720),
    "8. Beaufort Sea": (650, 520, 850, 700),
    "9. Canadian Arctic Archipelago": (650, 650, 880, 860),
    "10. Central Arctic Ocean": (820, 500, 1050, 720),
    "11. Greenland Sea": (980, 650, 1180, 900),
    "12. Baffin Bay": (760, 740, 980, 980),
}

# ---------------------------------------------------------
# Fetch image (daily updated)
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL_SEC)
def load_amsr2_png():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

def classify_pixel(rgb):
    r, g, b = rgb

    # Land: bright green dominance
    if g > 160 and g > r * 1.1 and g > b * 1.1:
        return "land"

    # Open water: deep/dark blue dominance
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "water"

    # Everything else: sea ice (any concentration color)
    return "ice"

def compute_region_index(arr, roi, step=3):
    """
    Returns:
      index_0_100: ice-dominance based risk index (0=open ~ 100=ice-dominant)
      ice_ratio:   ice / (ice+water)
      water_ratio: water / (ice+water)
      ocean_n:     counted ocean pixels
    """
    h, w, _ = arr.shape
    x1, y1, x2, y2 = roi

    # clamp
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h))

    ice = water = ocean = 0

    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel(arr[y, x])
            if c == "land":
                continue
            ocean += 1
            if c == "ice":
                ice += 1
            else:
                water += 1

    if ocean == 0:
        return None, 0.0, 0.0, 0

    ice_ratio = ice / ocean
    water_ratio = water / ocean

    # Polar CUDA Ice Risk Index (0~100)
    index_0_100 = float(np.clip(ice_ratio * 100.0, 0, 100))
    return index_0_100, ice_ratio, water_ratio, ocean

def label_from_index(idx):
    # non-directive labels (awareness only)
    if idx >= 80:
        return "🔴 Ice-dominant"
    if idx >= 60:
        return "🟠 High ice"
    if idx >= 35:
        return "🟡 Mixed"
    return "🟢 More open"

def draw_rois(img, regions):
    out = img.copy()
    d = ImageDraw.Draw(out)
    for name, (x1, y1, x2, y2) in regions.items():
        d.rectangle([x1, y1, x2, y2], outline=(255, 215, 0), width=3)  # yellow-ish
    return out

# =========================================================
# UI
# =========================================================
st.title("🧊 POLAR CUDA – Ice Risk Index")
st.caption("A simple, daily situational-awareness index (Fear/Greed style) for Arctic sea-ice conditions by sea region.")

colA, colB = st.columns([1, 1])
with colA:
    analysis_date = datetime.date.today()
    st.write(f"**Analysis date (local):** {analysis_date}")
with colB:
    if st.button("🔄 Refresh now (ignore cache)"):
        st.cache_data.clear()
        st.experimental_rerun()

img = load_amsr2_png()
arr = np.array(img)

# Top: map with yellow ROIs
st.subheader("Map view (expert-defined fixed ROIs)")
overlay = draw_rois(img, REGIONS)
st.image(overlay, use_container_width=True)

# Compute all indices
rows = []
valid_indices = []
for region, roi in REGIONS.items():
    idx, ice_r, water_r, ocean_n = compute_region_index(arr, roi, step=3)

    if idx is None:
        rows.append({
            "Region": region,
            "Index (0-100)": None,
            "Label": "⚪ No ocean pixels",
            "Ice %": 0.0,
            "Water %": 0.0,
            "Ocean samples": 0
        })
        continue

    valid_indices.append(idx)

    rows.append({
        "Region": region,
        "Index (0-100)": round(idx, 1),
        "Label": label_from_index(idx),
        "Ice %": round(ice_r * 100.0, 1),
        "Water %": round(water_r * 100.0, 1),
        "Ocean samples": int(ocean_n)
    })

df = pd.DataFrame(rows)

# Overall index (simple mean of regions)
if valid_indices:
    overall = float(np.mean(valid_indices))
else:
    overall = None

st.subheader("Today’s Polar CUDA Index (summary)")
if overall is None:
    st.error("Unable to compute overall index (no valid ocean pixels).")
else:
    st.metric(label="Polar CUDA Index (mean of 12 regions)", value=f"{overall:.1f} / 100", delta=None)
    st.caption("Interpretation: higher = more ice-dominant across your operational sea regions. This is NOT a routing decision.")

st.subheader("Sea-region index table (simple view)")
st.dataframe(df, use_container_width=True, hide_index=True)

# Optional: compact list view (like Fear/Greed dashboard)
st.subheader("Sea-Region Feasibility (very simple list)")
for _, r in df.iterrows():
    if pd.isna(r["Index (0-100)"]):
        st.write(f"**{r['Region']}** → {r['Label']}")
    else:
        st.write(f"**{r['Region']}** → {r['Label']}  |  **Index:** {r['Index (0-100)']}  |  Ice {r['Ice %']}% / Water {r['Water %']}%")

# ---------------------------------------------------------
# Legal / methodology notice
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    f"""
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG  
(Arctic_AMSR2_nic.png; publicly accessible daily image).  

**Method**: This app computes a simple **image-derived ice-dominance ratio** within
**expert-defined fixed ROIs** (yellow boxes) and expresses it as an **Index (0–100)**.  
0 ≈ more open-water dominant; 100 ≈ more ice-dominant.  

**Non-authoritative / Non-directive notice**:  
This output is **situational awareness only** and is **not** an ice-routing service,
not an official ice chart, and not a navigational decision system.  
Final operational decisions and liabilities remain with operators and vessel masters.
"""
)
