# =========================================================
# 🌌 Cosmic Mirror
# Universe – Consciousness – Human
# Zero-SDK / Zero-Error Stable Version
# =========================================================

import os
import json
import datetime
import requests
import streamlit as st

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🌌",
    layout="centered"
)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("🌌 Cosmic Mirror")
st.caption(
    "This is not divination.\n\n"
    "Birth information is treated only as a symbolic coordinate —\n"
    "a mirror to reflect the relationship between\n"
    "**the universe, consciousness, and human life**."
)

st.divider()

# ---------------------------------------------------------
# API Key handling (NO ERROR, ONLY MESSAGE)
# ---------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.warning(
        "🔑 OpenAI API key is not configured yet.\n\n"
        "To activate Cosmic Mirror:\n"
        "1. Open **Streamlit Cloud**\n"
        "2. Click **Manage app → Settings → Secrets**\n"
        "3. Add:\n\n"
        "```\nOPENAI_API_KEY = \"sk-...\"\n```\n\n"
        "Until then, this page remains safely inactive."
    )
    st.stop()

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
    "Place of birth (city / country)",
    placeholder="Seoul, Korea"
)

intent = st.text_area(
    "What question or uncertainty are you living with right now?",
    height=120,
    placeholder=(
        "- A decision you are postponing\n"
        "- A quiet anxiety\n"
        "- A turning point\n"
        "- Something you cannot yet name\n"
    )
)

st.divider()

# ---------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------
def build_prompt():
    return f"""
You are NOT an astrologer.
You are NOT a fortune teller.

You are a philosopher of science and consciousness.

Birth data below is symbolic only.
It is NOT used for prediction.

Birth:
- Date: {birth_date}
- Time: {birth_time}
- Place: {birth_place}

Current human contemplation:
{intent}

Rules:
- No prediction
- No advice
- No destiny or fate language
- No astrology or divination terms

Perspective:
- the universe as a process
- rotation, time, emergence
- observation as reality-forming
- human consciousness as a local expression of the cosmos

End with a short section titled:
"Quiet Reminder"

Tone:
calm, grounded, precise, compassionate

Length:
5–7 short paragraphs
"""

# ---------------------------------------------------------
# OpenAI HTTP call (safe)
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
            {
                "role": "system",
                "content": (
                    "You speak with philosophical clarity, "
                    "scientific restraint, and ethical calm."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        return None, response.text

    data = response.json()
    return data["choices"][0]["message"]["content"], None

# ---------------------------------------------------------
# Action button
# ---------------------------------------------------------
if st.button("🌠 Reflect", type="primary"):
    with st.spinner("Listening to the universe..."):
        reflection, error = call_openai(build_prompt())

        st.divider()

        if error:
            st.error("The universe remained silent this time.")
            st.code(error)
        else:
            st.subheader("🪞 Reflection")
            st.write(reflection)

            st.caption(
                "This reflection does not define you.\n"
                "It marks a moment where the universe\n"
                "briefly recognizes itself as lived experience."
            )

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "Cosmic Mirror is not a prediction system.\n"
    "It is a narrative interface between\n"
    "cosmic history, symbolic language, and human awareness."
)
