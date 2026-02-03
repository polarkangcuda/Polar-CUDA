# =========================================================
# 🌌 Cosmic Mirror
# Cosmos – Consciousness – Human
# (Pure HTTP OpenAI call, no SDK required)
# =========================================================

import os
import json
import datetime
import requests
import streamlit as st

# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🌌",
    layout="centered"
)

# ---------------------------------------------------------
# API Key
# ---------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY is not set.\n\n"
        "Streamlit Cloud → Settings → Secrets\n"
        "OPENAI_API_KEY = sk-..."
    )
    st.stop()

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🌌 Cosmic Mirror")
st.caption(
    "This is not fortune telling.\n\n"
    "Birth data is used only as a symbolic coordinate\n"
    "to reflect the relationship between\n"
    "**the universe, consciousness, and human life**."
)

st.divider()

# ---------------------------------------------------------
# Inputs
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
    "Place of birth",
    placeholder="Seoul, Korea"
)

intent = st.text_area(
    "What uncertainty or question are you living with right now?",
    height=120,
    placeholder=(
        "- A decision you are postponing\n"
        "- A quiet fear\n"
        "- A turning point\n"
        "- A question without words\n"
    )
)

# ---------------------------------------------------------
# Prompt
# ---------------------------------------------------------
def build_prompt():
    return f"""
You are NOT an astrologer.
You are a philosopher of science and consciousness.

Birth data is symbolic, not predictive.

Birth:
- Date: {birth_date}
- Time: {birth_time}
- Place: {birth_place}

Current contemplation:
{intent}

Rules:
- No prediction
- No advice
- No astrology
- No destiny language

Frame the reflection through:
- cosmic formation
- rotation and time
- observation and emergence
- human consciousness as a mirror of the universe

End with a short section titled:
"Quiet Reminder"

Tone:
calm, precise, compassionate

Length:
5–7 short paragraphs
"""

# ---------------------------------------------------------
# OpenAI call (HTTP)
# ---------------------------------------------------------
def call_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": "You speak with philosophical clarity and scientific restraint."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(response.text)

    data = response.json()
    return data["choices"][0]["message"]["content"]

# ---------------------------------------------------------
# Button
# ---------------------------------------------------------
if st.button("🌠 Reflect", type="primary"):
    with st.spinner("Listening to the universe..."):
        try:
            reflection = call_openai(build_prompt())

            st.divider()
            st.subheader("🪞 Reflection")
            st.write(reflection)

            st.caption(
                "This reflection does not define you.\n"
                "It mirrors a moment where the universe\n"
                "recognizes itself as experience."
            )

        except Exception as e:
            st.error("Failed to generate reflection.")
            st.code(str(e))

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "Cosmic Mirror is not divination.\n"
    "It is a narrative interface between\n"
    "cosmic history, symbolic language, and human awareness."
)
