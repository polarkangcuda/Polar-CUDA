import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

# ---- optional deps (we try both xarray and netCDF4) ----
try:
    import xarray as xr
    _HAS_XARRAY = True
except Exception:
    _HAS_XARRAY = False

try:
    from netCDF4 import Dataset, num2date
    _HAS_NETCDF4 = True
except Exception:
    _HAS_NETCDF4 = False

try:
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False


# =========================================================
# Polar CUDA – Fleet Ops (Regional "Real" Ice Concentration)
# Data: NSIDC MASAM2 (G10005_V2) = MASIE + AMSR2, 4 km grid
# =========================================================

st.set_page_config(page_title="Polar CUDA – Fleet Ops", layout="wide")

UTC_TODAY = dt.datetime.utcnow().date()


# -------------------------------
# Regions (simple bbox masks)
# NOTE: lon in dataset may be 0..360 or -180..180; we normalize to -180..180
# -------------------------------
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
    # Bering crosses dateline → handle separately in code
    "Bering Sea": {"lat": (55, 66), "lon": ("DATELINE", (-180, -160), (160, 180))},
}

DEFAULT_REGION_LIST = list(REGIONS.keys())


# -------------------------------
# Helpers
# -------------------------------
def lon_to_180(lon):
    """Convert longitude array to [-180, 180]."""
    lon = np.array(lon)
    lon = ((lon + 180) % 360) - 180
    return lon


def mask_bbox(lat2d, lon2d, region_name):
    """Return boolean mask for a region using bounding boxes."""
    spec = REGIONS[region_name]
    lat_min, lat_max = spec["lat"]

    lat_ok = (lat2d >= lat_min) & (lat2d <= lat_max)

    if spec["lon"][0] == "DATELINE":
        # spec["lon"] = ("DATELINE", (lon1_min, lon1_max), (lon2_min, lon2_max))
        _, r1, r2 = spec["lon"]
        lon1_min, lon1_max = r1
        lon2_min, lon2_max = r2
        lon_ok = ((lon2d >= lon1_min) & (lon2d <= lon1_max)) | ((lon2d >= lon2_min) & (lon2d <= lon2_max))
        return lat_ok & lon_ok

    lon_min, lon_max = spec["lon"]
    lon_ok = (lon2d >= lon_min) & (lon2d <= lon_max)
    return lat_ok & lon_ok


def classify_status(risk_index):
    # You can tune thresholds later for ops
    if risk_index < 15:
        return "LOW", "🟢"
    elif risk_index < 35:
        return "MODERATE", "🟡"
    elif risk_index < 60:
        return "HIGH", "🟠"
    else:
        return "EXTREME", "🔴"


