import streamlit as st
import pandas as pd
import datetime as dt
import numpy as np

from io import BytesIO
from PIL import Image, ImageDraw
import urllib.request


# ==========================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Level 2: NOAA/NSIDC Sea Ice Index v4 extent (G02135)
# Level 3: Bremen AMSR2 PNG -> colorbar-based quantization (EXPERIMENTAL PROXY)
# ==========================================================

st.set_page_config(
    page_title="POLAR CUDA – Cryospheric Unified Decision Assistant",
    layout="centered",
)

TODAY = dt.date.today()

BREMEN_PNG_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"
NSIDC_V4_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/"
    "north/daily/data/N_seaice_extent_daily_v4.0.csv"
)

# ----------------------------------------------------------
# Regions (Sea of Okhotsk excluded per your decision)
# Level 3 ROI are "operational ROIs" on the PNG image space.
# You can tune them easily if you want.
# ----------------------------------------------------------
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

# Level 2 seasonal normalization references (operational scaling)
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

# ----------------------------------------------------------
# Level 3 ROI definitions (relative to detected "map bbox")
# Each ROI is (x0, y0, x1, y1) as ratios [0..1] within map bbox.
# These are intentionally conservative; tune if needed.
# ----------------------------------------------------------
ROI_RATIOS = {
    "Entire Arctic (Pan-Arctic)": (0.08, 0.08, 0.92, 0.92),

    "Bering Sea": (0.70, 0.62, 0.86, 0.78),
    "Chukchi Sea": (0.63, 0.50, 0.78, 0.65),
    "Beaufort Sea": (0.50, 0.46, 0.63, 0.60),

    "East Siberian Sea": (0.62, 0.40, 0.78, 0.52),
    "Laptev Sea": (0.52, 0.33, 0.64, 0.45),
    "Kara Sea": (0.44, 0.30, 0.54, 0.42),

    "Barents Sea": (0.36, 0.30, 0.46, 0.42),
    "Greenland Sea": (0.26, 0.34, 0.36, 0.52),

    "Baffin Bay": (0.14, 0.52, 0.28, 0.68),
    "Lincoln Sea": (0.36, 0.18, 0.55, 0.30),
}

# ----------------------------------------------------------
# Status classification
# ----------------------------------------------------------
def classify_status(risk_index: float):
    if risk_index < 30:
        return "LOW", "🟢"
    if risk_index < 50:
        return "MODERATE", "🟡"
    if risk_index < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"


