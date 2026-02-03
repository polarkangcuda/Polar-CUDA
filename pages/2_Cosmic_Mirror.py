# pages/2_Cosmic_Mirror.py
# Cosmic Mirror — Reflection Without Prediction
# Offline / No API required

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
# Reflection library (100+ allowed, no hard limit)
# ------------------------------------------------------------
REFLECTIONS = [
    {"en": "You do not need permission to become more truthful.", "ko": "더 진실해지기 위해 허락을 받을 필요는 없습니다."},
    {"en": "You are allowed to arrive unfinished.", "ko": "미완성인 채로 도착해도 괜찮습니다."},
    {"en": "Uncertainty is not a defect. It is the real weather of life.", "ko": "불확실성은 결함이 아닙니다. 삶의 실제 날씨입니다."},
    {"en": "Do not ask what will happen. Ask what you are responsible for.", "ko": "무엇이 일어날지를 묻기보다, 무엇에 책임질지를 물어보세요."},
    {"en": "A good stance is stronger than a perfect plan.", "ko": "완벽한 계획보다 좋은 태도가 더 강합니다."},
    {"en": "When you cannot decide, name what you refuse to betray.", "ko": "결정을 못하겠다면, 무엇만큼은 배반하지 않겠는지 먼저 적어보세요."},
    {"en": "Your next step does not require certainty—only honesty.", "ko": "다음 걸음에는 확신이 아니라 정직함이 필요합니다."},
    {"en": "The future is not a message. It is a consequence.", "ko": "미래는 ‘메시지’가 아니라 ‘결과’입니다."},
    {"en": "Symbols do not predict you. They reflect what you choose to carry.", "ko": "상징은 당신을 예언하지 않습니다. 당신이 무엇을 지니는지 비춥니다."},
    {"en": "If you feel lost, reduce the problem to one clean sentence.", "ko": "길을 잃었다면 문제를 한 문장으로 정리해 보세요."},
    {"en": "What you repeat becomes your reality. Repeat with care.", "ko": "반복하는 것이 현실이 됩니다. 신중하게 반복하세요."},
    {"en": "A quiet decision can be more courageous than a loud ambition.", "ko": "조용한 결정이 요란한 야망보다 더 용감할 때가 있습니다."},
    {"en": "The point is not to be right. The point is to be accountable.", "ko": "중요한 것은 옳음이 아니라 책임입니다."},
    {"en": "Do not confuse urgency with importance.", "ko": "긴급함을 중요함으로 착각하지 마세요."},
    {"en": "A boundary is not a wall. It is a promise to reality.", "ko": "경계는 벽이 아닙니다. 현실에 대한 약속입니다."},
    {"en": "Your life becomes clearer when your standards become explicit.", "ko": "기준이 명시될수록 삶은 선명해집니다."},
    {"en": "You can be kind without being unclear.", "ko": "불분명하지 않으면서도 충분히 친절할 수 있습니다."},
    {"en": "The most reliable compass is the value you will not trade.", "ko": "가장 믿을 만한 나침반은 ‘팔지 않을 가치’입니다."},
    {"en": "When you feel weak, return to your smallest duty.", "ko": "약해질 때는 가장 작은 의무로 돌아가세요."},
    {"en": "Restraint is not delay. It is precision.", "ko": "절제는 지연이 아닙니다. 정밀함입니다."},
    {"en": "If you cannot change the world, change the sentence you live by.", "ko": "세상을 바꾸지 못하더라도, 당신이 사는 문장은 바꿀 수 있습니다."},
    {"en": "The mind calms when it stops demanding guarantees.", "ko": "마음은 보장을 요구하는 것을 멈출 때 가라앉습니다."},
    {"en": "What matters is not speed, but sequence.", "ko": "중요한 것은 속도가 아니라 순서입니다."},
    {"en": "Do not outsource your conscience to a system.", "ko": "양심을 시스템에 외주 주지 마세요."},
    {"en": "The honest question is better than the impressive answer.", "ko": "멋진 답보다 정직한 질문이 더 낫습니다."},
    {"en": "A life is not solved. It is stewarded.", "ko": "인생은 ‘해결’되는 것이 아니라 ‘관리’됩니다."},
    {"en": "The moment you name your fear, it shrinks into shape.", "ko": "두려움을 이름 붙이면, 그것은 모양을 갖추며 작아집니다."},
    {"en": "You are not behind. You are becoming.", "ko": "당신은 뒤처진 것이 아니라, 되어 가는 중입니다."},
    {"en": "The most dangerous story is the one that removes your agency.", "ko": "가장 위험한 이야기는 당신의 주체성을 빼앗는 이야기입니다."},
    {"en": "Choose a principle you can repeat on hard days.", "ko": "힘든 날에도 반복할 수 있는 원칙을 고르세요."},
    {"en": "A promise kept to yourself is a form of dignity.", "ko": "자기 자신에게 한 약속을 지키는 것은 존엄의 한 형태입니다."},
    {"en": "You do not need a sign. You need a standard.", "ko": "징조가 필요한 게 아니라, 기준이 필요합니다."},
    {"en": "The right question can turn anxiety into action.", "ko": "올바른 질문은 불안을 행동으로 바꿉니다."},
    {"en": "When the world is noisy, be specific.", "ko": "세상이 소란할수록, 구체적으로."},
    {"en": "Truth often arrives without drama.", "ko": "진실은 종종 드라마 없이 도착합니다."},
    {"en": "Your attention is your most powerful vote.", "ko": "주의(집중)는 당신의 가장 강력한 투표입니다."},
    {"en": "Do not fear complexity. Fear unclear responsibilities.", "ko": "복잡함을 두려워하지 말고, 불분명한 책임을 두려워하세요."},
    {"en": "You can hold uncertainty without turning it into superstition.", "ko": "불확실성을 미신으로 바꾸지 않고도 품을 수 있습니다."},
    {"en": "The strongest mind is the one that can wait without collapsing.", "ko": "가장 강한 마음은 무너지지 않고 기다릴 수 있는 마음입니다."},
    {"en": "A clean ‘no’ protects a meaningful ‘yes.’", "ko": "명확한 ‘아니오’가 의미 있는 ‘예’를 지킵니다."},
    {"en": "If you cannot see the whole, take care of the edge you touch.", "ko": "전체가 보이지 않으면, 내가 닿는 가장자리부터 돌보세요."},
    {"en": "The goal is not certainty. The goal is integrity under uncertainty.", "ko": "목표는 확실성이 아니라, 불확실성 속의 정합성입니다."},
    {"en": "Ask: What am I trying to avoid feeling?", "ko": "물어보세요: 나는 무엇을 ‘느끼지 않으려’ 하고 있는가?"},
    {"en": "Your values are visible in your calendar.", "ko": "당신의 가치는 달력에 드러납니다."},
    {"en": "Do not wait for motivation. Build a ritual.", "ko": "동기를 기다리지 말고 의식을 만드세요."},
    {"en": "A good life is often a series of small honest repairs.", "ko": "좋은 삶은 작은 정직한 수리의 연속일 때가 많습니다."},
    {"en": "You can be gentle and still be exact.", "ko": "부드러우면서도 정확할 수 있습니다."},
    {"en": "Your past is a place of origin, not a border.", "ko": "과거는 출발점이지 경계선이 아닙니다."},
    {"en": "What you call ‘fate’ may be a habit asking for revision.", "ko": "당신이 ‘운명’이라 부르는 것은 수정이 필요한 습관일 수 있습니다."},
    {"en": "Clarity is not harshness. It is kindness to tomorrow.", "ko": "명료함은 냉혹함이 아닙니다. 내일을 위한 친절입니다."},
    {"en": "Notice what drains you. Then name what restores you.", "ko": "무엇이 나를 소진시키는지 보고, 무엇이 나를 회복시키는지 이름 붙이세요."},
    {"en": "If you must choose, choose what you can explain without shame.", "ko": "선택해야 한다면, 부끄러움 없이 설명할 수 있는 것을 고르세요."},
    {"en": "The mind matures when it stops demanding a single story.", "ko": "마음은 하나의 이야기만을 요구하지 않을 때 성숙해집니다."},
    {"en": "Do not confuse being informed with being grounded.", "ko": "정보를 아는 것과 뿌리내린 것은 다릅니다."},
    {"en": "A symbol is a mirror: it shows your stance, not your destiny.", "ko": "상징은 거울입니다. 운명이 아니라 태도를 보여줍니다."},
    {"en": "When you feel rushed, reduce your commitments by one.", "ko": "서두르게 느껴질 때는 약속 하나를 줄이세요."},
    {"en": "Some questions are answered by living, not by knowing.", "ko": "어떤 질문은 ‘앎’이 아니라 ‘삶’으로 답해집니다."},
    {"en": "Your life is not a verdict. It is a practice.", "ko": "당신의 삶은 판결이 아니라 연습입니다."},
    {"en": "If you want peace, make fewer hidden deals with yourself.", "ko": "평화를 원한다면 자신과의 ‘숨은 거래’를 줄이세요."},
    {"en": "Hold your standards gently—but hold them.", "ko": "기준을 부드럽게, 그러나 분명히 붙드세요."},
    {"en": "In confusion, return to what is measurable: time, care, effort.", "ko": "혼란 속에서는 측정 가능한 것으로 돌아가세요: 시간, 돌봄, 노력."},
    {"en": "If you cannot predict, you can still prepare.", "ko": "예측할 수 없어도 준비할 수는 있습니다."},
    {"en": "The most honest answer is sometimes: ‘I don’t know yet.’", "ko": "가장 정직한 답은 때로 ‘아직 모르겠습니다’입니다."},
    {"en": "You are not here to satisfy the narrative. You are here to live.", "ko": "당신은 서사를 만족시키기 위해 사는 것이 아니라, 살기 위해 여기 있습니다."},
    {"en": "A disciplined life is not smaller. It is freer.", "ko": "절제된 삶은 더 작지 않습니다. 더 자유롭습니다."},
    {"en": "When you name your priority, anxiety loses its throne.", "ko": "우선순위를 이름 붙이면 불안은 왕좌를 잃습니다."},
    {"en": "Your ‘why’ should be stable enough to survive bad news.", "ko": "당신의 ‘왜’는 나쁜 소식에도 견딜 만큼 안정적이어야 합니다."},
    {"en": "Do not chase certainty—chase coherence.", "ko": "확실성을 쫓지 말고 정합성을 쫓으세요."},
    {"en": "Let your actions become your evidence.", "ko": "행동이 당신의 증거가 되게 하세요."},
    {"en": "If you feel stuck, lower the bar for starting, not for finishing.", "ko": "막혔다면 ‘시작의 문턱’을 낮추고 ‘완성의 기준’을 낮추지는 마세요."},
    {"en": "What you avoid today becomes tomorrow’s noise.", "ko": "오늘 피한 것은 내일의 소음이 됩니다."},
    {"en": "You can honor the past without reenacting it.", "ko": "과거를 존중하면서도 되풀이하지 않을 수 있습니다."},
    {"en": "A life without prediction still needs direction.", "ko": "예언 없는 삶에도 방향은 필요합니다."},
    {"en": "Your mood is not a map. Your values are.", "ko": "기분은 지도가 아닙니다. 가치는 지도입니다."},
    {"en": "When you are tempted by magic, ask what pain you’re trying to soothe.", "ko": "마법에 끌릴 때, 내가 달래려는 고통이 무엇인지 물어보세요."},
    {"en": "You can be spiritual without being credulous.", "ko": "쉽게 믿지 않으면서도 영적인 사람이 될 수 있습니다."},
    {"en": "The world changes when you stop lying to yourself in small ways.", "ko": "작은 거짓말을 멈출 때 세상은 바뀌기 시작합니다."},
    {"en": "Discipline is compassion for your future self.", "ko": "훈련은 미래의 나에 대한 연민입니다."},
    {"en": "If you want a new life, write a new sentence and live it.", "ko": "새 삶을 원한다면 새 문장을 쓰고 그 문장대로 사세요."},
    {"en": "Be careful with stories that remove complexity to sell comfort.", "ko": "위안을 팔기 위해 복잡함을 제거하는 이야기를 조심하세요."},
    {"en": "A reliable life is built by repeatable choices.", "ko": "신뢰할 수 있는 삶은 반복 가능한 선택으로 만들어집니다."},
    {"en": "You do not need to win every argument. You need to keep your soul.", "ko": "모든 논쟁에서 이길 필요는 없습니다. 영혼을 지키면 됩니다."},
    {"en": "Ask for fewer signs; practice deeper listening.", "ko": "징조를 덜 요구하고, 더 깊이 경청하는 연습을 하세요."},
    {"en": "When you feel scattered, choose one task and finish it slowly.", "ko": "산만할 때는 한 가지 일을 고르고 천천히 끝내세요."},
    {"en": "Your standards become your shelter.", "ko": "기준은 당신의 피난처가 됩니다."},
    {"en": "A meaningful day is often an ordinary day lived with attention.", "ko": "의미 있는 하루는 대개 ‘주의 깊게 산 평범한 하루’입니다."},
    {"en": "The mind suffers when it treats possibility as prophecy.", "ko": "가능성을 예언으로 취급할 때 마음은 괴로워집니다."},
    {"en": "If you fear the unknown, practice naming what you do know.", "ko": "미지를 두려워한다면, 내가 아는 것을 이름 붙이는 연습을 하세요."},
    {"en": "A small truth today is better than a grand illusion tomorrow.", "ko": "오늘의 작은 진실이 내일의 거대한 환상보다 낫습니다."},
    {"en": "Your attention should serve your life, not your fear.", "ko": "주의는 두려움이 아니라 삶을 섬겨야 합니다."},
    {"en": "Do not confuse intensity with depth.", "ko": "강렬함을 깊이로 착각하지 마세요."},
    {"en": "Courage can be as simple as telling the truth in a calm voice.", "ko": "용기는 차분한 목소리로 진실을 말하는 것만큼 단순할 수 있습니다."},
    {"en": "When nothing makes sense, care is still meaningful.", "ko": "아무것도 의미 없어 보일 때에도 ‘돌봄’은 의미가 있습니다."},
    {"en": "Your life becomes lighter when you stop performing certainty.", "ko": "확실한 척을 멈출 때 삶은 가벼워집니다."},
    {"en": "A mirror does not command. It reveals.", "ko": "거울은 명령하지 않습니다. 드러낼 뿐입니다."},
    {"en": "You can be wrong and still be sincere. Keep the sincerity.", "ko": "틀릴 수 있어도 진실할 수 있습니다. 그 진실함을 지키세요."},
    {"en": "The best protection against superstition is a written standard.", "ko": "미신을 막는 최고의 방어는 ‘기록된 기준’입니다."},
    {"en": "Do not ask the universe to decide. Decide what you will honor.", "ko": "우주에게 대신 결정해 달라 하지 말고, 당신이 무엇을 존중할지 결정하세요."},
    {"en": "Peace is a skill you practice, not a mood you wait for.", "ko": "평화는 기다리는 기분이 아니라 연습하는 기술입니다."},
    {"en": "A real life is not optimized. It is lived with care.", "ko": "진짜 삶은 최적화되지 않습니다. 돌봄 속에서 살아집니다."},
    {"en": "What you can repeat becomes your culture.", "ko": "반복할 수 있는 것이 당신의 문화가 됩니다."},
    {"en": "If you want change, begin with what you can keep doing.", "ko": "변화를 원한다면 ‘계속할 수 있는 것’부터 시작하세요."},
    {"en": "Do not fear emptiness. Sometimes it is space for truth.", "ko": "비어 있음이 두렵지 않도록. 그것은 진실이 들어올 공간일 수 있습니다."},
    {"en": "A life of reflection is a life that refuses cheap certainty.", "ko": "성찰하는 삶은 값싼 확실성을 거부하는 삶입니다."},
    {"en": "You can stand where you are and still move forward.", "ko": "지금 자리에 서 있으면서도 앞으로 나아갈 수 있습니다."},
    {"en": "The most human thing you can do is to choose with open eyes.", "ko": "가장 인간다운 일은 눈을 뜬 채 선택하는 것입니다."},
    {"en": "If you feel tired, simplify. If you feel hollow, reconnect.", "ko": "지치면 단순화하고, 공허하면 다시 연결하세요."},
    {"en": "You do not need a prophecy. You need a practice.", "ko": "예언이 필요한 게 아니라, 실천이 필요합니다."},
    {"en": "Let your life be a proof of the values you speak.", "ko": "당신이 말하는 가치가, 당신의 삶에서 증명되게 하세요."},
]

