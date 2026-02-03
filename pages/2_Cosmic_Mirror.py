# pages/3_Reflection_Library.py
import streamlit as st
from datetime import datetime

# =========================================================
# Cosmic Mirror — Reflection Without Prediction
# Reflection Library (175 templates) / No LLM / No API
# =========================================================

st.set_page_config(
    page_title="Cosmic Mirror — Reflection Library (175)",
    page_icon="🪞",
    layout="wide",
)

# -----------------------------
# Language toggle
# -----------------------------
LANG = st.radio("Language / 언어", ["English", "한국어"], horizontal=True)

def t(en: str, ko: str) -> str:
    return en if LANG == "English" else ko

st.title(t("Cosmic Mirror — Reflection Library (175)",
           "Cosmic Mirror — Reflection Library (175)"))

st.caption(t(
    "This is not divination. These are reflection templates designed to be filled with symbolic coordinates (place) and a living question (optional).",
    "이것은 점술이 아닙니다. 출생지(상징)와 ‘살아 있는 질문(선택)’을 채워 넣을 수 있도록 설계된 성찰 템플릿 목록입니다."
))

with st.expander(t("Philosophy baked into this library",
                   "이 라이브러리에 내장된 철학"), expanded=False):
    st.markdown(t(
        """
- No prediction. No authority invoked. Only reflection and responsibility.
- Birth information is treated as a symbolic coordinate, not destiny.
- Reality is approached as relationship and observation, not fixed substance.
- The “self” is not a rigid object; it is a stance that can be clarified.
- The middle way: neither “everything is fixed” nor “everything is illusion.”
- Leaving a question empty is also a form of courage.
- The mirror is a record: you can return, compare, and refine your stance.
        """.strip(),
        """
- 예언하지 않습니다. 권위를 호출하지 않습니다. 성찰과 책임만 남깁니다.
- 출생 정보는 운명이 아니라 ‘상징 좌표’로만 취급합니다.
- 실재는 고정된 물질이 아니라 관계·관찰·상호작용으로 접근합니다.
- ‘나’는 단단한 실체가 아니라 지금 선택하는 ‘입장(stance)’입니다.
- 중도: “모든 것이 정해졌다”와 “모든 것이 환상이다”의 극단을 넘습니다.
- 질문을 비워두는 것 또한 용기입니다.
- 이 거울은 기록입니다: 다시 돌아와 비교하고, 입장을 다듬게 합니다.
        """.strip()
    ))

st.divider()

# =========================================================
# 175 templates = 7 * 5 * 5
# (Era tone) * (Time tone) * (Place archetype)
# =========================================================

ERA_TONES_EN = [
    "a time shaped by rebuilding and patience",
    "a time shaped by expansion and responsibility",
    "a time shaped by restraint and endurance",
    "a time shaped by questioning inherited structures",
    "a time shaped by quiet consolidation",
    "a time shaped by rapid change and re-learning",
    "a time shaped by integration and transmission",
]
ERA_TONES_KO = [
    "복구와 인내가 삶의 리듬이 되던 시기",
    "확장과 책임이 함께 커지던 시기",
    "절제와 견딤이 실력을 만들던 시기",
    "상속된 구조를 의심하고 다시 묻던 시기",
    "조용한 축적과 정리가 힘이 되던 시기",
    "급격한 변화 속에서 다시 배우던 시기",
    "통합과 전수가 과제가 되던 시기",
]

TIME_TONES_EN = [
    "beginnings",
    "emergence",
    "orientation",
    "commitment",
    "integration",
]
TIME_TONES_KO = [
    "시작",
    "발아",
    "정렬",
    "헌신",
    "통합",
]

PLACE_ARCH_EN = [
    "a point of origin, not a boundary",
    "a reminder that belonging precedes ambition",
    "a ground that taught continuity",
    "a threshold that trained your sense of scale",
    "a starting point, never a cage",
]
PLACE_ARCH_KO = [
    "경계가 아니라 출발점",
    "야망보다 먼저 ‘소속’을 기억하게 하는 자리",
    "연속성을 몸으로 익히게 한 땅",
    "스케일 감각을 훈련시킨 문턱",
    "시작점일 뿐, 결코 감옥이 아닌 자리",
]