# ----------------------------------------------------------
# Simple semi-gauge (HTML/CSS) - no plotly/matplotlib
# ----------------------------------------------------------
def render_semigauge(value_0_100: float):
    v = float(np.clip(value_0_100, 0, 100))
    # rotate needle: -90deg (0) to +90deg (100)
    angle = -90 + (v * 180.0 / 100.0)

    html = f"""
<div style="max-width: 420px; margin: 0 auto;">
  <div style="position: relative; width: 100%; aspect-ratio: 2 / 1;">
    <div style="
      position:absolute; inset:0;
      border-top-left-radius: 999px;
      border-top-right-radius: 999px;
      border: 14px solid rgba(255,255,255,0.10);
      border-bottom: 0;
      background:
        conic-gradient(
          from 180deg,
          rgba(46, 204, 113, 0.95) 0deg,
          rgba(241, 196, 15, 0.95) 54deg,
          rgba(230, 126, 34, 0.95) 108deg,
          rgba(231, 76, 60, 0.95) 180deg
        );
      -webkit-mask:
        radial-gradient(circle at 50% 100%, transparent 55%, #000 56%);
      mask:
        radial-gradient(circle at 50% 100%, transparent 55%, #000 56%);
    "></div>

    <div style="
      position:absolute; left:50%; bottom:0%;
      width: 4px; height: 52%;
      background: rgba(255,255,255,0.92);
      transform-origin: bottom center;
      transform: translateX(-50%) rotate({angle}deg);
      border-radius: 4px;
      box-shadow: 0 0 10px rgba(0,0,0,0.35);
    "></div>

    <div style="
      position:absolute; left:50%; bottom:0%;
      width: 18px; height: 18px;
      background: rgba(255,255,255,0.92);
      transform: translate(-50%, 50%);
      border-radius: 999px;
      box-shadow: 0 0 12px rgba(0,0,0,0.35);
    "></div>

    <div style="
      position:absolute; left:0; right:0; bottom:-6px;
      display:flex; justify-content:space-between;
      font-size: 12px; opacity: 0.7;
    ">
      <span>0</span><span>50</span><span>100</span>
    </div>
  </div>

  <div style="text-align:center; margin-top: 10px;">
    <div style="font-size: 34px; font-weight: 800; line-height: 1;">
      {v:.1f}<span style="font-size: 14px; opacity:0.8;"> / 100</span>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ----------------------------------------------------------
# Network safe image fetch
# ----------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_png(url: str):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = r.read()
        img = Image.open(BytesIO(data)).convert("RGB")
        return img, None
    except Exception as e:
        return None, str(e)


# ----------------------------------------------------------
# Detect "map bbox" (exclude white margins)
# ----------------------------------------------------------
def detect_map_bbox(img: Image.Image):
    arr = np.asarray(img).astype(np.int16)
    # "non-white" mask (tune threshold)
    nonwhite = np.any(arr < 245, axis=2)
    ys, xs = np.where(nonwhite)
    if len(xs) < 1000:
        return None
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    # pad slightly
    pad = 6
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(img.width - 1, x1 + pad)
    y1 = min(img.height - 1, y1 + pad)
    return (x0, y0, x1, y1)


# ----------------------------------------------------------
# Extract colorbar palette from the PNG itself
# - Find a row near bottom with maximum color variance
# - Sample along x to build palette(0..100)
# ----------------------------------------------------------
def extract_palette_from_colorbar(img: Image.Image):
    w, h = img.size
    arr = np.asarray(img).astype(np.int16)

    y_start = int(h * 0.72)
    y_end = int(h * 0.95)
    if y_end <= y_start + 10:
        return None, None

    # find row with max std across RGB
    best_y = None
    best_score = -1.0
    for y in range(y_start, y_end):
        row = arr[y, :, :]
        score = float(np.std(row[:, 0]) + np.std(row[:, 1]) + np.std(row[:, 2]))
        if score > best_score:
            best_score = score
            best_y = y

    if best_y is None:
        return None, None

    # take a small strip around best_y and average
    y0 = max(0, best_y - 2)
    y1 = min(h, best_y + 3)
    strip = arr[y0:y1, :, :].mean(axis=0)  # shape (w,3)

    # find x-range of the colorbar: exclude near-white/near-black background
    mask = np.logical_and(
        np.any(strip < 240, axis=1),
        np.any(strip > 10, axis=1),
    )
    xs = np.where(mask)[0]
    if len(xs) < w * 0.2:
        # colorbar range too small; give up
        return None, None

    x_min = int(xs.min())
    x_max = int(xs.max())

    # sample 101 points -> palette for 0..100
    palette = []
    for v in range(101):
        x = int(round(x_min + (x_max - x_min) * (v / 100.0)))
        rgb = strip[x, :].astype(np.int16)
        palette.append(rgb)
    palette = np.array(palette, dtype=np.int16)  # (101,3)
    return palette, (x_min, best_y, x_max, best_y)


# ----------------------------------------------------------
# Quantize ROI pixels into concentration using palette
# - Downsample for speed
# - Mask pixels that are too far from palette (land/ocean/gridlines)
# ----------------------------------------------------------
def roi_mean_concentration(img: Image.Image, map_bbox, roi_ratio, palette, stride=4):
    x0, y0, x1, y1 = map_bbox
    mx0, my0 = x0, y0
    mw, mh = (x1 - x0 + 1), (y1 - y0 + 1)

    rx0 = int(mx0 + roi_ratio[0] * mw)
    ry0 = int(my0 + roi_ratio[1] * mh)
    rx1 = int(mx0 + roi_ratio[2] * mw)
    ry1 = int(my0 + roi_ratio[3] * mh)

    rx0, ry0 = max(0, rx0), max(0, ry0)
    rx1, ry1 = min(img.width - 1, rx1), min(img.height - 1, ry1)

    if rx1 <= rx0 + 10 or ry1 <= ry0 + 10:
        return None, (rx0, ry0, rx1, ry1), 0.0, 0

    crop = img.crop((rx0, ry0, rx1, ry1))
    arr = np.asarray(crop).astype(np.int16)

    # downsample
    arr = arr[::stride, ::stride, :]
    pix = arr.reshape(-1, 3)  # (N,3)

    pal = palette  # (101,3)

    # compute nearest palette entry
    # distance^2 = sum((pix - pal)^2)
    # shape (N,101) -> argmin
    diff = pix[:, None, :] - pal[None, :, :]
    dist2 = np.sum(diff * diff, axis=2)
    idx = np.argmin(dist2, axis=1)
    best = np.min(dist2, axis=1)

    # threshold to reject non-ice colors (land/ocean/gridlines)
    # (tuned; adjust if needed)
    valid = best < (35 * 35)

    if valid.sum() < 50:
        return None, (rx0, ry0, rx1, ry1), 0.0, int(valid.sum())

    conc = idx.astype(np.float32)  # 0..100
    conc_valid = conc[valid]

    mean_conc = float(np.mean(conc_valid))
    ice_frac_15 = float(np.mean(conc_valid >= 15.0) * 100.0)

    return mean_conc, (rx0, ry0, rx1, ry1), ice_frac_15, int(valid.sum())


# ----------------------------------------------------------
# Level 2: NSIDC v4 loader (ultra safe)
# ----------------------------------------------------------
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    df = pd.read_csv(NSIDC_V4_URL)
    df.columns = [c.strip().lower() for c in df.columns]

    # date detection
    date_col = None
    for cand in ["date", "datetime", "time"]:
        if cand in df.columns:
            date_col = cand
            break

    if date_col is None and all(c in df.columns for c in ["year", "month", "day"]):
        df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
        date_col = "date"

    if date_col is None:
        return None, f"NSIDC v4: cannot detect date column. Columns: {list(df.columns)}"

    # extent detection
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break

    if extent_col is None:
        # numeric fallback with realistic magnitude (million km^2)
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > len(df) * 0.9 and numeric.max() > 5:
                extent_col = col
                break

    if extent_col is None:
        return None, f"NSIDC v4: cannot detect extent column. Columns: {list(df.columns)}"

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")
    df = df.dropna(subset=["date", "extent"]).sort_values("date").reset_index(drop=True)
    return df, None


# ----------------------------------------------------------
# Mobile-first controls
# ----------------------------------------------------------
st.markdown(
    """
