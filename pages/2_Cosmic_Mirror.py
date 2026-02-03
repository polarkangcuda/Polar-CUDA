import streamlit as st
from datetime import date, time

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🪞",
    layout="wide"
)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("🪞 Cosmic Mirror")

st.write("**This is not divination.**")
st.write(
    "Birth information is treated only as a symbolic coordinate — "
    "a mirror to reflect the relationship between the universe, "
    "consciousness, and human life."
)
st.write("- No future is predicted.")
st.write("- No authority is invoked.")
st.write("- Only reflection and responsibility.")

st.divider()

# --------------------------------------------------
# Input section
# --------------------------------------------------
st.header("Symbolic Birth Coordinates")

col1, col2 = st.columns(2)

with col1:
    dob = st.date_input(
        "Date of birth",
        value=date(1960, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today()
    )

    tob = st.time_input(
        "Time of birth",
        value=time(6, 0)
    )

with col2:
    pob = st.text_input(
        "Place of birth (symbolic)",
        value=""
    )

    question = st.text_area(
        "What question is alive in you now?",
        placeholder="Not 'What will happen?', but 'How should I stand where I am?'",
        height=120
    )

st.divider()

# --------------------------------------------------
# Reflection engine (NO AI, NO API)
# --------------------------------------------------
def cosmic_reflection(dob, tob, pob, question):
    year = dob.year
    hour = tob.hour
    today_year = date.today().year
    age = today_year - year

    # Time symbolism
    if hour < 6:
        time_symbol = "the quiet threshold between night and beginning"
    elif hour < 12:
        time_symbol = "the slow rising of clarity and responsibility"
    elif hour < 18:
        time_symbol = "the long arc of engagement and consequence"
    else:
        time_symbol = "the descent toward reflection and release"

    # Life phase
    if age < 40:
        life_phase = "a period of accumulation and formation"
    elif age < 60:
        life_phase = "a period of discernment and weight-bearing choices"
    else:
        life_phase = "a period of integration, transmission, and restraint"

    # Place line
    if pob.strip() == "":
        place_line = (
            "You did not name a place. "
            "This suggests that your question is anchored not to geography, "
            "but to time and inner stance."
        )
    else:
        place_line = (
            f"You named '{pob}' not as destiny, "
            "but as a reminder that every life begins somewhere, "
            "yet is never confined there."
        )

    # Question line
    if question.strip() == "":
        question_line = (
            "You did not pose a question. "
            "Silence itself can be a form of inquiry."
        )
    else:
        question_line = (
            "You brought this living question:\n\n"
            f"\"{question}\"\n\n"
            "This is not a request for prediction, "
            "but a signal of readiness to carry uncertainty."
        )

    # Assemble reflection safely
    reflection = (
        "### 🪞 Reflection\n\n"
        f"You were born in {year}, at a moment shaped by {time_symbol}.\n\n"
        f"You are now in {life_phase}.\n\n"
        f"{place_line}\n\n"
        f"{question_line}\n\n"
        "What matters now is not what the universe will give you.\n\n"
        "What matters is:\n"
        "- What weight you can now carry without resentment.\n"
        "- What you can release without denial.\n"
        "- What you must do without waiting for permission.\n\n"
        "The universe does not speak in instructions.\n"
        "It responds to clarity of stance.\n\n"
        "This mirror does not tell you who you are.\n"
        "It asks whether you are willing to stand where you already are."
    )

    return reflection

# --------------------------------------------------
# Action
# --------------------------------------------------
if st.button("🚀 Reflect"):
    with st.spinner("Holding the mirror steady..."):
        text = cosmic_reflection(dob, tob, pob, question)
    st.markdown(text)
