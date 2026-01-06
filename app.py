import streamlit as st
import pandas as pd
import datetime as dt
import numpy as np
import urllib.request
import gzip
import io

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Level 3: NOAA/NSIDC IMS 24km GRID (regional proxy)
# Fallback: NSIDC Sea Ice Index v4 (extent)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Cryospheric Unified Decision Assistant",
    layout="centered",
)

TODAY = dt.date.today()

# -----------------------------------------------------
# Regions (Sea of Okhotsk excluded)
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
# Level 3 ROI (IMS 24km grid is 1024 x 1024)
# - Approximate operational ROIs in IMS polar stereographic grid.
# - Can be refined later with proper sector masks.
# Coordinate note (per IMS doc): (1,1) starts at lower-left corner.
# Here we treat array indexing as [row, col] with row=0 at top after parsing,
# so ROIs are defined for that orientation (empirically "good enough" starter).
# -----------------------------------------------------
ROI_1024 = {
    # (row_start, row_end, col_start, col_end)  [end is exclusive]
    "Entire Arctic (Pan-Arctic)": (120, 940, 80, 944),

    "Bering Sea": (520, 700, 120, 250),
    "Chukchi Sea": (380, 540, 200, 360),
    "Beaufort Sea": (330, 500, 360, 520),

    "East Siberian Sea": (330, 520, 120, 260),
    "Laptev Sea": (260, 430, 170, 330),
    "Kara Sea": (240, 420, 330, 470),

    "Barents Sea": (260, 440, 470, 650),
    "Greenland Sea": (260, 520, 650, 790),
    "Baffin Bay": (360, 620, 780, 910),
    "Lincoln Sea": (180, 340, 700, 880),
}

# -----------------------------------------------------
# Level 2 (fallback) regional normalization references
# (winter_max, summer_min) – operational scaling only
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
# Helpers
# -----------------------------------------------------
def classify_status(risk_index: float):
    if risk_index < 30:
        return "LOW", "🟢"
    if risk_index < 50:
        return "MODERATE", "🟡"
    if risk_index < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"


def dial_emoji(risk_index: float) -> str:
    # 0–100 -> 10 blocks
    filled = int(max(0, min(100, risk_index)) // 10)
    return "🟩" * min(filled, 3) + "🟨" * max(min(filled - 3, 2), 0) + "🟧" * max(
        min(filled - 5, 2), 0
    ) + "🟥" * max(filled - 7, 0)


def doy(d: dt.date) -> int:
    return int(d.strftime("%j"))


# -----------------------------------------------------
# Level 3: NOAA/NSIDC IMS 24km ASCII GRID loader
# - No xarray/netCDF4 needed
# - Reads .asc.gz, parses header+grid, returns np.ndarray (1024x1024) and valid_date
# IMS values (per user guide):
# 0 outside NH, 1 sea, 2 land, 3 sea ice, 4 snow
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_ims_24km_latest(max_lookback_days: int = 7):
    base = "https://noaadata.apps.nsidc.org/NOAA/G02156/24km"
    last_err = None

    for back in range(0, max_lookback_days):
        d = TODAY - dt.timedelta(days=back)
        y = d.year
        j = doy(d)
        url = f"{base}/{y}/ims{y}{j:03d}_24km_v1.3.asc.gz"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()

            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                text = gz.read().decode("utf-8", errors="ignore")

            lines = text.splitlines()

            # Find first "data-like" line: mostly digits/spaces and contains 1–4
            start_idx = None
            for i, line in enumerate(lines):
                s = line.strip()
                if not s:
                    continue
                ok = all((ch.isdigit() or ch.isspace()) for ch in s)
                if not ok:
                    continue
                # Must contain at least some separators and some digits
                if len(s) < 50:
                    continue
                # Heuristic: should have at least one of these codes
                if any(c in s for c in [" 1", " 2", " 3", " 4", " 0"]):
                    start_idx = i
                    break

            if start_idx is None:
                last_err = f"IMS file parsed but data block not found: {url}"
                continue

            data_str = "\n".join(lines[start_idx:])
            arr = np.fromstring(data_str, sep=" ", dtype=np.int16)

            # Expect 1024*1024 values (24km product)
            if arr.size % 1024 != 0:
                last_err = f"IMS grid size unexpected ({arr.size} values): {url}"
                continue

            nrows = arr.size // 1024
            if nrows < 900:  # sanity
                last_err = f"IMS grid rows too small ({nrows}): {url}"
                continue

            grid = arr.reshape((nrows, 1024))

            # Some files might include more than 1024 rows in rare cases; trim to last 1024
            if grid.shape[0] != 1024:
                grid = grid[-1024:, :]

            # Final sanity
            if grid.shape != (1024, 1024):
                last_err = f"IMS grid final shape unexpected {grid.shape}: {url}"
                continue

            return {"grid": grid, "data_date_utc": d, "source_url": url}, None

        except Exception as e:
            last_err = str(e)
            continue

    return None, f"Unable to load IMS 24km within {max_lookback_days} days. Last error: {last_err}"


def ims_roi_ice_fraction_percent(grid_1024: np.ndarray, region: str) -> float:
    rs, re, cs, ce = ROI_1024[region]
    sub = grid_1024[rs:re, cs:ce]

    # Only count ocean + sea ice pixels
    ocean = (sub == 1)
    ice = (sub == 3)
    denom = int(ocean.sum() + ice.sum())

    if denom == 0:
        return float("nan")

    return float(ice.sum() / denom * 100.0)


# -----------------------------------------------------
# Level 2 fallback: NSIDC Sea Ice Index v4 extent loader
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4_extent():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )
    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # date column detection
    date_col = None
    for cand in ["date", "datetime", "time"]:
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None and all(c in df.columns for c in ["year", "month", "day"]):
        df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
        date_col = "date"
    if date_col is None:
        return None, f"Date column not found. Columns: {list(df.columns)}"

    # extent column detection
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break
    if extent_col is None:
        # fallback: numeric column with max > 5
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
                extent_col = col
                break
    if extent_col is None:
        return None, f"Extent column not found. Columns: {list(df.columns)}"

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")
    df = df.dropna(subset=["date", "extent"]).sort_values("date").reset_index(drop=True)

    return df, None