STANCE_LINES_EN = [
    "What matters now is not what the universe will give you, but what stance you are willing to hold.",
    "The mirror does not answer for you. It sharpens the question you can carry.",
    "Clarity is not certainty. Clarity is the refusal to pretend.",
    "You are not asked to control the future—only to choose your next honest position.",
    "Responsibility is the courage to stay with what you see, without embellishment.",
]
STANCE_LINES_KO = [
    "지금 중요한 것은 우주가 무엇을 주느냐가 아니라, 내가 어떤 입장을 지킬 것인가입니다.",
    "거울은 대신 답하지 않습니다. 내가 ‘들고 갈 질문’의 윤곽을 또렷하게 합니다.",
    "명료함은 확신이 아닙니다. 명료함은 ‘모른 척하지 않겠다’는 결심입니다.",
    "미래를 통제하라는 것이 아닙니다. 다음의 정직한 위치를 선택하라는 것입니다.",
    "책임이란, 보이는 것을 과장 없이 끝까지 바라보는 용기입니다.",
]

EMPTY_Q_EN = [
    "You left the question empty. That is not absence—it is restraint.",
    "An empty question can be an ethical choice: not to demand, not to rush.",
    "To leave space is to admit reality is larger than your current language.",
]
EMPTY_Q_KO = [
    "질문을 비워두었습니다. 그것은 공백이 아니라 절제입니다.",
    "질문을 비우는 것은 ‘재촉하지 않겠다’는 윤리적 선택일 수 있습니다.",
    "공간을 남긴다는 것은, 실재가 지금의 언어보다 크다는 인정입니다.",
]

QUESTION_FRAME_EN = [
    "Your living question:",
    "The question you bring today:",
    "The question that remains alive in you:",
]
QUESTION_FRAME_KO = [
    "당신의 살아 있는 질문:",
    "오늘 당신이 가져온 질문:",
    "지금도 당신 안에 살아 있는 질문:",
]

CLOSE_EN = [
    "No prediction is offered here. Only reflection, and the responsibility of choice.",
    "This mirror does not define you. It asks if you will stand where you already are.",
    "Return to this record later. Compare what changed—not in fate, but in stance.",
]
CLOSE_KO = [
    "여기에는 예언이 없습니다. 성찰과 선택의 책임만 있습니다.",
    "이 거울은 당신을 규정하지 않습니다. 지금 서 있는 자리에서 설 것인지 묻습니다.",
    "나중에 이 기록으로 돌아오세요. 운명이 아니라 ‘입장’이 어떻게 달라졌는지 비교해 보세요.",
]

def build_template(era_i: int, time_i: int, place_i: int) -> str:
    # deterministic variation per template index
    k = (era_i * 25) + (time_i * 5) + place_i  # 0..174
    idx_stance = k % 5
    idx_qframe = k % 3
    idx_close = k % 3
    idx_empty = k % 3

    if LANG == "English":
        era = ERA_TONES_EN[era_i]
        time_tone = TIME_TONES_EN[time_i]
        place_arch = PLACE_ARCH_EN[place_i]
        stance = STANCE_LINES_EN[idx_stance]
        qframe = QUESTION_FRAME_EN[idx_qframe]
        close = CLOSE_EN[idx_close]
        empty_q = EMPTY_Q_EN[idx_empty]
        return f"""[CM-{k+1:03d}] Cosmic Mirror — Reflection Without Prediction

Coordinate (symbolic):
- Era tone: {era}
- Phase: {time_tone}
- Place meaning: {place_arch}

Inputs (to be filled):
- Place of birth (symbolic): {{place}}
- Living question (optional): {{question}}

Reflection:
You were born in a moment shaped by {era}.
Your time suggests a phase of {time_tone}.

You name "{{place}}" not as destiny,
but as {place_arch}.

{qframe}
"{{question}}"

If the question is empty:
{empty_q}

{stance}

Three prompts:
• What can you release without denial?
• What must you do without waiting for permission?
• What boundary protects what you love?

{close}
"""
    else:
        era = ERA_TONES_KO[era_i]
        time_tone = TIME_TONES_KO[time_i]
        place_arch = PLACE_ARCH_KO[place_i]
        stance = STANCE_LINES_KO[idx_stance]
        qframe = QUESTION_FRAME_KO[idx_qframe]
        close = CLOSE_KO[idx_close]
        empty_q = EMPTY_Q_KO[idx_empty]
        return f"""[CM-{k+1:03d}] Cosmic Mirror — Reflection Without Prediction

좌표(상징):
- 시대 톤: {era}
- 국면: {time_tone}
- 출생지 의미: {place_arch}

입력(채워 넣기):
- 출생지(상징): {{place}}
- 살아 있는 질문(선택): {{question}}

성찰:
당신은 {era}에 태어났습니다.
당신의 시간은 ‘{time_tone}’의 국면을 암시합니다.

당신은 "{{place}}"를 운명으로 부르지 않습니다.
그것은 {place_arch}일 뿐입니다.

{qframe}
"{{question}}"

질문이 비어 있다면:
{empty_q}

{stance}

세 가지 프롬프트:
• 부정 없이 내려놓을 수 있는 것은 무엇인가?
• 허락을 기다리지 않고 해야 할 일은 무엇인가?
• 내가 사랑하는 것을 지키는 경계는 무엇인가?

{close}
"""

