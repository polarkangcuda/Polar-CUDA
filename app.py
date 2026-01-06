import streamlit as st
import pandas as pd
import datetime
import numpy as np
from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image

# =====================================================
# POLAR CUDA – Cryospheric Unified Decision Assistant
# Level 2: NOAA/NSIDC Sea Ice Index v4 (extent proxy)
# Level 3: Bremen AMSR2 daily PNG (experimental regional concentration proxy)
# =====================================================

st.set_page_config(
    page_title="POLAR CUDA – Cryospheric Unified Decision Assistant",
    layout="centered",
)

today = datetime.date.today()

# -----------------------------
# Regions (Sea of Okhotsk excluded)
# -----------------------------
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

# -----------------------------
# Level 2 normalization ranges (operational proxy, not scientific climatology)
# -----------------------------
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

# -----------------------------
# Level 3 ROI boxes (fractions in MAP FRAME coordinates)
# NOTE: These are operational ROIs for situational awareness proxy.
#       They are intentionally conservative (smaller) to reduce land contamination.
# -----------------------------
ROI_FRAC = {
    "Bering Sea": (0.05, 0.62, 0.20, 0.78),
    "Chukchi Sea": (0.07, 0.44, 0.18, 0.58),
    "Beaufort Sea": (0.18, 0.41, 0.32, 0.53),
    "East Siberian Sea": (0.34, 0.39, 0.46, 0.54),
    "Laptev Sea": (0.46, 0.37, 0.56, 0.52),
    "Kara Sea": (0.40, 0.28, 0.50, 0.41),
    "Barents Sea": (0.54, 0.40, 0.66, 0.56),
    "Greenland Sea": (0.58, 0.58, 0.70, 0.74),
    "Baffin Bay": (0.40, 0.60, 0.52, 0.78),
    "Lincoln Sea": (0.44, 0.49, 0.56, 0.62),
    # Entire Arctic handled separately (radial mask)
}

# Pole center (in MAP FRAME fractional coords) for radial mask (Pan-Arctic)
# Empirically stable for this Bremen polar stereographic PNG.
POLE_FRAC = (0.50, 0.56)

# -----------------------------
# Helpers
# -----------------------------
def classify_status(risk_index: float):
    if risk_index < 30:
        return "LOW", "🟢"
    if risk_index < 50:
        return "MODERATE", "🟡"
    if risk_index < 70:
        return "HIGH", "🟠"
    return "EXTREME", "🔴"


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def svg_semi_gauge(value_0_100: float):
    # Simple SVG semicircle gauge (no matplotlib, mobile-friendly)
    v = float(np.clip(value_0_100, 0, 100))
    # needle angle: -90 (0) to +90 (100)
    ang = -90 + (v / 100.0) * 180.0
    # SVG arc segments (4 colors)
    # We keep it minimal; colors are muted by default theme.
    svg = f"""
    <div style="width:100%; max-width:520px; margin: 8px 0 4px 0;">
      <svg viewBox="0 0 200 120" width="100%" height="120" aria-label="risk gauge">
        <!-- background -->
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="18" stroke-linecap="round"/>
        <!-- segments -->
        <path d="M 20 100 A 80 80 0 0 1 60 44" fill="none" stroke="rgba(0, 200, 120, 0.75)" stroke-width="18" stroke-linecap="round"/>
        <path d="M 60 44 A 80 80 0 0 1 100 20" fill="none" stroke="rgba(240, 200, 0, 0.75)" stroke-width="18" stroke-linecap="round"/>
        <path d="M 100 20 A 80 80 0 0 1 140 44" fill="none" stroke="rgba(255, 140, 0, 0.75)" stroke-width="18" stroke-linecap="round"/>
        <path d="M 140 44 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255, 80, 80, 0.75)" stroke-width="18" stroke-linecap="round"/>
        <!-- needle -->
        <g transform="translate(100,100) rotate({ang})">
          <line x1="0" y1="0" x2="0" y2="-70" stroke="rgba(255,255,255,0.92)" stroke-width="3.5" stroke-linecap="round"/>
          <circle cx="0" cy="0" r="6" fill="rgba(255,255,255,0.92)"/>
        </g>
        <!-- labels -->
        <text x="20" y="116" fill="rgba(255,255,255,0.65)" font-size="10">0</text>
        <text x="96" y="116" fill="rgba(255,255,255,0.65)" font-size="10">50</text>
        <text x="172" y="116" fill="rgba(255,255,255,0.65)" font-size="10">100</text>
      </svg>
    </div>
    """
    return svg


