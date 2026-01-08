import streamlit as st
import numpy as np
import urllib.request
from io import BytesIO
from PIL import Image
import datetime as dt

st.set_page_config(page_title="POLAR CUDA – Sea-based Level 3", layout="centered")

TODAY = dt.date.today()

# =====================================================
# 1. Sea-based operational regions (PIXEL ROI)
#    Values tuned to the provided reference image
# =====================================================
SEA_REGIONS = {
    "1. Sea of Okhotsk": (180, 60, 300, 180),
    "2. Bering Sea": (60, 160, 200, 280),
    "3. Chukchi Sea": (160, 200, 260, 320),
    "4. East Siberian Sea": (260, 200, 360, 320),
    "5. Laptev Sea": (360, 200, 460, 320),
    "6. Kara Sea": (460, 220, 560, 320),
    "7. Barents Sea": (520, 260, 640, 360),
    "8. Beaufort Sea": (120, 260, 260, 380),
    "9. Canadian Arctic Archipelago": (160, 320, 300, 460),
    "10. Central Arctic Ocean": (260, 260, 420, 420),
    "11. Greenland Sea": (420, 320, 540, 460),
    "12. Baffin Bay": (300, 360, 420, 500),
}

# =====================================================
# 2. Bremen AMSR2 PNG loader
# =====================================================
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=900)
def load_bremen_png():
    req = urllib.request.Request(
        BREMEN_URL,
        headers={"User-Agent": "POLAR-CUDA"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        img = Image.open(BytesIO(r.read())).convert("RGB")
    return np.array(img)

# =====================================================
# 3. Concentration proxy from ROI
# =====================================================
def compute_proxy(img, roi):
    x1, y1, x2, y2 = roi
    roi_img = img[y1:y2, x1:x2].astype(np.float32)

    r, g, b = roi_img[:,:,0], roi_img[:,:,1], roi_img[:,:,2]

    ocean = (b > 120) & (r < 90)
    land  = (g > 120) & (b < 140)
    valid = ~(ocean | land)

    if valid.sum() < 400:
        return None

    warmth = 0.55*r + 0.35*g - 0.25*b
    w = warmth[valid]

    lo, hi = np.percentile(w, [5, 95])
    conc = np.clip((warmth - lo) / (hi - lo) * 100, 0, 100)

    mean_c = float(np.mean(conc[valid]))
    cov15  = float((conc[valid] >= 15).mean() * 100)
    heavy  = float((conc[valid] >= 70).mean() * 100)

    risk = np.clip(
        0.45*mean_c + 0.35*cov15 + 0.20*heavy,
        0, 100
    )

    return mean_c, cov15, heavy, risk

# =====================================================
# 4. UI
# =====================================================
st.title("🧊 POLAR CUDA – Level 3 (Sea-based)")
st.caption(f"Today (local): {TODAY}")

sea = st.selectbox("Select Sea Region", list(SEA_REGIONS.keys()))

img = load_bremen_png()
result = compute_proxy(img, SEA_REGIONS[sea])

st.markdown("---")

if result is None:
    st.error("Insufficient valid ice pixels for this region.")
else:
    mean_c, cov15, heavy, risk = result

    status = (
        "LOW" if risk < 30 else
        "MODERATE" if risk < 50 else
        "HIGH" if risk < 70 else
        "EXTREME"
    )

    st.subheader(sea)
    st.markdown(f"### {status}")
    st.progress(int(risk))
    st.markdown(f"**Risk Index:** {risk:.1f} / 100")

    st.markdown("**Drivers (proxy)**")
    st.write(f"- Mean concentration: {mean_c:.1f}%")
    st.write(f"- Coverage ≥15%: {cov15:.1f}%")
    st.write(f"- Heavy ice ≥70%: {heavy:.1f}%")

st.markdown("---")
st.caption(
    "Level 3 (Experimental): Sea-based operational proxy derived from Bremen AMSR2 PNG. "
    "For situational awareness only. Not an authoritative ice service product."
)