# ------------------------------------------------------------
# UI text (EN / KR)
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
        "reflection_title": "Reflection",
        "btn_next": "Show another reflection",
        "btn_save": "Save reflection (TXT)",
        "footer": "This mirror offers no answers—only a place to stand.",
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
        "reflection_title": "성찰",
        "btn_next": "다른 성찰 보기",
        "btn_save": "성찰 저장 (TXT)",
        "footer": "이 거울은 답을 주지 않습니다 — 다만 설 자리를 제공합니다.",
    },
}

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def init_deck():
    if "deck" not in st.session_state or not st.session_state.deck:
        deck = list(range(len(REFLECTIONS)))
        random.shuffle(deck)
        st.session_state.deck = deck

def next_reflection():
    init_deck()
    return st.session_state.deck.pop()

def ensure_current():
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = next_reflection()

def save_text(lang, text):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    return f"""{UI[lang]['title']}
-----------------------------
{now}

{text}

{UI[lang]['footer']}
"""

# --------------------------------------------------
# Language toggle (KEYERROR-SAFE)
# --------------------------------------------------

# 1. Initialize session state
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# 2. UI-safe lang value (force normalize)
lang = st.session_state.lang if st.session_state.lang in ["en", "ko"] else "en"
st.session_state.lang = lang

