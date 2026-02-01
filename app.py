import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd
import plotly.graph_objects as go

# =========================================================
# POLAR CUDA – Sea Ice Situational Awareness Gauge
# ---------------------------------------------------------
# IMPORTANT:
# - Not a navigation tool
# - Not an ice chart
# - Not routing/feasibility advice
# - Decision responsibility remains with the user/operator
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Sea Ice Gauge", layout="centered")

AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# Expert-defined fixed ROIs (pixel coordinates)
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

# Human visual correction factors (α) – can be tuned
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
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# Visual classifier (simple)
def classify_pixel(rgb):
    r, g, b = rgb

    # LAND: vivid green
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"

    # WATER: blue-dominant tones
    if b > r and b > g:
        return "water"

    # ICE: everything else (pink/purple/yellow/red/white)
    return "ice"

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

def clamp_0_100(x: float) -> float:
    return max(0.0, min(100.0, x))

def compute_hybrid_ice(arr, region, roi, correction, step=4):
    raw = compute_raw_ice(arr, roi, step=step)
    if raw is None:
        return None, None
    alpha = correction.get(region, 1.0)
    hybrid = clamp_0_100(raw * alpha)
    return round(raw, 1), round(hybrid, 1)

# ---------------------------------------------------------
# Gauge mapping (Fear & Greed style)
# We avoid "navigable/non-navigable" language.
# Instead: Operational Friction (how constrained it "looks")
# ---------------------------------------------------------
def friction_label_from_ice(ice_pct: float, bands: dict):
    """
    ice_pct: Hybrid ice area (%) 0..100
    bands example (ascending):
        {"Extreme Open": 15, "Open": 35, "Neutral": 60, "Constrained": 85}
    returns 5-level label
    """
    t1 = bands["Extreme Open"]
    t2 = bands["Open"]
    t3 = bands["Neutral"]
    t4 = bands["Constrained"]

    # Low ice -> more open (less friction)
    if ice_pct <= t1:
        return "Extreme Open", "🟢"
    if ice_pct <= t2:
        return "Open", "🟩"
    if ice_pct <= t3:
        return "Neutral", "🟡"
    if ice_pct <= t4:
        return "Constrained", "🟠"
    return "Extreme Constrained", "🔴"

def make_gauge(title: str, value: float):
    # Plotly indicator gauge; neutral wording.
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%"},
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "white"},
        }
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=50, b=10))
    return fig

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Sea Ice Situational Awareness Gauge")
st.caption("A daily, visual-proxy gauge for sea-ice situation awareness (not operational advice).")

with st.expander("⚠️ Important disclaimer (please read)", expanded=True):
    st.markdown(
        """
**This application is NOT an ice navigation product.**  
It does **not** provide routing advice, navigability judgments, or operational clearance.

- Data are derived from a **daily PNG visualization** (University of Bremen AMSR2).
- Calculations are **approximate** and **human-vision–aligned**, not a validated geophysical area product.
- Use of this gauge is for **situational awareness only**.
- **All operational decisions** (route planning, speed, ice class, escort, insurance, regulatory compliance, safety)  
  must be made by the responsible operator using official ice services, ice charts, and professional expertise.
        """
    )

ack = st.checkbox("I understand. Show situational awareness outputs (not operational advice).", value=False)
if not ack:
    st.stop()

today = datetime.date.today()
st.write(f"**Analysis date:** {today}")

colA, colB = st.columns(2)

with colA:
    step = st.slider("Sampling step (speed vs detail)", min_value=2, max_value=12, value=4, step=1)
with colB:
    st.button("🔄 Refresh (clear cache)", on_click=lambda: st.cache_data.clear())

# Gauge thresholds (tunable)
st.subheader("Gauge settings (tunable thresholds)")
st.caption("These thresholds map Hybrid Ice Area (%) to a 5-level situational gauge (Fear & Greed style).")

t_ext_open = st.slider("Extreme Open ≤", 0, 40, 15, 1)
t_open = st.slider("Open ≤", 10, 60, 35, 1)
t_neutral = st.slider("Neutral ≤", 20, 80, 60, 1)
t_constrained = st.slider("Constrained ≤", 40, 95, 85, 1)

# Ensure monotonic (simple safeguard)
if not (t_ext_open < t_open < t_neutral < t_constrained):
    st.error("Thresholds must satisfy: Extreme Open < Open < Neutral < Constrained.")
    st.stop()

bands = {
    "Extreme Open": t_ext_open,
    "Open": t_open,
    "Neutral": t_neutral,
    "Constrained": t_constrained
}

# Correction factors editor (optional)
st.subheader("Hybrid calibration (regional correction α)")
st.caption("These α values align satellite color-signal to your visual judgement. You can tune them anytime.")

correction = {}
with st.expander("Edit correction factors (advanced)", expanded=False):
    for k in DEFAULT_CORRECTION:
        correction[k] = st.number_input(f"{k} α", min_value=0.10, max_value=3.00, value=float(DEFAULT_CORRECTION[k]), step=0.05)
else:
    correction = DEFAULT_CORRECTION.copy()

# Load image & compute
arr = load_image()

rows = []
hybrid_values = []

for region, roi in REGIONS.items():
    raw, hybrid = compute_hybrid_ice(arr, region, roi, correction, step=step)
    if hybrid is None:
        rows.append({
            "Region": region,
            "Raw (%)": "N/A",
            "Hybrid Ice Area (%)": "N/A",
            "Gauge": "⚪ No data",
        })
        continue

    lvl, icon = friction_label_from_ice(hybrid, bands)
    rows.append({
        "Region": region,
        "Raw (%)": raw,
        "Hybrid Ice Area (%)": hybrid,
        "Gauge": f"{icon} {lvl}",
    })
    hybrid_values.append(hybrid)

df = pd.DataFrame(rows)

# Overall gauge (mean of regions; awareness-only)
st.markdown("---")
st.subheader("Overall situational gauge (average across regions)")
if hybrid_values:
    overall = round(sum(hybrid_values) / len(hybrid_values), 1)
    lvl, icon = friction_label_from_ice(overall, bands)
    st.metric("POLAR CUDA (Hybrid, overall)", f"{overall}%", help="Average across the defined ROIs; not an operational metric.")
    st.write(f"Overall gauge: **{icon} {lvl}**")
    st.plotly_chart(make_gauge("Overall Hybrid Ice Area", overall), use_container_width=True)
else:
    st.warning("No valid data returned from the image today.")

# Region outputs
st.markdown("---")
st.subheader("Sea-region situational gauge (Fear & Greed style)")

# Show as text + optional per-region gauge charts
show_gauges = st.checkbox("Show per-region gauges", value=False)

for _, r in df.iterrows():
    st.write(
        f"**{r['Region']}** → {r['Gauge']}  |  "
        f"Hybrid: {r['Hybrid Ice Area (%)']}% (raw {r['Raw (%)']}%)"
    )
    if show_gauges and isinstance(r["Hybrid Ice Area (%)"], (int, float, np.floating)):
        st.plotly_chart(make_gauge(r["Region"], float(r["Hybrid Ice Area (%)"])), use_container_width=True)

# Download table
st.markdown("---")
st.subheader("Download today's table")
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Download CSV", data=csv, file_name=f"polar_cuda_{today}.csv", mime="text/csv")

st.caption(
    """
**Data source**: University of Bremen AMSR2 daily sea-ice concentration PNG.  
**POLAR CUDA** provides **situational awareness only**. It does not certify navigability or operational feasibility.
"""
)
