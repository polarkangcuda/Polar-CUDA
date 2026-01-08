import streamlit as st
import numpy as np
import datetime
from PIL import Image
import requests
from io import BytesIO
import math

# =====================================================
# POLAR CUDA – Operational Risk Infrastructure (v2.1)
# Level 3: Bremen AMSR2 PNG → colorbar-derived quantization
# Observe → Assess → Decide → Act → Learn
# =====================================================

st.set_page_config(page_title="POLAR CUDA – Ops Risk", layout="centered")
TODAY = datetime.date.today()

# -----------------------------------------------------
# Regions as polar-sector ROI (operational approximation)
# theta: degrees clockwise from North (0 at top, 90 right)
# r: fraction of image half-size
# -----------------------------------------------------
REGION_SECTORS = {
    "Entire Arctic (Pan-Arctic)": dict(theta=(0, 360), r=(0.18, 0.93)),
    "Chukchi Sea": dict(theta=(240, 285), r=(0.52, 0.82)),
    "Beaufort Sea": dict(theta=(285, 330), r=(0.52, 0.82)),
    "Laptev Sea": dict(theta=(60, 110), r=(0.52, 0.82)),
    "East Siberian Sea": dict(theta=(110, 165), r=(0.52, 0.82)),
    "Kara Sea": dict(theta=(20, 60), r=(0.52, 0.82)),
    "Barents Sea": dict(theta=(330, 360), r=(0.52, 0.82)),
    "Greenland Sea": dict(theta=(300, 330), r=(0.52, 0.82)),
    "Baffin Bay": dict(theta=(255, 305), r=(0.60, 0.92)),
    "Lincoln Sea": dict(theta=(350, 30), r=(0.24, 0.52)),  # wrap-around
    "Bering Sea": dict(theta=(215, 250), r=(0.78, 0.99)),
}

# -----------------------------------------------------
# Data loader: Bremen AMSR2 daily PNG
# -----------------------------------------------------
@st.cache_data(ttl=1800)
def load_bremen_png():
    url = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    return img, url

# -----------------------------------------------------
# Helpers: land/ocean/no-data masks (heuristics)
# These do NOT claim geophysical truth; they are for removing map background.
# -----------------------------------------------------
def is_land(rgb):
    r, g, b = rgb
    # Bremen map land is typically green-ish
    return (g > 110 and g > r + 25 and g > b + 25)

def is_ocean(rgb):
    r, g, b = rgb
    # ocean background is dark blue-ish
    return (b > 90 and b > r + 30 and b > g + 20 and (r + g) < 140)

def is_text_or_grid(rgb):
    r, g, b = rgb
    # black/gray annotations & gridlines
    mx = max(r, g, b)
    mn = min(r, g, b)
    return (mx < 70) or (mx - mn < 10 and mx < 160)

# -----------------------------------------------------
# Colorbar detection (robust-ish):
# Scan bottom band for row with high color diversity, then find longest colorful segment.
# Build palette from that segment (RGB → 0..100%).
# -----------------------------------------------------
def build_palette_from_colorbar(img: Image.Image, n=64):
    arr = np.array(img)
    h, w, _ = arr.shape

    y0 = int(h * 0.84)
    y1 = h - 1

    best_y = None
    best_score = -1
    # choose row with most unique colors in bottom band
    for y in range(y0, y1):
        row = arr[y, :, :]
        # downsample to speed
        row_ds = row[::3]
        uniq = np.unique(row_ds.reshape(-1, 3), axis=0)
        score = len(uniq)
        if score > best_score:
            best_score = score
            best_y = y

    if best_y is None or best_score < 40:
        return None, None, None  # cannot find

    row = arr[best_y, :, :]
    # identify "colorful" pixels (exclude land/ocean/text-ish)
    mask = []
    for x in range(w):
        rgb = tuple(row[x])
        colorful = (not is_land(rgb)) and (not is_ocean(rgb)) and (not is_text_or_grid(rgb))
        mask.append(colorful)
    mask = np.array(mask, dtype=bool)

    # find longest contiguous True segment
    best = (0, 0, 0)  # length, start, end
    start = None
    for x in range(w):
        if mask[x] and start is None:
            start = x
        if (not mask[x] or x == w - 1) and start is not None:
            end = x if not mask[x] else x
            length = end - start + 1
            if length > best[0]:
                best = (length, start, end)
            start = None

    length, x_start, x_end = best
    if length < int(w * 0.18):
        return None, None, None

    # sample N points uniformly in that segment
    xs = np.linspace(x_start, x_end, n).astype(int)
    palette_rgb = arr[best_y, xs, :].astype(np.float32)  # (n,3)
    palette_val = np.linspace(0, 100, n).astype(np.float32)

    return palette_rgb, palette_val, dict(y=best_y, x1=x_start, x2=x_end)

