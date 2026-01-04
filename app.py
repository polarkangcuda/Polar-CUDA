# =========================================================
# Polar CUDA – Semi-Circular Gauge (Matplotlib only)
# =========================================================

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import datetime

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Polar CUDA – Risk Gauge",
    layout="wide"
)

# -----------------------------
# Inputs (placeholder → real data later)
# -----------------------------
today = datetime.date.today()
risk_value = 47.6  # 0–100

# -----------------------------
# Gauge definition
# -----------------------------
zones = [
    (0, 25, "Extreme", "#c0392b"),
    (25, 45, "Fear", "#e67e22"),
    (45, 55, "Neutral", "#bdc3c7"),
    (55, 75, "Greed", "#7fb3d5"),
    (75, 100, "Extreme", "#2e86c1"),
]

# -----------------------------
# Create gauge figure
# -----------------------------
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_aspect("equal")
ax.axis("off")

theta = np.linspace(np.pi, 0, 500)

# Draw background arc
ax.plot(np.cos(theta), np.sin(theta), color="#eeeeee", linewidth=30)

# Draw colored zones
for start, end, label, color in zones:
    theta_zone = np.linspace(
        np.pi * (1 - start / 100),
        np.pi * (1 - end / 100),
        100
    )
    ax.plot(
        np.cos(theta_zone),
        np.sin(theta_zone),
        linewidth=30,
        color=color,
        solid_capstyle="butt"
    )

# Draw ticks
for v in [0, 25, 50, 75, 100]:
    angle = np.pi * (1 - v / 100)
    ax.text(
        0.85 * np.cos(angle),
        0.85 * np.sin(angle),
        f"{v}",
        ha="center",
        va="center",
        fontsize=10,
        color="#555"
    )

# Draw needle
needle_angle = np.pi * (1 - risk_value / 100)
ax.plot(
    [0, 0.75 * np.cos(needle_angle)],
    [0, 0.75 * np.sin(needle_angle)],
    color="black",
    linewidth=4
)

# Needle center
ax.scatter(0, 0, s=100, color="black")

# Value text
ax.text(
    0, -0.15,
    f"{risk_value:.0f}",
    ha="center",
    va="center",
    fontsize=28,
    fontweight="bold"
)

# Label
ax.text(
    0, 1.05,
    "Polar Risk Index",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold"
)

# -----------------------------
# Streamlit layout
# -----------------------------
st.title("🧊 Polar CUDA")
st.caption(f"Date: {today}")

col1, col2 = st.columns([2, 1])

with col1:
    st.pyplot(fig)

with col2:
    st.markdown("### Historical Context")
    st.markdown("**Previous close:** Fear (44)")
    st.markdown("**1 week ago:** Neutral (52)")
    st.markdown("**1 month ago:** Extreme (23)")
    st.markdown("**1 year ago:** Extreme (24)")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption(
    """
Data sources (planned): NOAA/NSIDC Sea Ice Index v4 (AMSR2),
wind reanalysis, ice drift products.

This index is provided for situational awareness only.
It does not constitute operational or navigational guidance.
"""
)
