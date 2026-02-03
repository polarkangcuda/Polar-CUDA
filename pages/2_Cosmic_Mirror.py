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

st.markdown(
    """
**This is not divination.**

Birth information is treated only as a **symbolic coordinate** —  
a mirror to reflect the relationship between the **universe, consciousness, and human life**.

- No future is predicted.  
- No authority is invoked.  
- Only **reflection and responsibility**.
"""
)

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

    # Temporal framing
    if hour < 6:
        time_symbol = "the quiet threshold between night and beginning"
    elif hour < 12:
        time_symbol = "the slow rising of clarity and responsibility"
    elif hour < 18:
        time_symbol = "the long arc of engagement and consequence"
    else:
        time_symbol = "the descent toward reflection and release"

    # Age-as-structure (not prediction)
    age = date.today().year - year

    if age < 40:
        life_phase = "a period of accumulation and formation"
    elif age < 60:
        life_phase = "a period of discernment and weight-bearing choices"
    else:
        life_phase = "a period of integration, transmission, and restraint"

    # Place handling (symbolic, optional)
    if pob.strip() == "":
        place_line = (
            "You did not name a place.  
This itself is meaningful:  
your question is not anchored to geography, but to **time and stance**."
        )
    else:
        place_line = (
            f"You named **{pob}**, not as destiny,  
but as a reminder that every human life begins **somewhere**,  
yet is never confined there."
        )

    # Question handling
    if question.strip() == "":
        question_line = (
            "You did not pose a question.  
Silence is also a form of inquiry.  
Sometimes the task is not to ask more, but to **listen longer**."
        )
    else:
        question_line = (
            f"You brought this living question:\n\n> *{question}*\n\n"
            "This is not a request for answers,  
but a signal of **readiness to carry uncertainty**."
        )

    # Final reflection text
    reflection = f"""
### 🪞 Reflection

You were born in **{year}**, at a moment shaped by  
**{time_symbol}**.

You are now in **{life_phase}** —  
not because time commands you,  
but because **time reveals what can no longer be avoided**.

{place_line}

{question_line}

What matters now is not what the universe will give you.

What matters is:

- What weight are you now able to carry without resentment?
- What can you release without denial?
- What must you do **without waiting for permission**?

The universe does not speak in instructions.  
It responds to **clarity of stance**.

This mirror does not tell you who you are.  
It asks whether you are willing to **stand where you already are**.
"""
    return reflection


# --------------------------------------------------
# Action button
# --------------------------------------------------
if st.button("🚀 Reflect"):
    with st.spinner("Holding the mirror steady..."):
        result = cosmic_reflection(dob, tob, pob, question)

    st.markdown(result)