# -----------------------------------------------------
# Nearest-palette mapping
# (vectorized enough for sampled ROI points)
# -----------------------------------------------------
def rgb_to_conc_by_palette(rgb, palette_rgb, palette_val):
    # rgb: (3,)
    d = palette_rgb - rgb
    dist2 = np.sum(d * d, axis=1)
    idx = int(np.argmin(dist2))
    return float(palette_val[idx])

# -----------------------------------------------------
# Sector metrics from palette-quantized concentration
# -----------------------------------------------------
def compute_sector_metrics(img, sector, palette_rgb, palette_val, stride=3):
    w, h = img.size
    px = img.load()
    cx, cy = w // 2, h // 2
    max_r = min(cx, cy)

    t1, t2 = sector["theta"]
    r1, r2 = sector["r"]

    conc_list = []
    valid = 0
    total = 0

    for y in range(0, h, stride):
        for x in range(0, w, stride):
            total += 1
            dx = x - cx
            dy = cy - y  # screen coords -> math coords (north up)
            rr = math.hypot(dx, dy)
            if rr <= 1:
                continue

            rn = rr / max_r
            if not (r1 <= rn <= r2):
                continue

            ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            in_theta = (t1 <= ang <= t2) if (t1 <= t2) else (ang >= t1 or ang <= t2)
            if not in_theta:
                continue

            rgb = px[x, y]
            if is_land(rgb) or is_text_or_grid(rgb):
                continue

            # ocean is valid concentration 0
            if is_ocean(rgb):
                conc = 0.0
            else:
                conc = rgb_to_conc_by_palette(np.array(rgb, dtype=np.float32), palette_rgb, palette_val)

            conc_list.append(conc)
            valid += 1

    if valid < 400:  # guard
        return None

    arr = np.array(conc_list, dtype=float)
    mean_c = float(arr.mean())
    p15 = float((arr >= 15).mean() * 100)
    p70 = float((arr >= 70).mean() * 100)

    # confidence proxy: more samples -> higher
    conf = float(np.clip(valid / 6000.0, 0.0, 1.0))

    return dict(mean_c=mean_c, p15=p15, p70=p70, conf=conf, n=valid)

# -----------------------------------------------------
# Risk model (transparent, operational)
# -----------------------------------------------------
def risk_index_from_metrics(m):
    # emphasize coverage + heavy ice as ops risk drivers
    mean_norm = np.clip(m["mean_c"], 0, 100)
    cov_norm = np.clip(m["p15"], 0, 100)
    heavy_norm = np.clip(m["p70"] * 1.25, 0, 100)
    return float(np.clip(0.40 * mean_norm + 0.40 * cov_norm + 0.20 * heavy_norm, 0, 100))

def classify_status(x):
    if x < 30:
        return "LOW", "🟢"
    if x < 50:
        return "MODERATE", "🟡"
    if x < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"

def badge_conf(conf):
    if conf >= 0.85:
        return "HIGH", "🟢"
    if conf >= 0.60:
        return "MED", "🟡"
    return "LOW", "🟠"

