import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

# =========================================================
# POLAR CUDA – Fleet Operations Dashboard
# =========================================================

st.set_page_config(page_title="POLAR CUDA – Fleet Ops", layout="wide")
UTC_TODAY = dt.datetime.utcnow().date()

# ---------------------------------------------------------
# Optional dependencies (do NOT crash if missing)
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
# Regions (bbox approximation)
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
# Dependency guard
# =========================================================
if not (HAS_XARRAY or HAS_NETCDF4):
    st.warning("MASAM2 NetCDF reader is not available in this environment.")
    st.info(
        "Add a requirements.txt file with:\n"
        "xarray\nnetCDF4\nplotly\nnumpy\npandas\n\n"
        "Then Commit → Streamlit Cloud → Manage app → Reboot."
    )
    st.stop()


# =========================================================
# MASAM2 loader
# =========================================================
@st.cache_data(ttl=3600)
def load_masam2_latest():
    year, month = UTC_TODAY.year, UTC_TODAY.month

    def try_month(y, m):
        url = (
            f"https://noaadata.apps.nsidc.org/NOAA/G10005_V2/"
            f"Data/{y}/masam2_minconc40_{y}{m:02d}_v2.nc"
        )
        if HAS_XARRAY:
            return xr.open_dataset(url), url
        else:
            return Dataset(url), url

    try:
        return try_month(year, month)
    except Exception:
        prev = dt.date(year, month, 1) - dt.timedelta(days=1)
        return try_month(prev.year, prev.month)


# =========================================================
# Compute regional concentration
# =========================================================
try:
    ds, src_url = load_masam2_latest()

    if HAS_XARRAY:
        conc = ds["sea_ice_concentration"].isel(time=-1).values
        lat = ds["latitude"].values
        lon = lon_to_180(ds["longitude"].values)
        data_date = pd.to_datetime(ds["time"].values[-1]).date()
    else:
        time_var = ds.variables["time"]
        times = num2date(time_var[:], time_var.units)
        data_date = times[-1].date()
        conc = ds.variables["sea_ice_concentration"][-1, :, :]
        lat = ds.variables["latitude"][:, :]
        lon = lon_to_180(ds.variables["longitude"][:, :])

    spec = REGIONS[region]
    mask = (
        (lat >= spec["lat"][0]) & (lat <= spec["lat"][1]) &
        (lon >= spec["lon"][0]) & (lon <= spec["lon"][1]) &
        (conc >= 0) & (conc <= 100)
    )

    mean_conc = float(np.nanmean(conc[mask]))

except Exception as e:
    st.error("Failed to compute regional ice concentration.")
    st.exception(e)
    st.stop()


# =========================================================
# Display
# =========================================================
risk = round(mean_conc, 1)
status, icon = classify_status(risk)

st.subheader("Regional Navigation Risk (Grid-based)")
st.caption(f"MASAM2 Data Date (UTC): {data_date}")
st.caption(f"Source: {src_url}")

col1, col2 = st.columns([2, 1])

with col1:
    if HAS_PLOTLY:
        st.plotly_chart(semicircle_gauge(risk, region), use_container_width=True)
    else:
        st.metric(label=region, value=f"{risk} %")
        st.progress(int(risk))

with col2:
    st.markdown(f"## {icon} {status}")
    st.markdown(f"**Mean Ice Concentration:** {risk} %")

st.markdown(
    "This value represents the mean sea-ice concentration (%) computed directly "
    "from the NSIDC MASAM2 4 km grid for situational awareness only."
)

st.markdown("---")
st.caption(
    "Data Source: NOAA / NSIDC MASAM2 (G10005_V2). "
    "This tool provides situational awareness only and does not replace "
    "official ice services or navigational judgment."
)
