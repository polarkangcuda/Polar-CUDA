# pages/2_Cosmic_Mirror.py
"""
Cosmic Mirror — Reflection Without Prediction

Principles:
- No prediction
- No divination
- No authority invoked
- No guidance given

This application exists solely to reflect responsibility,
not to forecast outcomes.
"""

from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
import streamlit as st

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror — Reflection Without Prediction",
    page_icon="🪞",
    layout="wide",
)

KST = timezone(timedelta(hours=9))

# ------------------------------------------------------------
# Reflection library
# ------------------------------------------------------------
REFLECTIONS = [
    {"en": "You do not need permission to become more truthful.",
     "ko": "더 진실해지기 위해 허락을 받을 필요는 없습니다."},

    {"en": "You are allowed to arrive unfinished.",
     "ko": "미완성인 채로 도착해도 괜찮습니다."},

    {"en": "Uncertainty is not a defect. It is the real weather of life.",
     "ko": "불확실성은 결함이 아닙니다. 삶의 실제 날씨입니다."},

    {"en": "Do not ask what will happen. Ask what you are responsible for.",
     "ko": "무엇이 일어날지를 묻기보다, 무엇에 책임질지를 물어보세요."},

    {"en": "A good stance is stronger than a perfect plan.",
     "ko": "완벽한 계획보다 좋은 태도가 더 강합니다."},

    {"en": "When you cannot decide, name what you refuse to betray.",
     "ko": "결정을 못하겠다면, 무엇만큼은 배반하지 않겠는지 먼저 적어보세요."},

    {"en": "Your next step does not require certainty—only honesty in action.",
     "ko": "다음 걸음에는 확신이 아니라 행동으로 드러나는 정직함이 필요합니다."},

    {"en": "The future is not a message. It is a consequence of choices.",
     "ko": "미래는 ‘메시지’가 아니라 선택의 결과입니다."},

    {"en": "Symbols do not predict you. They reflect what you choose to carry.",
     "ko": "상징은 당신을 예언하지 않습니다. 당신이 무엇을 지니기로 선택했는지를 비춥니다."},

    {"en": "If you feel lost, reduce the problem to one clean sentence you can act on.",
     "ko": "길을 잃었다면, 행동으로 옮길 수 있는 한 문장으로 문제를 줄여보세요."},

    {"en": "What you repeat through action becomes your reality.",
     "ko": "반복되는 행동이 당신의 현실을 만듭니다."},

    {"en": "A quiet decision can be more courageous than a loud ambition.",
     "ko": "조용한 결정이 요란한 야망보다 더 용감할 때가 있습니다."},

    {"en": "The point is not to be right. The point is to be accountable.",
     "ko": "중요한 것은 옳음이 아니라 책임입니다."},

    {"en": "Do not confuse urgency with importance.",
     "ko": "긴급함을 중요함으로 착각하지 마세요."},

    {"en": "A boundary is not a wall. It is a promise you keep with reality.",
     "ko": "경계는 벽이 아닙니다. 현실과 맺는 약속입니다."},

    {"en": "Your life becomes clearer when your standards become explicit.",
     "ko": "기준이 명시될수록 삶은 선명해집니다."},

    {"en": "You can be kind without being unclear.",
     "ko": "불분명하지 않으면서도 충분히 친절할 수 있습니다."},

    {"en": "The most reliable compass is the value you refuse to trade.",
     "ko": "가장 믿을 만한 나침반은 끝내 팔지 않겠다고 정한 가치입니다."},

    {"en": "When you feel weak, return to your smallest concrete duty.",
     "ko": "약해질 때는 가장 작고 구체적인 의무로 돌아가세요."},

    {"en": "Restraint is not delay. It is precision.",
     "ko": "절제는 지연이 아닙니다. 정밀함입니다."},

    {"en": "Do not wait for clarity. Act honestly and clarity will follow.",
     "ko": "명확해지기를 기다리지 말고 정직하게 행동하세요. 명확함은 따라옵니다."},

    {"en": "If a choice cannot be explained, it is not ready.",
     "ko": "설명할 수 없는 선택은 아직 준비되지 않은 선택입니다."},

    {"en": "A standard written down is stronger than motivation felt.",
     "ko": "느껴진 동기보다 기록된 기준이 더 강합니다."},

    {"en": "Your calendar reveals your real priorities.",
     "ko": "달력은 당신의 진짜 우선순위를 드러냅니다."},

    {"en": "Consistency is not repetition. It is alignment.",
     "ko": "일관성은 반복이 아니라 정렬입니다."},

    {"en": "Do not outsource your conscience to chance.",
     "ko": "양심을 우연에 외주 주지 마세요."},

    {"en": "A clear ‘no’ is an act of care.",
     "ko": "명확한 ‘아니오’는 돌봄의 한 형태입니다."},

    {"en": "The most honest answer is sometimes: not yet.",
     "ko": "가장 정직한 답은 때로 ‘아직’입니다."},

    {"en": "If something drains you repeatedly, name it.",
     "ko": "무언가가 반복해서 당신을 소진시킨다면, 그것을 이름 붙이세요."},

    {"en": "Integrity is what remains when no one is watching.",
     "ko": "정합성은 아무도 보지 않을 때 남는 것입니다."},

    {"en": "Do not rush decisions that will have to be lived with.",
     "ko": "살아내야 할 결정은 서두르지 마세요."},

    {"en": "A smaller promise kept is better than a grand one broken.",
     "ko": "지켜진 작은 약속이 깨진 거대한 약속보다 낫습니다."},

    {"en": "What you tolerate becomes your environment.",
     "ko": "당신이 용인하는 것이 곧 당신의 환경이 됩니다."},

    {"en": "Responsibility clarifies more than certainty.",
     "ko": "책임은 확신보다 더 많은 것을 선명하게 합니다."},

    {"en": "You are not here to perform certainty.",
     "ko": "당신은 확실한 척하기 위해 여기 있지 않습니다."},

    {"en": "A decision recorded is a decision owned.",
     "ko": "기록된 결정은 소유된 결정입니다."},

    {"en": "Choose what you can stand by on difficult days.",
     "ko": "힘든 날에도 설 수 있는 선택을 하세요."},

    {"en": "Do not confuse hope with avoidance.",
     "ko": "희망을 회피와 혼동하지 마세요."},

    {"en": "Clarity grows from limits, not from endless options.",
     "ko": "명확함은 무한한 선택지가 아니라 한계에서 자랍니다."},

    {"en": "Your attention is an ethical act.",
     "ko": "주의를 기울이는 것은 윤리적 행위입니다."},

    {"en": "A disciplined life is a lighter life.",
     "ko": "절제된 삶은 더 가벼운 삶입니다."},

    {"en": "If you feel overwhelmed, reduce, then repeat.",
     "ko": "버거울 때는 줄이고, 다시 반복하세요."},

    {"en": "A mirror does not judge. It reflects.",
     "ko": "거울은 판단하지 않습니다. 비출 뿐입니다."},

    {"en": "Your values should survive inconvenience.",
     "ko": "당신의 가치는 불편함을 견뎌야 합니다."},

    {"en": "Do not ask for signs. Write standards.",
     "ko": "징조를 구하지 말고 기준을 쓰세요."},

    {"en": "What you can explain calmly is usually right-sized.",
     "ko": "차분히 설명할 수 있는 선택은 대개 적정한 크기입니다."},

    {"en": "A life without prediction still needs direction.",
     "ko": "예언 없는 삶에도 방향은 필요합니다."},

    {"en": "Direction comes from values, not forecasts.",
     "ko": "방향은 예측이 아니라 가치에서 나옵니다."},

    {"en": "Careful choices age better than clever ones.",
     "ko": "영리한 선택보다 신중한 선택이 더 오래 갑니다."},

    {"en": "Your future self will live with what you decide today.",
     "ko": "미래의 당신은 오늘의 결정을 안고 살아갑니다."},

    {"en": "Do not confuse intensity with depth.",
     "ko": "강렬함을 깊이로 착각하지 마세요."},

    {"en": "A practice repeated is stronger than insight admired.",
     "ko": "감탄한 통찰보다 반복된 실천이 더 강합니다."},

    {"en": "If you want peace, reduce hidden compromises.",
     "ko": "평화를 원한다면 숨은 타협을 줄이세요."},

    {"en": "Your stance today is enough.",
     "ko": "오늘의 입장만으로도 충분합니다."},
]