def semicircle_gauge(value, title="Risk", units="%", vmin=0, vmax=100):
    """
    Half-dial gauge using Plotly (preferred).
    If plotly is not available, caller should fall back to st.metric/progress.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            number={"suffix": f" {units}"},
            title={"text": title},
            gauge={
                "axis": {"range": [vmin, vmax]},
                "bar": {"color": "black"},
                "steps": [
                    {"range": [0, 15], "color": "#d7f5d7"},
                    {"range": [15, 35], "color": "#fff4c2"},
                    {"range": [35, 60], "color": "#ffd1a6"},
                    {"range": [60, 100], "color": "#ffb3b3"},
                ],
            },
        )
    )
    # Make it a semi-circle look
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=0),
        height=240,
    )
    # Plotly doesn't truly "half" indicator; we fake it by cropping with domain
    # by shrinking height and letting it look like a dial.
    return fig


# -------------------------------
# NSIDC MASAM2 loader (robust)
# Directory + naming confirmed by NSIDC user guide:
# https://noaadata.apps.nsidc.org/NOAA/G10005_V2/Data/YYYY/masam2_minconc40_YYYYMM_v2.nc
# -------------------------------
@st.cache_data(ttl=3600)
def load_masam2_month(year: int, month: int):
    yyyymm = f"{year}{month:02d}"
    url = (
        f"https://noaadata.apps.nsidc.org/NOAA/G10005_V2/"
        f"Data/{year}/masam2_minconc40_{yyyymm}_v2.nc"
    )

    if _HAS_XARRAY:
        ds = xr.open_dataset(url)
        # Expected variables (per guide): sea_ice_concentration, latitude, longitude, time
        if "sea_ice_concentration" not in ds.variables:
            raise ValueError(f"MASAM2: 'sea_ice_concentration' not found. Vars: {list(ds.variables)}")
        return {"backend": "xarray", "url": url, "ds": ds}

    if _HAS_NETCDF4:
        nc = Dataset(url)
        if "sea_ice_concentration" not in nc.variables:
            raise ValueError(f"MASAM2: 'sea_ice_concentration' not found. Vars: {list(nc.variables.keys())}")
        return {"backend": "netcdf4", "url": url, "nc": nc}

    raise ImportError("Need xarray or netCDF4 to read MASAM2 .nc files.")


def pick_latest_available_day_from_month(obj, max_date_utc: dt.date):
    """
    Return (data_date_utc, conc2d, lat2d, lon2d)
    conc2d in percent, masked later.
    """
    if obj["backend"] == "xarray":
        ds = obj["ds"]

        # decode time
        time = ds["time"].values  # numpy datetime64 if decoded
        # Sometimes time is numeric; xarray usually decodes. Still be safe:
        try:
            time_dates = pd.to_datetime(time).date
        except Exception:
            time_dates = pd.to_datetime(ds["time"].values).date

        # find last index <= max_date_utc
        idx = None
        for i in range(len(time_dates) - 1, -1, -1):
            if time_dates[i] <= max_date_utc:
                idx = i
                break
        if idx is None:
            raise ValueError("No MASAM2 data in this month up to requested date.")

        conc = ds["sea_ice_concentration"].isel(time=idx).values
        lat = ds["latitude"].values
        lon = ds["longitude"].values

        return time_dates[idx], conc, lat, lon

    # netCDF4
    nc = obj["nc"]
    time_var = nc.variables["time"]
    time_units = getattr(time_var, "units", None)
    time_calendar = getattr(time_var, "calendar", "standard")
    times = num2date(time_var[:], units=time_units, calendar=time_calendar)
    time_dates = np.array([t.date() for t in times])

    idx = None
    for i in range(len(time_dates) - 1, -1, -1):
        if time_dates[i] <= max_date_utc:
            idx = i
            break
    if idx is None:
        raise ValueError("No MASAM2 data in this month up to requested date.")

    conc = nc.variables["sea_ice_concentration"][idx, :, :]
    lat = nc.variables["latitude"][:, :]
    lon = nc.variables["longitude"][:, :]
    return time_dates[idx], np.array(conc), np.array(lat), np.array(lon)


def compute_region_mean_conc(conc2d, lat2d, lon2d, region_name):
    """
    conc2d: MASAM2 concentration values.
      Valid: 0 or 40..100 (percent)
      Flags: 104,110,119,120 etc -> exclude
    """
    lon180 = lon_to_180(lon2d)
    region_mask = mask_bbox(lat2d, lon180, region_name)

    # valid concentration values only
    valid = (conc2d >= 0) & (conc2d <= 100)

    m = region_mask & valid
    if np.count_nonzero(m) < 50:
        return np.nan

    return float(np.nanmean(conc2d[m]))


# -------------------------------
# UI: Tabs 유지 (Dashboard 중심)
# -------------------------------
tab_dashboard, tab_map, tab_about = st.tabs(["Dashboard (Ops)", "Map (Browse)", "About / Legal"])


with tab_dashboard:
    st.title("🧊 Polar CUDA – Fleet Operations Dashboard")
    st.caption(f"UTC Today: {UTC_TODAY}  |  Update cycle: Daily (NSIDC MASAM2)")

    # Select region(s)
    st.markdown("### Region Scope")
    mode = st.radio("View", ["Single region", "Multi-region (Fleet)"], horizontal=True)

    if mode == "Single region":
        selected = [st.selectbox("Select Region", DEFAULT_REGION_LIST)]
    else:
        selected = st.multiselect("Select Regions", DEFAULT_REGION_LIST, default=["Chukchi Sea", "Beaufort Sea"])

    # Load current month; if no data yet, fall back to previous month automatically
    year, month = UTC_TODAY.year, UTC_TODAY.month

    def safe_load_latest():
        # try current month
        try:
            obj = load_masam2_month(year, month)
            return obj
        except Exception:
            # fallback: previous month
            prev = (dt.date(year, month, 1) - dt.timedelta(days=1))
            obj2 = load_masam2_month(prev.year, prev.month)
            return obj2

    try:
        obj = safe_load_latest()
        data_date, conc2d, lat2d, lon2d = pick_latest_available_day_from_month(obj, UTC_TODAY)
    except Exception as e:
        st.error("MASAM2 데이터를 불러오지 못했습니다. (Streamlit Cloud 로그에서 상세 확인 가능)")
        st.exception(e)
        st.stop()

    # Compute region values
    rows = []
    for r in selected:
        mean_conc = compute_region_mean_conc(conc2d, lat2d, lon2d, r)
        rows.append({"Region": r, "Mean Ice Concentration (%)": mean_conc})

    df = pd.DataFrame(rows)
    df["Risk Index (0-100)"] = df["Mean Ice Concentration (%)"].round(1)  # risk = mean concentration (direct)
    df["Status"] = df["Risk Index (0-100)"].apply(lambda x: classify_status(x)[0] if pd.notna(x) else "N/A")
    df["Icon"] = df["Risk Index (0-100)"].apply(lambda x: classify_status(x)[1] if pd.notna(x) else "⚪")

    st.markdown("---")
    st.subheader("Latest Data")
    st.write(f"**NSIDC MASAM2 data date (UTC): {data_date}**")
    st.write(f"**Source file:** {obj.get('url', '')}")

    # Display gauges
    st.markdown("---")
    st.subheader("Regional Navigation Risk (Real grid-based)")

    if mode == "Single region":
        r = selected[0]
        val = df.loc[df["Region"] == r, "Risk Index (0-100)"].values[0]
        status, icon = classify_status(val) if pd.notna(val) else ("N/A", "⚪")

        c1, c2 = st.columns([2, 1])
        with c1:
            if _HAS_PLOTLY:
                fig = semicircle_gauge(val, title=f"{r}", units="%")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.metric(label=r, value=f"{val:.1f} / 100", delta=status)
                st.progress(int(val) if pd.notna(val) else 0)

        with c2:
            st.markdown("### Status")
            st.markdown(f"## {icon} **{status}**")
            st.markdown("### Value")
            st.markdown(f"**Mean Ice Concentration:** {val:.1f}%")

    else:
        # Fleet view: show multiple small gauges + summary table (no heavy charts)
        cols = st.columns(3)
        for i, row in df.iterrows():
            col = cols[i % 3]
            region_name = row["Region"]
            val = row["Risk Index (0-100)"]
            status = row["Status"]
            icon = row["Icon"]

            with col:
                st.markdown(f"#### {region_name}")
                if pd.isna(val):
                    st.warning("Insufficient valid grid cells in bbox.")
                else:
                    if _HAS_PLOTLY:
                        fig = semicircle_gauge(val, title=f"{icon} {status}", units="%")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.metric(label=f"{icon} {status}", value=f"{val:.1f} / 100")
                        st.progress(int(val))

        st.markdown("---")
        st.subheader("Fleet Summary (ops-friendly)")
        show = df.copy()
        show["Mean Ice Concentration (%)"] = show["Mean Ice Concentration (%)"].round(1)
        st.dataframe(show[["Region", "Mean Ice Concentration (%)", "Risk Index (0-100)", "Icon", "Status"]], use_container_width=True)

    st.markdown("---")
    st.markdown(
        """
