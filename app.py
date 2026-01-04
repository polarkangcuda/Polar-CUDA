import streamlit as st
import pandas as pd
import datetime
import numpy as np

# ==========================================
# Polar CUDA – Navigation Risk (ULTRA STABLE)
# ==========================================

st.set_page_config(
    page_title="Polar CUDA – Navigation Risk",
    layout="centered"
)

# ------------------------------------------
# Date
# ------------------------------------------
today = datetime.date.today()

# ------------------------------------------
# Region weights (navigation sensitivity)
# ------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 1.00,
    "Beaufort Sea": 1.10,
    "Chukchi Sea": 1.15,
    "East Siberian Sea": 1.20,
    "Barents Sea": 0.90,
}

region = st.selectbox("Select Region", list(REGIONS.keys()))
region_weight = REGIONS[region]

# ------------------------------------------
# Load NSIDC v4 Sea Ice Index (FAIL-SAFE)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)

    # 원본 컬럼 백업
    raw_columns = list(df.columns)

    # 1️⃣ 날짜 컬럼 자동 탐색
    date_col = None
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().sum() > len(df) * 0.9:
            date_col = col
            df["__date"] = parsed
            break

    # 2️⃣ 해빙 면적 컬럼 자동 탐색
    extent_col = None
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        # 수백~수천 단위면 일단 제외
        if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
            extent_col = col
            df["__extent"] = numeric
            break

    if date_col is None or extent_col is None:
        return None, raw_columns

    df = df[["__date", "__extent"]].dropna()
    df = df.sort_values("__date").reset_index(drop=True)

    df.rename(
        columns={"__date": "date", "__extent": "extent"},
        inplace=True
    )

    return df, raw_columns

df, raw_columns = load_nsidc_v4()

# ------------------------------------------
# Header
# ------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Today: {today}")
st.caption(f"Region: {region}")

# ------------------------------------------
# If data load failed → graceful message
# ------------------------------------------
if df is None or df.empty:
    st.error("⚠ Unable to parse NSIDC v4 dataset.")
    st.caption("Detected columns:")
    st.code(raw_columns)
    st.stop()

# ------------------------------------------
# Latest available data
# ------------------------------------------
latest = df.iloc[-1]
extent_today = float(latest["extent"])
data_date = latest["date"].date()

st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Sea Ice Extent: {extent_today:.2f} million km²")

st.markdown("---")

# ------------------------------------------
# Navigation Risk Logic (WINTER-CORRECT)
# ------------------------------------------
# Winter maximum reference
MAX_ICE_EXTENT = 14.8  # million km² (Arctic max)

risk_index = round(
    np.clip(
        (extent_today / MAX_ICE_EXTENT) * 100.0 * region_weight,
        0,
        100
    ),
    1
)

# ------------------------------------------
# Status classification
# ------------------------------------------
if risk_index < 30:
    status = "LOW"
    color = "🟢"
elif risk_index < 50:
    status = "MODERATE"
    color = "🟡"
elif risk_index < 70:
    status = "HIGH"
    color = "🟠"
else:
    status = "EXTREME"
    color = "🔴"

# ------------------------------------------
# Gauge-style display (no external libs)
# ------------------------------------------
st.subheader("Polar Navigation Risk Gauge")

st.markdown(
    f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

filled = int(risk_index // 10)
dial = (
    "🟢" * min(filled, 3)
    + "🟡" * max(min(filled - 3, 2), 0)
    + "🟠" * max(min(filled - 5, 2), 0)
    + "🔴" * max(filled - 7, 0)
)

st.markdown(f"**Risk Dial:** {dial}")
st.progress(int(risk_index))

# ------------------------------------------
# Interpretation
# ------------------------------------------
st.markdown(
    f"""
**Operational Interpretation**

Current sea ice conditions indicate **{status.lower()} navigation risk**
for **{region}**.

Winter-season ice extent strongly constrains route flexibility,
escort requirements, and emergency maneuver margins.
"""
)

# ------------------------------------------
# Legal / Data Attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice extent data are sourced from **NOAA / NSIDC Sea Ice Index (G02135),
Version 4**, provided under the NOAA Open Data policy.

This application is for situational awareness only and does not replace
official ice services, onboard navigation systems, or the judgment of vessel masters.
"""
)
