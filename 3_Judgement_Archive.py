# pages/3_Judgment_Archive.py
"""
Judgment Archive — Record Without Performance

Principles:
- No prediction
- No divination
- No authority invoked
- No personalized guidance given
- Record standards, not outcomes

This page exists to preserve responsibility as text.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
import json
import streamlit as st

# ------------------------------------------------------------
# Page config (must be first Streamlit call)
# ------------------------------------------------------------
st.set_page_config(
    page_title="Judgment Archive — Record Without Performance",
    page_icon="📘",
    layout="wide",
)

KST = timezone(timedelta(hours=9))

# ------------------------------------------------------------
# UI text (EN / KO)
# ------------------------------------------------------------
UI = {
    "en": {
        "lang_label": "Language / 언어",
        "title": "Judgment Archive — Record Without Performance",
        "subtitle": [
            "This is not advice.",
            "This is not prediction.",
            "No authority is invoked.",
            "Only a record of standards, choices, and responsibility.",
        ],
        "section_new": "New Entry",
        "section_history": "Saved Entries (this device session)",
        "btn_save": "Save entry",
        "btn_clear_form": "Clear form",
        "btn_clear_all": "Clear all saved entries (session)",
        "btn_download_one": "Download this entry (JSON)",
        "btn_download_all": "Download all entries (JSON)",
        "footer": "A record is a boundary. A boundary is a promise to reality.",
        "fields": {
            "date": "Date / Time",
            "title": "Title (one line)",
            "context": "Context (facts only)",
            "decision": "Decision / Choice",
            "alternatives": "Alternatives considered (optional)",
            "standards": "Standards used (explicit)",
            "refuse": "What I refuse to betray",
            "assumptions": "Assumptions (what I think is true)",
            "unknowns": "Unknowns (what I do not know yet)",
            "risk": "Risk & downside boundary",
            "sequence": "Sequence (next steps)",
            "signals": "Signals I will watch (measurable if possible)",
            "review": "Review date / checkpoint",
            "notes": "Notes (short)",
        },
        "placeholders": {
            "title": "e.g., Hold / Exit / Wait / Publish / Decline / Commit",
            "context": "Write only verifiable facts. Avoid stories.",
            "decision": "What will I do? Be concrete.",
            "alternatives": "What else could I have done?",
            "standards": "List the standards you will repeat on hard days.",
            "refuse": "Name the one thing you will not trade.",
            "assumptions": "What am I assuming?",
            "unknowns": "What do I not know yet?",
            "risk": "Define worst-case I accept / do not accept.",
            "sequence": "What is the next smallest step?",
            "signals": "What will change my stance? (numbers, dates, events)",
            "review": "e.g., 2 weeks later / next quarter / after milestone",
            "notes": "One paragraph max.",
        },
        "labels": {
            "mode": "Entry mode",
            "mode_simple": "Simple (fast)",
            "mode_full": "Full (standard)",
            "tone": "Text language",
            "tone_en": "English",
            "tone_ko": "Korean",
        },
        "simple_fields": {
            "one_sentence": "One clean sentence (what is the problem?)",
            "stance": "My stance (not prediction)",
            "next_step": "Next smallest step",
            "boundary": "Boundary (what I will not do)",
        },
        "simple_placeholders": {
            "one_sentence": "Reduce the problem to one clean sentence.",
            "stance": "What position can I stand by?",
            "next_step": "One action I can do within 30 minutes.",
            "boundary": "Name what you refuse to do even under pressure.",
        },
    },
    "ko": {
        "lang_label": "Language / 언어",
        "title": "Judgment Archive — 판단 기록 아카이브",
        "subtitle": [
            "이것은 조언이 아닙니다.",
            "이것은 예언이 아닙니다.",
            "어떤 권위도 호출하지 않습니다.",
            "기준·선택·책임을 텍스트로 남깁니다.",
        ],
        "section_new": "새 기록",
        "section_history": "저장된 기록 (이 기기 세션)",
        "btn_save": "기록 저장",
        "btn_clear_form": "입력 초기화",
        "btn_clear_all": "저장 기록 전체 삭제(세션)",
        "btn_download_one": "이 기록 다운로드(JSON)",
        "btn_download_all": "전체 기록 다운로드(JSON)",
        "footer": "기록은 경계다. 경계는 현실과의 약속이다.",
        "fields": {
            "date": "기록 시각",
            "title": "제목 (한 줄)",
            "context": "상황(사실만)",
            "decision": "선택(구체적으로)",
            "alternatives": "대안(선택 사항)",
            "standards": "사용한 기준(명시)",
            "refuse": "끝내 배반하지 않을 것",
            "assumptions": "가정(내가 사실이라 믿는 것)",
            "unknowns": "미지(아직 모르는 것)",
            "risk": "리스크/하방 경계",
            "sequence": "순서(다음 단계)",
            "signals": "관찰 신호(가능하면 수치/측정)",
            "review": "점검 시점(리뷰)",
            "notes": "메모(짧게)",
        },
        "placeholders": {
            "title": "예: 보유/정리/유보/공개/거절/약속",
            "context": "검증 가능한 사실만. 이야기는 쓰지 않기.",
            "decision": "무엇을 할 것인가? 행동으로 쓰기.",
            "alternatives": "다른 선택지는 무엇이었나?",
            "standards": "힘든 날에도 반복할 기준을 적기.",
            "refuse": "내가 끝내 팔지 않을 가치 1개.",
            "assumptions": "내가 지금 전제하는 것은?",
            "unknowns": "아직 확인하지 못한 것은?",
            "risk": "감당 가능한 최악/불가능한 최악을 구분.",
            "sequence": "다음 ‘가장 작은’ 한 단계.",
            "signals": "입장을 바꿀 신호(수치/일정/이벤트).",
            "review": "예: 2주 후 / 분기말 / 마일스톤 후",
            "notes": "한 문단 이내.",
        },
        "labels": {
            "mode": "기록 모드",
            "mode_simple": "간단(빠르게)",
            "mode_full": "표준(정식)",
            "tone": "언어",
            "tone_en": "English",
            "tone_ko": "한국어",
        },
        "simple_fields": {
            "one_sentence": "한 문장 문제 정의",
            "stance": "나의 입장(예언 아님)",
            "next_step": "다음 최소 행동",
            "boundary": "경계(하지 않을 것)",
        },
        "simple_placeholders": {
            "one_sentence": "문제를 ‘한 문장’으로 줄이기.",
            "stance": "내가 설 수 있는 입장은 무엇인가?",
            "next_step": "30분 안에 할 수 있는 한 가지 행동.",
            "boundary": "압박 속에서도 하지 않을 것 1개.",
        },
    },
}

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def now_kst_str() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

def init_state():
    if "lang" not in st.session_state:
        st.session_state.lang = "ko"
    if "entries" not in st.session_state:
        st.session_state.entries = []  # session-only memory

def entry_template_full(lang: str) -> dict:
    return {
        "recorded_at": now_kst_str(),
        "title": "",
        "context": "",
        "decision": "",
        "alternatives": "",
        "standards": "",
        "refuse_to_betray": "",
        "assumptions": "",
        "unknowns": "",
        "risk_boundary": "",
        "sequence_next_steps": "",
        "signals_to_watch": "",
        "review_checkpoint": "",
        "notes": "",
        "meta": {
            "language": lang,
            "type": "full",
            "version": "1.0",
        },
    }

def entry_template_simple(lang: str) -> dict:
    return {
        "recorded_at": now_kst_str(),
        "one_sentence_problem": "",
        "stance": "",
        "next_smallest_step": "",
        "boundary_not_to_cross": "",
        "meta": {
            "language": lang,
            "type": "simple",
            "version": "1.0",
        },
    }

def safe_json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")

# ------------------------------------------------------------
# App
# ------------------------------------------------------------
init_state()

# Language toggle
lang = st.session_state.lang if st.session_state.lang in ["en", "ko"] else "ko"
choice = st.radio(
    UI[lang]["lang_label"],
    ["English", "한국어"],
    index=0 if lang == "en" else 1,
    horizontal=True,
)
st.session_state.lang = "en" if choice == "English" else "ko"
lang = st.session_state.lang

st.markdown(f"# 📘 {UI[lang]['title']}")
for line in UI[lang]["subtitle"]:
    st.markdown(f"- {line}")
st.divider()

# Mode selector
mode = st.radio(
    UI[lang]["labels"]["mode"],
    [UI[lang]["labels"]["mode_simple"], UI[lang]["labels"]["mode_full"]],
    horizontal=True,
)

st.markdown(f"## {UI[lang]['section_new']}")

# Form
with st.form("judgment_form", clear_on_submit=False):
    if mode == UI[lang]["labels"]["mode_simple"]:
        data = entry_template_simple(lang)
        one_sentence = st.text_input(UI[lang]["simple_fields"]["one_sentence"], value="", placeholder=UI[lang]["simple_placeholders"]["one_sentence"])
        stance = st.text_area(UI[lang]["simple_fields"]["stance"], value="", placeholder=UI[lang]["simple_placeholders"]["stance"], height=90)
        next_step = st.text_area(UI[lang]["simple_fields"]["next_step"], value="", placeholder=UI[lang]["simple_placeholders"]["next_step"], height=80)
        boundary = st.text_area(UI[lang]["simple_fields"]["boundary"], value="", placeholder=UI[lang]["simple_placeholders"]["boundary"], height=80)

        data["one_sentence_problem"] = one_sentence.strip()
        data["stance"] = stance.strip()
        data["next_smallest_step"] = next_step.strip()
        data["boundary_not_to_cross"] = boundary.strip()

    else:
        data = entry_template_full(lang)
        title = st.text_input(UI[lang]["fields"]["title"], value="", placeholder=UI[lang]["placeholders"]["title"])
        context = st.text_area(UI[lang]["fields"]["context"], value="", placeholder=UI[lang]["placeholders"]["context"], height=110)
        decision = st.text_area(UI[lang]["fields"]["decision"], value="", placeholder=UI[lang]["placeholders"]["decision"], height=90)
        alternatives = st.text_area(UI[lang]["fields"]["alternatives"], value="", placeholder=UI[lang]["placeholders"]["alternatives"], height=80)

        st.markdown("### Standards")
        standards = st.text_area(UI[lang]["fields"]["standards"], value="", placeholder=UI[lang]["placeholders"]["standards"], height=110)
        refuse = st.text_area(UI[lang]["fields"]["refuse"], value="", placeholder=UI[lang]["placeholders"]["refuse"], height=70)

        st.markdown("### Uncertainty & boundaries")
        assumptions = st.text_area(UI[lang]["fields"]["assumptions"], value="", placeholder=UI[lang]["placeholders"]["assumptions"], height=80)
        unknowns = st.text_area(UI[lang]["fields"]["unknowns"], value="", placeholder=UI[lang]["placeholders"]["unknowns"], height=80)
        risk = st.text_area(UI[lang]["fields"]["risk"], value="", placeholder=UI[lang]["placeholders"]["risk"], height=90)

        st.markdown("### Next")
        sequence = st.text_area(UI[lang]["fields"]["sequence"], value="", placeholder=UI[lang]["placeholders"]["sequence"], height=90)
        signals = st.text_area(UI[lang]["fields"]["signals"], value="", placeholder=UI[lang]["placeholders"]["signals"], height=90)
        review = st.text_input(UI[lang]["fields"]["review"], value="", placeholder=UI[lang]["placeholders"]["review"])
        notes = st.text_area(UI[lang]["fields"]["notes"], value="", placeholder=UI[lang]["placeholders"]["notes"], height=90)

        data["title"] = title.strip()
        data["context"] = context.strip()
        data["decision"] = decision.strip()
        data["alternatives"] = alternatives.strip()
        data["standards"] = standards.strip()
        data["refuse_to_betray"] = refuse.strip()
        data["assumptions"] = assumptions.strip()
        data["unknowns"] = unknowns.strip()
        data["risk_boundary"] = risk.strip()
        data["sequence_next_steps"] = sequence.strip()
        data["signals_to_watch"] = signals.strip()
        data["review_checkpoint"] = review.strip()
        data["notes"] = notes.strip()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        submitted = st.form_submit_button(UI[lang]["btn_save"], use_container_width=True)
    with col_b:
        clear_form = st.form_submit_button(UI[lang]["btn_clear_form"], use_container_width=True)
    with col_c:
        # placeholder to keep symmetry; no action here
        st.write("")

# Actions after submit
if clear_form:
    # Streamlit doesn't fully clear form without rerun; simplest is to rerun.
    st.rerun()

if submitted:
    # Minimal validation: require at least a stance/decision line
    if data["meta"]["type"] == "simple":
        ok = bool(data["one_sentence_problem"] or data["stance"] or data["next_smallest_step"])
    else:
        ok = bool(data.get("title") or data.get("decision") or data.get("standards"))

    if not ok:
        st.warning("내용이 비어 있습니다. 최소 1개 항목은 입력해 주세요.")
    else:
        st.session_state.entries.insert(0, data)  # newest first
        st.success("저장되었습니다(세션).")
        st.rerun()

st.divider()

# History
st.markdown(f"## {UI[lang]['section_history']}")

if not st.session_state.entries:
    st.info("아직 저장된 기록이 없습니다. 위에서 첫 기록을 남겨 보세요.")
else:
    # Download all
    all_bytes = safe_json_bytes(st.session_state.entries)
    st.download_button(
        UI[lang]["btn_download_all"],
        data=all_bytes,
        file_name="judgment_archive_all.json",
        mime="application/json",
        use_container_width=True,
    )

    # Clear all
    if st.button(UI[lang]["btn_clear_all"], use_container_width=True):
        st.session_state.entries = []
        st.rerun()

    st.markdown("---")

    # Render each entry (collapsed)
    for i, e in enumerate(st.session_state.entries):
        label = e.get("title") or e.get("one_sentence_problem") or f"Entry {i+1}"
        when = e.get("recorded_at", "")
        with st.expander(f"{label}  ·  {when}", expanded=(i == 0)):
            st.code(json.dumps(e, ensure_ascii=False, indent=2), language="json")
            st.download_button(
                UI[lang]["btn_download_one"],
                data=safe_json_bytes(e),
                file_name=f"judgment_entry_{i+1}.json",
                mime="application/json",
                use_container_width=True,
            )

st.markdown("---")
st.markdown(f"*{UI[lang]['footer']}*")
