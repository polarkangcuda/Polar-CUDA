import streamlit as st
import numpy as np
from PIL import Image
import datetime
import requests
from io import BytesIO

# =========================================================
# POLAR CUDA – Level 3 (Sea-based, Bremen AMSR2 PNG auto-update)
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Level 3 (Sea-based)", layout="centered")
today = datetime.date.today()

BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

# ---------------------------------------------------------
# Fetch latest Bremen PNG (auto-updating)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)  # 30분마다 자동 갱신 (원하시면 3600=1시간)
def fetch_bremen_png(url: str) -> Image.Image:
    headers = {
        "User-Agent": "POLAR-CUDA/1.0 (Streamlit; +https://streamlit.io)",
        "Accept": "image/png,image/*;q=0.9,*/*;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return img

# ---------------------------------------------------------
# Pixel classification
#   - land: bright green (map background land)
#   - open_water: dark blue (no ice)
#   - ice: everything else (including green/yellow/orange/red/purple of colorbar)
# ---------------------------------------------------------
def classify_pixel(r, g, b):
    # 육상(지도 배경의 선명한 초록) 제거
    if g > 200 and r < 120 and b < 120:
        return "land"
    # 해빙 없음(짙은 파랑) = open water
    if b > 120 and r < 70 and g < 90:
        return "open_water"
    return "ice"

# ---------------------------------------------------------
# Ice concentration proxy (RGB → %)
#  - NOTE: PNG 색상 팔레트 기반 '실험적' 근사치
#  - “해빙 농도 스케일의 초록색(25–50%)”을 육상 초록과 구분하도록
#    육상은 위 classify_pixel에서 제거되며,
#    여기서는 스케일 초록(연녹/청록 계열)은 농도값으로 매핑됩니다.
# ---------------------------------------------------------
def ice_concentration_from_rgb(r, g, b):
    # open water는 0 (대개 파랑 계열)
    if b > r and b > g:
        return 0.0

    # 스케일 초록/청록(대략 25–50%) 추정
    # (육상 초록은 이미 land로 제거되므로 여기의 green은 해빙농도 색으로 간주)
    if g > r and g > b:
        return 35.0

    # 노랑(대략 50–75%)
    if r > 200 and g > 200:
        return 60.0

    # 빨강(대략 75–90%)
    if r > 200 and g < 150:
        return 85.0

    # 보라(90–100%) 등
    return 100.0

# ---------------------------------------------------------
# ROI = (x_min, y_min, x_max, y_max) in PNG pixel coords
# (당신이 이미 확정한 12개 ROI를 그대로 넣으시면 됩니다)
# ---------------------------------------------------------
SEA_REGIONS = {
    "1. Sea of Okhotsk": (260, 140, 420, 300),
    "2. Bering Sea": (180, 260, 340, 420),
    "3. Chukchi Sea": (300, 300, 460, 460),
    "4. East Siberian Sea": (360, 300, 520, 460),
    "5. Laptev Sea": (420, 260, 600, 420),
    "6. Kara Sea": (520, 260, 680, 380),
    "7. Barents Sea": (620, 320, 820, 480),
    "8. Beaufort Sea": (260, 380, 420, 560),
    "9. Canadian Arctic Archipelago": (240, 480, 420, 660),
    "10. Central Arctic Ocean": (360, 360, 540, 540),
    "11. Greenland Sea": (560, 420, 720, 660),
    "12. Baffin Bay": (420, 520, 600, 760),
}

def compute_region_proxy(img: Image.Image, roi):
    arr = np.array(img)
    x0, y0, x1, y1 = roi
    sub = arr[y0:y1, x0:x1]

    ice_vals = []
    valid_sea_px = 0
    heavy_cnt = 0

    for row in sub:
        for r, g, b in row:
            cls = classify_pixel(r, g, b)
            if cls == "land":
                continue
            valid_sea_px += 1
            if cls == "ice":
                c = ice_concentration_from_rgb(r, g, b)
                if c >= 15:
                    ice_vals.append(c)
                if c >= 70:
                    heavy_cnt += 1

    # 바다 픽셀 자체가 너무 적으면 ROI가 육상에 치우친 것
    if valid_sea_px < 300:
        return None

    # coverage: 바다 픽셀 중 15% 이상인 비율
    coverage_ratio = (len(ice_vals) / valid_sea_px) * 100.0 if valid_sea_px else 0.0
    mean_conc = float(np.mean(ice_vals)) if ice_vals else 0.0
    heavy_ratio = (heavy_cnt / valid_sea_px) * 100.0 if valid_sea_px else 0.0

    confidence = int(min(100, (valid_sea_px / ((x1-x0)*(y1-y0))) * 100))

    return {
        "mean_concentration": round(mean_conc, 1),
        "coverage_ge_15": round(coverage_ratio, 1),
        "heavy_ge_70": round(heavy_ratio, 1),
        "confidence": confidence,
        "valid_sea_px": valid_sea_px,
    }

def compute_risk_index(mean_c, cov, heavy):
    # 운영용 간단 가중합(원하면 조정 가능)
    return round(0.4 * mean_c + 0.4 * cov + 0.2 * heavy, 1)

def classify_status(risk):
    if risk < 30: return "LOW", "🟢"
    if risk < 50: return "MODERATE", "🟡"
    if risk < 70: return "HIGH", "🟠"
    return "EXTREME", "🔴"

# =========================================================
# UI
# =========================================================
st.title("🧊 POLAR CUDA – Level 3 (Sea-based)")
st.caption("Auto-updating from Bremen AMSR2 daily PNG")
st.caption(f"Today (local): {today}")

region = st.selectbox("Select Sea Region", list(SEA_REGIONS.keys()), index=2)

st.markdown("---")

# Fetch latest image
try:
    img = fetch_bremen_png(BREMEN_URL)
except Exception as e:
    st.error("Could not fetch the latest Bremen AMSR2 PNG. Check network/URL.")
    st.caption(f"Error: {e}")
    st.stop()

# Compute region
result = compute_region_proxy(img, SEA_REGIONS[region])
if result is None:
    st.error("Insufficient valid sea pixels for this region. ROI likely overlaps land too much.")
    st.stop()

risk = compute_risk_index(result["mean_concentration"], result["coverage_ge_15"], result["heavy_ge_70"])
status, color = classify_status(risk)

st.subheader("Regional Navigation Risk (Status-Based)")
st.markdown(f"### {color} **{status}**")
st.markdown(f"**Risk Index:** {risk} / 100")
st.progress(int(max(0, min(100, risk))))

st.markdown("**Drivers (proxy):**")
st.markdown(f"- Mean concentration (ice≥15% only): **{result['mean_concentration']}%**")
st.markdown(f"- Coverage ≥15% (within ROI sea pixels): **{result['coverage_ge_15']}%**")
st.markdown(f"- Heavy ice ≥70% (within ROI sea pixels): **{result['heavy_ge_70']}%**")
st.markdown(f"- Data confidence: **{result['confidence']}%**")
st.caption(f"Valid sea pixels used: {result['valid_sea_px']}")

st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): Derived from the publicly accessible daily Bremen AMSR2
sea-ice concentration map PNG by image-based palette quantization (situational awareness only).
This is **not** an authoritative gridded concentration product and must not replace official ice services
or navigational judgment.
"""
)

# Optional: show image preview (mobile에서는 기본 off 권장)
with st.expander("Preview source image (optional)"):
    st.image(img, caption="Bremen AMSR2 PNG (latest)", use_container_width=True)
