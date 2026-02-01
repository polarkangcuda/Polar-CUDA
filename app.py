import streamlit as st
import datetime
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from PIL import ImageDraw

# =========================================================
# POLAR CUDA – Level 3 (FINAL, PIXEL-LOCKED ROI MODEL)
# =========================================================

st.set_page_config(
    page_title="POLAR CUDA – Level 3",
    layout="wide"
)

# ---------------------------------------------------------
# Date
# ---------------------------------------------------------
today = datetime.date.today()

# ---------------------------------------------------------
# Bremen AMSR2 daily PNG
# ---------------------------------------------------------
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_bremen_png():
    r = requests.get(BREMEN_URL, timeout=15)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")

# ---------------------------------------------------------
# Pixel classification (simple & robust)
# ---------------------------------------------------------
def classify(rgb):
    r, g, b = rgb
    if g > 160 and g > r * 1.1 and g > b * 1.1:
        return "land"
    if b > 120 and b > r * 1.1 and b > g * 1.1:
        return "water"
    return "ice"

# ---------------------------------------------------------
# 🔒 FIXED PIXEL ROIs (HAND-DRAWN BOXES)
# Coordinates tuned to your provided image
# Format: (x1, y1, x2, y2)
# ---------------------------------------------------------
REGIONS = {
    "1. Sea of Okhotsk": (780, 90, 1040, 340),
    "2. Bering Sea": (520, 330, 780, 540),
    "3. Chukchi Sea": (700, 420, 930, 610),
    "4. East Siberian Sea": (880, 390, 1100, 600),
    "5. Laptev Sea": (1000, 390, 1230, 600),
    "6. Kara Sea": (1180, 430, 1400, 620),
    "7. Barents Sea": (1230, 600, 1480, 820),
    "8. Beaufort Sea": (640, 540, 900, 760),
    "9. Canadian Arctic Archipelago": (640, 700, 900, 950),
    "10. Central Arctic Ocean": (820, 520, 1120, 820),
    "11. Greenland Sea": (980, 820, 1180, 1100),
    "12. Baffin Bay": (760, 840, 960, 1120),
}

# ---------------------------------------------------------
# Region assessment
# ---------------------------------------------------------
def assess(img, roi):
    arr = np.array(img)
    x1, y1, x2, y2 = roi

    ice = water = ocean = 0

    for y in range(y1, y2, 3):
        for x in range(x1, x2, 3):
            c = classify(arr[y, x])
            if c == "land":
                continue
            ocean += 1
            if c == "ice":
                ice += 1
            else:
                water += 1

    if ocean == 0:
        return "⚫ No data"

    ice_ratio = ice / ocean

    if ice_ratio > 0.75:
        return "🔴 Navigation NOT possible"
    elif ice_ratio > 0.4:
        return "🟠 Very high risk"
    elif ice_ratio > 0.15:
        return "🟡 Conditional"
    else:
        return "🟢 Relatively open"

# =========================================================
# UI
# =========================================================

st.title("🧊 POLAR CUDA – Level 3")
st.caption("Sea-Region Navigation Feasibility (Expert-defined fixed regions)")
st.caption(f"Analysis date: {today}")

img = load_bremen_png()

# Draw ROI boxes
draw = ImageDraw.Draw(img)
for roi in REGIONS.values():
    draw.rectangle(roi, outline="yellow", width=3)

st.image(img, caption="AMSR2 Arctic Sea Ice (with fixed expert-defined regions)", use_container_width=True)

st.markdown("## Sea-Region Navigation Feasibility (Simple View)")

for name, roi in REGIONS.items():
    st.markdown(f"**{name} → {assess(img, roi)}**")

st.markdown("---")

st.caption("""
**Data Source**
University of Bremen – AMSR2 daily sea-ice concentration PNG  
https://data.seaice.uni-bremen.de/amsr2/

**Legal & Scientific Notice**
• Regions are expert-defined, non-authoritative operational sectors  
• Pixel-based interpretation of public imagery  
• For situational awareness only  
• NOT for navigation, legal, or operational decision-making
""")