def build_all_175() -> list[str]:
    out = []
    for era_i in range(7):
        for time_i in range(5):
            for place_i in range(5):
                out.append(build_template(era_i, time_i, place_i))
    return out

templates = build_all_175()
assert len(templates) == 175

# =========================================================
# UI: preview + export
# =========================================================
colA, colB = st.columns([2, 1], vertical_alignment="top")

with colA:
    st.subheader(t("Preview", "미리보기"))
    sel = st.slider(t("Template index", "템플릿 번호"), 1, 175, 1)
    st.text_area(
        t("Selected template", "선택된 템플릿"),
        value=templates[sel - 1],
        height=420
    )

with colB:
    st.subheader(t("Export 175 templates", "175개 템플릿 추출"))

    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"cosmic_mirror_175_{'EN' if LANG=='English' else 'KR'}_{now}"

    txt_blob = ("\n\n" + ("=" * 70) + "\n\n").join(templates).encode("utf-8")
    md_blob = ("# Cosmic Mirror — Reflection Without Prediction (175)\n\n"
               + t(
                    "These are template reflections. Replace {place} and {question} with user inputs.\n\n",
                    "이 문서는 성찰 템플릿입니다. {place}, {question}을 사용자 입력으로 치환하세요.\n\n"
                 )
               + "\n\n---\n\n".join([f"```\n{r}\n```" for r in templates])
              ).encode("utf-8")

    st.download_button(
        label=t("Download TXT", "TXT 다운로드"),
        data=txt_blob,
        file_name=f"{base_name}.txt",
        mime="text/plain; charset=utf-8",
        use_container_width=True
    )
    st.download_button(
        label=t("Download Markdown (MD)", "마크다운(MD) 다운로드"),
        data=md_blob,
        file_name=f"{base_name}.md",
        mime="text/markdown; charset=utf-8",
        use_container_width=True
    )

    st.info(t(
        "Tip: In your main Cosmic Mirror page, you can select one of these 175 templates deterministically and then fill {place} and {question}.",
        "팁: 메인 Cosmic Mirror 페이지에서 175개 중 하나를 결정론적으로 선택한 뒤 {place}, {question}을 채워 넣으면 됩니다."
    ))

st.divider()

st.markdown(t(
    "### How to use this library in your main page\n"
    "- Choose an index (1–175) deterministically from user inputs\n"
    "- Take the corresponding template\n"
    "- Replace `{place}` and `{question}`\n"
    "- Display + allow saving\n",
    "### 메인 페이지에서 이 라이브러리 활용 방법\n"
    "- 사용자 입력에서 (1–175) 인덱스를 결정론적으로 계산\n"
    "- 해당 템플릿을 선택\n"
    "- `{place}`, `{question}`을 치환\n"
    "- 표시 + 저장 버튼 제공\n"
))
