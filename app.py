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
# (winter_max, summer_min)
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
# Load NSIDC v4 (robust)
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )
    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # auto-detect
    date_col = next(c for c in df.columns if "date" in c)
    extent_col = next(c for c in df.columns if "extent" in c)

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")

    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

df = load_nsidc_v4()

df_valid = df[df["date"].dt.date <= today]
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
# Regional seasonal-normalized risk
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
for **{region}**, normalized against its historical winter–summer range.

It explains why some regions (e.g., Sea of Okhotsk) remain **moderate**
even during full Arctic winter, while core Arctic basins approach **extreme**.
"""
)

# ------------------------------------------
# Legal / Attribution
# ------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Sea ice extent data are from **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
(AMSR2), used under NOAA Open Data policy.

This tool provides situational awareness only and does not replace
official ice services or navigational judgment.
"""
)