def level2_risk_from_extent(extent_today: float, region: str) -> float:
    winter_max, summer_min = REGION_CLIMATOLOGY[region]
    denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-9
    return float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100))


# =====================================================
# UI (mobile-friendly)
# =====================================================
tab_dashboard, tab_about, tab_definition, tab_logo = st.tabs(
    ["🧭 Dashboard", "📄 About (IMO/Gov)", "📚 Formal Definition", "🎨 Logo/Icon Concept"]
)

# =====================================================
# TAB 1: Dashboard
# =====================================================
with tab_dashboard:
    st.title("🧊 POLAR CUDA")
    st.caption("Cryospheric Unified Decision Assistant")
    st.caption(f"Today (local): {TODAY}")

    st.markdown("### Region")
    region = st.selectbox("Select Region", REGIONS, index=0, label_visibility="collapsed")

    st.markdown("### Data Level")
    level = st.radio(
        "Choose data level",
        ["Level 3 (IMS 24km Grid – Regional Proxy)", "Level 2 (NSIDC Extent – Fallback)"],
        index=0,
        horizontal=False,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # ----- Level 3 first (preferred) -----
    used_level = None
    risk_index = None
    status = None
    color = None

    if level.startswith("Level 3"):
        ims_obj, ims_err = load_ims_24km_latest(max_lookback_days=7)
        if ims_obj is not None:
            grid = ims_obj["grid"]
            data_date = ims_obj["data_date_utc"]
            src_url = ims_obj["source_url"]

            roi_pct = ims_roi_ice_fraction_percent(grid, region)
            if np.isnan(roi_pct):
                st.warning("Region ROI contains no valid ocean/ice pixels. Switching to Level 2 fallback.")
            else:
                risk_index = round(float(np.clip(roi_pct, 0, 100)), 1)
                status, color = classify_status(risk_index)
                used_level = "Level 3 (IMS 24km Grid – Regional Proxy)"

                st.caption(f"IMS Data Date (UTC): {data_date}")
                st.caption("Metric: ROI sea-ice fraction proxy (%) from IMS class grid (ice/(ice+sea))")
                st.caption(f"Source: {src_url}")

        else:
            st.warning("Level 3 dataset (IMS 24km) could not be loaded. Switching to Level 2 fallback.")
            if ims_err:
                st.caption(ims_err)

    # ----- Level 2 fallback -----
    if risk_index is None:
        df2, err2 = load_nsidc_v4_extent()
        if df2 is None or df2.empty:
            st.error("Unable to load NSIDC Sea Ice Index v4 (fallback).")
            if err2:
                st.caption(err2)
            st.stop()

        df2_valid = df2[df2["date"].dt.date <= TODAY]
        if df2_valid.empty:
            st.error("No valid NSIDC extent data available up to today.")
            st.stop()

        latest = df2_valid.iloc[-1]
        extent_today = float(latest["extent"])
        data_date2 = latest["date"].date()

        risk_index = round(level2_risk_from_extent(extent_today, region), 1)
        status, color = classify_status(risk_index)
        used_level = "Level 2 (NSIDC Extent – Seasonal Normalization Proxy)"

        st.caption(f"NSIDC Data Date (UTC): {data_date2}")
        st.caption(f"Pan-Arctic extent (million km²): {extent_today:.2f}")

    # ----- Main display -----
    st.subheader("Regional Navigation Risk (Status-Based)")

    st.markdown(
        f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100  
**Dial:** {dial_emoji(risk_index)}
"""
    )
    st.progress(int(risk_index))

    st.markdown(
        f"""
**Operational Interpretation (Non-Directive)**

- **Selected Region:** {region}  
- **Data Level Used:** {used_level}

This dashboard is designed for **situational awareness** (not route command).  
For Level 3, the index is a **grid-derived regional proxy** computed directly from the IMS class grid within an operational ROI.  
For Level 2 fallback, the index represents **relative seasonal severity** using a regional normalization reference.
"""
    )

# =====================================================
# TAB 2: About (IMO/Gov)
# =====================================================
with tab_about:
    st.header("About – POLAR CUDA (IMO/Government Style)")

    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a decision-support framework designed to enhance
situational awareness for navigation and operations in polar and ice-affected waters.

The system translates publicly available cryospheric datasets into a unified, regionally interpretable risk indicator,
supporting informed operational judgement without prescribing actions or replacing official ice services.

POLAR CUDA is intended to complement onboard navigation systems and national ice services by providing an additional
layer of context on regional and seasonal ice regimes. It does not constitute navigational guidance and does not supersede
the authority or responsibility of vessel masters, operators, or national authorities.

All datasets used are obtained from open-access sources distributed under established public data policies.
"""
    )

# =====================================================
# TAB 3: Formal Definition
# =====================================================
with tab_definition:
    st.header("Formal Definition – Academic / White Paper")

    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a modular decision-support system that converts multi-source
cryospheric observations into a unified, interpretable risk metric for polar operations.

At Level 3, POLAR CUDA computes region-specific indicators from gridded products (e.g., IMS) through operational
region-of-interest (ROI) extraction and robust quality checks. At Level 2, it provides a fall-back mode using coarse
pan-Arctic indicators normalized against region-specific seasonal reference ranges.

POLAR CUDA is explicitly designed as an *assistant* rather than a directive system; outputs are interpretive and intended
to support human decision-making while preserving legal accountability at the operator and vessel-master level.
"""
    )

# =====================================================
# TAB 4: Logo / Icon Concept
# =====================================================
with tab_logo:
    st.header("Logo / Icon Concept – Designer Brief")

    st.markdown(
        """
**Concept Statement**  
*POLAR CUDA visualizes the moment where ice data becomes decision awareness.*

**Design Keywords**  
- Minimal, instrument-like  
- Calm, authoritative, non-alarmist  
- Operational (not decorative, not military UI)

**Icon Concept**  
- A half-dial/gauge arc suggesting “status awareness”  
- Abstract ice-grid motif (not literal glacier art)  
- Muted green→yellow→orange→red risk logic

**Avoid**  
- Emergency alert look  
- Gaming UI  
- Command-and-control aesthetics

**One-line instruction**  
“This is a tool you glance at before deciding — not something that tells you what to do.”
"""
    )

# -----------------------------------------------------
# Footer (always visible)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice (NOAA/NSIDC Open Data)**

Level 3 (preferred): **NOAA/NESDIS IMS Daily Northern Hemisphere Snow and Ice Analysis (G02156)** – 24 km ASCII grid,
distributed via NOAA/NSIDC open data access.  
Level 2 (fallback): **NOAA / NSIDC Sea Ice Index (G02135), Version 4** (daily extent), distributed under NOAA open data principles.

This application provides **situational awareness only** and does not replace official ice services, onboard navigation systems,
or the judgment of vessel masters. Final operational decisions remain the responsibility of operators and vessel masters.
"""
)