# =====================================================
# Level 2: NSIDC v4 extent loader (robust)
# =====================================================
@st.cache_data(ttl=3600)
def load_nsidc_v4():
    url = (
        "https://noaadata.apps.nsidc.org/NOAA/G02135/"
        "north/daily/data/N_seaice_extent_daily_v4.0.csv"
    )

    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]

    # date col detect
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
            return None, f"Unable to detect date column. Columns: {list(df.columns)}"

    # extent col detect
    extent_col = None
    for cand in ["extent", "seaice_extent", "total_extent"]:
        if cand in df.columns:
            extent_col = cand
            break
    if extent_col is None:
        # fallback: numeric col with realistic magnitude
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > len(df) * 0.9 and safe_float(numeric.max(), 0) > 5:
                extent_col = col
                break
    if extent_col is None:
        return None, f"Unable to detect extent column. Columns: {list(df.columns)}"

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["extent"] = pd.to_numeric(df[extent_col], errors="coerce")
    df = df.dropna(subset=["date", "extent"]).sort_values("date").reset_index(drop=True)
    return df, None


# =====================================================
# Level 3: Bremen PNG loader + map-frame detection + colorbar quantization
# =====================================================
BREMEN_URL = "https://data.seaice.uni-bremen.de/amsr2/today/Arctic_AMSR2_nic.png"

@st.cache_data(ttl=3600)
def load_bremen_png():
    # Use a browser-like UA (some hosts are picky)
    req = Request(BREMEN_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=20) as r:
        content = r.read()
    img = Image.open(BytesIO(content)).convert("RGB")
    return img


def detect_map_frame_bbox(rgb_img: Image.Image):
    """
    Detect the main map frame by finding the largest contiguous region
    of 'non-white' pixels (excluding big white margins/labels).
    Returns bbox (x0, y0, x1, y1) in pixel coords.
    """
    arr = np.array(rgb_img)
    # non-white mask (tolerant)
    nonwhite = (arr[:, :, 0] < 245) | (arr[:, :, 1] < 245) | (arr[:, :, 2] < 245)

    row_non = nonwhite.mean(axis=1)
    col_non = nonwhite.mean(axis=0)

    # consider "map-ish" rows/cols where nonwhite dominates
    rows = np.where(row_non > 0.5)[0]
    cols = np.where(col_non > 0.5)[0]
    if len(rows) < 50 or len(cols) < 50:
        # fallback: use broad bbox excluding small margins
        h, w = arr.shape[:2]
        return (int(w * 0.06), int(h * 0.05), int(w * 0.94), int(h * 0.86))

    # find longest contiguous segment for rows
    def longest_segment(ix):
        ix = ix.tolist()
        segs = []
        s = ix[0]
        p = ix[0]
        for v in ix[1:]:
            if v == p + 1:
                p = v
            else:
                segs.append((s, p))
                s = v
                p = v
        segs.append((s, p))
        segs.sort(key=lambda t: (t[1] - t[0]), reverse=True)
        return segs[0]

    r0, r1 = longest_segment(rows)
    # refine cols using only those rows
    sub = nonwhite[r0 : r1 + 1, :]
    col_sub = sub.mean(axis=0)
    cols2 = np.where(col_sub > 0.5)[0]
    if len(cols2) < 50:
        c0, c1 = longest_segment(cols)
    else:
        c0, c1 = longest_segment(cols2)

    # return bbox
    return (int(c0), int(r0), int(c1), int(r1))


