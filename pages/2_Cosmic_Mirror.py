# pages/2_Cosmic_Mirror.py

import streamlit as st
from datetime import date, time
import os

# --- Page config ---
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🪞",
    layout="wide"
)

# --- Header ---
st.title("🪞 Cosmic Mirror")

st.markdown("""
**This is not divination.**

Birth information is treated only as a symbolic coordinate —  
a mirror to reflect the relationship between the universe, consciousness, and human life.

No future is predicted.  
No authority is invoked.  
Only reflection and responsibility.
""")

st.divider()

# --- Input section ---
st.header("Symbolic Birth Coordinates")

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        "Date of birth",
        value=date(1980, 1, 1),
        min_value=date(1800, 1, 1),
        max_value=date.today()
    )
    birth_time = st.time_input(
        "Time of birth",
        value=time(6, 30)
    )

with col2:
    birth_place = st.text_input(
        "Place of birth (symbolic)",
        value="Suwon Korea"
    )
    user_question = st.text_area(
        "What question is alive in you now?",
        placeholder="Not 'What will happen?', but 'How should I understand where I am?'"
    )

st.divider()

# --- API Key check ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.warning(
        "🔑 OpenAI API key is not configured.\n\n"
        "Streamlit Cloud → Manage app → Settings → Secrets\n\n"
        "Add:\n\n"
        "OPENAI_API_KEY = \"sk-...\""
    )
    st.stop()

# --- Reflect button ---
if st.button("🚀 Reflect"):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        prompt = f"""
You are a philosophical mirror, not a fortune teller.

A human provides symbolic birth coordinates and a living question.

Date of birth: {birth_date}
Time of birth: {birth_time}
Place of birth (symbolic): {birth_place}

The human asks:
\"\"\"{user_question}\"\"\"

Reflect on:
- time
- life phase
- responsibility
- freedom
- meaning

Do not predict the future.
Do not give instructions.
Offer a calm, grounded reflection in Korean.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a philosophical mirror."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        if not response or not response.choices:
            st.error("The mirror remains silent (empty response from API).")
        else:
            st.subheader("🪞 Reflection")
            st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error("The mirror remains silent (API response error).")
        st.code(str(e))
