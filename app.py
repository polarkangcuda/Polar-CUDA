import streamlit as st
import pandas as pd
import datetime
import numpy as np

# ==========================================
# Polar CUDA – Regional Navigation Risk
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
# Region list
# ------------------------------------------
REGIONS = [
    "Entire Arctic (Pan-Arctic)",
    "Sea of Okhotsk",
    "Bering Sea",
    "Chukchi Sea",
    "Beaufort Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Kara Sea",
    "Barents Sea",
    "Greenland Sea",
    "Baffin Bay",
    "Lincoln Sea",
]

region = st.selectbox("Select Region", REGIONS)

# ------------------------------------------
# Regional ice baseline (relative reference)
# ------------------------------------------
REGION_BASELINE = {
    "Entire Arctic (Pan-Arctic)": 14.8,  # million km²
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
}

# ------------------------------------------
# Load NSIDC v4 Sea Ice Index (robust)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)

    # 자동 날짜 컬럼 탐색
    date_col = None
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().sum() > len(df) * 0.9:
            df["_date"] = parsed
            date_col = col
            break

    # 자동 extent 컬럼 탐색
    extent_col = None
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
            df["_extent"] = numeric
            extent_col = col
            break

    if date_col is None or extent_col is None:
        return None

    df = df[["_date", "_extent"]].dropna()
    df = df.sort_values("_date").reset_index(drop=True)
    df.rename(columns={"_date": "date", "_extent": "extent"}, inplace=True)

    return df

df = load_nsidc_v4()

# ------------------------------------------
# Fail-safe
# ------------------------------------------
if df is None or df.empty:
    st.error("Unable to load NSIDC v4 sea ice data.")
    st.stop()

# ------------------------------------------
# Latest available observation (≤ today)
# ------------------------------------------
df_valid = df[df["date"].dt.date <= today]

if df_valid.empty:
    st.error("No valid NSIDC data available up to today.")
    st.stop()

latest = df_valid.iloc[-1]
extent_today = float(latest["extent"])  # Pan-Arctic extent
data_date = latest["date"].date()

# ------------------------------------------
# Header
# ------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Today: {today}")
st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Selected Region: {region}")

st.markdown("---")

# ------------------------------------------
# Regional normalization logic (FIXED)
# ------------------------------------------
pan_arctic_max = REGION_BASELINE["Entire Arctic (Pan-Arctic)"]
regional_baseline = REGION_BASELINE[region]

# Pan-Arctic extent → regional-equivalent intensity
regional_equivalent = extent_today * (regional_baseline / pan_arctic_max)

# Normalized regional risk (0–100)
risk_index = round(
    np.clip(
        (regional_equivalent / regional_baseline) * 100,
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
# Gauge-style display
# ------------------------------------------
st.subheader("Regional Navigation Risk")

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

Based on the latest **Pan-Arctic sea ice extent** adjusted for
the **typical ice regime of {region}**, the current navigation
risk level is assessed as **{status.lower()}**.

This reflects **relative seasonal severity**, not absolute ice thickness
or local pressure conditions.
"""
)

# ------------------------------------------
# Legal / Attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135),
Version 4**, distributed under the NOAA Open Data policy.

This application is for situational awareness only and does not replace
official ice services, onboard navigation systems, or the judgment of
vessel masters.
"""
)
