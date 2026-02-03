import streamlit as st
import random
from datetime import datetime

# ===============================
# Page config
# ===============================
st.set_page_config(
    page_title="Cosmic Mirror — Reflection Without Prediction",
    page_icon="🪞",
    layout="centered",
)

# ===============================
# Language toggle
# ===============================
LANG = st.radio("Language / 언어", ["English", "한국어"], horizontal=True)

def t(en, ko):
    return en if LANG == "English" else ko

# ===============================
# Title & philosophy
# ===============================
st.title("🪞 Cosmic Mirror — Reflection Without Prediction")

st.markdown(t(
    """
This is not divination.  
No future is predicted.  
No authority is invoked.  

This mirror exists only for reflection and responsibility.
""",
    """
이것은 점술이 아닙니다.  
미래를 예측하지 않습니다.  
어떠한 권위도 호출하지 않습니다.  

이 거울은 오직 성찰과 책임을 위해 존재합니다.
"""
))

st.divider()

# ===============================
# Reflection pools (100 each)
# ===============================
REFLECTS_EN = [
    "You do not need permission to become more truthful.",
    "This moment asks for clarity, not urgency.",
    "You are not behind; you are becoming deliberate.",
    "What you release now creates space without loss.",
    "You are allowed to pause without explanation.",
    "Responsibility begins where excuses quietly end.",
    "Nothing is missing. Something is ripening.",
    "You are not here to predict, but to choose your stance.",
    "Silence can be an answer when listening deepens.",
    "What matters now is not speed, but direction.",
    "You are not required to finish what no longer fits.",
    "Clarity often follows restraint.",
    "You can carry uncertainty without fear.",
    "This moment does not demand resolution.",
    "What you face today is asking for honesty.",
    "You are allowed to arrive slowly.",
    "Not choosing is also a choice—make it consciously.",
    "You are not late. You are arriving differently.",
    "What you hold defines you more than what you seek.",
    "The future responds to posture, not prediction.",
    "You are permitted to simplify.",
    "This is not the end of something, but the easing of force.",
    "You are not obligated to repeat yourself.",
    "What you protect shapes what grows.",
    "There is strength in leaving some questions open.",
    "You are not here to impress the moment.",
    "Clarity is quieter than certainty.",
    "You may stop proving and start standing.",
    "This mirror does not rush you.",
    "What you choose not to carry matters.",
    "You are allowed to be exact, not dramatic.",
    "Patience is not delay—it is alignment.",
    "You are not required to explain your stillness.",
    "Some answers arrive only after release.",
    "You are permitted to rest without justification.",
    "What you honor now becomes durable.",
    "This moment favors precision over force.",
    "You are not lost; you are recalibrating.",
    "What you step away from defines your direction.",
    "You are allowed to refuse unnecessary weight.",
    "Clarity does not shout.",
    "You are not here to chase certainty.",
    "What you accept shapes your next boundary.",
    "You may stand without resolution.",
    "This moment is sufficient as it is.",
    "You are allowed to trust your restraint.",
    "What you leave unsaid can still be complete.",
    "You are not required to hurry meaning.",
    "The mirror reflects posture, not outcome.",
    "You may choose less without loss.",
    "This moment values steadiness.",
    "You are allowed to arrive unfinished.",
    "What you keep defines your center.",
    "You are permitted to stop negotiating with doubt.",
    "This is a place to stand, not a place to perform.",
    "You do not need to convince the future.",
    "What you clarify now will hold later.",
    "You are not required to resolve everything.",
    "This moment favors honesty over optimism.",
    "You are allowed to be exact.",
    "What you set down frees your hands.",
    "You may rest inside uncertainty.",
    "This mirror does not instruct—it reflects.",
    "You are not obligated to accelerate clarity.",
    "What you align with now will endure.",
    "You are allowed to choose quietly.",
    "This moment does not ask for answers.",
    "You are permitted to stand without defense.",
    "What you honor becomes stable.",
    "You may stop seeking permission.",
    "This mirror meets you where you stand.",
    "You are not required to explain your choice.",
    "What you simplify strengthens you.",
    "You are allowed to hold less.",
    "This moment asks for steadiness.",
    "You are permitted to trust what remains.",
    "What you release creates room.",
    "You may choose direction without certainty.",
    "This mirror offers no command.",
    "You are allowed to be deliberate.",
    "What you refuse defines your integrity.",
    "You may stop rehearsing outcomes.",
    "This moment is not a test.",
    "You are permitted to stand exactly here.",
]

