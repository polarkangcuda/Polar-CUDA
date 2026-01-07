import streamlit as st
import numpy as np
import datetime
from PIL import Image
import requests
from io import BytesIO
import math

# =====================================================
# POLAR CUDA – Operational Risk Infrastructure (v2)
# Cryospheric Unified Decision Assistant
# Observe → Assess → Decide → Act → Learn
# =====================================================

st.set_page_config(page_title="POLAR CUDA – Ops Risk", layout="centered")

TODAY = datetime.date.today()

# -----------------------------------------------------
# Regions as polar-sector ROI (image-based proxy)
# angle: clockwise from Greenwich meridian (approx.)
# r: fraction of image half-size (approx.)
# NOTE: This is an operational approximation, not an authoritative geospatial mask.
# -----------------------------------------------------
REGION_SECTORS = {
    "Entire Arctic (Pan-Arctic)": dict(theta=(0, 360), r=(0.18, 0.93)),
    "Chukchi Sea": dict(theta=(210, 250), r=(0.48, 0.80)),
    "Beaufort Sea": dict(theta=(250, 300), r=(0.48, 0.80)),
    "Laptev Sea": dict(theta=(90, 140), r=(0.48, 0.80)),
    "East Siberian Sea": dict(theta=(140, 200), r=(0.48, 0.80)),
    "Kara Sea": dict(theta=(40, 80), r=(0.48, 0.80)),
    "Barents Sea": dict(theta=(330, 360), r=(0.48, 0.80)),
    "Greenland Sea": dict(theta=(300, 330), r=(0.48, 0.80)),
    "Baffin Bay": dict(theta=(280, 320), r=(0.52, 0.86)),
    "Lincoln Sea": dict(theta=(0, 40), r=(0.22, 0.48)),
    "Bering Sea": dict(theta=(200, 230), r=(0.70, 0.98)),
}

# -----------------------------------------------------
# Data loader: Bremen AMSR2 PNG (no extra deps)
# -----------------------------------------------------
@st.cache_data(ttl=1800)
def load_bremen_png():
    url = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    r = requests.get(url, timeout=12)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return img, url

# -----------------------------------------------------
# Conservative pixel → concentration proxy
# (we avoid claiming exact mapping; we use a stable monotonic proxy)
# -----------------------------------------------------
def rgb_to_conc_proxy(rgb):
    r, g, b = rgb
    # treat very dark as "no-data/land/labels"
    if (r < 40 and g < 40 and b < 40):
        return np.nan
    # monotonic proxy in [0..100]
    return float(np.clip(((r + g + b) / 3.0) / 255.0 * 100.0, 0, 100))

