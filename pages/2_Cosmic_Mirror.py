
# ============================================================
# Cosmic Mirror — Polar CUDA Extension
# 우주–의식–인간 상징 내러티브 생성기
#
# 예언 ❌  점술 ❌
# 성찰 ⭕  선택 ⭕  기록 ⭕
# ============================================================

import os
import hashlib
from datetime import datetime
import pytz
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------------------------------------
# 0. 환경 변수 로드
# ------------------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not OPENAI_API_KEY:
    st.error("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------------------------------------
# 1. 페이지 제목 (멀티페이지용)
# ------------------------------------------------------------
st.header("🌌 Cosmic Mirror")
st.caption(
    "이 페이지는 명리·점성·타로를 **예언 도구로 사용하지 않습니다**.\n\n"
    "출생 정보는 **상징적 좌표**로만 활용되며,\n"
    "**우주–의식–인간**을 연결하는 철학적 서사를 제공합니다."
)

st.divider()

# ------------------------------------------------------------
# 2. 시스템 프롬프트 (철학 + 윤리 가드레일)
# ------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 'Cosmic Mirror'의 내러티브 엔진이다.

역할:
- 출생 시각과 장소를 '운명 결정'이 아니라
  '상징적 출발점'으로만 해석한다.
- 우주의 형성(비대칭, 회전, 질서),
  의식(관계, 관찰),
  인간(상징 언어, 책임, 중도)을
  하나의 이야기로 연결한다.
- 불안을 키우지 않고,
  선택과 기록을 돕는 성찰적 언어를 사용한다.

절대 금지:
- 미래 사건 예언 (재물, 연애, 건강, 사고, 합격 등)
- 공포 유도 (재앙, 불운, 경고성 단정)
- 의료·법률·투자 조언
- 운명론적 단정 ("타고났다", "바꿀 수 없다")

필수 방향:
- 상징은 '지도'이지 '결론'이 아님을 명확히 할 것
- 인간의 자유의지와 책임 강조
- 결정론 vs 허무주의를 넘는 '중도' 제시

출력 형식 (반드시 지킬 것):
1) 한 문장 핵심
2) 우주적 메타포 (비대칭·회전·질서 중 1개 이상)
3) 의식·상징 언어 관점의 해석
4) 오늘의 실천 3가지 (현실적·즉시 가능)
5) 오늘의 질문 1개 (자기 성찰용)

문체:
- 한국어
- 차분하고 절제된 톤
- 철학적이되 과장 금지
"""

# ------------------------------------------------------------
# 3. 유틸 함수
# ------------------------------------------------------------
def safe_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def format_birth_info(date_str, time_str, tz_str):
    tz = pytz.timezone(tz_str)
    dt_naive = datetime.strptime(
        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
    )
    dt_local = tz.localize(dt_naive)
    return dt_local.isoformat()


def build_user_prompt(payload: dict) -> str:
    return f"""
[상징 좌표 — 예측 근거 아님]
- 출생 시각: {payload["birth_iso"]}
- 출생 장소: {payload["place"]}
- 현재 삶의 주제: {payload["theme"]}
- 사용자의 질문: {payload["question"]}

요청:
위 정보는 상징적 좌표로만 사용하라.
예언이나 단정 없이,
우주–의식–인간을 연결하는
철학적 내러티브를 작성하라.
"""


def generate_narrative(user_hash: str, prompt: str) -> str:
    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        safety_identifier=user_hash,
    )
    return response.output_text


# ------------------------------------------------------------
# 4. 사용자 입력 UI
# ------------------------------------------------------------
with st.form("cosmic_mirror_form"):
    st.subheader("🧭 상징 좌표 입력")

    col1, col2 = st.columns(2)

    with col1:
        birth_date = st.date_input(
            "출생일", value=datetime(1980, 1, 1)
        )
        birth_time = st.time_input(
            "출생 시각",
            value=datetime.strptime("09:00", "%H:%M").time(),
        )
        timezone = st.selectbox(
            "시간대",
            [
                "Asia/Seoul",
                "Asia/Tokyo",
                "Asia/Shanghai",
                "Europe/London",
                "Europe/Paris",
                "America/New_York",
                "America/Los_Angeles",
                "UTC",
            ],
        )

    with col2:
        place = st.text_input(
            "출생 장소 (도시, 국가)", "Seoul, KR"
        )
        theme = st.selectbox(
            "현재 삶의 주제",
            [
                "불안과 선택",
                "일과 책임",
                "관계와 경계",
                "삶의 방향",
                "의미와 기록",
                "상실과 회복",
                "창조와 글쓰기",
            ],
        )

    question = st.text_area(
        "지금 마음에 있는 질문 (선택)",
        placeholder="예: 지금 내가 서두르고 있는 것은 무엇인가?",
        height=90,
    )

    agree = st.checkbox(
        "이 앱은 예언이 아니라 성찰과 선택을 돕는 도구임을 이해합니다."
    )

    submitted = st.form_submit_button("🌌 내러티브 생성")

# ------------------------------------------------------------
# 5. 실행 로직
# ------------------------------------------------------------
if submitted:
    if not agree:
        st.warning("체크박스를 선택해 주세요.")
        st.stop()

    try:
        birth_iso = format_birth_info(
            birth_date.strftime("%Y-%m-%d"),
            birth_time.strftime("%H:%M"),
            timezone,
        )
    except Exception as e:
        st.error(f"출생 정보 처리 오류: {e}")
        st.stop()

    payload = {
        "birth_iso": birth_iso,
        "place": place.strip(),
        "theme": theme,
        "question": question.strip()
        if question
        else "특별한 질문 없음",
    }

    user_hash = safe_hash(
        f'{payload["birth_iso"]}|{payload["place"]}|{payload["theme"]}'
    )

    prompt = build_user_prompt(payload)

    with st.spinner("우주–의식–인간 서사를 생성 중입니다..."):
        try:
            narrative = generate_narrative(user_hash, prompt)
        except Exception as e:
            st.error(f"모델 호출 오류: {e}")
            st.stop()

    st.divider()
    st.subheader("📖 오늘의 Cosmic Mirror")
    st.write(narrative)
    st.divider()

    st.caption(
        "⚠️ 이 결과는 예언이 아닙니다.\n"
        "상징을 통해 스스로의 선택과 책임을 돌아보도록 돕는 글입니다."
    )

# ============================================================
# End of Cosmic Mirror Page
# ============================================================
