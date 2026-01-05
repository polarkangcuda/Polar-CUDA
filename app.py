import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

# =========================================================
# POLAR CUDA – Fleet Operations Dashboard
# Real regional ice concentration (MASAM2-ready, SAFE)
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Fleet Ops", layout="wide")
UTC_TODAY = dt.datetime.utcnow().date()

# ---------------------------------------------------------
# Try optional dependencies (do NOT crash if missing)
# ---------------------------------------------------------
HAS_XARRAY = False
HAS_NETCDF4 = False
HAS_PLOTLY = False

try:
    import xarray as xr
    HAS_XARRAY = True
except Exception:
    pass

try:
    from netCDF4 import Dataset, num2date
    HAS_NETCDF4 = True
except Exception:
    pass

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except Exception:
    pass


# ---------------------------------------------------------
# Regions (bbox approximation; ops-level)
# ---------------------------------------------------------
REGIONS = {
    "Chukchi Sea": {"lat": (66, 75), "lon": (-180, -157)},
    "Beaufort Sea": {"lat": (70, 78), "lon": (-155, -120)},
    "East Siberian Sea": {"lat": (70, 80), "lon": (140, 180)},
    "Laptev Sea": {"lat": (72, 80), "lon": (105, 140)},
    "Kara Sea": {"lat": (70, 80), "lon": (50, 90)},
    "Barents Sea": {"lat": (70, 80), "lon": (20, 60)},
    "Greenland Sea": {"lat": (70, 80), "lon": (-20, 20)},
    "Baffin Bay": {"lat": (65, 78), "lon": (-80, -50)},
    "Lincoln Sea": {"lat": (80, 88), "lon": (-110, -40)},
}

REGION_LIST = list(REGIONS.keys())


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def lon_to_180(lon):
    lon = np.array(lon)
    return ((lon + 180) % 360) - 180


def classify_status(val):
    if val < 15:
        return "LOW", "🟢"
    elif val < 35:
        return "MODERATE", "🟡"
    elif val < 60:
        return "HIGH", "🟠"
    else:
        return "EXTREME", "🔴"


def semicircle_gauge(val, title):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(val),
            number={"suffix": " %"},
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "steps": [
                    {"range": [0, 15], "color": "#d7f5d7"},
                    {"range": [15, 35], "color": "#fff4c2"},
                    {"range": [35, 60], "color": "#ffd1a6"},
                    {"range": [60, 100], "color": "#ffb3b3"},
                ],
            },
        )
    )
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=0))
    return fig


# =========================================================
# UI
# =========================================================
st.title("🧊 POLAR CUDA – Fleet Operations")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"UTC Date: {UTC_TODAY}")

region = st.selectbox("Select Region", REGION_LIST)

st.markdown("---")

# =========================================================
# Dependency guard (CRITICAL)
# =========================================================
if not (HAS_XARRAY or HAS_NETCDF4):
    st.warning("⚠️ MASAM2 NetCDF reader is not available in this environment.")
    st.markdown(
        """
### Action Required (1-time setup)

To enable **real regional ice concentration** calculations,  
please add the following file to your GitHub repository root:

**`requirements.txt`**
```txt
xarray
netCDF4
plotly
numpy
pandas
