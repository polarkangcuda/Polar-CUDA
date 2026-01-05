import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# (Regional Navigation Risk – Situational Awareness)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Cryospheric Unified Decision Assistant",
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
# Regional climatological range (winter_max, summer_min)
# NOTE: These are operational normalization references
# (not a scientific climatology claim). Used for
# situational awareness scaling across regions.
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
# NSIDC v4 Sea Ice Index loader (ULTRA SAFE)
# - Avoids StopIteration / KeyError
# - Works even if columns vary
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # Date column detection
    date_col = None
    for cand in ["date", "datetime", "time"]:
        if cand in df.columns:
            date_col = cand
            break

    # Fallback: year/month/day
    if date_col is None:
        if all(c in df.columns for c in ["year", "month", "day"]):
            df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
            date_col = "date"
        else:
            return None, f"Unable to detect date column. Columns: {list(df.columns)}"

    # Extent column detection
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
        return None, f"Unable to detect extent column. Columns: {list(df.columns)}"

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")

    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date").reset_index(drop=True)

    return df, None


# -----------------------------------------------------
# Helper: status classification
# -----------------------------------------------------
def classify_status(risk_index: float):
    if risk_index < 30:
        return "LOW", "🟢"
    if risk_index < 50:
        return "MODERATE", "🟡"
    if risk_index < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"


# -----------------------------------------------------
# Sidebar: identity + region selector
# -----------------------------------------------------
st.sidebar.title("POLAR CUDA")
st.sidebar.caption("Cryospheric Unified Decision Assistant")
region = st.sidebar.selectbox("Region", REGIONS, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Mode:** Situational Awareness")
st.sidebar.markdown("**Not:** Navigational command system")

# -----------------------------------------------------
# Main tabs
# -----------------------------------------------------
tab_dashboard, tab_about, tab_definition, tab_logo = st.tabs(
    ["🧭 Dashboard", "📄 About (IMO/Gov)", "📚 Formal Definition", "🎨 Logo/Icon Concept"]
)

# =====================================================
# TAB 1: Dashboard
# =====================================================
with tab_dashboard:
    st.title("🧊 POLAR CUDA")
    st.caption("Cryospheric Unified Decision Assistant")
    st.caption(f"Today: {today}")

    # Load data
    df, err = load_nsidc_v4()
    if df is None or df.empty:
        st.error("Unable to load NSIDC v4 sea ice data.")
        if err:
            st.caption(err)
        st.stop()

    df_valid = df[df["date"].dt.date <= today]
    if df_valid.empty:
        st.error("No valid NSIDC data available up to today.")
        st.stop()

    latest = df_valid.iloc[-1]
    extent_today = float(latest["extent"])
    data_date = latest["date"].date()

    st.caption(f"NSIDC Data Date (UTC): {data_date}")
    st.caption(f"Selected Region: {region}")

    st.markdown("---")

    # Risk computation (seasonal normalization proxy)
    winter_max, summer_min = REGION_CLIMATOLOGY[region]
    denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-9

    risk_index = round(
        float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100)),
        1
    )

    status, color = classify_status(risk_index)

    st.subheader("Regional Navigation Risk (Status-Based)")

    st.markdown(
        f"""
### {color} **{status}**
**Risk Index:** {risk_index} / 100
"""
    )
    st.progress(int(risk_index))

    st.markdown(
        f"""
**Operational Interpretation (Non-Directive)**

This indicator expresses **relative seasonal ice severity** for **{region}**
using a **regional normalization range** (winter–summer reference).

It is intended to support **situational awareness** and **informed judgment**.
It does **not** provide tactical route guidance, and it does **not**
replace official ice services, onboard navigation systems, or vessel master judgment.
"""
    )

# =====================================================
# TAB 2: About (IMO/Gov)
# =====================================================
with tab_about:
    st.header("About – POLAR CUDA (IMO/Government Style)")

    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a decision-support framework
designed to enhance situational awareness for navigation and operations in polar and
ice-affected waters.

The system integrates publicly available cryospheric datasets—such as satellite-derived
sea ice extent—into a unified, regionally normalized risk index. By translating complex
ice conditions into an intuitive status-based indicator, POLAR CUDA supports informed
operational judgment without prescribing actions or replacing official ice services.

POLAR CUDA is intended to complement existing navigational systems by providing an
additional layer of contextual understanding, particularly for seasonal variability and
regional ice regimes. It does not constitute navigational guidance and does not supersede
the authority or responsibility of vessel masters, operators, or national ice services.

All data used within POLAR CUDA are sourced from open-access datasets distributed under
established public data policies.
"""
    )

# =====================================================
# TAB 3: Formal Definition (paper/white paper)
# =====================================================
with tab_definition:
    st.header("Formal Definition – Academic / White Paper")

    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is defined as a modular
decision-support system that converts multi-source cryospheric observations into a unified,
interpretable risk metric for polar navigation and operations.

The framework operates by normalizing large-scale cryospheric indicators—such as pan-Arctic
sea ice extent—against region-specific seasonal reference ranges, thereby contextualizing
seasonal severity relative to local ice regimes. This approach emphasizes *relative operational
risk* rather than absolute ice presence, enabling cross-regional comparison without requiring
high-resolution tactical data.

POLAR CUDA is explicitly designed as an *assistant* rather than a directive system. Its outputs
are interpretive in nature, supporting human decision-making while preserving operational
responsibility and legal accountability at the operator level.

The system prioritizes transparency, explainability, and robustness to data format variability,
making it suitable for operational experimentation and policy-oriented risk communication.
"""
    )

# =====================================================
# TAB 4: Logo/Icon concept
# =====================================================
with tab_logo:
    st.header("Logo / Icon Concept – Designer Brief")

    st.markdown(
        """
**Concept Statement**  
*POLAR CUDA visualizes the moment where ice data becomes decision awareness.*

**Design Keywords**  
- Minimal  
- Instrument-like (not decorative)  
- Calm, authoritative, non-alarmist  
- Operational rather than scientific  

**Icon Concept**  
- A **half-dial / gauge arc** suggesting situational status rather than control  
- Central element: a **simple ice or hexagonal grid motif**, abstract not literal  
- Subtle directional cue (northward or polar-centered)  
- Color logic aligned with risk states (green → yellow → orange → red), muted not saturated  

**Avoid**  
- Weather app look  
- Emergency alert look  
- Gaming UI  
- Military command interface  

**One-line instruction**  
“This is a tool you glance at before deciding — not something that tells you what to do.”
"""
    )

# -----------------------------------------------------
# Footer: Data source & legal notice (always visible)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice (NOAA/NSIDC Open Data)**

Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
(derived from satellite observations including AMSR2) and distributed under NOAA open data principles.

This application provides **situational awareness only** and does not replace official ice services,
onboard navigation systems, or the judgment of vessel masters. Final operational decisions remain the
responsibility of operators and vessel masters.
"""
)
