import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Mobile-First Operational UI
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA",
    layout="centered",
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
# Regional climatological normalization range
# (winter_max, summer_min) – operational reference
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
# NSIDC v4 loader (robust, mobile-safe)
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )
    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # Date detection
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    elif all(c in df.columns for c in ["year", "month", "day"]):
        df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
    else:
        return None

    # Extent detection
    extent_col = None
    for c in df.columns:
        numeric = pd.to_numeric(df[c], errors="coerce")
        if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
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
# MOBILE-FIRST DASHBOARD
# =====================================================

st.markdown("## 🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")

# --- Region selector (TOP PRIORITY) ---
region = st.selectbox("📍 Selected Region", REGIONS)

# --- Load data ---
df = load_nsidc_v4()
if df is None or df.empty:
    st.error("Unable to load NSIDC sea ice data.")
    st.stop()

df_valid = df[df["date"].dt.date <= today]
if df_valid.empty:
    st.error("No valid NSIDC data available.")
    st.stop()

latest = df_valid.iloc[-1]
extent_today = float(latest["extent"])
data_date = latest["date"].date()

st.caption(f"Data date (UTC): {data_date}")

st.markdown("---")

# -----------------------------------------------------
# Risk computation (Level 2 – seasonal proxy)
# -----------------------------------------------------
winter_max, summer_min = REGION_CLIMATOLOGY[region]
denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-6

risk_index = round(
    float(np.clip(((extent_today - summer_min) / denom) * 100, 0, 100)),
    1,
)

status, color = classify_status(risk_index)

# =====================================================
# CORE DECISION PANEL (1-SCREEN)
# =====================================================

st.markdown("### Regional Navigation Risk")

st.markdown(
    f"""
## {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

st.progress(int(risk_index))

# Dial-style visual (mobile friendly)
blocks = int(risk_index // 10)
dial = "🟩" * min(blocks, 3) + "🟨" * max(min(blocks - 3, 2), 0) \
       + "🟧" * max(min(blocks - 5, 2), 0) + "🟥" * max(blocks - 7, 0)

st.markdown(f"**Risk Dial:** {dial}")

# =====================================================
# SHORT OPERATIONAL SUMMARY (2 lines)
# =====================================================
st.markdown(
    f"""
**Summary**

Relative seasonal ice severity for **{region}** is assessed as **{status.lower()}**.  
This view uses **NSIDC Sea Ice Index (Level 2 seasonal normalization proxy)**.
"""
)

# =====================================================
# COLLAPSIBLE DETAILS (Mobile-Friendly)
# =====================================================
with st.expander("ℹ️ Data & Interpretation Details"):
    st.markdown(
        f"""
**Data Level**
- Level 2: NSIDC Sea Ice Index v4 (Pan-Arctic daily extent)
- Regional severity inferred via seasonal normalization

**Interpretation**
- Reflects *relative seasonal severity*, not local ice thickness or ridging
- Intended for situational awareness only

**Limitations**
- Does not provide tactical route guidance
- Level 3 grid-based regional concentration not shown in this view
"""
    )

# =====================================================
# FOOTER (LEGAL – LOW VISUAL WEIGHT)
# =====================================================
st.markdown("---")
st.caption(
    """
Sea ice extent data: **NOAA / NSIDC Sea Ice Index (G02135), Version 4**  
Distributed under NOAA Open Data principles.

POLAR CUDA provides situational awareness only and does not replace
official ice services, onboard navigation systems, or vessel master judgment.
"""
)
