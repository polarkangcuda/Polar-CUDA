import streamlit as st
from datetime import date, time
from io import BytesIO

# =========================================================
# App Config
# =========================================================
st.set_page_config(
    page_title="Cosmic Mirror — Reflection Without Prediction",
    layout="wide"
)

# =========================================================
# Language Toggle
# =========================================================
LANG = st.radio(
    "Language / 언어",
    ["English", "한국어"],
    horizontal=True
)

# =========================================================
# Text Dictionary
# =========================================================
TEXT = {
    "title": {
        "English": "Cosmic Mirror — Reflection Without Prediction",
        "한국어": "코스믹 미러 — 예측 없는 성찰"
    },
    "subtitle": {
        "English": "This is not divination.",
        "한국어": "이것은 점술이 아닙니다."
    },
    "principles": {
        "English": [
            "Birth information is treated only as a symbolic coordinate —",
            "a mirror to reflect the relationship between the universe, consciousness, and human life.",
            "No future is predicted.",
            "No authority is invoked.",
            "Only reflection and responsibility."
        ],
        "한국어": [
            "출생 정보는 상징적 좌표로만 사용됩니다 —",
            "우주, 의식, 인간 삶의 관계를 비추는 거울입니다.",
            "미래를 예측하지 않습니다.",
            "어떠한 권위도 호출하지 않습니다.",
            "오직 성찰과 책임만을 다룹니다."
        ]
    },
    "section_input": {
        "English": "Symbolic Birth Coordinates",
        "한국어": "상징적 출생 좌표"
    },
    "dob": {
        "English": "Date of birth",
        "한국어": "생년월일"
    },
    "tob": {
        "English": "Time of birth",
        "한국어": "출생 시간"
    },
    "place": {
        "English": "Place of birth (symbolic)",
        "한국어": "출생지 (상징)"
    },
    "question": {
        "English": "What question is alive in you now?",
        "한국어": "지금 당신 안에 살아 있는 질문은 무엇입니까?"
    },
    "reflect": {
        "English": "Reflect",
        "한국어": "성찰하기"
    },
    "reflection": {
        "English": "Reflection",
        "한국어": "성찰"
    },
    "download": {
        "English": "Save Reflection",
        "한국어": "성찰 기록 저장"
    }
}

# =========================================================
# Header
# =========================================================
st.title(TEXT["title"][LANG])
st.markdown(f"**{TEXT['subtitle'][LANG]}**")

for line in TEXT["principles"][LANG]:
    st.markdown(f"- {line}")

st.divider()

# =========================================================
# Inputs
# =========================================================
st.header(TEXT["section_input"][LANG])

col1, col2 = st.columns(2)

with col1:
    dob = st.date_input(
        TEXT["dob"][LANG],
        value=date(1960, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )

    tob = st.time_input(
        TEXT["tob"][LANG],
        value=time(6, 0)
    )

with col2:
    place = st.text_input(TEXT["place"][LANG], value="")
    question = st.text_area(TEXT["question"][LANG], height=120)

st.divider()

# =========================================================
# Reflection Logic
# =========================================================
def generate_reflection(lang, dob, place, question):
    year = dob.year

    if question.strip() == "":
        if lang == "English":
            return f"""
You were born in {year}.

You chose not to bring a question.

This is not absence.
It is restraint.

Silence can be a form of readiness.
Not everything meaningful arrives as language.

At this moment, what matters is not articulation,
but the willingness to stand without needing resolution.

The mirror reflects nothing urgent —
and that, too, is information.
"""
        else:
            return f"""
당신은 {year}년에 태어났습니다.

당신은 질문을 가져오지 않았습니다.

이것은 결핍이 아니라 절제입니다.
침묵은 준비의 한 형태일 수 있습니다.

모든 중요한 것이 언어로 도착하지는 않습니다.

지금 중요한 것은 설명이 아니라,
해결을 요구하지 않고 서 있으려는 태도입니다.

이 거울은 긴급한 답을 비추지 않습니다 —
그 자체로 하나의 신호입니다.
"""
    else:
        if lang == "English":
            return f"""
You were born in {year}, at a moment shaped by gradual responsibility.

You named "{place}" not as destiny,
but as a reminder that life begins somewhere,
yet is never confined there.

You brought this living question:

"{question}"

This is not a request for prediction,
but a signal of readiness to carry uncertainty.

What matters now is not what the universe will give you,
but what stance you are willing to hold.

The universe does not speak in instructions.
It responds to clarity of stance.

This mirror does not tell you who you are.
It asks whether you are willing to stand where you already are.
"""
        else:
            return f"""
당신은 {year}년에 태어났습니다.
점진적인 책임이 형성되던 시기였습니다.

당신은 "{place}"를 운명이 아니라,
삶이 시작된 지점을 기억하기 위한 표식으로 두었습니다.

당신이 가져온 살아 있는 질문은 다음과 같습니다:

"{question}"

이것은 예측을 요구하는 질문이 아니라,
불확실성을 감당할 준비가 되었다는 신호입니다.

지금 중요한 것은
우주가 무엇을 줄 것인가가 아니라,
당신이 어떤 태도로 서 있을 것인가입니다.

우주는 지시하지 않습니다.
명료한 입장에 반응할 뿐입니다.

이 거울은 당신이 누구인지 말하지 않습니다.
이미 서 있는 그 자리에 설 의지가 있는지를 묻습니다.
"""

# =========================================================
# Reflect Button
# =========================================================
if st.button(TEXT["reflect"][LANG]):
    reflection_text = generate_reflection(LANG, dob, place, question)
    st.subheader(TEXT["reflection"][LANG])
    st.markdown(reflection_text)

    # Save TXT
    txt_bytes = reflection_text.encode("utf-8")
    st.download_button(
        label=f"{TEXT['download'][LANG]} (TXT)",
        data=txt_bytes,
        file_name="cosmic_mirror_reflection.txt",
        mime="text/plain"
    )

    # Save PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        for line in reflection_text.split("\n"):
            c.drawString(40, y, line)
            y -= 14
            if y < 40:
                c.showPage()
                y = height - 50

        c.save()
        buffer.seek(0)

        st.download_button(
            label=f"{TEXT['download'][LANG]} (PDF)",
            data=buffer,
            file_name="cosmic_mirror_reflection.pdf",
            mime="application/pdf"
        )
    except Exception:
        pass