def render_gauge(value):
    angle = -90 + (value / 100.0) * 180.0
    x2 = 110 + 70 * math.cos(math.radians(angle))
    y2 = 112 - 70 * math.sin(math.radians(angle))
    return f"""
<svg viewBox="0 0 240 150" width="100%" style="max-width:560px;">
  <path d="M35 120 A85 85 0 0 1 205 120" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="18"/>
  <path d="M35 120 A85 85 0 0 1 95 52"  fill="none" stroke="rgba(46,204,113,0.78)" stroke-width="18" stroke-linecap="round"/>
  <path d="M95 52 A85 85 0 0 1 140 44" fill="none" stroke="rgba(241,196,15,0.78)" stroke-width="18" stroke-linecap="round"/>
  <path d="M140 44 A85 85 0 0 1 170 60" fill="none" stroke="rgba(243,156,18,0.78)" stroke-width="18" stroke-linecap="round"/>
  <path d="M170 60 A85 85 0 0 1 205 120" fill="none" stroke="rgba(231,76,60,0.78)" stroke-width="18" stroke-linecap="round"/>

  <line x1="120" y1="120" x2="{x2}" y2="{y2}" stroke="rgba(255,255,255,0.92)" stroke-width="4.5" stroke-linecap="round"/>
  <circle cx="120" cy="120" r="7" fill="rgba(255,255,255,0.92)"/>

  <text x="35" y="142" fill="rgba(255,255,255,0.60)" font-size="12">0</text>
  <text x="114" y="142" fill="rgba(255,255,255,0.60)" font-size="12">50</text>
  <text x="198" y="142" fill="rgba(255,255,255,0.60)" font-size="12">100</text>

  <text x="120" y="84" text-anchor="middle" fill="rgba(255,255,255,0.95)" font-size="24" font-weight="800">{value:.1f}</text>
  <text x="120" y="104" text-anchor="middle" fill="rgba(255,255,255,0.65)" font-size="12">Risk Index</text>
</svg>
"""

# -----------------------------------------------------
# Logbook for Learn loop
# -----------------------------------------------------
if "aar" not in st.session_state:
    st.session_state.aar = []

def add_aar(entry):
    st.session_state.aar.insert(0, entry)

# =====================================================
# Mobile-first top controls (no hidden sidebar)
# =====================================================
st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant (Operational Risk Infrastructure)")
st.caption(f"Today (local): {TODAY}")

c1, c2 = st.columns([2, 1])
with c1:
    region = st.selectbox("Region", list(REGION_SECTORS.keys()), index=0)
with c2:
    data_level = st.selectbox("Data Level", ["Level 3 (Bremen PNG – Experimental)"], index=0)

st.markdown("---")

tab_dash, tab_ops, tab_fleet, tab_about, tab_log = st.tabs(
    ["🧭 Dashboard", "🔁 Ops Loop", "🛳 Fleet/Port View", "📄 About (IMO/Gov)", "🗒 Logbook (Learn)"]
)

# =====================================================
# Observe: load image + build palette from colorbar
# =====================================================
with st.spinner("Loading Bremen AMSR2 PNG & calibrating colorbar…"):
    img, bremen_url = load_bremen_png()
    palette_rgb, palette_val, cb = build_palette_from_colorbar(img, n=64)

if palette_rgb is None:
    st.error("Could not detect the Bremen colorbar. (PNG format likely changed.)")
    st.stop()

metrics = compute_sector_metrics(img, REGION_SECTORS[region], palette_rgb, palette_val, stride=3)
if metrics is None:
    st.error("ROI produced too few valid samples. Please adjust ROI or stride.")
    st.stop()

risk = risk_index_from_metrics(metrics)
status, dot = classify_status(risk)
conf_txt, conf_dot = badge_conf(metrics["conf"])

# =====================================================
# Dashboard
# =====================================================
with tab_dash:
    st.subheader("Regional Navigation Risk (Status-Based)")
    st.markdown(f"**Selected Region:** {region}")
    st.markdown(f"**Data Level:** {data_level}  •  **Data Confidence:** {conf_dot} {conf_txt}")

    st.markdown(f"### {dot} **{status}**")
    st.markdown(f"**Risk Index:** {risk:.1f} / 100")
    st.markdown(render_gauge(risk), unsafe_allow_html=True)
    st.progress(int(risk))

    st.markdown("**Drivers (Bremen PNG → quantized concentration proxy):**")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Mean conc.", f"{metrics['mean_c']:.1f}%")
    d2.metric("Coverage ≥15%", f"{metrics['p15']:.1f}%")
    d3.metric("Heavy ≥70%", f"{metrics['p70']:.1f}%")
    d4.metric("Samples", f"{metrics['n']:,}")

    st.caption(
        f"Colorbar detected at y={cb['y']}, x={cb['x1']}..{cb['x2']} • Source: Bremen AMSR2 PNG"
    )

    st.markdown(
        """
**Operational Interpretation (Non-Directive)**  
This is a **risk-reduction indicator**, not an “open/closed route” claim.  
It supports **situational awareness** by translating cryospheric observations into a
status-based operational risk signal. Final operational decisions remain with operators and vessel masters.
"""
    )

