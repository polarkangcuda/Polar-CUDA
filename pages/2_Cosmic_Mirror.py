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
# Reflection pool (간결하지만 의미 있는 문장들)
# ===============================
REFLECTS_EN = [
    "You are not here to receive answers. You are here to clarify your stance.",
    "Nothing is missing. What feels unclear is asking for patience, not urgency.",
    "This moment does not demand certainty—only honesty.",
    "You are allowed to stand still without calling it delay.",
    "The future is not waiting for your prediction, but for your readiness.",
    "Clarity often arrives after you stop forcing conclusions.",
    "You do not need permission to become more truthful.",
    "What you release now creates space without loss.",
    "Responsibility begins where excuses quietly end.",
    "This mirror does not tell you who you are. It asks where you stand.",
    "Not choosing is also a choice—make it consciously.",
    "You are not late. You are arriving differently.",
    "Silence can be an answer when listening deepens.",
    "You are allowed to carry uncertainty without fear.",
    "What matters is not speed, but direction with integrity.",
]

REFLECTS_KO = [
    "당신은 답을 받기 위해 여기 있는 것이 아닙니다. 입장을 분명히 하기 위해 여기 있습니다.",
    "지금 부족한 것은 없습니다. 불분명함은 조급함이 아니라 인내를 요구합니다.",
    "이 순간은 확신을 요구하지 않습니다. 정직함만을 요구합니다.",
    "멈춰 서 있는 것을 지연이라 부르지 않아도 됩니다.",
    "미래는 예측을 기다리지 않습니다. 준비된 태도를 기다립니다.",
    "명료함은 결론을 강요하지 않을 때 찾아옵니다.",
    "더 정직해지는 데에는 허락이 필요 없습니다.",
    "지금 내려놓는 것은 상실이 아니라 여백을 만듭니다.",
    "책임은 변명이 조용히 끝나는 자리에서 시작됩니다.",
    "이 거울은 당신이 누구인지 말하지 않습니다. 어디에 서 있는지 묻습니다.",
    "선택하지 않는 것도 선택입니다. 의식적으로 하십시오.",
    "당신은 늦지 않았습니다. 다른 방식으로 도착했을 뿐입니다.",
    "침묵은 더 깊이 들을 때 하나의 응답이 됩니다.",
    "불확실성을 두려움 없이 지닐 수 있습니다.",
    "중요한 것은 속도가 아니라, 정직한 방향입니다.",
]

POOL = REFLECTS_EN if LANG == "English" else REFLECTS_KO

# ===============================
# Session state: keep one reflect until refreshed
# ===============================
if "reflection" not in st.session_state:
    st.session_state.reflection = random.choice(POOL)

# ===============================
# Show reflection
# ===============================
st.subheader(t("Reflection", "성찰"))

st.markdown(
    f"""
> {st.session_state.reflection}
"""
)

# ===============================
# Buttons
# ===============================
col1, col2 = st.columns(2)

with col1:
    if st.button(t("Show another reflection", "다른 성찰 보기")):
        st.session_state.reflection = random.choice(POOL)
        st.rerun()

with col2:
    text_to_save = (
        f"Cosmic Mirror — Reflection Without Prediction\n"
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{st.session_state.reflection}\n"
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
