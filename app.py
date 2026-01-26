import streamlit as st
import pandas as pd
import datetime
import numpy as np

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# + Arctic Decision Checklist (10)
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
# Operational normalization references (situational awareness scaling)
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
# Arctic Decision Checklist (10)
# -----------------------------------------------------
CHECKLIST = [
    {
        "id": 1,
        "q": "지금 이 이야기는 데이터인가, 분위기인가?",
        "confirm": "최신 관측 자료·장기 시계열·오차 범위가 제시되는가?",
        "caution": "“이미 열렸다”, “곧 된다” 같은 단정형 표현",
        "critical": True,
    },
    {
        "id": 2,
        "q": "“열렸다”면, 어떤 조건에서 열렸는가?",
        "confirm": "계절·지역·연도별 변동성, 재결빙 가능성이 포함되는가?",
        "caution": "특정 사례를 전체로 일반화",
        "critical": False,
    },
    {
        "id": 3,
        "q": "관측 공백은 어디에 있는가?",
        "confirm": "위성/현장 관측 사각지대, 겨울철 데이터 부족이 명시되는가?",
        "caution": "공백을 성과 전망으로 덮는 설명",
        "critical": True,
    },
    {
        "id": 4,
        "q": "모델의 불확실성은 공개되었는가?",
        "confirm": "가정, 민감도, 신뢰구간, 대체 시나리오가 함께 제시되는가?",
        "caution": "단일 예측값만 제시",
        "critical": True,
    },
    {
        "id": 5,
        "q": "실패 시 누가 책임지는가?",
        "confirm": "책임 주체·중단 기준(Stop rule)·철수 비용이 명확한가?",
        "caution": "책임이 “시장/환경”으로 흐려지는 구조",
        "critical": True,
    },
    {
        "id": 6,
        "q": "이 결정의 리스크 상한선(cap)은 얼마인가?",
        "confirm": "최악의 경우 손실 범위(상한)가 숫자로 명시되는가?",
        "caution": "수익만 강조하고 손실 상한이 없음",
        "critical": True,
    },
    {
        "id": 7,
        "q": "주권·안보·규범과 충돌 지점은 없는가?",
        "confirm": "연안국 권리, 국제법, 안보 민감성이 검토되었는가?",
        "caution": "기술·상업 논리로 정치·안보를 우회",
        "critical": True,
    },
    {
        "id": 8,
        "q": "단독 행동인가, 사안별 연합인가?",
        "confirm": "관측·안전·환경·표준별 협력 구조가 설계되었는가?",
        "caution": "단일 동맹 편승 또는 상징적 참여",
        "critical": False,
    },
    {
        "id": 9,
        "q": "지금은 행동의 순간인가, 유보의 순간인가?",
        "confirm": "추가 관측으로 불확실성을 줄일 수 있는가?",
        "caution": "“늦으면 끝”이라는 압박",
        "critical": True,
    },
    {
        "id": 10,
        "q": "이 판단은 10년 뒤에도 설명 가능한가?",
        "confirm": "오늘의 근거가 미래에도 재현/설명 가능한가?",
        "caution": "당시 유행한 서사에만 의존",
        "critical": True,
    },
]


# -----------------------------------------------------
# Sidebar (mobile-first)
# -----------------------------------------------------
st.sidebar.title("POLAR CUDA")
st.sidebar.caption("Cryospheric Unified Decision Assistant")

region = st.sidebar.selectbox("Region", REGIONS, index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Mode: Situational Awareness (Non-directive)")


# -----------------------------------------------------
# Main tabs
# -----------------------------------------------------
tab_dashboard, tab_check, tab_about, tab_definition, tab_logo = st.tabs(
    ["🧭 Dashboard", "✅ Decision Checklist", "📄 About (IMO/Gov)", "📚 Formal Definition", "🎨 Logo/Icon Concept"]
)

# =====================================================
# TAB 1: Dashboard
# =====================================================
with tab_dashboard:
    st.title("🧊 POLAR CUDA")
    st.caption("Cryospheric Unified Decision Assistant")
    st.caption(f"Today (local): {today}")
    st.caption(f"Region: {region}")
    st.markdown("---")

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

    winter_max, summer_min = REGION_CLIMATOLOGY[region]
    denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-9

    risk_index = round(
        float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100)),
        1
    )

    status, color = classify_status(risk_index)

    st.subheader("Regional Navigation Risk (Status-Based)")
    st.markdown(f"### {color} **{status}**")
    st.metric("Risk Index", f"{risk_index} / 100")
    st.progress(int(risk_index))

    st.markdown(
        """
**Operational Interpretation (Non-Directive)**  
This indicator supports situational awareness and informed judgment.  
It does **not** provide route commands and does **not** replace official ice services, onboard systems, or vessel master judgment.
"""
    )