# =====================================================
# Ops loop
# =====================================================
with tab_ops:
    st.subheader("Operational Loop (Standardized)")
    st.markdown("### 1) Observe")
    st.markdown(
        f"""
- Source: Bremen AMSR2 daily PNG (experimental, image-derived proxy)  
- Method: colorbar-derived quantization (nearest palette mapping) within **{region}** ROI  
- Drivers: Mean {metrics['mean_c']:.1f}%, Coverage≥15 {metrics['p15']:.1f}%, Heavy≥70 {metrics['p70']:.1f}%  
"""
    )

    st.markdown("### 2) Assess")
    st.markdown(f"- Status: **{status}** ({risk:.1f}/100) • Confidence: **{conf_txt}**")

    st.markdown("### 3) Decide (Non-Directive Options)")
    if status in ["LOW", "MODERATE"]:
        st.info("Suggested posture: routine monitoring + confirm with official ice service for tactical decisions.")
    elif status == "HIGH":
        st.warning("Suggested posture: tighten review cadence; require cross-check with authoritative products.")
    else:
        st.error("Suggested posture: escalation posture; apply operator review gate before commitment.")

    st.markdown("### 4) Act (Checklist)")
    st.markdown(
        """
- ☐ Cross-check official ice service bulletin  
- ☐ Verify vessel capability vs expected ice regime  
- ☐ Update comms plan / redundancy  
- ☐ Define no-go / slow-go thresholds (operator policy)  
- ☐ Port/route contingency readiness (ETA/ETD, SAR posture)  
"""
    )

    st.markdown("### 5) Learn (AAR)")
    with st.form("aar_form", clear_on_submit=True):
        op = st.text_input("Operation / Voyage name", value="")
        note = st.text_area("What did the indicator get right/wrong?", value="", height=100)
        decision = st.selectbox("Posture taken", ["Routine", "Tightened review", "Escalated", "Held/Delayed", "Rerouted"])
        if st.form_submit_button("Save AAR entry"):
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
# Fleet/Port view (ecosystem framing)
# =====================================================
with tab_fleet:
    st.subheader("Fleet / Port / Safety Context (Non-Directive)")
    st.markdown(
        """
This view reflects the shift from “route open/close” to **continuous operational risk reduction**:
- Decisions are coupled to **port readiness, fleet allocation, safety posture**, not only navigation.
- Icebreakers/research vessels function as **mobile operational platforms** linking:
  observation → comms → modeling → decision → execution.
"""
    )

# =====================================================
# About (IMO/Gov)
# =====================================================
with tab_about:
    st.subheader("About – POLAR CUDA (IMO/Government Style)")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is an operational decision-support framework
designed to reduce risk in polar and ice-affected waters by standardizing an end-to-end loop:

**Observe → Assess → Decide → Act → Learn**

POLAR CUDA supports continuous operational judgment by translating cryospheric observations into an interpretable,
status-based risk signal and a structured operational review process.

POLAR CUDA is **non-directive**. It does not issue navigational commands and does not replace official ice services,
onboard systems, or vessel master judgment.
"""
    )

# =====================================================
# Logbook
# =====================================================
with tab_log:
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
# Footer: legal / attribution
# -----------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

Level 3 (Experimental): This dashboard derives an **image-based proxy** from the publicly accessible daily
Bremen AMSR2 sea-ice concentration PNG by **colorbar-derived quantization** within an operational ROI.

This is **not an authoritative gridded concentration product** and must not be used as a substitute for official ice services,
onboard navigation systems, or professional judgment. Final operational decisions remain the responsibility of operators and vessel masters.
"""
)
