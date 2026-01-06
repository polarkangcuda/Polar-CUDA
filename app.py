import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Mobile-First Operational Dashboard
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA",
    layout="centered"
)

today = datetime.date.today()

# -----------------------------------------------------
# Regions (Sea of Okhotsk intentionally excluded)
# -----------------------------------------------------
REGIONS = [
    "Entire Arctic (Pan-Arctic)",
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

# -----------------------------------------------------
# Regional seasonal normalization ranges
# (winter_max, summer_min)
# Operational reference only
# -----------------------------------------------------
REGION_CLIMATOLOGY = {
    "Entire Arctic (Pan-Arctic)": (15.5, 4.0),
    "Bering Sea": (1.8, 0.2),
    "Chukchi Sea": (2.8, 0.5),
    "Beaufort Sea": (3.2, 0.8),
    "East Siberian Sea": (3.8, 1.0),
    "Laptev Sea": (4.2, 1.2),
    "Kara Sea": (3.0, 0.6),
    "Barents Sea": (2.0, 0.2),
    "Greenland Sea": (2.4, 0.4),
    "Baffin Bay": (2.8, 0.6),
    "Lincoln Sea": (4.8, 3.0),
}

# -----------------------------------------------------
# NSIDC v4 loader (robust & mobile-safe)
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # Detect date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    elif all(c in df.columns for c in ["year", "month", "day"]):
        df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
    else:
        return None

    # Detect extent
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break

    if extent_col is None:
        for c in df.columns:
            num = pd.to_numeric(df[c], errors="coerce")
            if num.notna().sum() > len(df) * 0.9 and num.max() > 5:
                extent_col = c
                break

    if extent_col is None:
        return None

    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")
    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

# -----------------------------------------------------
# Status classification
# -----------------------------------------------------
def classify_status(val):
    if val < 30:
        return "LOW", "🟢"
    if val < 50:
        return "MODERATE", "🟡"
    if val < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

# =====================================================
# TOP: Region selector (mobile-first)
# =====================================================
st.markdown("### 🌐 Select Region")
region = st.selectbox("", REGIONS, index=REGIONS.index("Laptev Sea"))

st.markdown("---")

# =====================================================
# DATA LOAD
# =====================================================
df = load_nsidc_v4()
if df is None or df.empty:
    st.error("NSIDC sea ice data unavailable.")
    st.stop()

df_valid = df[df["date"].dt.date <= today]
if df_valid.empty:
    st.error("No valid NSIDC data available.")
    st.stop()

latest = df_valid.iloc[-1]
extent_today = float(latest["extent"])
data_date = latest["date"].date()

# =====================================================
# RISK COMPUTATION (seasonally normalized)
# =====================================================
winter_max, summer_min = REGION_CLIMATOLOGY[region]
denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-6

risk_index = round(
    float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100)),
    1
)

status, color = classify_status(risk_index)

# =====================================================
# MAIN DASHBOARD (NO SCROLL CORE)
# =====================================================
st.markdown("## 🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")

st.markdown(
    f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

st.progress(int(risk_index))

st.caption(f"Data: NSIDC Sea Ice Index v4 ({data_date}, UTC)")

# =====================================================
# DETAILS (collapsed by default)
# =====================================================
with st.expander("ℹ️ Details & Interpretation"):
    st.markdown(
        f"""
**Operational Interpretation**

This indicator represents **relative seasonal ice severity** for **{region}**,
normalized against its historical winter–summer range.

It is intended to support **situational awareness only**.
It does **not** provide route guidance and does **not** replace
official ice services, onboard navigation systems, or vessel master judgment.
"""
    )

    st.markdown(
        """
**Data Source & Legal Notice**

Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**,
distributed under NOAA Open Data policy.

Final operational decisions remain the responsibility of operators and vessel masters.
"""
    )
