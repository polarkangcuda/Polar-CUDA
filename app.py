import streamlit as st
import pandas as pd
import datetime
import numpy as np
import requests
from io import BytesIO

# ==========================================
# Polar CUDA – NSIDC v4 Regional/Sector (Real)
# ==========================================

st.set_page_config(page_title="Polar CUDA – Regional/Sector", layout="centered")
today = datetime.date.today()

# -------------------------------------------------
# Regions we expose (you can add more later)
# -------------------------------------------------
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

# -------------------------------------------------
# Regional baseline for normalization (million km²)
# (policy/ops-friendly reference maxima)
# -------------------------------------------------
REGION_BASELINE = {
    "Entire Arctic (Pan-Arctic)": 14.8,
    "Sea of Okhotsk": 1.5,
    "Bering Sea": 1.2,
    "Chukchi Sea": 2.5,
    "Beaufort Sea": 3.0,
    "East Siberian Sea": 3.5,
    "Laptev Sea": 4.0,
    "Kara Sea": 2.8,
    "Barents Sea": 1.8,
    "Greenland Sea": 2.2,
    "Baffin Bay": 2.6,
    "Lincoln Sea": 4.5,
}

# -------------------------------------------------
# NSIDC v4 Regional Daily Excel (Northern Hemisphere)
# -------------------------------------------------
NSIDC_V4_REGIONAL_XLSX = (
    "https://masie_web.apps.nsidc.org/pub/DATASETS/NOAA/G02135/seaice_analysis/"
    "N_Sea_Ice_Index_Regional_Daily_Data_G02135_v4.0.xlsx"
)

def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in str(s) if ch.isalnum())

def _find_date_col(cols):
    # pick column that looks like date (most parseable)
    best = None
    best_score = -1
    for c in cols:
        parsed = pd.to_datetime(pd.Series([c]), errors="coerce")
        # ignore column names that parse as date; we need actual column with date values later
        # This helper is for column-name matching; we'll do value-based below.
    return best

def _pick_column_by_tokens(df: pd.DataFrame, tokens):
    """
    Choose a column whose normalized name contains all tokens (any order).
    """
    cols = list(df.columns)
    ncols = [_norm(c) for c in cols]
    for i, nc in enumerate(ncols):
        if all(t in nc for t in tokens):
            return cols[i]
    return None

