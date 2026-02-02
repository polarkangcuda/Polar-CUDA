import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd

# =========================================================
# POLAR CUDA (v2.4)
# =========================================================
CUDA_ACRONYM = "Cryospheric Uncertainty–Driven Awareness"
APP_TITLE = "POLAR CUDA – Arctic Ice Situational Awareness Gauge"
APP_SUBTITLE = (
    "Human-vision–aligned sea-ice sentiment gauge "
    "for decision awareness (not decision-making)."
)

DISCLAIMER_TEXT = """
### ⚠ Mandatory disclaimer (situational awareness only)

**POLAR CUDA** is a **situational awareness gauge**, not an operational tool.

- NOT navigation, routing, feasibility, or forecasting  
- NOT an official ice service or ice chart  
- NOT legal, safety, or operational advice  

This tool supports **human-in-the-loop awareness only**.  
All decisions and responsibility remain with the user.
"""

PHILOSOPHY_ONE_LINER = (
    "POLAR CUDA does not tell you what to do — "
    "it helps you recognize when not to decide yet."
)

st.set_page_config(page_title=APP_TITLE, layout="centered")

# =========================================================
# Session state (PWA hint – show once)
# =========================================================
if "pwa_hint_shown" not in st.session_state:
    st.session_state.pwa_hint_shown = False

# =========================================================
# Data source
# =========================================================
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
CACHE_TTL = 3600

# ---------------------------------------------------------
# AMSR2 image date (HTTP header)
# ---------------------------------------------------------
def get_amsr2_image_date():
    try:
        r = requests.head(AMSR2_URL, timeout=10)
        if "Last-Modified" in r.headers:
            return pd.to_datetime(r.headers["Last-Modified"]).date()
    except Exception:
        pass
    return None

# ---------------------------------------------------------
# Regions (ROIs)
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
# Region groups
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
# Alpha correction (human visual alignment)
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
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

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
# Ice computation
# ---------------------------------------------------------
def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape

    for y in range(max(0, y1), min(h, y2), step):
        for x in range(max(0, x1), min(w, x2), step):
            c = classify_pixel(arr[y, x])
            if c == "ice":
                ice += 1
            elif c == "water":
                water += 1

    if ice + water == 0:
        return None
    return (ice / (ice + water)) * 100

def clamp(v):
    return max(0, min(100, v))

def friction_level(v):
    if v <= 15: return "🟢 Extreme Open"
    if v <= 35: return "🟩 Open"
    if v <= 60: return "🟡 Neutral"
    if v <= 85: return "🟠 Constrained"
    return "🔴 Extreme Constrained"

# =========================================================
# UI – HEADER
# =========================================================
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)
st.info(f"**CUDA = {CUDA_ACRONYM}**")

with st.expander("⚠ Disclaimer & Scope", expanded=True):
    st.markdown(DISCLAIMER_TEXT)
    st.markdown(f"> *{PHILOSOPHY_ONE_LINER}*")

if not st.checkbox("I understand and wish to continue"):
    st.stop()

# =========================================================
# 📱 PWA INSTALL GUIDE (1회만 표시)
# =========================================================
if not st.session_state.pwa_hint_shown:
    st.markdown("---")
    st.subheader("📱 Install POLAR CUDA as an App")

    st.components.v1.html(
        """
<script>
const ua = navigator.userAgent || navigator.vendor || window.opera;
let msg = "";

if (/iPad|iPhone|iPod/.test(ua)) {
  msg = "<b>📱 iPhone / iPad</b><br>Safari → Share → Add to Home Screen";
} else if (/android/i.test(ua)) {
  msg = "<b>📱 Android</b><br>Browser menu → Install app / Add to Home Screen";
} else {
  msg = "<b>💻 Desktop</b><br>Bookmark or install as PWA if supported";
}

document.getElementById("pwa-msg").innerHTML = msg;
</script>

<div style="border:1px solid #ddd;padding:14px;border-radius:8px;background:#f9f9f9">
  <div id="pwa-msg"></div>
  <p style="margin-top:8px;color:#666">
  Once installed, POLAR CUDA runs in full-screen app mode.
  </p>
</div>
""",
        height=180,
    )

    if st.button("✅ Got it — don’t show again"):
        st.session_state.pwa_hint_shown = True
        st.rerun()

# =========================================================
# Dates
# =========================================================
today = datetime.date.today()
amsr2_date = get_amsr2_image_date()

st.markdown("---")
st.write(f"**Analysis date (app run):** {today}")
st.write(f"**Sea-ice image date (AMSR2):** {amsr2_date if amsr2_date else 'Unknown'}")

# =========================================================
# Analysis
# =========================================================
step = st.slider("Sampling step (speed vs detail)", 2, 12, 4)
arr = load_image()

rows = []
for region, roi in REGIONS.items():
    raw = compute_raw_ice(arr, roi, step)
    if raw is None:
        continue
    hybrid = clamp(raw * DEFAULT_CORRECTION.get(region, 1.0))
    rows.append({"Region": region, "Hybrid": round(hybrid, 1)})

df = pd.DataFrame(rows)

# =========================================================
# GROUP AVERAGES
# =========================================================
st.markdown("---")
st.subheader("Regional group averages")

cols = st.columns(2)
for i, (group, members) in enumerate(REGION_GROUPS.items()):
    vals = df[df["Region"].isin(members)]["Hybrid"]
    with cols[i]:
        avg = round(vals.mean(), 1)
        st.metric(group, f"{avg}%")
        st.write(friction_level(avg))
        st.progress(int(avg))

# =========================================================
# INDIVIDUAL REGIONS
# =========================================================
st.markdown("---")
st.subheader("Sea-region situational gauges")

for _, r in df.iterrows():
    lvl = friction_level(r["Hybrid"])
    st.write(f"**{r['Region']}** → {lvl} | {r['Hybrid']}%")
    st.progress(int(r["Hybrid"]))

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    f"CUDA = {CUDA_ACRONYM}. "
    f"Sea-ice image: University of Bremen AMSR2 daily PNG "
    f"(image date: {amsr2_date if amsr2_date else 'unknown'}). "
    "POLAR CUDA provides situational awareness only."
)
