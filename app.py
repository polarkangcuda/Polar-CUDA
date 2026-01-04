import streamlit as st
import pandas as pd
import datetime
import numpy as np

# ==========================================
# Polar CUDA – NSIDC Regional Ice Risk
# ==========================================

st.set_page_config(
    page_title="Polar CUDA – Regional Ice Risk",
    layout="centered"
)

today = datetime.date.today()

# ------------------------------------------
# Supported NSIDC regions (v3)
# ------------------------------------------
REGION_COLUMN_MAP = {
    "Sea of Okhotsk": "Sea_of_Okhotsk",
    "Bering Sea": "Bering",
    "Chukchi Sea": "Chukchi",
    "Beaufort Sea": "Beaufort",
    "East Siberian Sea": "East_Siberian",
    "Laptev Sea": "Laptev",
    "Kara Sea": "Kara",
    "Barents Sea": "Barents",
    "Greenland Sea": "Greenland",
    "Baffin Bay": "Baffin",
    "Lincoln Sea": "Lincoln",
    "Entire Arctic (Pan-Arctic)": "Total",
}

region = st.selectbox("Select Region", list(REGION_COLUMN_MAP.keys()))
region_col = REGION_COLUMN_MAP[region]

# ------------------------------------------
# Load NSIDC Sea Ice Index v3 (Regional)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_regional_v3():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v3.0.csv"
    )

    df = pd.read_csv(url)

    # 컬럼 정리
    df.columns = [c.strip() for c in df.columns]

    # 날짜 처리
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

df = load_nsidc_regional_v3()

# ------------------------------------------
# Fail-safe
# ------------------------------------------
if region_col not in df.columns:
    st.error(f"Region '{region}' not found in NSIDC dataset.")
    st.stop()

# ------------------------------------------
# Latest valid observation (≤ today)
# ------------------------------------------
df_valid = df[df["date"].dt.date <= today]

if df_valid.empty:
    st.error("No valid NSIDC regional data available.")
    st.stop()

latest = df_valid.iloc[-1]

extent = float(latest[region_col])  # million km²
data_date = latest["date"].date()

# ------------------------------------------
# Regional baseline (for normalization)
# ------------------------------------------
REGION_BASELINE = {
    "Sea of Okhotsk": 1.5,
    "Bering Sea": 1.2,
    "Chukchi Sea": 2.5,
    "Beaufort Sea": 3.0,
    "East Siberian Sea": 3.5,
    "Laptev Sea": 4.0,
    "Kara Sea": 2.8,
    "Barents Sea": 1.8,
    "Greenland Sea": 2.2,
    "Baffin Bay": 2.6,
    "Lincoln Sea": 4.5,
    "Entire Arctic (Pan-Arctic)": 14.8,
}

baseline = REGION_BASELINE[region]

# ------------------------------------------
# Risk calculation (regional, corrected)
# ------------------------------------------
risk_index = round(
    np.clip((extent / baseline) * 100, 0, 100),
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
# Display
# ------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Region: {region}")
st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Sea Ice Extent: {extent:.2f} million km²")

st.markdown("---")

st.subheader("Regional Ice Navigation Risk")

st.markdown(
    f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

st.progress(int(risk_index))

# ------------------------------------------
# Interpretation
# ------------------------------------------
st.markdown(
    f"""
**Interpretation**

This assessment is based on **actual NSIDC regional sea ice extent**
for **{region}**, normalized against its typical seasonal maximum.

The index reflects **relative navigational constraint**, not ice thickness
or pressure ridging.
"""
)

# ------------------------------------------
# Legal / Attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source**

Regional sea ice extent data are provided by  
**NOAA / NSIDC Sea Ice Index (G02135), Version 3**  
under the NOAA Open Data policy.

This tool is for situational awareness only and does not replace
official ice services or vessel master judgment.
"""
)