# 3. Radio (display labels only)
choice = st.radio(
    UI[lang]["lang_label"],
    ["English", "한국어"],
    index=0 if lang == "en" else 1,
    horizontal=True,
)

# 4. Map display → internal key
if choice == "English":
    st.session_state.lang = "en"
else:
    st.session_state.lang = "ko"

# 5. Final normalized lang
lang = st.session_state.lang



# 4. 선택 결과를 세션 상태에 반영
st.session_state.lang = "en" if choice == "English" else "ko"

# 5. 다시 lang 동기화 (중요)
lang = st.session_state.lang

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(f"# 🪞 {UI[lang]['title']}")
for line in UI[lang]["subtitle"]:
    st.markdown(f"- {line}")

st.divider()

# ------------------------------------------------------------
# Reflection display
# ------------------------------------------------------------
ensure_current()
idx = st.session_state.current_idx
reflection = REFLECTIONS[idx][lang]

st.markdown(f"## {UI[lang]['reflection_title']}")
st.markdown(
    f"""
> ### {reflection}
""")

# ------------------------------------------------------------
# Buttons
# ------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button(UI[lang]["btn_next"], use_container_width=True):
        st.session_state.current_idx = next_reflection()
        st.rerun()

with col2:
    txt = save_text(lang, reflection)
    st.download_button(
        UI[lang]["btn_save"],
        data=txt.encode("utf-8"),
        file_name="cosmic_mirror_reflection.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.markdown("---")
st.markdown(f"*{UI[lang]['footer']}*")