# =====================================================
# TAB 2: Decision Checklist (10)
# =====================================================
with tab_check:
    st.header("북극 판단 체크리스트 10 (Decision Layer)")
    st.caption("핵심: 늦는 것이 아니라, 불확실한데도 ‘하는 척’하는 것이 가장 위험합니다.")
    st.markdown("---")

    st.subheader("Checklist 입력")
    st.caption("각 항목을 ‘이번 의사결정에서 충족되었는가?’ 기준으로 체크하세요.")

    answers = {}
    critical_fail = []

    for item in CHECKLIST:
        with st.expander(f"{item['id']}. {item['q']}", expanded=False):
            st.markdown(f"**확인:** {item['confirm']}")
            st.markdown(f"**경계:** {item['caution']}")
            key = f"chk_{item['id']}"
            answers[item["id"]] = st.checkbox("충족됨 (Yes)", key=key)

    # Scoring
    total = len(CHECKLIST)
    yes = sum(1 for k in answers if answers[k])
    score = round(100 * yes / total, 0)

    # critical fails
    for item in CHECKLIST:
        if item["critical"] and not answers[item["id"]]:
            critical_fail.append(item["id"])

    st.markdown("---")
    st.subheader("Decision Readiness (준비도)")

    colA, colB = st.columns(2)
    with colA:
        st.metric("Checklist Score", f"{int(score)} / 100")
        st.progress(int(score))
    with colB:
        if len(critical_fail) >= 2:
            st.markdown("### ⛔ **HOLD (유보 권고)**")
            st.caption(f"Critical 항목 미충족: {', '.join(map(str, critical_fail))}")
        elif len(critical_fail) == 1:
            st.markdown("### ⚠️ **CAUTION (조건부 진행)**")
            st.caption(f"Critical 항목 미충족: {', '.join(map(str, critical_fail))}")
        else:
            st.markdown("### ✅ **PROCEED (진행 가능)**")
            st.caption("Critical 항목이 모두 충족되었습니다.")

    st.markdown(
        """
**한 줄 요약**  
북극에서 가장 위험한 선택은 ‘늦는 것’이 아니라, **불확실한데도 모두가 하는 척하는 것**입니다.  
**판단을 멈출 줄 아는 능력**이 북극에서 가장 강한 힘입니다.
"""
    )

# =====================================================
# TAB 3: About (IMO/Gov)
# =====================================================
with tab_about:
    st.header("About – POLAR CUDA (IMO/Government Style)")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a decision-support framework
designed to enhance situational awareness for operations in polar and ice-affected waters.

The system integrates publicly available cryospheric datasets into a unified, interpretable
status-based indicator. It supports informed operational judgment while preserving human
authority, responsibility, and legal accountability.

POLAR CUDA is **non-directive**: it does not provide tactical route guidance and does not
replace official ice services, onboard navigation systems, or vessel master judgment.
"""
    )

# =====================================================
# TAB 4: Formal Definition (paper/white paper)
# =====================================================
with tab_definition:
    st.header("Formal Definition – Academic / White Paper")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a modular decision-support system
that converts multi-source cryospheric observations into a unified, interpretable indicator for
situational awareness in polar operations.

The framework emphasizes transparency, explainability, robustness to data variability, and
explicit separation between **situational awareness** and **directive navigation**.
"""
    )

# =====================================================
# TAB 5: Logo/Icon concept
# =====================================================
with tab_logo:
    st.header("Logo / Icon Concept – Designer Brief")
    st.markdown(
        """
**Concept**: *When ice data becomes decision awareness.*

**Visual keywords**: Minimal, instrument-like, calm, authoritative, non-alarmist.  
**Icon**: Half-dial / gauge arc + subtle polar/grid motif.  
**Avoid**: Weather-app look, emergency alert look, gaming UI.
"""
    )

# -----------------------------------------------------
# Footer: Data source & legal notice
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice (NOAA/NSIDC Open Data)**  
Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
and distributed under NOAA/NSIDC open data access principles.

This application provides **situational awareness only** and does not replace official ice services,
onboard navigation systems, or the judgment of vessel masters. Final operational decisions remain the
responsibility of operators and vessel masters.
"""
)
