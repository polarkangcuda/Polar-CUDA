import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# POLAR CUDA
# Cryospheric Uncertainty & Decision Awareness
# Visual Ice Awareness Index
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Visual Ice Awareness",
    layout="wide"
)

IMAGE_URL = (
    "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_visual.png"
)

# ---------------------------------------------------------
# Expert-defined ROIs (from red boxes, pixel coordinates)
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
# Load image
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_image():
    r = requests.get(IMAGE_URL, timeout=20)
    r.raise_for_status()
    return Image.open(BytesIO(r.content))

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Visual Ice Awareness")
st.caption(
    "Cryospheric Uncertainty & Decision Awareness\n\n"
    "This view is designed for **situational awareness only**, "
    "not decision-making."
)

st.write(f"**Analysis date:** {datetime.date.today()}")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

img = load_image()

st.markdown("---")
st.subheader("Arctic Sea Regions – Visual State (Human-Eye View)")

# Display regions in grid
cols = st.columns(3)

i = 0
for name, (x1, y1, x2, y2) in REGIONS.items():
    roi = img.crop((x1, y1, x2, y2))
    with cols[i % 3]:
        st.markdown(f"**{name}**")
        st.image(roi, use_column_width=True)
    i += 1

st.markdown("---")
st.caption(
    """
**Data source**: University of Bremen AMSR2 visual ice map.

POLAR CUDA intentionally **does not compute navigability or ice concentration**.
It mirrors what a human expert sees on the map, region by region,
to support independent judgment.

⚠ This tool does **not** replace official ice services,
operational planning systems, or navigational decisions.
"""
)
