import streamlit as st
import datetime
import pandas as pd

# =====================================================
# Polar CUDA – Status Gauge (NSIDC v4 FINAL SAFE)
# =====================================================

st.set_page_config(
    page_title="Polar CUDA – Status",
    layout="centered"
)

# -----------------------------------------------------
# Date
# -----------------------------------------------------
today = datetime.date.today()

# -----------------------------------------------------
# Region Weights (Operations Logic)
# -----------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 1.00,
    "Chukchi Sea": 1.10,
    "East Siberian Sea": 1.15,
    "Beaufort Sea": 1.05,
    "Barents Sea": 0.90,
}

selected_region = st.selectbox(
    "Select Region",
    list(REGIONS.keys())
)

region_weight = REGIONS[selected_region]

# -----------------------------------------------------
# Load NSIDC v4 Data (BULLETPROOF)
# -----------------------------------------------------
NSIDC_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

df = pd.read_csv(NSIDC_URL)

# 1️⃣ 컬럼명 정규화 (공백 제거 + 소문자)
df.columns = [c.strip().lower() for c in df.columns]

# 2️⃣ 날짜 컬럼 처리 (date or year/month/day)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

elif {"year", "month", "day"}.issubset(df.columns):
    df["date"] = pd.to_datetime(
        df[["year", "month", "day"]],
        errors="coerce"
    )

else:
    st.error("NSIDC dataset date format not recognized.")
    st.stop()

# 3️⃣ extent 컬럼 확인
if "extent" not in df.columns:
    st.error("Extent column not found in NSIDC dataset.")
    st.stop()

# 4️⃣ 숫자 강제 변환 (⭐ TypeError 방지 핵심 ⭐)
df["extent"] = pd.to_numeric(df["extent"], errors="coerce")

# 5️⃣ 필수 데이터만 남기기
df = df[["date", "extent"]].dropna()
df = df.sort_values("date")

if df.empty:
    st.error("No valid NSIDC data available.")
    st.stop()

# -----------------------------------------------------
# Latest Sea Ice Extent
# -----------------------------------------------------
extent_today = float(df.iloc[-1]["extent"])

# -----------------------------------------------------
# Risk Index (Explainable & Conservative)
# -----------------------------------------------------
risk_index = round(
    min(
        max((12.0 - extent_today) / 12.0 * 100.0 * region_weight, 0.0),
        100.0
    ),
    1
)

# -----------------------------------------------------
# Status Classification
# -----------------------------------------------------
if risk_index < 30:
    status = "LOW"
    color = "🟢"
    gauge = "🟢🟢🟢🟢⚪"
elif risk_index < 50:
    status = "MODERATE"
    color = "🟡"
    gauge = "🟢🟢🟢⚪⚪"
elif risk_index < 70:
    status = "HIGH"
    color = "🟠"
    gauge = "🟢🟢⚪⚪⚪"
else:
    status = "EXTREME"
    color = "🔴"
    gauge = "🟢⚪⚪⚪⚪"

# -----------------------------------------------------
# UI
# -----------------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Date: {today}")
st.caption(f"Region: {selected_region}")
st.caption(f"NSIDC Sea Ice Extent (latest): {extent_today:.2f} million km²")

st.markdown("---")

st.markdown("## Polar Navigation Risk Gauge")

st.markdown(
    f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100  

{gauge}
"""
)

st.progress(int(risk_index))

st.markdown(
    """
**Operational Interpretation**

This indicator provides high-level situational awareness for polar navigation.
It supports planning and scheduling decisions and does not replace onboard
navigation systems or the judgment of vessel masters.
"""
)

# -----------------------------------------------------
# Legal / Data Attribution
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Attribution & Legal Notice**

Sea ice extent data are provided by **NOAA/NSIDC Sea Ice Index Version 4 (G02135)**,
an official **NOAA Open Data** product.

NOAA open data may be freely used, adapted, and redistributed with attribution.
This dashboard provides situational awareness only and does **not** constitute
navigational, safety, or legal guidance.
"""
)