**Ops Interpretation (very short)**  
- This dashboard computes **regional mean sea-ice concentration (%) directly from the MASAM2 4 km grid** (not a Pan-Arctic proxy).  
- **Higher concentration ⇒ higher navigation difficulty** (generalized; does not include pressure/thickness/lead structure).  
"""
    )


with tab_map:
    st.title("🗺️ Browse Map (Context)")
    st.caption("This is a browse image for situational context (not used for calculations).")

    # Bremen browse image (user provided)
    bremen_png = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    st.image(bremen_png, caption="AMSR2 Sea Ice Concentration Browse (Uni Bremen)")

    st.markdown(
        """
**Note**  
- The **calculation** in this app uses **NSIDC MASAM2** gridded concentration data.  
- This tab is just a visual context layer to help a human “sanity-check” patterns quickly.
"""
    )


with tab_about:
    st.title("About / Legal (Policy-ready)")

    st.markdown(
        """
### What this is
**Polar CUDA** is a situational-awareness dashboard for fleet/route planning that converts
public cryospheric grids into **simple, explainable regional risk signals**.

### Data used (primary)
- **NSIDC MASAM2: Daily 4 km Arctic Sea Ice Concentration, Version 2 (G10005_V2)**  
  Delivered via: `https://noaadata.apps.nsidc.org/NOAA/G10005_V2/`  
  (Gridded concentration blended from MASIE ice coverage + AMSR2 concentration; min concentration set to 40% where MASIE indicates ice.)

### Legal / Disclaimer
This application uses **publicly accessible NOAA/NSIDC-hosted data** for **situational awareness** only.
It **does not** constitute navigational guidance and **does not** replace official ice services,
onboard sensors, ECDIS/ice radar, or the judgment of the vessel master and operating company.

### Citation (recommended in policy docs)
Fetterer, F., J. S. Stewart, and W. N. Meier. 2023. **MASAM2: Daily 4 km Arctic Sea Ice Concentration, Version 2.**
Boulder, Colorado USA. NSIDC: National Snow and Ice Data Center. doi:10.7265/bqd9-vm28. (Accessed: include your date)
"""
    )
