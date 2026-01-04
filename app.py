import streamlit as st
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# Polar CUDA – Fleet Operations (NSIDC v4 + Gauge)
# =====================================================

st.set_page_config(
    page_title="Polar CUDA – Fleet Operations",
    layout="wide"
)

# -----------------------------------------------------
# Date
# -----------------------------------------------------
today = datetime.date.today()

# -----------------------------------------------------
# Region Selection (운영용 단순 가중치)
# -----------------------------------------------------
REGIONS = {
    "Entire Arctic (Pan-Arctic)": 1.00,
    "Chukchi Sea": 1.10,
    "East Siberian Sea": 1.15,
    "Beaufort Sea": 1.05,
    "Barents Sea": 0.90,
}

selected_region = st.selectbox(
    "Select Region",
    list(REGIONS.keys())
)

region_weight = REGIONS[selected_region]

# -----------------------------------------------------
# NSIDC v4 Sea Ice Extent (⭐ 단 한 줄 연결 ⭐)
# -----------------------------------------------------
NSIDC_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

df = pd.read_csv(NSIDC_URL)  # ← 이것이 실데이터 연결 "한 줄"

# v4 구조 대응
df.columns = [c.strip() for c in df.columns]
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[["date", "Extent"]].dropna().sort_values("date")

latest = df.iloc[-1]
extent_today = latest["Extent"]

# -----------------------------------------------------
# Risk Index (단순·설명 가능)
# 낮은 얼음 면적 = 높은 위험
# -----------------------------------------------------
risk_index = round(
    min(max((12 - extent_today) / 12 * 100 * region_weight, 0), 100),
    1
)

# -----------------------------------------------------
# Status Classification
# -----------------------------------------------------
if risk_index < 30:
    status = "LOW"
    color = "#2ecc71"
elif risk_index < 50:
    status = "MODERATE"
    color = "#f1c40f"
elif risk_index < 70:
    status = "HIGH"
    color = "#e67e22"
else:
    status = "EXTREME"
    color = "#e74c3c"

# -----------------------------------------------------
# 반원형 게이지 (Matplotlib)
# -----------------------------------------------------
def draw_gauge(value, status_label, color):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.set_aspect("equal")
    ax.axis("off")

    # 구간
    zones = [
        (0, 30, "#2ecc71"),
        (30, 50, "#f1c40f"),
        (50, 70, "#e67e22"),
        (70, 100, "#e74c3c"),
    ]

    # 반원
    for start, end, c in zones:
        theta = np.linspace(
            np.pi * (1 - start / 100),
            np.pi * (1 - end / 100),
            100
        )
        ax.plot(np.cos(theta), np.sin(theta), linewidth=30, color=c)

    # 바늘
    angle = np.pi * (1 - value / 100)
    ax.plot([0, 0.75 * np.cos(angle)],
            [0, 0.75 * np.sin(angle)],
            linewidth=4, color="black")
    ax.scatter(0, 0, s=80, color="black")

    # 숫자
    ax.text(0, -0.15, f"{value:.1f}",
            ha="center", va="center",
            fontsize=28, fontweight="bold")

    ax.text(0, 1.1, status_label,
            ha="center", va="center",
            fontsize=16, color=color, fontweight="bold")

    return fig

# -----------------------------------------------------
# UI
# -----------------------------------------------------
st.title("🧊 Polar CUDA – Fleet Operations Monitor")
st.caption(f"Date: {today}")
st.caption(f"Region: {selected_region}")
st.caption(f"NSIDC Sea Ice Extent (latest): {extent_today:.2f} million km²")

col1, col2 = st.columns([2, 1])

with col1:
    fig = draw_gauge(risk_index, status, color)
    st.pyplot(fig)

with col2:
    st.subheader("Operational Status")
    st.markdown(f"### **{status}**")
    st.markdown(f"Risk Index: **{risk_index} / 100**")

    st.markdown(
        """
**Operational Guidance**

This indicator provides fleet-level situational awareness.
Operational review is recommended if conditions trend upward.
"""
    )

# -----------------------------------------------------
# Legal / Data Attribution (중요)
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Attribution & Legal Notice**

Sea ice extent data are sourced from **NOAA/NSIDC Sea Ice Index Version 4**
(G02135, AMSR2), an official **NOAA Open Data** product.

These data are publicly available and may be used, redistributed,
and adapted in accordance with NOAA open data policies.

This dashboard is provided for situational awareness only and does not
constitute navigational or legal guidance. Final operational decisions
remain the responsibility of vessel operators and masters.
"""
)