def detect_colorbar_row(rgb_img: Image.Image):
    """
    Find an approximate colorbar row near the bottom by scanning for
    high horizontal color variability.
    Returns y index (pixel row) or None.
    """
    arr = np.array(rgb_img)
    h, w = arr.shape[:2]
    y_start = int(h * 0.78)
    y_end = int(h * 0.92)
    best_y = None
    best_score = -1

    for y in range(y_start, y_end, 2):
        row = arr[y, :, :]
        # count unique colors roughly by quantizing
        q = (row // 8).astype(np.uint8)  # 32-level quantization
        uniq = np.unique(q.reshape(-1, 3), axis=0)
        score = len(uniq)
        if score > best_score:
            best_score = score
            best_y = y

    if best_score < 40:
        return None
    return best_y


def build_colorbar_palette(rgb_img: Image.Image):
    """
    Build (colors, values) from the detected colorbar.
    colors: Nx3 uint8
    values: N floats from 0..100
    """
    arr = np.array(rgb_img)
    h, w = arr.shape[:2]
    y = detect_colorbar_row(rgb_img)
    if y is None:
        return None, "Colorbar not found."

    # sample a small band around y to stabilize
    band = arr[max(0, y - 2) : min(h, y + 3), :, :].mean(axis=0).astype(np.uint8)

    # find "colored" segment (exclude near-white background)
    not_bg = np.any(band < 245, axis=1)
    xs = np.where(not_bg)[0]
    if len(xs) < 100:
        return None, "Colorbar segment too small."

    x0, x1 = xs[0], xs[-1]
    strip = band[x0 : x1 + 1, :]  # M x 3

    # downsample to fixed N
    N = 256
    idx = np.linspace(0, len(strip) - 1, N).astype(int)
    colors = strip[idx, :]
    values = np.linspace(0, 100, N).astype(float)

    return (colors, values), None


def rgb_to_concentration_map(pixels_rgb: np.ndarray, palette_colors: np.ndarray, palette_values: np.ndarray):
    """
    Map pixels (HxWx3 uint8) to concentration (HxW float) by nearest color in palette.
    Implemented by compressing unique colors to reduce compute.
    """
    flat = pixels_rgb.reshape(-1, 3)
    # unique colors
    uniq, inv = np.unique(flat, axis=0, return_inverse=True)

    # compute nearest palette color (euclidean)
    # uniq: Ux3, palette: Px3 => distances UxP
    # do in chunks to avoid big memory
    P = palette_colors.astype(np.int16)
    U = uniq.astype(np.int16)
    nearest_vals = np.zeros((U.shape[0],), dtype=np.float32)

    chunk = 2000
    for i in range(0, U.shape[0], chunk):
        u = U[i : i + chunk]  # cx3
        # (c,1,3) - (1,P,3) => c,P,3
        diff = u[:, None, :] - P[None, :, :]
        dist2 = (diff * diff).sum(axis=2)  # c,P
        j = dist2.argmin(axis=1)  # c
        nearest_vals[i : i + chunk] = palette_values[j].astype(np.float32)

    mapped = nearest_vals[inv].reshape(pixels_rgb.shape[0], pixels_rgb.shape[1])
    return mapped


def compute_level3_bremen_proxy(region: str):
    """
    Returns:
      ok: bool
      info: dict with fields:
        map_crop (PIL Image) - for display
        roi_bbox (x0,y0,x1,y1) in crop pixels or None (pan-arctic)
        mean_conc (0..100)
        ice_frac_15 (0..100)
        risk_index (0..100)
        data_date_str (string or 'today')
        note (string)
    """
    try:
        img = load_bremen_png()
    except Exception as e:
        return False, {"note": f"Failed to load Bremen PNG: {e}"}

    # detect map frame and crop
    bbox = detect_map_frame_bbox(img)
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return False, {"note": "Failed to detect map frame bbox."}

    map_crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    arr = np.array(map_crop)
    H, W = arr.shape[:2]

    # palette from full image (colorbar is outside map frame)
    palette, perr = build_colorbar_palette(img)
    if palette is None:
        return False, {"note": f"Failed to build color palette: {perr}"}
    pal_colors, pal_vals = palette

    # land mask (green-ish), and nodata mask (gray-ish)
    R = arr[:, :, 0].astype(np.int16)
    G = arr[:, :, 1].astype(np.int16)
    B = arr[:, :, 2].astype(np.int16)

    land = (G > 120) & (R < 140) & (B < 140)
    nodata = (np.abs(R - G) < 10) & (np.abs(G - B) < 10) & (R > 120) & (R < 200)

    valid = (~land) & (~nodata)

    # map RGB -> concentration (0..100)
    conc = rgb_to_concentration_map(arr.astype(np.uint8), pal_colors, pal_vals)

    # apply masks: invalid pixels -> NaN
    conc = conc.astype(np.float32)
    conc[~valid] = np.nan

    # pick ROI
    roi_bbox = None
    roi_mask = None

    if region == "Entire Arctic (Pan-Arctic)":
        # radial mask inside map frame to reduce lower-lat contamination
        cx = int(POLE_FRAC[0] * W)
        cy = int(POLE_FRAC[1] * H)
        yy, xx = np.mgrid[0:H, 0:W]
        rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        rmax = np.nanmax(rr)
        # keep inside ~0.74 of max radius (empirical: closer to Arctic basin)
        roi_mask = rr <= (0.74 * rmax)
    else:
        if region not in ROI_FRAC:
            return False, {"note": f"ROI not defined for region: {region}"}
        fx0, fy0, fx1, fy1 = ROI_FRAC[region]
        rx0 = int(np.clip(fx0 * W, 0, W - 1))
        ry0 = int(np.clip(fy0 * H, 0, H - 1))
        rx1 = int(np.clip(fx1 * W, 0, W - 1))
        ry1 = int(np.clip(fy1 * H, 0, H - 1))
        # enforce proper ordering
        if rx1 <= rx0 + 5 or ry1 <= ry0 + 5:
            return False, {"note": f"ROI bbox too small for {region}."}
        roi_bbox = (rx0, ry0, rx1, ry1)
        roi_mask = np.zeros((H, W), dtype=bool)
        roi_mask[ry0:ry1, rx0:rx1] = True

    # compute stats inside ROI
    roi_conc = conc[roi_mask]
    roi_conc_valid = roi_conc[~np.isnan(roi_conc_valid := roi_conc)]  # safe extraction

    if roi_conc_valid.size < 100:
        return False, {"note": "ROI has too few valid ocean pixels (masking removed most pixels)."}

    mean_conc = float(np.nanmean(roi_conc_valid))

    # ice threshold: >= 15%
    ice_pixels = roi_conc_valid[roi_conc_valid >= 15.0]
    ice_frac_15 = float((ice_pixels.size / roi_conc_valid.size) * 100.0)
    mean_ice_conc = float(np.nanmean(ice_pixels)) if ice_pixels.size > 0 else 0.0

    # risk index (0..100): emphasize coverage + intensity among ice
    risk_index = float(np.clip(0.65 * ice_frac_15 + 0.35 * mean_ice_conc, 0, 100))

    return True, {
        "map_crop": map_crop,
        "roi_bbox": roi_bbox,
        "mean_conc": mean_conc,
        "ice_frac_15": ice_frac_15,
        "risk_index": risk_index,
        "data_date_str": "Bremen daily map (today URL)",
        "note": "Experimental image-derived proxy (ROI + colorbar quantization).",
    }


def draw_roi_overlay(map_crop: Image.Image, roi_bbox):
    # Draw ROI rectangle on the map_crop (yellow)
    if roi_bbox is None:
        return map_crop
    im = map_crop.copy()
    arr = np.array(im)
    # simple rectangle border using numpy (avoid ImageDraw import variability)
    x0, y0, x1, y1 = roi_bbox
    x0 = int(np.clip(x0, 0, arr.shape[1]-1))
    x1 = int(np.clip(x1, 0, arr.shape[1]-1))
    y0 = int(np.clip(y0, 0, arr.shape[0]-1))
    y1 = int(np.clip(y1, 0, arr.shape[0]-1))
    # thickness
    t = 3
    yellow = np.array([255, 220, 0], dtype=np.uint8)
    arr[y0:y0+t, x0:x1] = yellow
    arr[y1-t:y1, x0:x1] = yellow
    arr[y0:y1, x0:x0+t] = yellow
    arr[y0:y1, x1-t:x1] = yellow
    return Image.fromarray(arr)


# =====================================================
# Mobile-first controls (top, not sidebar)
# =====================================================
st.markdown(
    """
    <style>
    /* Slightly tighter spacing for mobile */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h1, h2, h3 { letter-spacing: 0.2px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧊 POLAR CUDA")
st.caption("Cryospheric Unified Decision Assistant")
st.caption(f"Today (local): {today}")

with st.expander("⚙️ Controls", expanded=True):
    region = st.selectbox("Region", REGIONS, index=0)
    data_level = st.radio(
        "Data Level",
        [
            "Level 3 (Bremen AMSR2 PNG – Experimental Regional Proxy)",
            "Level 2 (NOAA/NSIDC Extent – Fallback Proxy)",
        ],
        index=0,
    )

tab_dashboard, tab_about, tab_definition, tab_logo = st.tabs(
    ["🧭 Dashboard", "📄 About (IMO/Gov)", "📚 Formal Definition", "🎨 Logo/Icon Concept"]
)

# =====================================================
# TAB 1: Dashboard
# =====================================================
with tab_dashboard:
    st.subheader("Regional Navigation Risk (Status-Based)")
    st.caption(f"Selected Region: {region}")

    used_level = None
    risk_index = None
    status = None
    color = None

    # -----------------------------
    # Try Level 3 if selected
    # -----------------------------
    if data_level.startswith("Level 3"):
        ok, info = compute_level3_bremen_proxy(region)
        if ok:
            used_level = "Level 3 (Bremen AMSR2 PNG – Experimental Proxy)"
            risk_index = round(float(info["risk_index"]), 1)
            status, color = classify_status(risk_index)

            st.caption(f"Data Level Used: {used_level}")
            st.caption(f"Bremen-derived mean concentration (proxy): {info['mean_conc']:.1f}%")
            st.caption(f"Ice coverage ≥15% within ROI (proxy): {info['ice_frac_15']:.1f}%")

            # ROI overlay image
            overlay = draw_roi_overlay(info["map_crop"], info["roi_bbox"])
            st.image(overlay, caption="Bremen AMSR2 PNG (map frame crop + ROI overlay)", use_container_width=True)

        else:
            st.warning("Level 3 dataset (Bremen PNG proxy) could not be computed. Switching to Level 2 fallback.")
            st.caption(f"Reason: {info.get('note','Unknown error')}")
            data_level = "Level 2 (NOAA/NSIDC Extent – Fallback Proxy)"

    # -----------------------------
    # Level 2 fallback or selected
    # -----------------------------
    if data_level.startswith("Level 2"):
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

        used_level = "Level 2 (NOAA/NSIDC Extent – Seasonal Normalization Proxy)"
        st.caption(f"Data Level Used: {used_level}")
        st.caption(f"NSIDC Data Date (UTC): {data_date}")
        st.caption(f"Pan-Arctic extent (million km²): {extent_today:.2f}")

        winter_max, summer_min = REGION_CLIMATOLOGY[region]
        denom = (winter_max - summer_min) if (winter_max - summer_min) != 0 else 1e-9
        risk_index = round(float(np.clip(((extent_today - summer_min) / denom) * 100.0, 0, 100)), 1)

        status, color = classify_status(risk_index)

    # -----------------------------
    # Display: gauge + status
    # -----------------------------
    if risk_index is None:
        st.error("Unable to compute risk index.")
        st.stop()

    st.markdown(f"### {color} **{status}**")
    st.markdown(f"**Risk Index:** {risk_index:.1f} / 100")

    st.markdown(svg_semi_gauge(risk_index), unsafe_allow_html=True)
    st.progress(int(np.clip(risk_index, 0, 100)))

    st.markdown("---")
    st.markdown(
        f"""
**Operational Interpretation (Non-Directive)**

- This indicator is designed for **situational awareness**, not route command.
- **Level 3 (Bremen PNG)** is an **experimental, image-derived regional proxy** computed within an operational ROI.
- **Level 2 (NSIDC extent)** is a **fallback seasonal proxy** and does **not** represent local concentration/thickness/pressure.

Final operational decisions remain with operators and vessel masters.
"""
    )

# =====================================================
# TAB 2: About (IMO/Gov)
# =====================================================
with tab_about:
    st.header("About – POLAR CUDA (IMO/Government Style)")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is a decision-support framework
designed to enhance situational awareness for navigation and operations in polar and ice-affected waters.

The system integrates publicly available cryospheric information into a unified, interpretable status-based index.
POLAR CUDA supports informed operational judgment without prescribing actions or replacing official ice services.

POLAR CUDA is an **assistant**, not a directive system. It does not constitute navigational guidance and does not
supersede the authority or responsibility of vessel masters, operators, or national ice services.
"""
    )

# =====================================================
# TAB 3: Formal Definition
# =====================================================
with tab_definition:
    st.header("Formal Definition – Academic / White Paper")
    st.markdown(
        """
**POLAR CUDA (Cryospheric Unified Decision Assistant)** is defined as a modular decision-support system that converts
cryospheric observations into a unified, interpretable risk/status metric for polar operations.

Level 2 implements a robust, low-dependency seasonal proxy using pan-Arctic sea ice extent normalized against
region-specific operational reference ranges.

Level 3 extends the framework with an experimental regional proxy derived from image-based quantization of daily
sea-ice concentration maps within an operational region of interest (ROI). The framework prioritizes transparency,
robustness to format variability, and non-directive interpretation.
"""
    )

# =====================================================
# TAB 4: Logo/Icon Concept
# =====================================================
with tab_logo:
    st.header("Logo / Icon Concept – Designer Brief")
    st.markdown(
        """
**Concept Statement**  
*POLAR CUDA visualizes the moment where ice data becomes decision awareness.*

**Design Keywords**  
- Minimal, instrument-like  
- Calm, authoritative, non-alarmist  
- Operational (not “command UI”)  

**Icon Concept**  
- A **half-dial / gauge arc** suggesting situational status rather than control  
- A subtle **ice-grid motif** (abstract, not literal)  
- Muted green→yellow→orange→red semantics  

**Avoid**  
- Emergency alert look  
- Gaming UI  
- Military command interface  

**One-line instruction**  
“This is a tool you glance at before deciding — not something that tells you what to do.”
"""
    )

# =====================================================
# Footer: Data source & legal notice
# =====================================================
st.markdown("---")
st.caption(
    """
**Data Source & Legal Notice**

- **Level 2 (Fallback):** Sea ice extent data are provided by **NOAA / NSIDC Sea Ice Index (G02135), Version 4**
  and distributed under NOAA/NSIDC open data access principles.
- **Level 3 (Experimental):** Regional proxy is derived from the publicly accessible daily imagery
  **University of Bremen AMSR2 sea-ice concentration map (PNG)** by **image colorbar quantization within an ROI**
  for situational awareness. For authoritative concentration products, use official gridded datasets and ice services.

This application provides **situational awareness only** and does not replace official ice services, onboard navigation systems,
or the judgment of vessel masters. Final operational decisions remain the responsibility of operators and vessel masters.
"""
)
