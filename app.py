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
# Regional climatological range
# (winter_max, summer_min) [million km²]
# ------------------------------------------
REGION_CLIMATOLOGY = {
    "Entire Arctic (Pan-Arctic)": (15.5, 4.0),
    "Sea of Okhotsk": (2.0, 0.3),
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

# ------------------------------------------
# Load NSIDC v4 Sea Ice Index (ULTRA SAFE)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # -----------------------------
    # Date column detection
    # -----------------------------
    date_col = None
    for cand in ["date", "datetime", "time"]:
        if cand in df.columns:
            date_col = cand
            break

    # Fallback: year / month / day
    if date_col is None:
        if all(c in df.columns for c in ["year", "month", "day"]):
            df["date"] = pd.to_datetime(
                df[["year", "month", "day"]],
                errors="coerce"
            )
            date_col = "date"
        else:
            st.error(
                f"Unable to detect date column. Columns found: {list(df.columns)}"
            )
            return None

    # -----------------------------
    # Extent column detection
    # -----------------------------
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break

    # Fallback: numeric column with realistic magnitude
    if extent_col is None:
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
                extent_col = col
                break

    if extent_col is None:
        st.error(
            f"Unable to detect extent column. Columns found: {list(df.columns)}"
        )
        return None

    # -----------------------------
    # Final clean dataframe
    # -----------------------------
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")

    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

df = load_nsidc_v4()

# ------------------------------------------
# Fail-safe
# ------------------------------------------
if df is None or df.empty:
    st.stop()

df_valid = df[df["date"].dt.date <= today]

if df_valid.empty:
    st.error("No valid NSIDC data available up to today.")
    st.stop()

latest = df_valid.iloc[-1]
extent_today = float(latest["extent"])
data_date = latest["date"].date()

# ------------------------------------------
# Header
# ------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Today: {today}")
st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Region: {region}")

st.markdown("---")

# ------------------------------------------
# Seasonal-normalized regional risk
# ------------------------------------------
winter_max, summer_min = REGION_CLIMATOLOGY[region]

risk_index = round(
    np.clip(
        (extent_today - summer_min)
        / (winter_max - summer_min)
        * 100,
        0,
        100,
    ),
    1,
)

# ------------------------------------------
# Status
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
st.subheader("Regional Navigation Risk")

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

This index represents the **relative seasonal ice severity**
for **{region}**, normalized against its historical
**winter–summer climatological range**.

This explains why peripheral seas (e.g., Sea of Okhotsk,
Barents Sea) may remain **moderate**, while central Arctic
basins approach **extreme** during winter.
"""
)

# ------------------------------------------
# Legal / Attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index
(G02135), Version 4**, derived from AMSR2 observations and
distributed under the NOAA Open Data policy.

This application provides situational awareness only and does
not replace official ice services, onboard navigation systems,
or the judgment of vessel masters.
"""
)