<style>
/* Make select/radio feel bigger on mobile */
div[data-baseweb="select"] > div { min-height: 50px; }
div[role="radiogroup"] label { padding: 6px 0; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("## 🧊 **POLAR CUDA**")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Today (local): {TODAY}")

st.markdown("### Region")
region = st.selectbox("", REGIONS, index=0, label_visibility="collapsed")

st.markdown("### Data Level")
data_level = st.radio(
    "",
    [
        "Level 3 (Bremen AMSR2 PNG – Experimental Regional Proxy)",
        "Level 2 (NOAA/NSIDC Extent – Fallback Proxy)",
    ],
    index=0,
    label_visibility="collapsed",
)

tab_dashboard, tab_about, tab_formal, tab_logo = st.tabs(
    ["🧭 Dashboard", "📄 About (IMO/Gov)", "📚 Formal Definition", "🎨 Logo/Icon Concept"]
)

# ==========================================================
# TAB: Dashboard
# ==========================================================
with tab_dashboard:
    st.markdown("---")

    used_level = None
    data_date_str = "Unknown"
    risk_index = None
    mean_conc = None
    ice_frac_15 = None
    debug_msg = None

    # -------- Level 3 attempt ----------
    if data_level.startswith("Level 3"):
        img, err = fetch_png(BREMEN_PNG_URL)
        if img is None:
            debug_msg = f"Level 3 could not load Bremen PNG. Reason: {err}"
        else:
            map_bbox = detect_map_bbox(img)
            palette, _ = extract_palette_from_colorbar(img)

            if map_bbox is None or palette is None:
                debug_msg = "Level 3 could not detect map bbox or colorbar palette reliably."
            else:
                roi_ratio = ROI_RATIOS.get(region, ROI_RATIOS["Entire Arctic (Pan-Arctic)"])
                mean_conc, roi_px, ice_frac_15, n_valid = roi_mean_concentration(
                    img=img,
                    map_bbox=map_bbox,
                    roi_ratio=roi_ratio,
                    palette=palette,
                    stride=4,
                )

                if mean_conc is None:
                    debug_msg = (
                        f"Level 3 quantization failed (too few valid ice pixels). "
                        f"Valid pixels: {n_valid}. Switching to Level 2 fallback."
                    )
                else:
                    # risk index: blend mean concentration + 15% ice coverage
                    # (more stable operational proxy than mean only)
                    risk_index = float(np.clip(0.7 * mean_conc + 0.3 * ice_frac_15, 0, 100))
                    used_level = "Level 3 (Bremen AMSR2 PNG – Experimental Proxy)"

                    # Prepare an annotated preview for transparency
                    preview = img.copy()
                    draw = ImageDraw.Draw(preview)
                    # draw ROI box
                    draw.rectangle(roi_px, outline=(255, 255, 0), width=4)
                    # draw map bbox
                    draw.rectangle(map_bbox, outline=(255, 255, 255), width=2)

                    st.caption("Bremen AMSR2 PNG (ROI overlay – yellow box)")
                    st.image(preview, use_container_width=True)

    # -------- Level 2 fallback ----------
    if risk_index is None:
        df, nerr = load_nsidc_v4()
        if df is None or df.empty:
            st.error("Unable to load NSIDC v4 sea ice extent data.")
            if nerr:
                st.caption(nerr)
            if debug_msg:
                st.caption(debug_msg)
            st.stop()

        df_valid = df[df["date"].dt.date <= TODAY]
        if df_valid.empty:
            st.error("No valid NSIDC data available up to today.")
            if debug_msg:
                st.caption(debug_msg)
            st.stop()

        latest = df_valid.iloc[-1]
        extent_today = float(latest["extent"])
        data_date = latest["date"].date()
        data_date_str = str(data_date)

        winter_max, summer_min = REGION_CLIMATOLOGY[region]
        denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-9
        risk_index = float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100))
        used_level = "Level 2 (NOAA/NSIDC Sea Ice Index v4 extent – Seasonal Proxy)"

    # -------- Present results ----------
    status, color = classify_status(risk_index)

    st.markdown("### Regional Navigation Risk (Status-Based)")
    st.markdown(f"**Selected Region:** {region}")
    st.markdown(f"**Data Level Used:** {used_level}")

    if mean_conc is not None:
        st.caption(f"Bremen-derived mean concentration (proxy): {mean_conc:.1f}%")
        st.caption(f"Ice coverage ≥15% within ROI (proxy): {ice_frac_15:.1f}%")

    if "NSIDC" in used_level:
        st.caption("NSIDC Data Date (UTC): " + data_date_str)

    st.markdown(f"## {color} **{status}**")
    render_semigauge(risk_index)
    st.progress(int(round(risk_index)))

    st.markdown(
        f"""
**Operational Interpretation (Non-Directive)**

- This indicator is designed for **situational awareness**, not route command.
- **Level 3** (Bremen PNG) is an **experimental, image-derived proxy** computed by colorbar-based quantization
  within an operational ROI for the selected region.
- **Level 2** (NSIDC extent) is a **fallback seasonal proxy** and does not represent local concentration.

Final operational decisions remain with operators and vessel masters.
"""
    )

    if debug_msg:
        st.warning(debug_msg)