@st.cache_data(ttl=3600)
def load_nsidc_regional_v4_excel(url: str) -> pd.DataFrame:
    """
    Robust download via requests (avoids urllib HTTPError),
    then parse Excel and return a tidy dataframe:
    columns: date, <region extent columns...>
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (PolarCUDA; +https://streamlit.io) requests"
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    bio = BytesIO(r.content)
    xls = pd.ExcelFile(bio)

    # Try sheets in a sensible order.
    # Different NSIDC xlsx sometimes uses names like "Daily Extent", "Extent", "Data", etc.
    sheet_candidates = xls.sheet_names

    # Load each sheet and choose the one that contains a date-like column + numeric extent columns
    best_df = None
    best_quality = -1

    for sh in sheet_candidates:
        try:
            tmp = pd.read_excel(xls, sheet_name=sh)
        except Exception:
            continue

        # Normalize column names
        tmp.columns = [str(c).strip() for c in tmp.columns]

        # Find a date column by value-parsability
        date_col = None
        best_date_parse = 0
        for c in tmp.columns:
            parsed = pd.to_datetime(tmp[c], errors="coerce")
            score = parsed.notna().sum()
            if score > best_date_parse:
                best_date_parse = score
                date_col = c

        if date_col is None or best_date_parse < 100:  # must have plenty of dates
            continue

        # Count numeric columns that look like extent (max > 0.1 and many non-null)
        numeric_like = 0
        for c in tmp.columns:
            if c == date_col:
                continue
            vals = pd.to_numeric(tmp[c], errors="coerce")
            if vals.notna().sum() > 100 and vals.max() > 0.1:
                numeric_like += 1

        quality = best_date_parse + numeric_like * 10
        if quality > best_quality:
            best_quality = quality
            best_df = tmp.copy()
            best_df["_date_col"] = date_col

    if best_df is None:
        raise ValueError("Could not find a valid data sheet in the NSIDC regional Excel file.")

    date_col = best_df["_date_col"].iloc[0] if "_date_col" in best_df.columns else None
    if date_col is None:
        # fallback: assume first column
        date_col = best_df.columns[0]

    # Build tidy df
    df = best_df.drop(columns=[c for c in ["_date_col"] if c in best_df.columns]).copy()
    df.columns = [str(c).strip() for c in df.columns]

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["date"]).copy()

    # Drop the original date_col if it's not already named "date"
    if date_col != "date" and date_col in df.columns:
        df = df.drop(columns=[date_col])

    # Clean obvious non-data rows/columns
    # Keep only columns that are mostly numeric
    keep = ["date"]
    for c in df.columns:
        if c == "date":
            continue
        vals = pd.to_numeric(df[c], errors="coerce")
        if vals.notna().sum() > len(df) * 0.7:
            keep.append(c)

    df = df[keep].sort_values("date").reset_index(drop=True)
    return df

def resolve_region_column(df: pd.DataFrame, region_name: str) -> str:
    """
    Map UI region name to a real column in NSIDC Excel (fuzzy).
    """
    # Try common token sets
    # We search in normalized column names, so "Sea of Okhotsk" can match "Okhotsk"
    rules = {
        "Entire Arctic (Pan-Arctic)": [["total"], ["panarctic"], ["arctictotal"]],
        "Sea of Okhotsk": [["okhotsk"]],
        "Bering Sea": [["bering"]],
        "Chukchi Sea": [["chukchi"]],
        "Beaufort Sea": [["beaufort"]],
        "East Siberian Sea": [["eastsiberian"], ["siberian", "east"]],
        "Laptev Sea": [["laptev"]],
        "Kara Sea": [["kara"]],
        "Barents Sea": [["barents"]],
        "Greenland Sea": [["greenland"]],
        "Baffin Bay": [["baffin"]],
        "Lincoln Sea": [["lincoln"]],
    }

    cols = list(df.columns)
    ncols = {_norm(c): c for c in cols if c != "date"}

    for token_list in rules.get(region_name, []):
        # find column whose normalized name includes all tokens
        for nc, orig in ncols.items():
            if all(t in nc for t in token_list):
                return orig

    # If not found, give a helpful error
    raise KeyError(
        f"Region column not found for '{region_name}'. "
        f"Available columns (sample): {cols[:25]} ..."
    )

# -------------------------------------------------
# Load data
# -------------------------------------------------
try:
    df = load_nsidc_regional_v4_excel(NSIDC_V4_REGIONAL_XLSX)
except requests.HTTPError as e:
    st.error("NSIDC server returned an HTTP error while downloading the dataset.")
    st.caption(f"HTTP details: {e}")
    st.stop()
except Exception as e:
    st.error("Failed to load NSIDC v4 regional dataset.")
    st.caption(f"Details: {e}")
    st.stop()

# Resolve region column
try:
    region_col = resolve_region_column(df, region)
except Exception as e:
    st.error("Could not match the selected region to a column in NSIDC dataset.")
    st.caption(str(e))
    st.stop()

# Latest valid (<= today)
df_valid = df[df["date"].dt.date <= today]
if df_valid.empty:
    st.error("No valid observations available up to today in the NSIDC dataset.")
    st.stop()

latest = df_valid.iloc[-1]
data_date = latest["date"].date()

extent = pd.to_numeric(latest[region_col], errors="coerce")
if pd.isna(extent):
    st.error("Latest value is not numeric (dataset format may have changed).")
    st.stop()

extent = float(extent)

# -------------------------------------------------
# Risk index = normalized against regional baseline
# -------------------------------------------------
baseline = REGION_BASELINE[region]
risk_index = round(np.clip((extent / baseline) * 100.0, 0, 100), 1)

# Status
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

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Today: {today}")
st.caption(f"NSIDC Data Date (UTC): {data_date}")
st.caption(f"Region: {region}")

st.markdown("---")

st.subheader("Regional Ice Risk (NSIDC v4)")
st.markdown(f"### {color} **{status}**")
st.markdown(f"**Regional Extent:** {extent:.2f} million km²")
st.markdown(f"**Risk Index:** {risk_index} / 100")
st.progress(int(risk_index))

st.markdown(
    f"""
**Interpretation**

- This index uses **NSIDC Sea Ice Index (G02135) v4 Regional Daily Data**
  and expresses **regional constraint severity** relative to a regional baseline.
- It reflects **conditions derived from concentration fields**, summarized as regional extent.
- It does **not** represent ice thickness, ridging, or tactical route guidance.
"""
)

st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Regional sea ice statistics are sourced from **NOAA/NSIDC Sea Ice Index (G02135), Version 4**
(Regional Daily Data spreadsheets) made available via NOAA@NSIDC public distribution.

This dashboard is for situational awareness only and does not replace official ice services,
onboard navigation systems, or the judgment of vessel masters.
"""
)
