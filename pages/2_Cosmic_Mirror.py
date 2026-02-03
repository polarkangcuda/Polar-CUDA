# =========================================================
# 🌌 Cosmic Mirror
# Birth data → Philosophical reflection (Cosmos–Mind–Human)
# Compatible with Streamlit Cloud (NO dotenv required)
# =========================================================

import os
import datetime
import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🌌",
    layout="centered"
)

# ---------------------------------------------------------
# API key check
# ---------------------------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    st.error(
        "OPENAI_API_KEY is not set.\n\n"
        "• Streamlit Cloud: Settings → Secrets\n"
        "• Local: export OPENAI_API_KEY=...\n"
    )
    st.stop()

client = OpenAI(api_key=API_KEY)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🌌 Cosmic Mirror")
st.caption(
    "Birth data is not used for prediction.\n"
    "It is used as a symbolic coordinate to reflect\n"
    "**cosmos → consciousness → human life**."
)

st.divider()

# ---------------------------------------------------------
# User input
# ---------------------------------------------------------
st.subheader("🧭 Birth Coordinates (Symbolic)")

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
    "What are you contemplating right now?",
    placeholder=(
        "e.g.\n"
        "- uncertainty about the future\n"
        "- fear of aging\n"
        "- decision at a crossroads\n"
        "- meaning of my work\n"
    ),
    height=120
)

st.divider()

# ---------------------------------------------------------
# Prompt template
# ---------------------------------------------------------
def build_prompt(date, time, place, intent_text):
    return f"""
You are NOT an astrologer.
You are a philosophical narrator connecting
cosmic formation, human consciousness, and symbolic meaning.

The following birth data is NOT for fortune telling.
It is a symbolic coordinate for reflection.

Birth:
- Date: {date}
- Time: {time}
- Place: {place}

Contemplation:
{intent_text}

Guidelines:
1. Do NOT predict the future.
2. Do NOT give advice like "you should".
3. Do NOT mention astrology, fate, destiny, or luck.
4. Frame the reflection as:
   - the universe remembering itself
   - rotation, time, emergence, observation
5. Speak gently, precisely, and without mysticism.
6. End with a short paragraph titled "Quiet Reminder".

Tone:
- calm
- grounded
- compassionate
- scientifically literate
- philosophically deep

Length:
- 5 to 7 paragraphs total.
"""

# ---------------------------------------------------------
# Generate button
# ---------------------------------------------------------
if st.button("🌠 Reflect", type="primary"):
    with st.spinner("The cosmos is listening..."):

        prompt = build_prompt(
            birth_date,
            birth_time,
            birth_place,
            intent
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a philosopher of science and consciousness."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )

            result = response.choices[0].message.content

            st.divider()
            st.subheader("🪞 Reflection")
            st.write(result)

            st.caption(
                "This reflection does not define you.\n"
                "It simply mirrors a moment in which the universe\n"
                "has become aware of itself as *you*."
            )

        except Exception as e:
            st.error("An error occurred while generating reflection.")
            st.exception(e)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "Cosmic Mirror is not a divination tool.\n"
    "It is a narrative interface between\n"
    "cosmic history, human consciousness, and choice."
)
