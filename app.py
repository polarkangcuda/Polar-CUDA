import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
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
# Regional climatological reference ranges
# (winter_max, summer_min)
# Operational normalization references for situational awareness
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
# Load NSIDC Sea Ice Index v4 (robust & fail-safe)
# -----------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # Detect date column
    date_col = None
    for cand in ["date", "datetime", "time"]:
        if cand in df.columns:
            date_col = cand
            break

    if date_col is None:
        if all(c in df.columns for c in ["year", "month", "day"]):
            df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
            date_col = "date"
        else:
            return None, "Date column could not be detected."

    # Detect extent column
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break

    if extent_col is None:
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
                extent_col = col
                break

    if extent_col is None:
        return None, "Extent column could not be detected."

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")

    df = df.dropna(subset=["date", "extent"])
    df = df.sort_values("date").reset_index(drop=True)

    return df, None


# -----------------------------------------------------
# Risk status classification
# -----------------------------------------------------
def classify_status(value: float):
    if value < 30:
        return "LOW", "🟢"
    if value < 50:
        return "MODERATE", "🟡"
    if value < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"


# -----------------------------------------------------
# Arctic Decision Checklist (10)
# -----------------------------------------------------
CHECKLIST = [
    {
        "id": 1,
        "question": "Is this assessment based on data or narrative momentum?",
        "confirm": "Are recent observations, long-term time series, and uncertainty ranges provided?",
        "warning": "Definitive claims such as 'already open' or 'soon accessible'.",
        "critical": True,
    },
    {
        "id": 2,
        "question": "If it is said to be 'open', under what conditions?",
        "confirm": "Seasonal, regional, and interannual variability are explicitly stated.",
        "warning": "Generalizing a single event to the entire Arctic.",
        "critical": False,
    },
    {
        "id": 3,
        "question": "Where are the observation gaps?",
        "confirm": "Blind spots in satellite or in-situ data are acknowledged.",
        "warning": "Covering gaps with optimistic projections.",
        "critical": True,
    },
    {
        "id": 4,
        "question": "Is model uncertainty explicitly disclosed?",
        "confirm": "Assumptions, sensitivities, and alternative scenarios are described.",
        "warning": "Single deterministic forecast presented as certainty.",
        "critical": True,
    },
    {
        "id": 5,
        "question": "Who bears responsibility if the operation fails?",
        "confirm": "Clear responsibility, stop rules, and withdrawal costs are defined.",
        "warning": "Responsibility diffused to 'the market' or 'the environment'.",
        "critical": True,
    },
    {
        "id": 6,
        "question": "What is the risk cap of this decision?",
        "confirm": "Worst-case loss or damage thresholds are specified.",
        "warning": "Upside emphasized without downside limits.",
        "critical": True,
    },
    {
        "id": 7,
        "question": "Are there conflicts with sovereignty, security, or norms?",
        "confirm": "Coastal state rights and international law are considered.",
        "warning": "Bypassing political or security issues through technical logic.",
        "critical": True,
    },
    {
        "id": 8,
        "question": "Is this unilateral action or issue-based cooperation?",
        "confirm": "Structures for cooperation on safety, environment, and standards exist.",
        "warning": "Symbolic participation without operational substance.",
        "critical": False,
    },
    {
        "id": 9,
        "question": "Is this the moment to act or to pause?",
        "confirm": "Additional observations could reduce uncertainty.",
        "warning": "Pressure framed as 'now or never'.",
        "critical": True,
    },
    {
        "id": 10,
        "question": "Will this decision remain defensible in ten years?",
        "confirm": "Evidence and assumptions are reproducible and explainable.",
        "warning": "Reliance on contemporary narratives alone.",
        "critical": True,
    },
]


# -----------------------------------------------------
# Sidebar
# -----------------------------------------------------
st.sidebar.title("POLAR CUDA")
st.sidebar.caption("Cryospheric Unified Decision Assistant")

region = st.sidebar.selectbox("Region", REGIONS)
st.sidebar.markdown("---")
st.sidebar.caption("Mode: Situational Awareness (Non-Directive)")


# -----------------------------------------------------
# Tabs
# -----------------------------------------------------
tab_dashboard, tab_checklist, tab_about, tab_definition, tab_logo = st.tabs(
    [
        "🧭 Dashboard",
        "✅ Decision Checklist",
        "📄 About (IMO/Government)",
        "📚 Formal Definition",
        "🎨 Logo / Icon Concept",
    ]
)

