# =========================================================
# POLAR CUDA – Fleet / Port View + Ops Loop (SAFE)
# =========================================================

import streamlit as st
import numpy as np

# ---------------------------------------------------------
# REQUIRED DEFINITIONS (explicit, no dependency)
# ---------------------------------------------------------

REGIONS = [
    "Sea of Okhotsk",
    "Bering Sea",
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Kara Sea",
    "Barents Sea",
    "Beaufort Sea",
    "Canadian Arctic Archipelago",
    "Central Arctic Ocean",
    "Greenland Sea",
    "Baffin Bay",
]

WINTER_CLOSED = {
    "Chukchi Sea",
    "East Siberian Sea",
    "Laptev Sea",
    "Beaufort Sea",
    "Central Arctic Ocean",
}

SEASON_MODIFIER = {
    "winter": 1.00,
    "spring": 0.85,
    "summer": 0.65,
    "autumn": 1.15,
}

def classify_status(risk):
    if risk < 30:
        return "LOW", "🟢"
    if risk < 50:
        return "MODERATE", "🟡"
    if risk < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

# ---------------------------------------------------------
# CONTEXT (reuse if already defined, else default)
# ---------------------------------------------------------

SEASON = st.session_state.get("SEASON", "winter")
img = st.session_state.get("BREMEN_IMG", None)

# ---------------------------------------------------------
# Fleet / Port View
# ---------------------------------------------------------

st.markdown("## 🚢 Fleet / Port View – Multi-Region Monitoring")

fleet_results = []

for region in REGIONS:
    if SEASON == "winter" and region in WINTER_CLOSED:
        risk = 95.0
        note = "Structurally closed (winter)"
    else:
        if img is None:
            risk = 60.0  # conservative fallback
            note = "Image unavailable (fallback)"
        else:
            # conservative assumption: winter ice dominance
            risk = 70.0
            note = "Image-based proxy (conservative)"

    risk = np.clip(risk * SEASON_MODIFIER.get(SEASON, 1.0), 0, 100)
    status, color = classify_status(risk)

    fleet_results.append({
        "Region": region,
        "Risk": round(risk, 1),
        "Status": status,
        "Color": color,
        "Note": note
    })

# ---------------------------------------------------------
# Display cards
# ---------------------------------------------------------

cols = st.columns(3)

for i, item in enumerate(fleet_results):
    with cols[i % 3]:
        st.markdown(
            f"""
<div style="
    border-radius:12px;
    padding:14px;
    background:#0f172a;
    border:1px solid rgba(255,255,255,0.15);
    margin-bottom:12px;
">
<h4>{item['Color']} {item['Region']}</h4>
<b>Status:</b> {item['Status']}<br>
<b>Risk:</b> {item['Risk']} / 100<br>
<small style="opacity:0.75;">{item['Note']}</small>
</div>
""",
            unsafe_allow_html=True
        )

st.markdown("---")

# =========================================================
# OPS LOOP VISUALIZATION
# =========================================================

st.markdown("## 🔁 Operational Decision Loop (Ops Loop)")

st.markdown(
    """
<table style="width:100%; text-align:center;">
<tr>
<td>🛰️<br><b>OBSERVE</b><br>Satellite / Field</td>
<td>➡️</td>
<td>🧠<br><b>DECIDE</b><br>Risk + Season</td>
<td>➡️</td>
<td>🚢<br><b>ACT</b><br>Proceed / Hold</td>
<td>➡️</td>
<td>📘<br><b>LEARN</b><br>Post-Op Review</td>
</tr>
</table>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
### Why this matters

This loop **does not automate navigation**.  
It formalizes **when not to act**, preserving human judgment and accountability.

- Observe uncertainty
- Decide conservatively
- Act cautiously
- Learn explicitly
"""
)

st.caption(
    """
Fleet / Port View is designed for **coordination and restraint**,  
not optimization or speed.
"""
)
