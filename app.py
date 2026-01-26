# =========================================================
# POLAR CUDA – Fleet / Port View + Ops Loop
# =========================================================

import streamlit as st
import numpy as np

st.markdown("## 🚢 Fleet / Port View – Multi-Region Monitoring")

# ---------------------------------------------------------
# Fleet monitoring regions (same as Level 3)
# ---------------------------------------------------------
FLEET_REGIONS = REGIONS  # reuse from Level 3

# ---------------------------------------------------------
# Compute risk for all regions
# ---------------------------------------------------------
fleet_results = []

for r in FLEET_REGIONS:
    if SEASON == "winter" and r in WINTER_CLOSED:
        risk = 95.0
        status, color = classify_status(risk)
        note = "Structurally closed (winter)"
    else:
        if img is None:
            continue
        open_ratio = compute_openability(img)
        base = (1 - open_ratio) * 100
        risk = np.clip(base * SEASON_MODIFIER[SEASON], 0, 100)
        status, color = classify_status(risk)
        note = f"Open-water proxy {open_ratio*100:.1f}%"

    fleet_results.append({
        "Region": r,
        "Risk": round(risk, 1),
        "Status": status,
        "Color": color,
        "Note": note
    })

# ---------------------------------------------------------
# Display as cards
# ---------------------------------------------------------
cols = st.columns(3)

for idx, item in enumerate(fleet_results):
    with cols[idx % 3]:
        st.markdown(
            f"""
<div style="
    border-radius:12px;
    padding:14px;
    background:#0f172a;
    border:1px solid rgba(255,255,255,0.12);
">
<h4>{item['Color']} {item['Region']}</h4>
<b>Status:</b> {item['Status']}<br>
<b>Risk:</b> {item['Risk']} / 100<br>
<small>{item['Note']}</small>
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
<td>🧠<br><b>DECIDE</b><br>Risk Index + Season</td>
<td>➡️</td>
<td>🚢<br><b>ACT</b><br>Proceed / Hold / Retreat</td>
<td>➡️</td>
<td>📘<br><b>LEARN</b><br>Post-Operation Review</td>
</tr>
</table>
""",
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Decision guidance (non-directive)
# ---------------------------------------------------------
st.markdown(
    """
### Decision Guidance (Non-Directive)

- **OBSERVE**  
  Bremen AMSR2 imagery, seasonal context, structural closures

- **DECIDE**  
  Conservative risk interpretation  
  → “Can uncertainty be reduced by waiting?”

- **ACT**  
  Not a command:  
  **Proceed / Hold / Defer / Retreat**

- **LEARN**  
  Archive outcomes to refine future thresholds  
  (human-in-the-loop by design)

This loop formalizes **judgment**, not automation.
"""
)

st.markdown("---")

# =========================================================
# Port / Fleet Manager Note
# =========================================================
st.caption(
    """
**Fleet / Port Manager Note**

This view supports **coordination across vessels and ports** by
highlighting regions where operational decisions should be:
- Deferred
- Escalated for human review
- Excluded due to structural winter closure

POLAR CUDA does not issue navigational commands.
It structures **when to stop, wait, or reconsider**.
"""
)
