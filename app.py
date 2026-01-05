import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Level 3
# Cryospheric Unified Decision Assistant
# (MASIE Regional Ice Concentration)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Regional Ice Risk (MASIE)",
    layout="centered"
)

today = datetime.date.today()

# -----------------------------------------------------
# Regions (MASIE official names)
# -----------------------------------------------------
REGIONS = [
    "Central Arctic",
    "Beaufort Sea",
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Kara Sea",
    "Barents Sea",
    "Greenland Sea",
    "Baffin Bay",
    "Lincoln Sea",
    "Bering Sea",
]

region = st.sidebar.selectbox("Select Region", REGIONS)

# -----------------------------------------------------
# Load MASIE Regional CSV (SAFE)
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_masie_regional():
    """
    MASIE regional ice concentration (%)
    Source: NSIDC MASIE (Multi-sensor Analyzed Sea Ice Extent)
    """
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02186/masie_4km/"
        "regional/masie_regional.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # Standardize
    if "region" not in df.columns:
        return None, "Region column not found"

    # Detect date column
    date_col = None
    for c in df.columns:
        parsed = pd.to_datetime(df[c], errors="coerce")
        if parsed.notna().sum() > len(df) * 0.9:
            date_col = c
            df["date"] = parsed
            break

    if date_col is None:
        return None, "Date column not detected"

    # Detect concentration column
    conc_col = None
    for c in df.columns:
        numeric = pd.to_numeric(df[c], errors="coerce")
        if numeric.notna().sum() > len(df) * 0.9 and numeric.max() <= 100:
            conc_col = c
            df["concentration"] = numeric
            break

    if conc_col is None:
        return None, "Concentration column not detected"

    df = df[["date", "region", "concentration"]].dropna()
    df = df.sort_values("date").reset_index(drop=True)

    return df, None


df, err = load_masie_regional()
if df is None:
    st.error("Unable to load MASIE regional data.")
    if err:
        st.caption(err)
    st.stop()

# -----------------------------------------------------
# Latest available date
# -----------------------------------------------------
df_valid = df[df["date"].dt.date <= today]
if df_valid.empty:
    st.error("No valid MASIE data available.")
    st.stop()

latest_date = df_valid["date"].max()
df_latest = df_valid[df_valid["date"] == latest_date]

# Region value
row = df_latest[df_latest["region"].str.lower() == region.lower()]
if row.empty:
    st.error(f"No MASIE data for region: {region}")
    st.stop()

ice_conc = float(row.iloc[0]["concentration"])

# -----------------------------------------------------
# Risk Index (direct concentration-based)
# -----------------------------------------------------
risk_index = round(ice_conc, 1)

# -----------------------------------------------------
# Status classification (navigation-oriented)
# -----------------------------------------------------
if risk_index < 15:
    status, color = "LOW", "🟢"
elif risk_index < 40:
    status, color = "MODERATE", "🟡"
elif risk_index < 70:
    status, color = "HIGH", "🟠"
else:
    status, color = "EXTREME", "🔴"

# -----------------------------------------------------
# Display
# -----------------------------------------------------
st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Data Source: NSIDC MASIE (UTC)")
st.caption(f"Data Date: {latest_date.date()}")
st.caption(f"Region: {region}")

st.markdown("---")

st.subheader("Regional Ice Concentration Risk")

st.markdown(
    f"""
### {color} **{status}**
**Ice Concentration:** {risk_index} %
"""
)

st.progress(int(risk_index))

# -----------------------------------------------------
# Interpretation
# -----------------------------------------------------
st.markdown(
    f"""
**Operational Interpretation**

This indicator reflects the **actual observed sea ice concentration**
for **{region}**, derived from the NSIDC **MASIE multi-sensor analysis**.

Values represent **area-averaged ice concentration (%)** and are suitable
for **regional situational awareness** and **fleet-level planning**.

This is **not route-specific guidance** and does not account for
ice thickness, pressure, or short-term dynamics.
"""
)

# -----------------------------------------------------
# Legal / Attribution
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice concentration data are provided by the **NOAA / NSIDC MASIE**
(Multi-sensor Analyzed Sea Ice Extent, G02186), distributed under
NOAA Open Data policy.

This application provides situational awareness only and does not replace
official ice services, onboard navigation systems, or vessel master judgment.
"""
)

