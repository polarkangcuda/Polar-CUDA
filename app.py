import streamlit as st
import datetime
import pandas as pd

# =====================================================
# Polar CUDA – Status Gauge (NSIDC v4 BULLETPROOF)
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
# Region Weights
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
# Load NSIDC v4 Data (FINAL SAFE VERSION)
# -----------------------------------------------------
NSIDC_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

df = pd.read_csv(NSIDC_URL)

# 1️⃣ 컬럼명 정규화
df.columns = [c.strip().lower() for c in df.columns]

# 2️⃣ 날짜 처리 (두 가지 경우 모두 대응)
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

# 3️⃣ Extent 확인
if "extent" not in df.columns:
    st.error("Extent column not found in NSIDC dataset.")
    st.stop()

df = df[["date", "extent"]].dropna()
df = df.sort_values("date")

# -----------------------------------------------------
# Latest Sea Ice Extent
# -----------------------------------------------------
extent_today = df.iloc[-1]["extent"]

# -----------------------------------------------------
# Risk Index (Conservative Navigation Logic)
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

# -----------------------------------------------------
# Legal / Attribution
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Attribution & Legal Notice**

Sea ice extent data are provided by **NOAA/NSIDC Sea Ice Index Version 4 (G02135)**,
an official **NOAA Open Data** product.

NOAA open data may be freely used, adapted, and redistributed with attribution.
This dashboard provides situational awareness only and does not constitute
navigational or safety guidance.
"""
)
