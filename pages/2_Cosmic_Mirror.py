
Until then, this page remains **safely inactive**.
"""
    )
    st.stop()

# ------------------------------------------------------------
# User input (symbolic only)
# ------------------------------------------------------------
st.subheader("Symbolic Birth Coordinates")

col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input("Date of birth")
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

    if current_question.strip() == "":
        st.warning("Please enter a question to reflect on.")
        st.stop()

    # --------------------------------------------------------
    # Prompt (anti-divination, anti-prediction)
    # --------------------------------------------------------
    system_prompt = """
You are Cosmic Mirror.

You do NOT predict the future.
You do NOT give advice or instructions.
You do NOT claim hidden knowledge.

You reflect the relationship between:
- cosmic time,
- human consciousness,
- symbolic meaning.

You speak calmly, clearly, and responsibly.

Your task:
Transform anxiety into understanding.
Transform dependence into agency.
"""

    user_prompt = f"""
Symbolic coordinates (not causal):
- Date: {birth_date}
- Time: {birth_time}
- Place: {birth_place}

Human question:
"{current_question}"

Reflect this situation using:
- cosmic timescale
- impermanence
- responsibility
- observation over prediction

Do not answer with fortune-telling.
Do not promise outcomes.
"""

    # --------------------------------------------------------
    # OpenAI API call (raw HTTPS, no openai package)
    # --------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
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
            data=json.dumps(payload),
            timeout=30
        )

        if response.status_code != 200:
            st.error("The mirror remains silent. (API response error)")
            st.stop()

        result = response.json()
        reflection = result["choices"][0]["message"]["content"]

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
        st.caption(str(e))
