import streamlit as st
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import datetime
import pandas as pd
import zipfile

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
# Session state
# =========================================================
if "pwa_hint_shown" not in st.session_state:
    st.session_state.pwa_hint_shown = False

# =========================================================
# Data source
# =========================================================
AMSR2_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

def get_amsr2_image_date():
    try:
        r = requests.head(AMSR2_URL, timeout=10)
        if "Last-Modified" in r.headers:
            return pd.to_datetime(r.headers["Last-Modified"]).date()
    except Exception:
        pass
    return None

# =========================================================
# Regions
# =========================================================
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

REGION_GROUPS = {
    "Pacific Arctic": ["Bering Sea", "Chukchi Sea", "Beaufort Sea", "East Siberian Sea"],
    "Atlantic Arctic": ["Kara Sea", "Barents Sea", "Greenland Sea", "Baffin Bay"],
}

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

@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(AMSR2_URL, timeout=20)
    r.raise_for_status()
    return np.array(Image.open(BytesIO(r.content)).convert("RGB"))

def classify_pixel(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.15 and g > b * 1.15:
        return "land"
    if b > r and b > g:
        return "water"
    return "ice"

def compute_raw_ice(arr, roi, step=4):
    x1, y1, x2, y2 = roi
    ice = water = 0
    h, w, _ = arr.shape
    for y in range(y1, y2, step):
        for x in range(x1, x2, step):
            c = classify_pixel(arr[y, x])
            if c == "ice": ice += 1
            elif c == "water": water += 1
    if ice + water == 0:
        return None
    return ice / (ice + water) * 100

def clamp(v): return max(0, min(100, v))

def friction(v):
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

with st.expander("⚠ Disclaimer", expanded=True):
    st.markdown(DISCLAIMER_TEXT)
    st.markdown(f"> *{PHILOSOPHY_ONE_LINER}*")

if not st.checkbox("I understand and wish to continue"):
    st.stop()

# =========================================================
# 🎨 APP ICON GENERATOR
# =========================================================
st.markdown("---")
st.subheader("🎨 App Icon Generator (PNG 192 / 512)")

uploaded_icon = st.file_uploader(
    "Upload base icon (square PNG recommended, e.g. 1024×1024)",
    type=["png"]
)

if uploaded_icon:
    base_img = Image.open(uploaded_icon).convert("RGBA")
    st.image(base_img, caption="Original Icon", width=180)

    if st.button("🚀 Generate App Icons"):
        icon_192 = base_img.resize((192, 192), Image.LANCZOS)
        icon_512 = base_img.resize((512, 512), Image.LANCZOS)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            b1, b2 = BytesIO(), BytesIO()
            icon_192.save(b1, "PNG")
            icon_512.save(b2, "PNG")
            z.writestr("icon-192.png", b1.getvalue())
            z.writestr("icon-512.png", b2.getvalue())

        zip_buffer.seek(0)
        st.success("✅ App icons generated!")
        st.download_button(
            "⬇ Download App Icons (ZIP)",
            data=zip_buffer,
            file_name="polar-cuda-app-icons.zip",
            mime="application/zip"
        )

# =========================================================
# ANALYSIS
# =========================================================
st.markdown("---")
today = datetime.date.today()
amsr2_date = get_amsr2_image_date()
st.write(f"**Analysis date:** {today}")
st.write(f"**Sea-ice image date:** {amsr2_date}")

step = st.slider("Sampling step", 2, 12, 4)
arr = load_image()

rows = []
for r, roi in REGIONS.items():
    raw = compute_raw_ice(arr, roi, step)
    if raw is not None:
        hybrid = clamp(raw * DEFAULT_CORRECTION.get(r, 1.0))
        rows.append({"Region": r, "Hybrid": round(hybrid, 1)})

df = pd.DataFrame(rows)

st.markdown("---")
st.subheader("Sea-region situational gauges")
for _, r in df.iterrows():
    st.write(f"**{r['Region']}** → {friction(r['Hybrid'])} | {r['Hybrid']}%")
    st.progress(int(r["Hybrid"]))

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    f"CUDA = {CUDA_ACRONYM}. "
    f"Sea-ice image: University of Bremen AMSR2 daily PNG "
    f"(image date: {amsr2_date}). "
    "POLAR CUDA provides situational awareness only."
)