# ------------------------------------------------------------
# UI text
# ------------------------------------------------------------
UI = {
    "en": {
        "lang_label": "Language / 언어",
        "title": "Cosmic Mirror — Reflection Without Prediction",
        "subtitle": [
            "This is not divination.",
            "No future is predicted.",
            "No authority is invoked.",
            "This mirror exists only for reflection and responsibility.",
        ],
        "reflection_title": "Today’s Stance",
        "btn_next": "Reflect again",
        "btn_save": "Save stance (TXT)",
        "footer": "This mirror offers no answers—only a stance you can stand by.",
    },
    "ko": {
        "lang_label": "Language / 언어",
        "title": "Cosmic Mirror — 예언 없는 성찰",
        "subtitle": [
            "이것은 점술이 아닙니다.",
            "미래를 예측하지 않습니다.",
            "어떤 권위도 호출하지 않습니다.",
            "이 거울은 성찰과 책임을 위해 존재합니다.",
        ],
        "reflection_title": "오늘의 입장",
        "btn_next": "다른 입장 보기",
        "btn_save": "입장 저장 (TXT)",
        "footer": "이 거울은 답을 주지 않습니다 — 오늘 설 수 있는 입장만 제공합니다.",
    },
}

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def random_reflection():
    prev = st.session_state.get("reflection")
    candidate = random.choice(REFLECTIONS)
    while prev == candidate:
        candidate = random.choice(REFLECTIONS)
    return candidate

def save_text(lang, text):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    return f"""{UI[lang]['title']}
-----------------------------
Recorded at: {now}

STANCE (not prediction):
{text}

This text reflects my current position,
not a promise of outcomes.

{UI[lang]['footer']}
"""

# ------------------------------------------------------------
# Language toggle
# ------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "en"

lang = st.session_state.lang

choice = st.radio(
    UI[lang]["lang_label"],
    ["English", "한국어"],
    index=0 if lang == "en" else 1,
    horizontal=True,
)

st.session_state.lang = "en" if choice == "English" else "ko"
lang = st.session_state.lang

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(f"# 🪞 {UI[lang]['title']}")
for line in UI[lang]["subtitle"]:
    st.markdown(f"- {line}")
st.divider()

# ------------------------------------------------------------
# Reflection (완전 랜덤)
# ------------------------------------------------------------
if "reflection" not in st.session_state:
    st.session_state.reflection = random_reflection()

reflection = st.session_state.reflection[lang]

st.markdown(f"## {UI[lang]['reflection_title']}")
st.markdown(f"> ### {reflection}")

# ------------------------------------------------------------
# Buttons
# ------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button(UI[lang]["btn_next"], use_container_width=True):
        st.session_state.reflection = random_reflection()
        st.rerun()

with col2:
    txt = save_text(lang, reflection)
    st.download_button(
        UI[lang]["btn_save"],
        data=txt.encode("utf-8"),
        file_name="cosmic_mirror_stance.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.markdown("---")
st.markdown(f"*{UI[lang]['footer']}*")