# =====================================================
# TAB 1: Dashboard
# =====================================================
with tab_dashboard:
    st.title("🧊 POLAR CUDA")
    st.caption("Cryospheric Unified Decision Assistant")
    st.caption(f"Today (local): {today}")
    st.caption(f"Selected Region: {region}")
    st.markdown("---")

    df, err = load_nsidc_v4()
    if df is None or df.empty:
        st.error("Unable to load NSIDC Sea Ice Index v4 data.")
        if err:
            st.caption(err)
        st.stop()

    df_valid = df[df["date"].dt.date <= today]
    latest = df_valid.iloc[-1]

    extent_today = float(latest["extent"])
    data_date = latest["date"].date()

    st.caption(f"NSIDC Data Date (UTC): {data_date}")

    winter_max, summer_min = REGION_CLIMATOLOGY[region]
    denom = max(winter_max - summer_min, 1e-9)

    risk_index = round(
        float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100)),
        1,
    )

    status, color = classify_status(risk_index)

    st.subheader("Regional Navigation Risk (Status-Based)")
    st.markdown(f"### {color} **{status}**")
    st.metric("Risk Index", f"{risk_index} / 100")
    st.progress(int(risk_index))

    st.markdown(
        """
**Operational Interpretation (Non-Directive)**  
This indicator supports situational awareness and informed judgment only.  
It does not provide route commands and does not replace official ice services,
onboard navigation systems, or vessel master judgment.
"""
    )

# =====================================================
# TAB 2: Decision Checklist
# =====================================================
with tab_checklist:
    st.header("Arctic Decision Checklist (10)")
    st.caption(
        "Core principle: In the Arctic, acting under false certainty is more dangerous than delaying action."
    )
    st.markdown("---")

    answers = {}
    critical_failures = []

    for item in CHECKLIST:
        with st.expander(f"{item['id']}. {item['question']}"):
            st.markdown(f"**Verify:** {item['confirm']}")
            st.markdown(f"**Red flag:** {item['warning']}")
            answers[item["id"]] = st.checkbox("Satisfied", key=f"chk_{item['id']}")

    yes_count = sum(1 for v in answers.values() if v)
    score = round(100 * yes_count / len(CHECKLIST))

    for item in CHECKLIST:
        if item["critical"] and not answers[item["id"]]:
            critical_failures.append(item["id"])

    st.markdown("---")
    st.subheader("Decision Readiness")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Checklist Score", f"{score} / 100")
        st.progress(score)
    with col2:
        if len(critical_failures) >= 2:
            st.markdown("### ⛔ HOLD")
            st.caption(f"Critical items unmet: {critical_failures}")
        elif len(critical_failures) == 1:
            st.markdown("### ⚠️ CAUTION")
            st.caption(f"Critical item unmet: {critical_failures}")
        else:
            st.markdown("### ✅ PROCEED")
            st.caption("All critical criteria satisfied.")

    st.markdown(
        """
**Summary**  
The strongest capability in Arctic operations is the ability to pause judgment
when uncertainty remains unresolved.
"""
    )

# =====================================================
# TAB 3: About
# =====================================================
with tab_about:
    st.header("About – POLAR CUDA")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a non-directive
decision-support framework designed to enhance situational awareness
in polar and ice-affected waters.

It integrates open-access cryospheric datasets into an interpretable,
status-based indicator while preserving human authority, responsibility,
and legal accountability.
"""
    )

# =====================================================
# TAB 4: Formal Definition
# =====================================================
with tab_definition:
    st.header("Formal Definition")
    st.markdown(
        """
POLAR CUDA is a modular decision-support system that translates multi-source
cryospheric observations into a unified, interpretable situational indicator.

The framework explicitly separates situational awareness from directive
navigation and prioritizes transparency, explainability, and operational conservatism.
"""
    )

# =====================================================
# TAB 5: Logo / Icon Concept
# =====================================================
with tab_logo:
    st.header("Logo / Icon Concept")
    st.markdown(
        """
**Concept:** When ice data becomes decision awareness.  
**Style:** Instrument-like, calm, non-alarmist.  
**Icon:** Half-dial gauge with subtle polar motif.  
**Avoid:** Emergency alerts, gaming UI, military command visuals.
"""
    )

# -----------------------------------------------------
# Footer
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**  
Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
under NOAA open data principles.

This application provides situational awareness only and does not replace
official ice services, onboard navigation systems, or the judgment of vessel masters.
"""
)
