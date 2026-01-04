import streamlit as st
import pandas as pd
import datetime

# ==========================================
# Polar CUDA – Polar Navigation Risk (STABLE)
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
# Region settings (weight only, 안전)
# ------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 1.00,
    "Beaufort Sea": 1.05,
    "Chukchi Sea": 1.10,
    "East Siberian Sea": 1.15,
    "Barents Sea": 0.90,
}

region = st.selectbox("Select Region", list(REGIONS.keys()))
region_weight = REGIONS[region]

# ------------------------------------------
# Load NSIDC v4 Sea Ice Index (SAFE)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # v4: date, extent
    if "date" not in df.columns or "extent" not in df.columns:
        raise ValueError("Required columns not found in NSIDC v4 dataset.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date")

    return df

df = load_nsidc_v4()

# ------------------------------------------
# Latest available data
# ------------------------------------------
latest = df.iloc[-1]
extent_today = float(latest["extent"])
data_date = latest["date"].date()

# ------------------------------------------
# Navigation Risk Logic (IMPORTANT FIX)
# ------------------------------------------
# Winter max reference (NSIDC climatology)
MAX_ICE_EXTENT = 14.5  # million km²

risk_index = round(
    min(
        max((extent_today / MAX_ICE_EXTENT) * 100.0 * region_weight, 0.0),
        100.0
    ),
    1
)

# ------------------------------------------
# Status classification (navigation logic)
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
# Header
# ------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Today: {today}")
st.caption(f"Region: {region}")
st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Sea Ice Extent: {extent_today:.2f} million km²")

st.markdown("---")

# ------------------------------------------
# Navigation Risk Gauge (NO external libs)
# ------------------------------------------
st.subheader("Polar Navigation Risk Gauge")

st.markdown(
    f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
)

# Simple dial-style indicator (safe)
segments = int(risk_index // 10)
dial = "🟢" * min(segments, 3) + "🟡" * max(min(segments - 3, 2), 0) \
       + "🟠" * max(min(segments - 5, 2), 0) + "🔴" * max(segments - 7, 0)

st.markdown(f"**Risk Dial:** {dial}")

st.progress(int(risk_index))

# ------------------------------------------
# Operational interpretation
# ------------------------------------------
st.markdown(
    f"""
**Operational Interpretation**

Current conditions indicate **{status.lower()} navigation risk** for **{region}**.

This assessment is driven primarily by **seasonal ice coverage**.
Winter conditions with extensive sea ice significantly increase
ice interaction risk, maneuvering constraints, and operational uncertainty.
"""
)

# ------------------------------------------
# Legal / Data attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice data are sourced from **NOAA/NSIDC Sea Ice Index, Version 4 (G02135)**,
which is publicly available under NOAA Open Data policy.

This application provides **situational awareness only** and does not replace
official ice services, onboard navigation systems, or the judgment of vessel masters.
Final operational decisions remain the responsibility of operators and ship masters.
"""
)