def compute_sector_metrics(img, sector):
    w, h = img.size
    cx, cy = w // 2, h // 2
    max_r = min(cx, cy)

    t1, t2 = sector["theta"]
    r1, r2 = sector["r"]

    vals = []
    # Sampling stride: improves speed on Streamlit Cloud
    stride = 2  # 1=full, 2=fast
    for y in range(0, h, stride):
        for x in range(0, w, stride):
            dx = x - cx
            dy = cy - y
            r = math.sqrt(dx * dx + dy * dy)
            if r <= 1:
                continue
            rn = r / max_r
            if not (r1 <= rn <= r2):
                continue
            ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            # handle wrap-around ranges (e.g., 330..360)
            in_theta = (t1 <= ang <= t2) if (t1 <= t2) else (ang >= t1 or ang <= t2)
            if not in_theta:
                continue
            vals.append(rgb_to_conc_proxy(img.getpixel((x, y))))

    arr = np.array(vals, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return None

    mean_c = float(arr.mean())
    p15 = float((arr >= 15).mean() * 100)  # coverage proxy
    p70 = float((arr >= 70).mean() * 100)  # heavy ice proxy
    # confidence proxy: more valid pixels -> higher confidence
    conf = float(np.clip(arr.size / (w*h/16), 0, 1))  # heuristic scale
    return dict(mean_c=mean_c, p15=p15, p70=p70, conf=conf)

# -----------------------------------------------------
# Risk model: operational risk index (non-directive)
# We combine drivers; avoid "open/closed" framing.
# -----------------------------------------------------
def risk_index_from_metrics(m):
    # weights tuned to emphasize "coverage" and "heavy ice"
    # (still experimental; make explainable in UI)
    w_mean = 0.45
    w_cov = 0.35
    w_heavy = 0.20

    # Normalize drivers to 0..100
    mean_norm = np.clip(m["mean_c"], 0, 100)
    cov_norm = np.clip(m["p15"], 0, 100)
    heavy_norm = np.clip(m["p70"] * 1.25, 0, 100)  # boost heavy fraction

    raw = w_mean * mean_norm + w_cov * cov_norm + w_heavy * heavy_norm
    return float(np.clip(raw, 0, 100))

def classify_status(x):
    if x < 30:
        return "LOW", "🟢"
    if x < 50:
        return "MODERATE", "🟡"
    if x < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

# -----------------------------------------------------
# UI helpers: compact gauge (SVG, mobile-friendly)
# -----------------------------------------------------
def render_gauge(value):
    angle = -90 + (value / 100.0) * 180.0
    x2 = 100 + 62 * math.cos(math.radians(angle))
    y2 = 102 - 62 * math.sin(math.radians(angle))

    return f"""
<svg viewBox="0 0 220 140" width="100%" style="max-width:520px;">
  <!-- base arc -->
  <path d="M30 110 A80 80 0 0 1 190 110" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="16"/>
  <!-- colored arc segments (muted) -->
  <path d="M30 110 A80 80 0 0 1 86 43"  fill="none" stroke="rgba(46,204,113,0.75)" stroke-width="16" stroke-linecap="round"/>
  <path d="M86 43 A80 80 0 0 1 130 33" fill="none" stroke="rgba(241,196,15,0.75)" stroke-width="16" stroke-linecap="round"/>
  <path d="M130 33 A80 80 0 0 1 160 50" fill="none" stroke="rgba(243,156,18,0.75)" stroke-width="16" stroke-linecap="round"/>
  <path d="M160 50 A80 80 0 0 1 190 110" fill="none" stroke="rgba(231,76,60,0.75)" stroke-width="16" stroke-linecap="round"/>

  <!-- needle -->
  <line x1="110" y1="110" x2="{x2}" y2="{y2}" stroke="rgba(255,255,255,0.92)" stroke-width="4" stroke-linecap="round"/>
  <circle cx="110" cy="110" r="6" fill="rgba(255,255,255,0.92)"/>

  <!-- labels -->
  <text x="30" y="130" fill="rgba(255,255,255,0.65)" font-size="12">0</text>
  <text x="106" y="130" fill="rgba(255,255,255,0.65)" font-size="12">50</text>
  <text x="180" y="130" fill="rgba(255,255,255,0.65)" font-size="12">100</text>

  <text x="110" y="78" text-anchor="middle" fill="rgba(255,255,255,0.92)" font-size="22" font-weight="700">{value:.1f}</text>
  <text x="110" y="96" text-anchor="middle" fill="rgba(255,255,255,0.65)" font-size="12">Risk Index</text>
</svg>
"""

def badge_conf(conf):
    if conf >= 0.85:
        return "HIGH", "🟢"
    if conf >= 0.60:
        return "MED", "🟡"
    return "LOW", "🟠"

# -----------------------------------------------------
# Session logbook for Learn loop (AAR)
# -----------------------------------------------------
if "aar" not in st.session_state:
    st.session_state.aar = []

def add_aar(entry):
    st.session_state.aar.insert(0, entry)

# =====================================================
# TOP CONTROL – mobile first (no hidden sidebar)
# =====================================================
st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant (Operational Risk Infrastructure)")
st.caption(f"Today (local): {TODAY}")

colA, colB = st.columns([2, 1])
with colA:
    region = st.selectbox("Region", list(REGION_SECTORS.keys()), index=0)
with colB:
    data_level = st.selectbox("Data Level", ["Level 3 (Bremen PNG – Experimental)"], index=0)

st.markdown("---")

# =====================================================
# TABS
# =====================================================
tab_dash, tab_loop, tab_fleet, tab_about, tab_logs = st.tabs(
    ["🧭 Dashboard", "🔁 Ops Loop", "🛳 Fleet/Port View", "📄 About (IMO/Gov)", "🗒 Logbook (Learn)"]
)

# =====================================================
# OBSERVE (fetch + compute once)
# =====================================================
with st.spinner("Loading Level 3 observation (Bremen AMSR2 PNG)…"):
    img, bremen_url = load_bremen_png()
    metrics = compute_sector_metrics(img, REGION_SECTORS[region])

if metrics is None:
    st.error("Level 3 observation could not be computed (ROI returned no valid pixels).")
    st.stop()

risk = risk_index_from_metrics(metrics)
status, dot = classify_status(risk)
conf_txt, conf_dot = badge_conf(metrics["conf"])

# =====================================================
# TAB: Dashboard (Assess)
# =====================================================
with tab_dash:
    st.subheader("Regional Navigation Risk (Status-Based)")
    st.markdown(f"**Selected Region:** {region}")
    st.markdown(f"**Data Level:** {data_level}  •  **Data Confidence:** {conf_dot} {conf_txt}")

    st.markdown(f"### {dot} **{status}**")
    st.markdown(f"**Risk Index:** {risk:.1f} / 100")

    st.markdown(render_gauge(risk), unsafe_allow_html=True)

    st.progress(int(risk))

    st.markdown("**Drivers (proxy):**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean conc.", f"{metrics['mean_c']:.1f}%")
    c2.metric("Coverage ≥15%", f"{metrics['p15']:.1f}%")
    c3.metric("Heavy ≥70%", f"{metrics['p70']:.1f}%")

    st.markdown(
        """
**Operational Interpretation (Non-Directive)**  
This is a **risk-reduction indicator**, not an “open/closed route” claim.  
It supports **situational awareness** by translating cryospheric observations into a
status-based operational risk signal. Final operational decisions remain with operators
and vessel masters.
"""
    )

# =====================================================
# TAB: Ops Loop (Observe → Assess → Decide → Act → Learn)
# =====================================================
with tab_loop:
    st.subheader("Operational Loop (Standardized)")

    st.markdown("### 1) Observe")
    st.markdown(
        f"""
- Source: Bremen AMSR2 daily PNG (experimental proxy)  
- Region ROI: polar-sector approximation for **{region}**  
- Current drivers: Mean {metrics['mean_c']:.1f}%, Coverage≥15 {metrics['p15']:.1f}%, Heavy≥70 {metrics['p70']:.1f}%  
"""
    )

    st.markdown("### 2) Assess (Risk)")
    st.markdown(f"- Status: **{status}**  ({risk:.1f}/100)  • Confidence: **{conf_txt}**")

    st.markdown("### 3) Decide (Non-Directive Options)")
    if status in ["LOW", "MODERATE"]:
        st.info("Suggested posture: continue operations with routine monitoring + data refresh cadence.")
    elif status == "HIGH":
        st.warning("Suggested posture: tighten review cycle; confirm with official ice services before committing.")
    else:
        st.error("Suggested posture: escalation posture; require higher-confidence products + operational review gate.")

    st.markdown("### 4) Act (Operational Checklist)")
    st.markdown(
        """
- ☐ Confirm latest official ice service bulletin (national / regional)  
- ☐ Verify vessel class / ice capability vs expected regime  
- ☐ Update comms plan (satcom windows / redundancy)  
- ☐ Define no-go / slow-go thresholds (operator policy)  
- ☐ Port/route contingency readiness (ETA/ETD, bunkering, SAR posture)  
"""
    )

    st.markdown("### 5) Learn (AAR – After Action Review)")
    with st.form("aar_form", clear_on_submit=True):
        op = st.text_input("Operation / Voyage / Port call name", value="")
        note = st.text_area("What happened? What did the indicator get right/wrong? (short)", value="", height=100)
        decision = st.selectbox("Operational posture taken", ["Routine", "Tightened review", "Escalated", "Held/Delayed", "Rerouted"])
        submitted = st.form_submit_button("Save AAR entry")
        if submitted:
            add_aar({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "region": region,
                "risk": round(risk, 1),
                "status": status,
                "confidence": conf_txt,
                "operation": op.strip() or "(unnamed)",
                "posture": decision,
                "note": note.strip()
            })
            st.success("Saved to Logbook.")

# =====================================================
# TAB: Fleet/Port View (Ecosystem framing)
# =====================================================
with tab_fleet:
    st.subheader("Fleet / Port / Safety Context (Non-Directive)")

    st.markdown(
        """
This view reflects the shift from “route open/close” to **continuous operational risk reduction**:

- **Power–Industry–Port–Mobility–Safety** coupling means decisions are not only navigational.  
- Icebreakers and research vessels are **mobile operational platforms** linking:
  observation → comms → modeling → decision → execution.
"""
    )

    st.markdown("### Operational Gate (example)")
    gate = "Green" if status in ["LOW"] else "Amber" if status in ["MODERATE"] else "Red"
    st.markdown(f"- Current Gate: **{gate}** (based on status **{status}**)")

    st.markdown(
        """
**Use cases**
- Port readiness: berth scheduling, tug/ice assist planning  
- Fleet allocation: ice-capable asset assignment, convoy considerations  
- Safety posture: SAR coordination readiness, comms redundancy checks  
"""
    )

# =====================================================
# TAB: About (IMO/Gov) – concept language
# =====================================================
with tab_about:
    st.subheader("About – POLAR CUDA (IMO/Government Style)")

    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is an operational decision-support framework
designed to reduce risk in polar and ice-affected waters by standardizing an end-to-end loop:

**Observe → Assess → Decide → Act → Learn**

Rather than treating the Arctic as a binary “route open/closed” problem, POLAR CUDA supports
continuous operational judgment by translating cryospheric observations into an interpretable,
status-based risk signal and a structured operational review process.

POLAR CUDA is explicitly **non-directive**. It does not issue navigational commands and does not
replace official ice services, onboard systems, or vessel master judgment. It is intended to
complement existing practices by improving transparency, repeatability, and post-operation learning.
"""
    )

# =====================================================
# TAB: Logbook (Learn) – show AAR entries
# =====================================================
with tab_logs:
    st.subheader("Logbook (AAR – After Action Review)")
    if not st.session_state.aar:
        st.caption("No entries yet. Add one in the Ops Loop tab.")
    else:
        for i, e in enumerate(st.session_state.aar[:20], start=1):
            st.markdown(f"**{i}. {e['ts']}**  •  {e['operation']}  •  {e['region']}")
            st.caption(f"Status {e['status']} ({e['risk']}/100) • Confidence {e['confidence']} • Posture: {e['posture']}")
            if e["note"]:
                st.markdown(f"> {e['note']}")
            st.markdown("---")

# -----------------------------------------------------
# Footer: data/legal
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): This dashboard derives an **image-based proxy** from the publicly accessible
daily Bremen AMSR2 sea-ice concentration PNG. The proxy uses color-based quantization within an
approximate polar-sector ROI for situational awareness.

This is **not an authoritative gridded concentration product** and must not be used as a substitute
for official ice services, onboard navigation systems, or professional judgment. Final operational
decisions remain the responsibility of operators and vessel masters.
"""
)
