import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd
import os

# =========================================================
# POLAR CUDA – Sea Ice Situational Awareness Gauge (v2.2)
# ---------------------------------------------------------
# - Human-vision proxy + regional correction (alpha)
# - Logs alpha history
# - Seasonal alpha trend (monthly)
# - Yesterday vs Today delta
# - Regional group averages (Pacific/Atlantic)
#
# Designed for decision awareness, not decision-making.
# Not a navigation/routing/feasibility product.
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Sea Ice Gauge", layout="centered")

# ---------------------------------------------------------
# Data source (daily updated)
# ---------------------------------------------------------
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# ---------------------------------------------------------
# Files for logging
# ---------------------------------------------------------
ALPHA_HISTORY_FILE = "alpha_history.csv"

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
}

# ---------------------------------------------------------
# Regional groups (situational awareness buckets)
# You can adjust membership freely.
# ---------------------------------------------------------
REGION_GROUPS = {
    "Pacific Arctic": [
        "Sea of Okhotsk",
        "Bering Sea",
        "Chukchi Sea",
        "Beaufort Sea",
    ],
    "Atlantic Arctic": [
        "Barents Sea",
        "Greenland Sea",
        "Baffin Bay",
        "Kara Sea",
    ],
}

# ---------------------------------------------------------
# Default alpha correction (Dr. Kang visual alignment)
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
# Load AMSR2 image
# ---------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return np.array(img)

# ---------------------------------------------------------
# Pixel classifier (simple human-vision proxy)
# ---------------------------------------------------------
def classify_pixel(rgb):
    r, g, b = rgb

    # LAND: bright green
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"

    # WATER: blue-dominant tones (dark/light/cyan)
    if b > r and b > g:
        return "water"

    # ICE: everything else (pink/purple/yellow/red/white etc.)
    return "ice"

# ---------------------------------------------------------
# Raw ice percentage in ROI (satellite color proxy)
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
# Hybrid ice area (%) with alpha correction
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
# Fear & Greed style gauge labels (avoid navigability claims)
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
# Alpha history logging (append-only; idempotent per day)
# ---------------------------------------------------------
def save_alpha_history(correction, date_obj):
    date_str = str(date_obj)
    rows = [{"date": date_str, "region": r, "alpha": float(a)} for r, a in correction.items()]
    df_new = pd.DataFrame(rows)

    if os.path.exists(ALPHA_HISTORY_FILE):
        df_old = pd.read_csv(ALPHA_HISTORY_FILE)

        # Remove existing records for the same date (avoid duplicates)
        df_old = df_old[df_old["date"] != date_str]
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(ALPHA_HISTORY_FILE, index=False)

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Sea Ice Situational Awareness Gauge (v2.2)")
st.caption("Fear & Greed–style situational awareness gauge for sea-ice conditions")

with st.expander("⚠️ Mandatory disclaimer (read before use)", expanded=True):
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
yesterday = today - datetime.timedelta(days=1)

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

# Alpha correction selection
st.subheader("Hybrid calibration (regional correction α)")
use_custom_alpha = st.checkbox("Manually adjust correction factors (advanced users)", value=False)

if use_custom_alpha:
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

# Save alpha history for today (idempotent)
save_alpha_history(correction, today)

# Compute today values
arr = load_image()

rows = []
hybrid_values = []

for region, roi in REGIONS.items():
    raw, hybrid = compute_hybrid_ice(arr, region, roi, correction, step)
    if hybrid is None:
        rows.append({"Region": region, "Raw (%)": "N/A", "Hybrid Ice Area (%)": "N/A", "Gauge": "⚪ No data", "Note": ""})
        continue

    lvl, note = friction_level(hybrid, t1, t2, t3, t4)
    rows.append({
        "Region": region,
        "Raw (%)": raw,
        "Hybrid Ice Area (%)": hybrid,
        "Gauge": lvl,
        "Note": note,
        "Alpha (α)": round(float(correction.get(region, 1.0)), 2)
    })
    hybrid_values.append(hybrid)

df = pd.DataFrame(rows)

# Save today's table to local file (for delta comparison)
TODAY_FILE = f"polar_cuda_{today}.csv"
YESTERDAY_FILE = f"polar_cuda_{yesterday}.csv"
df.to_csv(TODAY_FILE, index=False)

# =========================================================
# OVERALL
# =========================================================
st.markdown("---")
st.subheader("Overall situational gauge (average across regions)")

if hybrid_values:
    overall = round(sum(hybrid_values) / len(hybrid_values), 1)
    overall_lvl, overall_note = friction_level(overall, t1, t2, t3, t4)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Overall (Hybrid %)", f"{overall}%")
    with col2:
        st.write(f"**Overall gauge:** {overall_lvl} — {overall_note}")

    st.progress(int(overall))
    st.caption("Progress bar is a visual proxy of Hybrid Ice Area (%).")
