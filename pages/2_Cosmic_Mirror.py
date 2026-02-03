# ============================================================
# Cosmic Mirror
# Symbolic Reflection Interface (NOT divination)
# UTF-8 SAFE final version (Korean / Unicode supported)
# ============================================================

import streamlit as st
import requests
import json
from datetime import date

# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Cosmic Mirror",
    page_icon="🪞",
    layout="centered"
)

# ------------------------------------------------------------
# Title & philosophy
# ------------------------------------------------------------
st.title("🪞 Cosmic Mirror")

st.markdown(
    "**This is not divination.**  \n\n"
    "Birth information is treated only as a **symbolic coordinate** — "
    "a mirror to reflect the relationship between the **universe**, "
    "**consciousness**, and **human life**.\n\n"
    "No future is predicted.  \n"
    "No authority is invoked.  \n"
    "Only reflection and responsibility."
)

st.divider()

# ------------------------------------------------------------
# API key check (Streamlit Cloud Secrets)
# ------------------------------------------------------------
API_KEY = st.secrets.get("OPENAI_API_KEY", "")

if not API_KEY:
    st.warning(
        "🔑 **OpenAI API key is not configured yet.**\n\n"
        "To activate **Cosmic Mirror**:\n\n"
        "1. Open **Streamlit Cloud**\n"
        "2. Go to **My apps → Polar-CUDA → Manage app**\n"
        "3. Click **Settings → Secrets**\n"
        "4. Add:\n\n"
        "`OPENAI_API_KEY = \"sk-...\"`\n\n"
        "Until then, this page remains **safely inactive**."
    )
    st.stop()

# ------------------------------------------------------------
# Symbolic user input
# ------------------------------------------------------------
st.subheader("Symbolic Birth Coordinates")

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        "Date of birth",
        value=date(1980, 1, 1),
        min_value=date(1800, 1, 1),
        max_value=date.today()
    )
    birth_time = st.time_input("Time of birth")

with col2:
    birth_place = st.text_input("Place of birth (symbolic)")
    current_question = st.text_area(
        "What question is alive in you now?",
        placeholder="Not 'What will happen?', but 'How should I understand where I am?'"
    )

st.divider()

# ------------------------------------------------------------
# Reflection trigger
# ------------------------------------------------------------
if st.button("🪐 Reflect", type="primary"):

    if not current_question.strip():
        st.warning("Please enter a question to reflect on.")
        st.stop()

    # --------------------------------------------------------
    # Prompts (Unicode-safe)
    # --------------------------------------------------------
    system_prompt = (
        "You are Cosmic Mirror. "
        "You do not predict the future. "
        "You do not give advice or instructions. "
        "You do not claim hidden knowledge. "
        "You reflect the relationship between cosmic time, "
        "human consciousness, and responsibility. "
        "Your role is to transform anxiety into understanding."
    )

    user_prompt = (
        "Symbolic coordinates (not causal):\n"
        f"- Date: {birth_date}\n"
        f"- Time: {birth_time}\n"
        f"- Place: {birth_place}\n\n"
        "Human question:\n"
        f"{current_question}\n\n"
        "Reflect this situation using:\n"
        "- cosmic timescale\n"
        "- impermanence\n"
        "- observation over prediction\n\n"
        "Do not perform fortune-telling.\n"
        "Do not promise outcomes."
    )

    # --------------------------------------------------------
    # OpenAI API call (UTF-8 enforced)
    # --------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.6
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30
        )

        if response.status_code != 200:
            st.error("The mirror remains silent (API response error).")
            st.stop()

        data = response.json()
        reflection = data["choices"][0]["message"]["content"]

        # ----------------------------------------------------
        # Display reflection
        # ----------------------------------------------------
        st.subheader("🪞 Reflection")
        st.markdown(reflection)

        st.caption(
            "This reflection does not describe your fate. "
            "It describes how you are standing within time."
        )

    except Exception as e:
        st.error("The mirror could not respond at this moment.")
        st.caption(repr(e))
