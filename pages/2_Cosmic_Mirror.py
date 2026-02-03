import streamlit as st
from datetime import date
from io import StringIO

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror — Reflection Without Prediction",
    layout="wide"
)

# --------------------------------------------------
# Language selector
# --------------------------------------------------
lang = st.radio(
    "Language / 언어",
    ["English", "한국어"],
    horizontal=True
)

def t(en, ko):
    return en if lang == "English" else ko

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title(t(
    "Cosmic Mirror — Reflection Without Prediction",
    "Cosmic Mirror — 예언 없는 성찰"
))

st.markdown(t(
    """
This is not divination.

• Birth information is treated only as a symbolic coordinate  
• A mirror to reflect responsibility, not destiny  
• No future is predicted  
• No authority is invoked  
• Only reflection and responsibility
""",
    """
이것은 점술이 아닙니다.

• 출생 정보는 상징적 좌표로만 사용됩니다  
• 운명이 아닌 책임을 비추는 거울입니다  
• 미래를 예측하지 않습니다  
• 권위를 부여하지 않습니다  
• 오직 성찰과 책임만을 다룹니다
"""
))

st.divider()

# --------------------------------------------------
# Inputs
# --------------------------------------------------
st.subheader(t("Symbolic Birth Coordinates", "상징적 출생 좌표"))

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        t("Date of birth", "생년월일"),
        value=date(1960, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )

    birth_time = st.selectbox(
        t("Time of birth", "출생 시각"),
        [f"{h:02d}:00" for h in range(0, 24)]
    )

with col2:
    place = st.text_input(
        t("Place of birth (symbolic)", "출생지 (상징)"),
        placeholder=t(
            "A place that represents where you began",
            "삶이 시작되었다고 느끼는 장소"
        )
    )

    question = st.text_area(
        t("What question is alive in you now?", "지금 마음속에 살아 있는 질문"),
        placeholder=t(
            "You may leave this empty.",
            "비워 두어도 괜찮습니다."
        )
    )

st.divider()

# --------------------------------------------------
# Reflection logic
# --------------------------------------------------
def generate_reflection(birth_date, place, question):
    year = birth_date.year

    if question.strip() == "":
        question_block = t(
            "You chose not to ask a question. That restraint itself is a form of clarity.",
            "질문을 비워두는 선택 자체가 이미 하나의 분명한 태도입니다."
        )
    else:
        question_block = t(
            f'You brought this living question:\n"{question}"',
            f'당신은 다음 질문을 가져왔습니다:\n"{question}"'
        )

    place_block = ""
    if place.strip() != "":
        place_block = t(
            f'You named "{place}" — not as destiny, but as a reminder that every life begins somewhere, yet is never confined there.',
            f'"{place}"를 출생지로 적었습니다. 그것은 운명이 아니라, 삶은 어딘가에서 시작되지만 거기에 갇히지는 않는다는 상기입니다.'
        )

    return t(
        f"""
You were born in {year}, a time shaped by gradual responsibility and long arcs rather than sudden certainty.

{place_block}

{question_block}

This mirror does not predict what comes next.

It asks:
• What weight can you now carry without resentment?
• What can you release without denial?
• Where can you stand without waiting for permission?

The universe does not speak in instructions.
It responds to clarity of stance.
""",
        f"""
당신은 {year}년에 태어났습니다. 그 시기는 급한 확신보다 점진적인 책임이 형성되던 시기였습니다.

{place_block}

{question_block}

이 거울은 미래를 말하지 않습니다.

대신 묻습니다:
• 이제 원망 없이 감당할 수 있는 무게는 무엇입니까?
• 부정하지 않고 내려놓을 수 있는 것은 무엇입니까?
• 허락을 기다리지 않고 설 수 있는 자리는 어디입니까?

우주는 지시하지 않습니다.
입장의 명료함에 응답할 뿐입니다.
"""
    )

# --------------------------------------------------
# Action
# --------------------------------------------------
if st.button(t("Reflect", "성찰하기")):
    reflection = generate_reflection(birth_date, place, question)

    st.subheader(t("Reflection", "성찰"))
    st.markdown(reflection)

    # Save TXT
    buffer = StringIO()
    buffer.write(reflection)

    st.download_button(
        t("Save Reflection (TXT)", "성찰 저장 (TXT)"),
        buffer.getvalue(),
        file_name="cosmic_mirror_reflection.txt",
        mime="text/plain"
    )