# ==========================================================
# TAB: About (IMO/Gov)
# ==========================================================
with tab_about:
    st.header("About – POLAR CUDA (IMO/Government Style)")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a decision-support framework
intended to enhance situational awareness for navigation and operations in polar and ice-affected waters.

POLAR CUDA integrates publicly accessible cryospheric datasets into a unified, interpretable status indicator
to support informed judgment by fleet operators and vessel masters. The system is designed as an assistant
and does **not** provide tactical route commands or replace official ice services.

Operational use should be accompanied by established bridge procedures, onboard sensors,
official ice products, and applicable regulatory frameworks.
"""
    )

# ==========================================================
# TAB: Formal Definition
# ==========================================================
with tab_formal:
    st.header("Formal Definition – Academic / White Paper")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is defined as a modular decision-support system that
converts cryospheric observations into a unified, explainable risk-status metric for polar operations.

The framework supports multiple data levels:
- **Level 2:** large-scale indicators (e.g., pan-Arctic extent) normalized to region-specific seasonal references.
- **Level 3:** higher-resolution regional proxies derived directly from spatial products (e.g., gridded concentration)
  or, when only imagery is available, via color-quantization methods as an experimental approximation.

POLAR CUDA is explicitly non-directive: outputs are interpretive in nature and preserve operational responsibility
and legal accountability at the operator and vessel-master level.
"""
    )

# ==========================================================
# TAB: Logo/Icon Concept
# ==========================================================
with tab_logo:
    st.header("Logo / Icon Concept – Designer Brief")
    st.markdown(
        """
**Concept Statement**  
*POLAR CUDA visualizes the moment where ice data becomes decision awareness.*

**Design Keywords**  
- Minimal / instrument-like  
- Calm, authoritative, non-alarmist  
- Operational rather than scientific  

**Icon Concept**  
- A **half-dial / gauge arc** suggesting situational status (not control)  
- A subtle **hex-grid / ice tile motif** (abstract, not literal)  
- Muted risk colors (green→yellow→orange→red)

**Avoid**  
- Emergency-alert aesthetics  
- Gaming UI  
- Military command styling

**One-line instruction**  
“This is a tool you glance at before deciding — not something that tells you what to do.”
"""
    )

# ----------------------------------------------------------
# Footer: Data source & legal notice
# ----------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

- **Level 2 (Fallback):** Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
  and distributed under NOAA/NSIDC open data access principles. :contentReference[oaicite:0]{index=0}
- **Level 3 (Experimental):** Regional proxy is derived from the publicly accessible daily imagery
  **Bremen AMSR2 sea-ice concentration map** (PNG) by image colorbar quantization for situational awareness.
  For authoritative concentration products, refer to official gridded datasets and ice services.

This application provides situational awareness only and does not replace official ice services,
onboard navigation systems, or the judgment of vessel masters.
"""
)
