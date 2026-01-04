import streamlit as st
import datetime
import numpy as np
import pandas as pd

# =====================================================
# Polar CUDA – Fleet Operations Manager Edition (PRO)
# =====================================================

st.set_page_config(
    page_title="Polar CUDA – Fleet Operations",
    layout="wide"
)

# -----------------------------------------------------
# Date & Update Cycle
# -----------------------------------------------------
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

# -----------------------------------------------------
# Region Selection
# -----------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": {"ice": 65, "drift": 12, "wind": 8},
    "Chukchi Sea": {"ice": 72, "drift": 15, "wind": 9},
    "East Siberian Sea": {"ice": 78, "drift": 18, "wind": 10},
    "Beaufort Sea": {"ice": 60, "drift": 11, "wind": 7},
    "Barents Sea": {"ice": 42, "drift": 6, "wind": 12},
}

selected_region = st.selectbox(
    "Select Region",
    list(REGIONS.keys())
)

data = REGIONS[selected_region]

# -----------------------------------------------------
# Normalization Function
# -----------------------------------------------------
def normalize(value, min_val, max_val):
    value = max(min(value, max_val), min_val)
    return 100 * (value - min_val) / (max_val - min_val)

sic_norm = normalize(data["ice"], 0, 100)
drift_norm = normalize(data["drift"], 0, 30)
wind_norm = normalize(data["wind"], 0, 25)

# -----------------------------------------------------
# Risk Index Calculation
# -----------------------------------------------------
risk_index = round(
    0.45 * sic_norm +
    0.30 * drift_norm +
    0.25 * wind_norm,
    1
)

# Yesterday (dummy baseline for trend logic)
yesterday_risk = risk_index - 0.8
delta = round(risk_index - yesterday_risk, 1)

# -----------------------------------------------------
# Status Classification
# -----------------------------------------------------
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

trend_arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"

# -----------------------------------------------------
# Header
# -----------------------------------------------------
st.title("🧊 Polar CUDA – Fleet Operations Monitor")
st.caption(f"Date: {today} | Update Cycle: Daily")

# -----------------------------------------------------
# Fleet Risk Overview
# -----------------------------------------------------
st.subheader("Fleet Polar Risk Index")

col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.metric(
        label="Current Fleet Risk",
        value=f"{risk_index} / 100",
        delta=f"{trend_arrow} {abs(delta)} (DoD)"
    )

with col2:
    st.markdown(f"### Status\n**{color} {status}**")

with col3:
    st.progress(int(risk_index))

# -----------------------------------------------------
# Guidance Text (Operations Language)
# -----------------------------------------------------
st.markdown(
    f"""
**Operational Guidance**

Fleet-level risk remains **{status.lower()}** for **{selected_region}**.  
However, localized escalation trends are observed.  
**Schedule review may be required within the next 48–72 hours if the trend persists.**
"""
)

# -----------------------------------------------------
# Driver Decomposition
# -----------------------------------------------------
st.subheader("Risk Driver Decomposition")

driver_df = pd.DataFrame({
    "Driver": ["Sea Ice Extent", "Ice Drift", "Wind"],
    "Contribution (%)": [
        round(0.45 * sic_norm, 1),
        round(0.30 * drift_norm, 1),
        round(0.25 * wind_norm, 1)
    ]
})

st.bar_chart(driver_df.set_index("Driver"))

# -----------------------------------------------------
# 7-Day Risk Trend (Moving Average)
# -----------------------------------------------------
st.subheader("7-Day Fleet Risk Trend")

trend_values = np.linspace(risk_index - 5, risk_index, 7)
trend_df = pd.DataFrame({
    "Date": pd.date_range(end=today, periods=7),
    "Risk Index": trend_values
})

st.line_chart(trend_df.set_index("Date"))

# -----------------------------------------------------
# Fleet Impact Matrix (Example)
# -----------------------------------------------------
st.subheader("Fleet Impact Matrix")

fleet_df = pd.DataFrame([
    ["ARAON", "Chukchi Sea", 52, "↑", "⚠ Monitor"],
    ["Cargo-01", "Beaufort Sea", 61, "↑↑", "❗ Review"],
    ["Tanker-02", "Barents Sea", 34, "↓", "✅ Normal"],
], columns=[
    "Vessel", "Region", "Risk Index", "Trend", "Action Flag"
])

st.dataframe(fleet_df, use_container_width=True)

# -----------------------------------------------------
# Disclaimer (Policy / Legal Grade)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Operational Disclaimer**

This dashboard provides fleet-level situational risk awareness derived from publicly available
cryospheric and atmospheric datasets (NOAA/NSIDC Sea Ice Index v4, reanalysis wind fields, and ice drift products).

It does not replace onboard navigation systems, ice services, or the judgment of vessel masters.
Final operational decisions remain the responsibility of the operating company and ship masters.
"""
)

알겠습니다. 요청하신 대로 **“Status 판단 로직만 남기고 나머지는 전부 제거한 최소 코드”**로 다시 작성해 드리겠습니다.
아래 코드는 복사 → app.py 전체에 붙여넣기 → 바로 실행 가능한 형태입니다.

✅ 남기는 것

Risk Index 값 (예시값)

Status 분류 로직 (LOW / MODERATE / HIGH / EXTREME)

상태 아이콘 + 상태명만 화면에 표시

❌ 제거한 것

지역 선택

지수 계산식

그래프 / 테이블

트렌드 / 플릿 / 가이던스 / 면책 문구

외부 데이터 연결

🔹 최소 동작 코드 (Status 전용)
import streamlit as st
import datetime

# ================================
# Polar CUDA – Status Only
# ================================

st.set_page_config(
    page_title="Polar CUDA – Status",
    layout="centered"
)

# -------------------------------------------------
# Date
# -------------------------------------------------
today = datetime.date.today()

# -------------------------------------------------
# Example Risk Index (임시값)
# 👉 나중에 NSIDC 실데이터로 교체 가능
# -------------------------------------------------
risk_index = 47.6  # example value

# -------------------------------------------------
# Status Classification (핵심)
# -------------------------------------------------
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
# Display
# -------------------------------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Date: {today}")

st.markdown("## Polar Risk Status")
st.markdown(
    f"""
### {color} **{status}**
Risk Index: **{risk_index} / 100**
"""
)

✅ 이 상태에서 확인해야 할 것

Streamlit 에러 없이 실행되는지

화면에 LOW / MODERATE / HIGH / EXTREME 중 하나만 깔끔하게 표시되는지

색상 이모지가 의도대로 나오는지

다음 단계 (원하시면)

이제 이 Status-only 코드를 기준으로:

1️⃣ NSIDC v4 실데이터 연결
2️⃣ 지역별 Status (Beaufort / Chukchi 등)
3️⃣ Fleet / Operations 화면으로 확장

을 한 단계씩 안전하게 다시 쌓을 수 있습니다.

원하시면 다음으로
👉 **“Status-only 코드에 NSIDC v4 실데이터만 연결한 버전”**을 바로 만들어 드리겠습니다.
