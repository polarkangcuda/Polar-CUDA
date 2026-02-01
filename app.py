import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd
# =========================================================
# POLAR CUDA
# Sea Ice Situational Awareness Gauge (NO PLOTLY)
## Designed for decision awareness, not decision-making.
# Not a navigation or routing tool.
# =========================================================
st.set_page_config(
    page_title="POLAR CUDA – Sea Ice Gauge",
    layout="centered"
)# ---------------------------------------------------------
# Data source (daily updated)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600
# ---------------------------------------------------------
# Fixed ROIs (expert-defined)
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
}# ---------------------------------------------------------
# Human visual correction factors (default)
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
}# ---------------------------------------------------------
# Load AMSR2 image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)
# ---------------------------------------------------------
# Pixel classifier (human-vision aligned)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb
    # LAND (bright green)
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"
    # WATER (any blue-dominant tone)
    if b > r and b > g:
        return "water"
    # ICE (pink / purple / yellow / red / white)
    return "ice"
# ---------------------------------------------------------
# Raw ice percentage (satellite color proxy)
# ---------------------------------------------------------
def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape
    x1, x2 = max(0, x1), min(w - 1, x2)
    y1, y2 = max(0, y1), min(h - 1, y2)
    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
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
# ---------------------------------------------------------
# Hybrid ice area (%)
# ---------------------------------------------------------
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
# Fear & Greed style mapping
# NOTE: We avoid "navigable / not navigable"
# Use "Operational Friction" language
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
def friction_color_band(ice_pct, t1, t2, t3, t4):
    # For a simple color hint in text only (no external libs)
    if ice_pct <= t1:
        return "green"
    if ice_pct <= t2:
        return "green"
    if ice_pct <= t3:
        return "orange"
    if ice_pct <= t4:
        return "orange"
    return "red"
# =========================================================
# UI
# =========================================================
st.title("🧊 POLAR CUDA – Sea Ice Situational Awareness Gauge")
st.caption("Fear & Greed–style situational gauge (awareness-only, not operational advice)")
with st.expander("⚠ Mandatory disclaimer (read before use)", expanded=True):
    st.markdown(
        """
**This tool provides situational awareness only.**
- NOT a navigation / routing / feasibility product  
- NOT an official ice chart or ice service  
- NOT legal, safety, or operational advice  
All operational and legal responsibility remains with the user/operator.  
Use official ice services, ice charts, and professional judgement for operations.
"""
    )
ack = st.checkbox("I understand and accept the above. Show outputs.", value=False)
if not ack:
    st.stop()
today = datetime.date.today()
st.write(f"**Analysis date:** {today}")
# Refresh
if st.button("🔄 Refresh (clear cache)"):
    st.cache_data.clear()
    st.rerun()
# Settings
step = st.slider("Sampling step (speed vs detail)", 2, 12, 4, 1)
st.subheader("Gauge thresholds (tunable)")
t1 = st.slider("Extreme Open ≤", 0, 40, 15)
t2 = st.slider("Open ≤", 10, 60, 35)
t3 = st.slider("Neutral ≤", 20, 80, 60)
t4 = st.slider("Constrained ≤", 40, 95, 85)
if not (t1 < t2 < t3 < t4):
    st.error("Thresholds must satisfy: Extreme Open < Open < Neutral < Constrained")
    st.stop()
# Correction factors
st.subheader("Hybrid calibration (regional correction α)")
use_custom_alpha = st.checkbox(
    "Manually adjust correction factors (advanced users)",
    value=False
)if use_custom_alpha:
    correction = {}
    with st.expander("Edit correction factors", expanded=True):
        for k in DEFAULT_CORRECTION:
            correction[k] = st.number_input(
                f"{k} α",
                min_value=0.10,
                max_value=3.00,
                value=float(DEFAULT_CORRECTION[k]),
                step=0.05
            )
else:
    correction = DEFAULT_CORRECTION.copy()
# Compute
arr = load_image()
rows = []
hybrid_values = []
for region, roi in REGIONS.items():
    raw, hybrid = compute_hybrid_ice(arr, region, roi, correction, step)
    if hybrid is None:
        rows.append({
            "Region": region,
            "Raw (%)": "N/A",
            "Hybrid Ice Area (%)": "N/A",
            "Gauge": "⚪ No data",
            "Note": ""
        })
        continue
    lvl, note = friction_level(hybrid, t1, t2, t3, t4)
    rows.append({
        "Region": region,
        "Raw (%)": raw,
        "Hybrid Ice Area (%)": hybrid,
        "Gauge": lvl,
        "Note": note
    })
    hybrid_values.append(hybrid)
df = pd.DataFrame(rows)
# Overall gauge
st.markdown("---")
st.subheader("Overall situational gauge (average across regions)")
if hybrid_values:
    overall = round(sum(hybrid_values) / len(hybrid_values), 1)
    overall_lvl, overall_note = friction_level(overall, t1, t2, t3, t4)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Overall (Hybrid %)", f"{overall}%")
    with col2:
        st.write(f"**Overall gauge:** {overall_lvl}  — {overall_note}")
    # Simple gauge visualization without plotly
    st.progress(int(overall))  # 0..100
    st.caption("Progress bar is a visual proxy of Hybrid Ice Area (%).")
else:
    st.warning("No valid data returned today.")
# Region list
st.markdown("---")
st.subheader("Sea-region situational gauges")
for _, r in df.iterrows():
    if isinstance(r["Hybrid Ice Area (%)"], (int, float, np.floating)):
        val = float(r["Hybrid Ice Area (%)"])
        st.write(
            f"**{r['Region']}** → {r['Gauge']}  |  "
            f"Hybrid: {r['Hybrid Ice Area (%)']}% (raw {r['Raw (%)']}%)  |  {r['Note']}"
        )
        st.progress(int(val))
    else:
        st.write(f"**{r['Region']}** → {r['Gauge']}")
# Table + download
st.markdown("---")
st.subheader("Table (downloadable)")
st.dataframe(df, use_container_width=True)
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇ Download today’s table (CSV)",
    data=csv,
    file_name=f"polar_cuda_{today}.csv",
    mime="text/csv"
)st.caption(
    "Data source: University of Bremen AMSR2 daily PNG. "
    "POLAR CUDA provides situational awareness only (not operational advice)."
)
