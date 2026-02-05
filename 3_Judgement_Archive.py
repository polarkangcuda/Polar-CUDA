# =========================================================
# Judgement Archive — A + B + C FULL VERSION
# Author: Sung-Ho Kang (personal decision archive)
# =========================================================

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# -------------------------------
# Basic setup
# -------------------------------
st.set_page_config(
    page_title="Judgement Archive",
    page_icon="📘",
    layout="wide"
)

# -------------------------------
# Fixed philosophy (C)
# -------------------------------
FIXED_JUDGEMENT_PHRASES = [
    "지금은 결정하지 않는다.",
    "기준은 유지, 행동은 보류한다.",
    "판단은 기록으로 남기고, 행동은 다음 단계로 넘긴다."
]

FOOTER_TEXT = "기록은 경계다. 경계는 현실과의 약속이다."

# -------------------------------
# Storage setup (A)
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RECORD_DIR = BASE_DIR / "records"
RECORD_DIR.mkdir(exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")

PRIVATE_JSON = RECORD_DIR / f"{TODAY}_private.json"
PUBLIC_JSON = RECORD_DIR / f"{TODAY}_public.json"
ALL_CSV = RECORD_DIR / f"{TODAY}_all.csv"

# -------------------------------
# Session storage
# -------------------------------
if "session_records" not in st.session_state:
    st.session_state.session_records = []

# -------------------------------
# UI
# -------------------------------
st.sidebar.title("app")
st.sidebar.markdown("**Judgement Archive**")

st.title("📘 Judgement Archive — 판단 기록 아카이브")

st.markdown("""
- 이것은 **조언이 아닙니다**
- 이것은 **예언이 아닙니다**
- 어떤 권위도 호출하지 않습니다
- **기준·선택·책임을 텍스트로 남깁니다**
""")

st.divider()

st.markdown("### 🧭 강 박사 전용 판단 원칙")
for p in FIXED_JUDGEMENT_PHRASES:
    st.markdown(f"- **{p}**")

st.divider()

# -------------------------------
# Input form
# -------------------------------
st.subheader("새 기록")

with st.form("judgement_form", clear_on_submit=False):

    title = st.text_input(
        "제목 (한 줄)",
        placeholder="예: 보유 / 정리 / 유보 / 공개 / 거절 / 약속"
    )

    situation = st.text_area(
        "상황 (사실만)",
        placeholder="검증 가능한 사실만 기록. 해석·이야기 금지."
    )

    decision = st.text_area(
        "선택 (구체적으로)",
        placeholder="무엇을 할 것인가? 행동 단위로 작성."
    )

    alternatives = st.text_area(
        "대안 (선택 사항)",
        placeholder="다른 선택지는 무엇이었는가?"
    )

    st.markdown("### Standards")

    standards = st.text_area(
        "사용한 기준 (명시)",
        placeholder="힘든 날에도 반복할 기준을 적는다."
    )

    non_negotiable = st.text_area(
        "끝내 배반하지 않을 것",
        placeholder="내가 끝내 팔지 않을 가치 1개."
    )

    st.markdown("### Uncertainty & boundaries")

    assumptions = st.text_area(
        "가정 (내가 사실이라 믿는 것)",
        placeholder="내가 지금 전제하는 것은?"
    )

    unknowns = st.text_area(
        "미지 (아직 모르는 것)",
        placeholder="아직 확인하지 못한 것은?"
    )

    risk_boundary = st.text_area(
        "리스크 / 하방 경계",
        placeholder="감당 가능한 최악 / 불가능한 최악 구분."
    )

    st.markdown("### Next")

    next_step = st.text_area(
        "다음 단계 (가장 작은 행동)",
        placeholder="다음 ‘가장 작은’ 한 단계."
    )

    signal = st.text_area(
        "관찰 신호 (가능하면 수치)",
        placeholder="입장을 바꿀 신호 (수치/일정/이벤트)."
    )

    review_time = st.text_input(
        "점검 시점",
        placeholder="예: 2주 후 / 분기말 / 마일스톤 이후"
    )

    memo = st.text_area(
        "메모 (짧게)",
        placeholder="한 문단 이내."
    )

    is_public = st.checkbox("☑ 공개 기록으로 저장 (기본: 개인 전용)", value=False)

    submitted = st.form_submit_button("기록 저장")

# -------------------------------
# Save logic (A + B)
# -------------------------------
if submitted:
    record = {
        "date": TODAY,
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "situation": situation,
        "decision": decision,
        "alternatives": alternatives,
        "standards": standards,
        "non_negotiable": non_negotiable,
        "assumptions": assumptions,
        "unknowns": unknowns,
        "risk_boundary": risk_boundary,
        "next_step": next_step,
        "signal": signal,
        "review_time": review_time,
        "memo": memo,
        "public": is_public,
        "fixed_phrases": FIXED_JUDGEMENT_PHRASES
    }

    st.session_state.session_records.append(record)

    # JSON append helper
    def append_json(path, data):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    append_json(PRIVATE_JSON, record)

    if is_public:
        append_json(PUBLIC_JSON, record)

    # CSV
    df = pd.DataFrame(st.session_state.session_records)
    df.to_csv(ALL_CSV, index=False, encoding="utf-8-sig")

    st.success(
        "공개 기록 포함 저장 완료" if is_public else "개인 기록으로 저장 완료"
    )

# -------------------------------
# Session view
# -------------------------------
st.divider()
st.subheader("저장된 기록 (이 기기 세션)")

if not st.session_state.session_records:
    st.info("아직 저장된 기록이 없습니다. 위에서 첫 기록을 남겨 보세요.")
else:
    st.dataframe(pd.DataFrame(st.session_state.session_records))

st.divider()
st.markdown(f"_{FOOTER_TEXT}_")
