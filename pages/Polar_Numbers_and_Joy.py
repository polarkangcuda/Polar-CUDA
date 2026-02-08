from __future__ import annotations

import base64
import cmath
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional

import streamlit as st


# ============================================================
# 0) Runtime / Time
# ============================================================
KST = timezone(timedelta(hours=9))


def now_kst_dt() -> datetime:
    return datetime.now(KST)


def now_kst_str() -> str:
    return now_kst_dt().strftime("%Y-%m-%d %H:%M KST")


# ============================================================
# 1) Page config
# ============================================================
st.set_page_config(
    page_title="Polar Numbers — Responsibility, not Control",
    page_icon="❄🎧",
    layout="centered",
)


# ============================================================
# 2) Session State (robust defaults)
# ============================================================
def ss_init() -> None:
    defaults = {
        "lang": "한국어",
        "mode": "Researcher",  # Researcher | Public
        "concept": "natural_integers",
        "log": [],  # list of dict entries
        "playlist_shuffle_start": False,
        "playlist_autoplay": True,
        "playlist_loop": True,
        "playlist_show_names": True,
        "ui_compact": False,
        "seed": None,  # optional reproducibility seed
        "inputs": {
            "count_points": 12,
            "temp_c": -1.83,
            "salinity_psu": 34.27,
            "ice_thickness_m": 0.06,
            "radius_km": 7.5,
            "days": 3,
            "complex_re": 2.0,
            "complex_im": 1.5,
            "confidence": 0.75,
            "err_margin": 0.08,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


ss_init()


# ============================================================
# 3) i18n helpers
# ============================================================
def t(ko: str, en: str) -> str:
    return ko if st.session_state["lang"] == "한국어" else en


def ui_label(key: str) -> str:
    labels = {
        "language": ("Language / 언어 선택", "Language / 언어 선택"),
        "mode": ("모드", "Mode"),
        "public": ("일반인(학습/전시)", "Public (learning/exhibit)"),
        "researcher": ("연구자(현업)", "Researcher (professional)"),
        "concept": ("숫자 개념", "Number concept"),
        "music": ("음악", "Music"),
        "upload": ("음악 파일 업로드 (.wav, .mp3)", "Upload music files (.wav, .mp3)"),
        "settings": ("설정", "Settings"),
        "log": ("기록", "Log"),
        "export": ("내보내기", "Export"),
        "reflection": ("오늘의 한 줄", "One line for today"),
        "write_optional": ("원할 때만 적으세요.", "Write only if you want to."),
    }
    ko, en = labels[key]
    return t(ko, en)


# ============================================================
# 4) Logging utilities
# ============================================================
def log_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    entry = {
        "time_kst": now_kst_str(),
        "event": event,
        "payload": payload or {},
        "lang": st.session_state["lang"],
        "mode": st.session_state["mode"],
    }
    st.session_state["log"].append(entry)


def export_log_jsonl() -> bytes:
    lines = [json.dumps(x, ensure_ascii=False) for x in st.session_state["log"]]
    return ("\n".join(lines) + "\n").encode("utf-8")


def export_log_txt() -> bytes:
    out = []
    out.append("Polar Numbers — Activity Log")
    out.append("--------------------------------")
    out.append(f"Exported: {now_kst_str()}")
    out.append("")
    for i, e in enumerate(st.session_state["log"], start=1):
        out.append(f"[{i}] {e['time_kst']} | {e['event']}")
        if e.get("payload"):
            out.append("  " + json.dumps(e["payload"], ensure_ascii=False))
    out.append("")
    return "\n".join(out).encode("utf-8")


# ============================================================
# 5) Concepts (data-driven architecture)
#    Add/modify cards here to scale the app.
# ============================================================
@dataclass(frozen=True)
class ConceptCard:
    key: str
    title_ko: str
    title_en: str
    tagline_ko: str
    tagline_en: str
    public_ko: str
    public_en: str
    researcher_ko: str
    researcher_en: str


CONCEPTS: List[ConceptCard] = [
    ConceptCard(
        key="natural_integers",
        title_ko="1⃣ 자연수 · 정수",
        title_en="1⃣ Natural Numbers & Integers",
        tagline_ko="개수와 횟수 — 재현성을 만드는 숫자",
        tagline_en="Counts & events — numbers that make work reproducible",
        public_ko="‘몇 번 했는가’는 과학에서 가장 기본적인 증거입니다.",
        public_en="‘How many times’ is the simplest evidence in science.",
        researcher_ko=(
            "Station/cast count, deployment count, failure count(음수 포함)은 "
            "현장 재현성과 QA/QC의 출발점입니다. 정수는 ‘성공’만이 아니라 ‘결함’도 기록합니다."
        ),
        researcher_en=(
            "Counts of stations/casts/deployments/failures (including negatives) "
            "are the foundation of reproducibility and QA/QC. Integers record defects, not only successes."
        ),
    ),
    ConceptCard(
        key="reals_decimals",
        title_ko="2⃣ 유리수 · 실수",
        title_en="2⃣ Rational & Real Numbers",
        tagline_ko="소수점 — 작은 차이가 계절을 바꾼다",
        tagline_en="Decimals — small differences can change a season",
        public_ko="0.1의 차이는 ‘사소함’이 아니라 ‘변곡점’일 수 있습니다.",
        public_en="A difference of 0.1 can be a turning point, not a detail.",
        researcher_ko=(
            "극지 해양은 -1.83°C 같은 소수점의 세계입니다. "
            "분해능/정확도/보정/오차전파를 함께 적지 않으면 수치가 의미를 잃습니다."
        ),
        researcher_en=(
            "Polar oceans live in decimals (e.g., -1.83°C). "
            "Without resolution/accuracy/calibration/uncertainty propagation, numbers lose meaning."
        ),
    ),
    ConceptCard(
        key="irrational_pi",
        title_ko="3⃣ 무리수 · π",
        title_en="3⃣ Irrational Numbers & π",
        tagline_ko="곡선 — 극지에는 직선 경계가 거의 없다",
        tagline_en="Curves — boundaries are rarely straight",
        public_ko="빙산, 소용돌이, 얼음 가장자리는 둥글고 휘어 있습니다.",
        public_en="Ice edges, bergs, and eddies are round and curved.",
        researcher_ko=(
            "면적/둘레/곡률은 격자/투영/분해능에 민감합니다. "
            "π는 ‘계산 도구’이기보다 ‘세계가 네모가 아님’을 상기시키는 표지입니다."
        ),
        researcher_en=(
            "Area/perimeter/curvature depend on grid/projection/resolution. "
            "π is less a tool than a reminder: the world is not square."
        ),
    ),
    ConceptCard(
        key="transcendent_e",
        title_ko="4⃣ 초월수 e",
        title_en="4⃣ Transcendental Numbers (e)",
        tagline_ko="지수 — 선형이 아닌 가속의 언어",
        tagline_en="Exponentials — language of acceleration, not lines",
        public_ko="처음엔 천천히, 어느 순간 갑자기. 극지 변화는 종종 그렇습니다.",
        public_en="Slow at first, then suddenly. Polar change is often like that.",
        researcher_ko=(
            "해빙/열/생물 생산성 변화는 비선형이 흔합니다. "
            "e는 예측을 강요하지 않고, ‘가속 가능성’을 경계로 남깁니다."
        ),
        researcher_en=(
            "Sea ice/heat/bioproductivity changes are often nonlinear. "
            "e doesn’t force forecasting; it records the possibility of acceleration as a boundary."
        ),
    ),
    ConceptCard(
        key="complex",
        title_ko="5⃣ 복소수",
        title_en="5⃣ Complex Numbers",
        tagline_ko="위상 — 보이지 않는 흐름을 기록하는 언어",
        tagline_en="Phase — recording invisible motion",
        public_ko="방향과 리듬(위상)이 함께 있어야 ‘움직임’이 됩니다.",
        public_en="Direction and rhythm (phase) together make ‘motion’.",
        researcher_ko=(
            "파랑/조석/관성진동/회전류는 위상이 핵심입니다. "
            "복소 표현은 크기와 위상을 한 번에 보존합니다."
        ),
        researcher_en=(
            "Waves/tides/inertial oscillations/rotating flows are phase-driven. "
            "Complex representation preserves magnitude and phase together."
        ),
    ),
    ConceptCard(
        key="probability",
        title_ko="6⃣ 확률과 통계",
        title_en="6⃣ Probability & Statistics",
        tagline_ko="불확실성 — ‘정답’ 대신 신뢰구간",
        tagline_en="Uncertainty — intervals instead of ‘answers’",
        public_ko="과학은 ‘확신’이 아니라 ‘얼마나 믿을 수 있는가’를 함께 말합니다.",
        public_en="Science speaks not only ‘what’, but ‘how sure’.",
        researcher_ko=(
            "극지는 관측 공백과 구조적 불확실성이 큽니다. "
            "수치는 단독이 아니라 CI/SE/오차모형과 함께 제시되어야 합니다."
        ),
        researcher_en=(
            "Polar work faces gaps and structural uncertainties. "
            "Numbers must be presented with CI/SE/error models, not alone."
        ),
    ),
]


def concept_by_key(key: str) -> ConceptCard:
    for c in CONCEPTS:
        if c.key == key:
            return c
    return CONCEPTS[0]


# ============================================================
# 6) Sidebar: controls & exports
# ============================================================
with st.sidebar:
    st.markdown(f"## {ui_label('settings')}")
    st.session_state["lang"] = st.radio(
        ui_label("language"),
        ["한국어", "English"],
        horizontal=True,
        index=0 if st.session_state["lang"] == "한국어" else 1,
    )

    mode_label = st.radio(
        ui_label("mode"),
        [ui_label("researcher"), ui_label("public")],
        index=0 if st.session_state["mode"] == "Researcher" else 1,
    )
    st.session_state["mode"] = "Researcher" if mode_label == ui_label("researcher") else "Public"

    st.session_state["ui_compact"] = st.checkbox(
        t("컴팩트 UI", "Compact UI"),
        value=st.session_state["ui_compact"],
        help=t("현장/작은 화면에서 스크롤을 줄입니다.", "Reduces scrolling on small/field screens."),
    )

    st.divider()

    # Playlist settings
    st.markdown(f"## {ui_label('music')}")
    st.session_state["playlist_autoplay"] = st.checkbox(
        t("자동 재생", "Autoplay"),
        value=st.session_state["playlist_autoplay"],
    )
    st.session_state["playlist_loop"] = st.checkbox(
        t("끝나면 다시 처음(순환)", "Loop playlist"),
        value=st.session_state["playlist_loop"],
    )
    st.session_state["playlist_shuffle_start"] = st.checkbox(
        t("시작 곡 무작위", "Random start track"),
        value=st.session_state["playlist_shuffle_start"],
        help=t("첫 곡만 무작위로 시작합니다(이후는 순차).", "Randomizes only the first track (then sequential)."),
    )
    st.session_state["playlist_show_names"] = st.checkbox(
        t("곡 목록 표시", "Show track list"),
        value=st.session_state["playlist_show_names"],
    )

    st.divider()

    # Reproducibility seed (optional)
    seed_str = st.text_input(
        t("재현용 시드(선택)", "Seed for reproducibility (optional)"),
        value="" if st.session_state["seed"] is None else str(st.session_state["seed"]),
        help=t("확률 예시를 같은 값으로 유지하고 싶을 때 사용합니다.", "Use to keep probability examples stable."),
    )
    if seed_str.strip() == "":
        st.session_state["seed"] = None
    else:
        try:
            st.session_state["seed"] = int(seed_str.strip())
        except ValueError:
            st.warning(t("시드는 정수여야 합니다.", "Seed must be an integer."))

    st.divider()

    # Export log
    st.markdown(f"## {ui_label('log')}")
    st.caption(t("이 앱은 외부로 전송하지 않고, 내부 기록만 남깁니다.", "This app keeps only local session logs."))
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            t("JSONL", "JSONL"),
            data=export_log_jsonl(),
            file_name=f"polar_numbers_log_{now_kst_dt().strftime('%Y%m%d_%H%M')}.jsonl",
            mime="application/json",
        )
    with col_b:
        st.download_button(
            t("TXT", "TXT"),
            data=export_log_txt(),
            file_name=f"polar_numbers_log_{now_kst_dt().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )
    if st.button(t("기록 초기화", "Clear log")):
        st.session_state["log"] = []
        log_event("log_cleared", {})
        st.success(t("기록을 초기화했습니다.", "Log cleared."))


# ============================================================
# 7) Main header
# ============================================================
st.markdown("# ❄ Polar Numbers")
st.markdown(
    t(
        "### 자연을 계산하지 않고, 오해하지 않기 위한 숫자",
        "### Numbers used not to calculate nature, but to avoid misunderstanding it",
    )
)

st.markdown(
    t(
        """
이 페이지는 세상을 통제하지 않습니다.  
관측자의 책임을 기록할 뿐입니다.

- 예측 없음  
- 최적화 없음  
- 확실성 없음  

숫자는 **겸손을 가르치는 언어**입니다.
""",
        """
This page does not control the world.  
It only records the observer’s responsibility.

- No prediction  
- No optimization  
- No certainty  

Numbers are a **language of humility**.
""",
    )
)

st.caption(f"Opened at: {now_kst_str()}")
st.divider()


# ============================================================
# 8) Music: Continuous playlist player (robust)
# ============================================================
st.markdown("## 🎧 " + t("음악", "Music"))

uploaded_files = st.file_uploader(
    ui_label("upload"),
    type=["wav", "mp3"],
    accept_multiple_files=True,
)

def build_playlist(files) -> List[Dict[str, str]]:
    playlist: List[Dict[str, str]] = []
    for f in files:
        encoded = base64.b64encode(f.read()).decode("utf-8")
        playlist.append({"name": f.name, "src": f"data:{f.type};base64,{encoded}"})
    return playlist

if uploaded_files:
    playlist = build_playlist(uploaded_files)
    playlist_json = json.dumps(playlist, ensure_ascii=False)

    # Optional: show names
    if st.session_state["playlist_show_names"]:
        st.caption(t("업로드된 트랙", "Uploaded tracks") + f": {len(playlist)}")
        if not st.session_state["ui_compact"]:
            st.write([p["name"] for p in playlist])

    autoplay_js = "autoplay" if st.session_state["playlist_autoplay"] else ""
    # loop is handled by JS, not by <audio loop>, because we want playlist looping
    shuffle_start = "true" if st.session_state["playlist_shuffle_start"] else "false"
    loop_playlist = "true" if st.session_state["playlist_loop"] else "false"

    # Embed HTML/JS playlist player
    st.components.v1.html(
        f"""
        <audio id="player" controls {autoplay_js} style="width:100%; margin-top:10px;"></audio>

        <script>
        const playlist = {playlist_json};
        const player = document.getElementById("player");
        let index = 0;

        // Random start (only first pick)
        const shuffleStart = {shuffle_start};
        if (shuffleStart && playlist.length > 1) {{
            index = Math.floor(Math.random() * playlist.length);
        }}

        const loopPlaylist = {loop_playlist};

        function playTrack(i) {{
            if (!playlist[i]) return;
            player.src = playlist[i].src;
            const playPromise = player.play();
            if (playPromise !== undefined) {{
                playPromise.catch(_ => {{
                    // Autoplay may be blocked by browser policies
                    // User can press play manually.
                }});
            }}
        }}

        player.addEventListener("ended", () => {{
            if (playlist.length === 0) return;
            const next = index + 1;

            // If end reached
            if (next >= playlist.length) {{
                if (loopPlaylist) {{
                    index = 0;
                    playTrack(index);
                }} else {{
                    // stop at end
                }}
            }} else {{
                index = next;
                playTrack(index);
            }}
        }});

        // Start
        playTrack(index);
        </script>
        """,
        height=120,
    )
    log_event("playlist_loaded", {"tracks": len(playlist)})
else:
    st.caption(t("침묵도 하나의 데이터입니다.", "Silence is also a valid dataset."))
    log_event("playlist_empty", {})

st.divider()


# ============================================================
# 9) Concept selector
# ============================================================
st.markdown("## " + t("숫자 개념", "Number concepts"))

concept_options = {f"{c.title_ko} — {c.tagline_ko}": c.key for c in CONCEPTS} if st.session_state["lang"] == "한국어" else \
                  {f"{c.title_en} — {c.tagline_en}": c.key for c in CONCEPTS}

selected_label = st.selectbox(
    t("오늘은 어떤 숫자를 ‘번역 언어’로 볼까요?", "Which number should we treat as a translation language today?"),
    options=list(concept_options.keys()),
    index=[c.key for c in CONCEPTS].index(st.session_state["concept"]) if st.session_state["concept"] in [c.key for c in CONCEPTS] else 0,
)
st.session_state["concept"] = concept_options[selected_label]
c = concept_by_key(st.session_state["concept"])
log_event("concept_selected", {"concept": c.key})


# ============================================================
# 10) Render concept card + interactive “feel it” section
# ============================================================
def render_card(concept: ConceptCard) -> None:
    title = t(concept.title_ko, concept.title_en)
    tagline = t(concept.tagline_ko, concept.tagline_en)
    st.markdown(f"### {title}")
    st.caption(tagline)

    if st.session_state["mode"] == "Public":
        st.info(t(concept.public_ko, concept.public_en))
    else:
        st.success(t(concept.researcher_ko, concept.researcher_en))


def set_seed_if_any() -> None:
    if st.session_state["seed"] is not None:
        random.seed(st.session_state["seed"])


def render_interactive(concept_key: str) -> None:
    inp = st.session_state["inputs"]

    if concept_key == "natural_integers":
        col1, col2 = st.columns(2)
        with col1:
            inp["count_points"] = st.slider(
                t("관측 지점 수(자연수)", "Number of stations (natural number)"),
                1, 50, int(inp["count_points"]),
            )
        with col2:
            sensor_fail = st.number_input(
                t("고장/결함 기록(정수, 음수 가능)", "Failure/defect record (integer; negatives allowed)"),
                value=int(-1),
                step=1,
            )
        st.markdown(
            t(
                f"👉 **{inp['count_points']}**는 ‘계획’이 아니라 **현장 기록의 단위**입니다. "
                f"정수 **{sensor_fail}**는 ‘실패도 데이터’라는 선언입니다.",
                f"👉 **{inp['count_points']}** is not a plan; it’s a **unit of field record**. "
                f"Integer **{sensor_fail}** declares that failures are data too.",
            )
        )
        log_event("interactive_natural_integers", {"count_points": inp["count_points"], "sensor_failures": sensor_fail})

    elif concept_key == "reals_decimals":
        col1, col2, col3 = st.columns(3)
        with col1:
            inp["temp_c"] = st.slider(t("수온 (°C)", "Temperature (°C)"), -2.5, 1.0, float(inp["temp_c"]), 0.01)
        with col2:
            inp["salinity_psu"] = st.slider(t("염분 (PSU)", "Salinity (PSU)"), 30.0, 36.0, float(inp["salinity_psu"]), 0.01)
        with col3:
            inp["ice_thickness_m"] = st.slider(t("해빙 두께 변화 (m)", "Ice thickness change (m)"), -0.50, 0.50, float(inp["ice_thickness_m"]), 0.01)

        st.markdown(
            t(
                "👉 소수점은 ‘예쁜 숫자’가 아니라 **분해능·보정·오차**를 함께 요구합니다.",
                "👉 Decimals are not pretty numbers; they demand **resolution, calibration, and uncertainty**.",
            )
        )
        log_event("interactive_reals_decimals", {"temp_c": inp["temp_c"], "salinity_psu": inp["salinity_psu"], "ice_thickness_m": inp["ice_thickness_m"]})

    elif concept_key == "irrational_pi":
        inp["radius_km"] = st.slider(t("원형(가정) 반경 (km)", "Assumed circular radius (km)"), 0.5, 50.0, float(inp["radius_km"]), 0.5)
        area_km2 = math.pi * (inp["radius_km"] ** 2)
        st.markdown(
            t(
                f"👉 반경 **{inp['radius_km']:.1f} km**의 원을 가정하면 면적은 **{area_km2:.2f} km²** 입니다.",
                f"👉 Assuming a circle of radius **{inp['radius_km']:.1f} km**, area is **{area_km2:.2f} km²**.",
            )
        )
        st.caption(
            t(
                "※ 연구자 메모: 투영/격자/경계 추출 방식이 달라지면 같은 π라도 다른 답이 됩니다.",
                "※ Researcher note: projection/grid/edge-detection choices change the result even with the same π.",
            )
        )
        log_event("interactive_irrational_pi", {"radius_km": inp["radius_km"], "area_km2": area_km2})

    elif concept_key == "transcendent_e":
        inp["days"] = st.slider(t("시간 창 (일)", "Time window (days)"), 1, 14, int(inp["days"]))
        # Conceptual exponential factor (not prediction)
        factor = math.e ** (inp["days"] / 3.0)
        st.markdown(
            t(
                f"👉 이는 예측이 아니라 ‘가속 가능성’을 상기시키는 표지입니다. "
                f"개념적 지수 요인: **{factor:.2f}** (e^(days/3))",
                f"👉 This is not a forecast; it’s a marker of possible acceleration. "
                f"Conceptual exponential factor: **{factor:.2f}** (e^(days/3))",
            )
        )
        log_event("interactive_transcendent_e", {"days": inp["days"], "factor": factor})

    elif concept_key == "complex":
        col1, col2 = st.columns(2)
        with col1:
            inp["complex_re"] = st.slider(t("실수부(동서 성분)", "Real part (E–W component)"), -5.0, 5.0, float(inp["complex_re"]), 0.1)
        with col2:
            inp["complex_im"] = st.slider(t("허수부(남북 성분)", "Imag part (N–S component)"), -5.0, 5.0, float(inp["complex_im"]), 0.1)

        z = complex(inp["complex_re"], inp["complex_im"])
        mag = abs(z)
        ph = cmath.phase(z)
        st.markdown(
            t(
                f"👉 복소 벡터 **{z}** | 크기 **{mag:.2f}** | 위상(방향) **{ph:.2f} rad**",
                f"👉 Complex vector **{z}** | magnitude **{mag:.2f}** | phase **{ph:.2f} rad**",
            )
        )
        st.caption(
            t(
                "※ 연구자 메모: 조석/파랑/관성진동 해석에서 위상은 ‘숫자’가 아니라 ‘시간-공간 정렬’입니다.",
                "※ Researcher note: in tides/waves/inertial motions, phase is time-space alignment, not just a number.",
            )
        )
        log_event("interactive_complex", {"re": inp["complex_re"], "im": inp["complex_im"], "magnitude": mag, "phase_rad": ph})

    elif concept_key == "probability":
        set_seed_if_any()

        inp["confidence"] = st.slider(
            t("신뢰 수준(예시)", "Confidence (example)"),
            0.50, 0.99, float(inp["confidence"]), 0.01
        )
        inp["err_margin"] = st.slider(
            t("오차 범위(±)", "Error margin (±)"),
            0.01, 0.30, float(inp["err_margin"]), 0.01
        )

        # A gentle, non-claim phrasing that matches your philosophy
        lower = max(0.0, inp["confidence"] - inp["err_margin"])
        upper = min(1.0, inp["confidence"] + inp["err_margin"])

        st.markdown(
            t(
                f"👉 이 수치는 **정답이 아니라 범위**입니다: **[{lower:.2f}, {upper:.2f}]**",
                f"👉 This is **not an answer, but an interval**: **[{lower:.2f}, {upper:.2f}]**",
            )
        )

        # A small “uncertainty language” sampler (expert-friendly)
        phrases_ko = [
            "관측 오차와 구조적 불확실성을 분리해 기록한다.",
            "모델이 맞는가가 아니라, 어디서 틀릴 수 있는지를 먼저 묻는다.",
            "신뢰구간을 말하는 것은 약함이 아니라 책임이다.",
        ]
        phrases_en = [
            "Record measurement error separately from structural uncertainty.",
            "Ask not whether the model is right, but where it may fail first.",
            "Stating intervals is not weakness; it is responsibility.",
        ]
        st.caption(t("불확실성 언어 예시:", "Uncertainty language samples:"))
        st.write(random.choice(phrases_ko if KR else phrases_en))

        log_event("interactive_probability", {"confidence": inp["confidence"], "err_margin": inp["err_margin"], "interval": [lower, upper]})

    else:
        st.caption(t("이 개념의 상호작용 모듈이 아직 없습니다.", "No interactive module yet for this concept."))


# Render selected concept
render_card(c)

if not st.session_state["ui_compact"]:
    st.markdown("---")

st.markdown("#### " + t("직접 ‘느껴보기’", "Try to ‘feel it’"))
render_interactive(c.key)

st.divider()


# ============================================================
# 11) Reflection + Exportable note (field-friendly)
# ============================================================
st.markdown("## ✍ " + ui_label("reflection"))
reflection = st.text_input(
    ui_label("write_optional"),
    placeholder=t("오늘, 숫자가 나를 겸손하게 만든 순간은?", "Today, when did a number make me humble?"),
)

note = {
    "time_kst": now_kst_str(),
    "lang": st.session_state["lang"],
    "mode": st.session_state["mode"],
    "concept": c.key,
    "inputs": st.session_state["inputs"],
    "reflection": reflection if reflection else "",
    "principle": t(
        "숫자는 지배의 수단이 아니라 책임의 증거다.",
        "Numbers are not tools of dominance; they are evidence of responsibility.",
    ),
}
log_event("reflection_updated", {"has_text": bool(reflection)})

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        t("오늘 기록 저장 (JSON)", "Save today (JSON)"),
        data=(json.dumps(note, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        file_name=f"polar_numbers_note_{now_kst_dt().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
    )
with col2:
    txt = (
        "Polar Numbers — Daily Note\n"
        "-------------------------\n"
        f"Time: {note['time_kst']}\n"
        f"Language: {note['lang']}\n"
        f"Mode: {note['mode']}\n"
        f"Concept: {note['concept']}\n"
        "\n"
        "Reflection:\n"
        f"{note['reflection'] if note['reflection'] else '(no entry)'}\n"
        "\n"
        f"Principle:\n{note['principle']}\n"
    )
    st.download_button(
        t("오늘 기록 저장 (TXT)", "Save today (TXT)"),
        data=txt.encode("utf-8"),
        file_name=f"polar_numbers_note_{now_kst_dt().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
    )

st.divider()

# ============================================================
# 12) Footer
# ============================================================
st.caption(
    t(
        "숫자가 많아질수록 우리는 더 겸손해져야 한다. 숫자는 지배의 수단이 아니라 책임의 증거다.",
        "The more numbers we collect, the more humble we must become. Numbers are evidence of responsibility, not dominance.",
    )
)
