import streamlit as st
import datetime
import pandas as pd

# =====================================================
# Polar CUDA – Fleet Operations (SAFE + NSIDC v4)
# =====================================================

st.set_page_config(
    page_title="Polar CUDA – Fleet Operations",
    layout="centered"
)

# -----------------------------------------------------
# Date
# -----------------------------------------------------
today = datetime.date.today()

# -----------------------------------------------------
# Region Selection (운항 관리자 가중치)
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
# NSIDC v4 Sea Ice Extent (안전 연결)
# -----------------------------------------------------
NSIDC_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

df = pd.read_csv(NSIDC_URL)

# 컬럼명 정리 (가장 중요)
df.columns = [c.strip().lower() for c in df.columns]

# date 컬럼 통일
df = df.rename(columns={"date": "date", "extent": "extent"})

# 날짜 파싱
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# 필수 컬럼만 사용
df = df[["date", "extent"]].dropna()

# 최신 데이터
extent_today = df.sort_values("date").iloc[-1]["extent"]

# -----------------------------------------------------
# Risk Index (설명 가능한 단순 모델)
# -----------------------------------------------------
risk_index = round(
    min(max((12 - extent_today) / 12 * 100 * region_weight, 0), 100),
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
It supports planning and scheduling decisions and does not replace onboard systems.
"""
)

# -----------------------------------------------------
# Legal / Data Attribution
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Attribution & Legal Notice**

Sea ice extent data are sourced from **NOAA/NSIDC Sea Ice Index Version 4 (G02135)**,
an official **NOAA Open Data** product.

NOAA open data may be freely used, adapted, and redistributed with attribution.
This dashboard does **not** constitute navigational or safety guidance.
Final operational decisions remain with vessel operators and masters.
"""
)
