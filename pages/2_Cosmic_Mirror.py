# =========================================================
# 🌌 Cosmic Mirror
# Cosmos – Consciousness – Human (Legacy OpenAI SDK safe)
# =========================================================

import os
import datetime
import streamlit as st
import openai

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🌌",
    layout="centered"
)

# ---------------------------------------------------------
# API key check
# ---------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY is None or OPENAI_API_KEY.strip() == "":
    st.error(
        "OPENAI_API_KEY is not set.\n\n"
        "• Streamlit Cloud: Settings → Secrets\n"
        "• Local: export OPENAI_API_KEY=...\n"
    )
    st.stop()

openai.api_key = OPENAI_API_KEY

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🌌 Cosmic Mirror")
st.caption(
    "This is not divination.\n\n"
    "Birth data is used only as a symbolic coordinate\n"
    "to reflect the relationship between\n"
    "**the universe, consciousness, and human life**."
)

st.divider()

# ---------------------------------------------------------
# User input
# ---------------------------------------------------------
st.subheader("🧭 Symbolic Birth Coordinates")

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        "Date of birth",
        value=datetime.date(1990, 1, 1)
    )

with col2:
    birth_time = st.time_input(
        "Time of birth",
        value=datetime.time(12, 0)
    )

birth_place = st.text_input(
    "Place of birth (city / country)",
    placeholder="Seoul, Korea"
)

intent = st.text_area(
    "What question or uncertainty are you living with right now?",
    placeholder=(
        "- A decision you are postponing\n"
        "- A fear you cannot name\n"
        "- A sense of being at a turning point\n"
        "- A quiet doubt beneath daily life\n"
    ),
    height=120
)

st.divider()

# ---------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------
def build_prompt(date, time, place, intent_text):
    return f"""
You are NOT an astrologer.
You are a philosopher of science and consciousness.

The following birth data is NOT used for prediction.
It is a symbolic coordinate for reflection.

Birth (symbolic):
- Date: {date}
- Time: {time}
- Place: {place}

Present contemplation:
{intent_text}

Guidelines:
1. Do NOT predict the future.
2. Do NOT give advice or instructions.
3. Do NOT use astrology, fate, destiny, or luck.
4. Frame the reflection through:
   - cosmic formation
   - rotation and time
   - observation and emergence
5. Treat the human as a moment where the universe
   becomes aware of itself.
6. End with a short section titled "Quiet Reminder".

Tone:
- calm
- grounded
- precise
- compassionate
- scientifically literate

Length:
- 5 to 7 short paragraphs total.
"""

# ---------------------------------------------------------
# Generate reflection
# ---------------------------------------------------------
if st.button("🌠 Reflect", type="primary"):
    with st.spinner("Listening to the universe..."):

        prompt = build_prompt(
            birth_date,
            birth_time,
            birth_place,
            intent
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You speak with philosophical clarity and scientific restraint."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )

            result = response["choices"][0]["message"]["content"]

            st.divider()
            st.subheader("🪞 Reflection")
            st.write(result)

            st.caption(
                "This text does not define you.\n"
                "It reflects a moment in which\n"
                "the universe recognizes itself as experience."
            )

        except Exception as e:
            st.error("An error occurred while generating the reflection.")
            st.exception(e)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "Cosmic Mirror is not a fortune-telling system.\n"
    "It is a narrative interface between\n"
    "cosmic history, symbolic language, and human awareness."
)