REFLECTS_KO = [
    "더 정직해지는 데에는 허락이 필요 없습니다.",
    "이 순간은 조급함이 아니라 명료함을 요구합니다.",
    "당신은 뒤처진 것이 아니라 신중해지고 있습니다.",
    "지금 내려놓는 것은 상실이 아니라 여백입니다.",
    "설명 없이 멈춰도 괜찮습니다.",
    "책임은 변명이 조용히 끝나는 자리에서 시작됩니다.",
    "지금 부족한 것은 없습니다. 익어가고 있을 뿐입니다.",
    "당신은 예측이 아니라 태도를 선택하기 위해 여기 있습니다.",
    "침묵은 더 깊이 들을 때 하나의 응답이 됩니다.",
    "중요한 것은 속도가 아니라 방향입니다.",
    "더 이상 맞지 않는 것을 끝낼 의무는 없습니다.",
    "명료함은 절제 뒤에 옵니다.",
    "불확실성을 두려움 없이 지닐 수 있습니다.",
    "이 순간은 결론을 요구하지 않습니다.",
    "오늘 마주한 것은 정직함을 요구합니다.",
    "천천히 도착해도 괜찮습니다.",
    "선택하지 않는 것도 선택입니다. 의식적으로 하십시오.",
    "당신은 늦지 않았습니다. 다른 방식으로 도착했을 뿐입니다.",
    "당신을 규정하는 것은 찾는 것보다 붙드는 것입니다.",
    "미래는 예측이 아니라 태도에 반응합니다.",
    "단순해질 수 있습니다.",
    "이것은 끝이 아니라 힘을 푸는 순간입니다.",
    "같은 말을 반복할 필요는 없습니다.",
    "지금 보호하는 것이 성장을 만듭니다.",
    "질문을 열어두는 것도 힘입니다.",
    "이 순간을 인상 깊게 만들 필요는 없습니다.",
    "명료함은 확신보다 조용합니다.",
    "증명하지 않아도 서 있을 수 있습니다.",
    "이 거울은 서두르지 않습니다.",
    "지금 들지 않기로 한 것이 중요합니다.",
    "정확해져도 됩니다. 과장할 필요는 없습니다.",
    "인내는 지연이 아니라 정렬입니다.",
    "고요함을 설명할 필요는 없습니다.",
    "어떤 답은 내려놓은 뒤에 옵니다.",
    "정당화 없이 쉬어도 됩니다.",
    "지금 존중하는 것이 오래 갑니다.",
    "이 순간은 힘보다 정밀함을 선호합니다.",
    "당신은 길을 잃은 것이 아니라 조정 중입니다.",
    "멀어진 것이 방향을 만듭니다.",
    "불필요한 무게를 거부해도 됩니다.",
    "명료함은 소리치지 않습니다.",
    "확신을 쫓지 않아도 됩니다.",
    "지금 받아들이는 것이 경계를 만듭니다.",
    "해결 없이 서 있을 수 있습니다.",
    "이 순간은 그 자체로 충분합니다.",
    "절제를 신뢰해도 됩니다.",
    "말하지 않은 것도 완전할 수 있습니다.",
    "의미를 서두르지 않아도 됩니다.",
    "이 거울은 결과가 아니라 태도를 비춥니다.",
    "적게 선택해도 잃지 않습니다.",
    "이 순간은 안정감을 중시합니다.",
    "미완으로 도착해도 괜찮습니다.",
    "붙드는 것이 중심을 만듭니다.",
    "의심과의 협상을 멈춰도 됩니다.",
    "여기는 연출의 자리가 아닙니다.",
    "미래를 설득할 필요는 없습니다.",
    "지금 분명히 한 것은 오래 갑니다.",
    "모든 것을 해결할 필요는 없습니다.",
    "이 순간은 낙관보다 정직을 원합니다.",
    "정확해져도 됩니다.",
    "내려놓은 것이 손을 자유롭게 합니다.",
    "불확실성 안에서 쉬어도 됩니다.",
    "이 거울은 지시하지 않습니다.",
    "명료함을 앞당길 필요는 없습니다.",
    "지금 정렬한 것은 지속됩니다.",
    "조용히 선택해도 됩니다.",
    "이 순간은 답을 요구하지 않습니다.",
    "방어 없이 서 있을 수 있습니다.",
    "존중한 것이 안정됩니다.",
    "허락을 구하지 않아도 됩니다.",
    "이 거울은 지금의 자리에 응답합니다.",
    "선택을 설명할 필요는 없습니다.",
    "단순함은 힘이 됩니다.",
    "적게 지녀도 됩니다.",
    "이 순간은 흔들림 없는 태도를 원합니다.",
    "남은 것을 신뢰해도 됩니다.",
    "내려놓음은 공간을 만듭니다.",
    "확신 없이도 방향을 정할 수 있습니다.",
    "이 거울은 명령하지 않습니다.",
    "신중해져도 됩니다.",
    "거부한 것이 당신의 윤리입니다.",
    "결과를 예행연습하지 않아도 됩니다.",
    "이 순간은 시험이 아닙니다.",
    "지금 이 자리에 그대로 서 있어도 됩니다.",
]

POOL = REFLECTS_EN if LANG == "English" else REFLECTS_KO

# ===============================
# Session state: shuffle once, then iterate
# ===============================
if "queue" not in st.session_state or st.session_state.get("lang") != LANG:
    st.session_state.queue = random.sample(POOL, len(POOL))
    st.session_state.index = 0
    st.session_state.lang = LANG

current_reflection = st.session_state.queue[st.session_state.index]

# ===============================
# Display
# ===============================
st.subheader(t("Reflection", "성찰"))
st.markdown(f"> {current_reflection}")

# ===============================
# Buttons
# ===============================
col1, col2 = st.columns(2)

with col1:
    if st.button(t("Show another reflection", "다른 성찰 보기")):
        st.session_state.index = (st.session_state.index + 1) % len(st.session_state.queue)
        st.rerun()

with col2:
    text_to_save = (
        f"Cosmic Mirror — Reflection Without Prediction\n"
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{current_reflection}\n"
    ).encode("utf-8")

    st.download_button(
        label=t("Save reflection (TXT)", "성찰 저장 (TXT)"),
        data=text_to_save,
        file_name="cosmic_mirror_reflection.txt",
        mime="text/plain; charset=utf-8"
    )

# ===============================
# Footer
# ===============================
st.divider()
st.caption(t(
    "This mirror offers no answers—only a place to stand.",
    "이 거울은 답을 주지 않습니다. 서 있을 자리를 내어줄 뿐입니다."
))