else:
    st.warning("No valid data returned today.")

# =========================================================
# GROUP AVERAGES
# =========================================================
st.markdown("---")
st.subheader("Regional group averages (Pacific / Atlantic)")

cols = st.columns(len(REGION_GROUPS))
for i, (group, members) in enumerate(REGION_GROUPS.items()):
    vals = df[df["Region"].isin(members)]["Hybrid Ice Area (%)"]
    vals = pd.to_numeric(vals, errors="coerce").dropna()
    if not vals.empty:
        avg = round(vals.mean(), 1)
        lvl, note = friction_level(avg, t1, t2, t3, t4)
        with cols[i]:
            st.metric(group, f"{avg}%")
            st.write(f"{lvl}")
            st.progress(int(avg))
    else:
        with cols[i]:
            st.metric(group, "N/A")
            st.write("⚪ No data")

# =========================================================
# REGIONAL OUTPUTS
# =========================================================
st.markdown("---")
st.subheader("Sea-region situational gauges")

for _, r in df.iterrows():
    if isinstance(r["Hybrid Ice Area (%)"], (int, float, np.floating)):
        val = float(r["Hybrid Ice Area (%)"])
        st.write(
            f"**{r['Region']}** → {r['Gauge']}  |  "
            f"Hybrid: {r['Hybrid Ice Area (%)']}% (raw {r['Raw (%)']}%)  |  "
            f"α={r.get('Alpha (α)', 'N/A')}  |  {r['Note']}"
        )
        st.progress(int(val))
    else:
        st.write(f"**{r['Region']}** → {r['Gauge']}")

# =========================================================
# YESTERDAY vs TODAY Δ
# =========================================================
st.markdown("---")
st.subheader("Yesterday vs Today Δ (Hybrid Ice Area %)")

if os.path.exists(YESTERDAY_FILE):
    df_y = pd.read_csv(YESTERDAY_FILE)
    df_t = df.copy()

    # numeric conversion
    df_t["Hybrid Ice Area (%)"] = pd.to_numeric(df_t["Hybrid Ice Area (%)"], errors="coerce")
    df_y["Hybrid Ice Area (%)"] = pd.to_numeric(df_y["Hybrid Ice Area (%)"], errors="coerce")

    delta = df_t.merge(df_y[["Region", "Hybrid Ice Area (%)"]], on="Region", suffixes=("_today", "_yesterday"))
    delta["Δ Hybrid (%)"] = (delta["Hybrid Ice Area (%)_today"] - delta["Hybrid Ice Area (%)_yesterday"]).round(1)

    # Simple delta label
    def delta_icon(x):
        if pd.isna(x):
            return "⚪"
        if x >= 5:
            return "🔺"
        if x <= -5:
            return "🔻"
        return "➖"

    delta["Δ"] = delta["Δ Hybrid (%)"].apply(delta_icon)

    st.dataframe(
        delta[["Region", "Δ", "Δ Hybrid (%)", "Hybrid Ice Area (%)_yesterday", "Hybrid Ice Area (%)_today"]],
        use_container_width=True
    )
else:
    st.info("Yesterday's local CSV not found yet. (Run once per day to build history.)")

# =========================================================
# ALPHA HISTORY + SEASONAL TREND
# =========================================================
st.markdown("---")
st.subheader("α history (saved) and seasonal trend (monthly)")

if os.path.exists(ALPHA_HISTORY_FILE):
    df_alpha = pd.read_csv(ALPHA_HISTORY_FILE)
    df_alpha["date"] = pd.to_datetime(df_alpha["date"])
    df_alpha["month"] = df_alpha["date"].dt.month

    st.caption("Latest α records (most recent first)")
    st.dataframe(
        df_alpha.sort_values("date", ascending=False).head(30),
        use_container_width=True
    )

    st.caption("Seasonal α trend (monthly mean)")
    seasonal = (
        df_alpha.groupby(["region", "month"])["alpha"]
        .mean()
        .reset_index()
        .sort_values(["region", "month"])
    )
    st.dataframe(seasonal, use_container_width=True)
else:
    st.info("No alpha history yet. It will be created after the first run.")

# =========================================================
# DOWNLOADS
# =========================================================
st.markdown("---")
st.subheader("Download today's table (CSV)")
csv_today = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Download polar_cuda_today.csv",
    data=csv_today,
    file_name=f"polar_cuda_{today}.csv",
    mime="text/csv"
)

st.caption(
    "Data source: University of Bremen AMSR2 daily PNG. "
    "POLAR CUDA provides situational awareness only (not operational advice)."
)
