#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from core.lab_parser import parse_lab_text
from core.excel_exporter import (
    rows_to_dataframe,
    qual_rows_to_dataframe,
    build_excel_bytes,
    rows_to_tsv,
    rows_grouped,
    qual_rows_grouped,
    style_lab_df,
    style_qual_df
)

from core.ui_theme import ui_card

def render_lab_to_excel_tool() -> None:
    """Streamlit 도구 화면 렌더링"""
    st.markdown("### 🧪 테이블 변환기")
    st.caption("정량/정성 검사를 시계열 데이터프레임으로 변환하여 엑셀로 추출합니다.")
    
    ui_card(
        "💡 가이드", 
        "보고서형 검사(영상/내시경/병리)는 표 변환 대신 <b>텍스트 클리너</b> 사용을 권장합니다.<br>"
        "정량 및 정성 데이터는 모두 '검사명, 결과값, 단위, 참고치'의 표준 4컬럼 구조로 통일되어 추출됩니다."
    )
    
    default_sample = (
        "[진검]  현장검사[Heparinized WB, Artery]\n"
        "　채혈: 2026-04-09 01:07  접수: 2026-04-09 05:39  보고: 2026-04-09 05:39  -\n"
        "　검사명                               결과값       단위         참고치\n"
        "　ABGA ,Ca++,electrolyte\n"
        "　　pH                                 7.430                     7.35~7.45\n"
        "　　PCO₂                              51.0  ▲     mmHg         35~45\n"
        "　　PO₂                               53.0  ▼     mmHg         83~108\n"
        "　　Na (ABGA)                          134.0  ▼    mmol/L       136~146\n"
        "　　K (ABGA)                           5.50  ▲     mmol/L       3.5~5.1\n\n"
        "[진검]  뇨[Urine, Random]\n"
        "　채혈: 2026-03-17 08:22  접수: 2026-03-17 10:48  보고: 2026-03-17 11:08  -\n"
        "　검사명                               결과값       단위         참고치\n"
        "　(뇨)Routine U/A (10종)\n"
        "　　(뇨) S.G                           1.024                     1.005~1.03\n"
        "　　(뇨) Protein                       2+ (65~200mg/dl)             Negative\n"
        "　　(뇨) Blood                         3+ (≥0.450mg/dl)             Negative\n"
        "　(뇨) Urine Microscopy\n"
        "　　(뇨) RBC                           100이상 cells/HPF             0~3 cells/HPF\n"
        "　　(뇨) WBC                           1~3 cells/HPF             0~3 cells/HPF\n"
    )

    # 샘플 버튼을 밖으로 노출


    def trigger_analysis(text: str):
        """데이터 분석 및 결과를 세션 상태에 저장하는 공통 함수"""
        if not text.strip():
            st.warning("분석할 텍스트가 없습니다. 원문을 먼저 입력해 주세요.")
            st.session_state["lab_results"] = None
            return

        with st.spinner("전문 엔진이 데이터를 구조화하고 있습니다..."):
            rows, qual_rows, unparsed_lines, report_lines = parse_lab_text(text)
            st.session_state["lab_results"] = {
                "rows": rows,
                "qual_rows": qual_rows,
                "unparsed_lines": unparsed_lines,
                "report_lines": report_lines,
                "df": rows_to_dataframe(rows),
                "qual_df": qual_rows_to_dataframe(qual_rows),
                "excel_bytes": build_excel_bytes(rows, qual_rows, text, unparsed_lines, report_lines),
                "tsv_text": rows_to_tsv(rows),
                "grouped": rows_grouped(rows),
                "qual_grouped": qual_rows_grouped(qual_rows),
            }
            st.session_state["scroll_to_results"] = True

    c_input, c_sample = st.columns([4, 1])
    with c_input:
        st.markdown("##### 📥 Lab / EMR 원문 입력")
    with c_sample:
        if st.button("📝 샘플 입력", width="stretch"):
            st.session_state["lab_excel_input"] = default_sample
            trigger_analysis(default_sample)
            st.rerun()

    c_action1, c_action2 = st.columns([1, 1])
    run = c_action1.button("⚡ 테이블 추출 및 분석 실행", type="primary", width="stretch")
    clear = c_action2.button("🗑️ 입력 초기화", width="stretch")
    
    if clear:
        st.session_state["lab_excel_input"] = ""
        st.session_state["lab_results"] = None
        st.rerun()

    raw_text = st.text_area(
        "EMR 결과값 원문을 아래에 붙여넣으세요", 
        key="lab_excel_input", 
        height=320, 
        placeholder="[진검] ... 검사명 결과값 단위 참고치 ...",
        label_visibility="collapsed"
    )

    # --- 데이터 처리 로직 ---
    if run:
        trigger_analysis(raw_text)

    # --- 결과 렌더링 로직 ---
    if st.session_state.get("lab_results") is not None:
        # 자동 스크롤 트리거 (JavaScript - 권장되는 components.html 방식 사용)
        if st.session_state.get("scroll_to_results"):
            st.markdown("<div id='result_section'></div>", unsafe_allow_html=True)
            # st.components.v1.html 직접 호출은 경고가 발생하므로 components.html 사용
            components.html(
                """
                <script>
                    window.parent.document.getElementById('result_section').scrollIntoView({behavior: 'smooth'});
                </script>
                """,
                height=0
            )
            st.session_state["scroll_to_results"] = False # 플래그 초기화

        res = st.session_state["lab_results"]
        rows, qual_rows = res["rows"], res["qual_rows"]
        unparsed_lines, report_lines = res["unparsed_lines"], res["report_lines"]
        df, qual_df = res["df"], res["qual_df"]
        grouped, qual_grouped = res["grouped"], res["qual_grouped"]
        
        st.divider()
        st.markdown("#### 📊 분석 요약")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("정량 데이터", f"{len(rows)} rows", delta=f"{len(grouped)} Tables")
        m2.metric("정성 데이터", f"{len(qual_rows)} rows", delta="Qualitative")
        m3.metric("보고서 분류", f"{len(report_lines)} lines", delta="Report", delta_color="off")
        m4.metric("미파싱/예외", f"{len(unparsed_lines)} lines", delta="Skipped", delta_color="inverse")

        st.markdown("#### 📂 다운로드")
        now_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d_%H%M")
        
        dl_container = st.container()
        with dl_container:
            dl_c1, dl_c2 = st.columns(2)
            dl_c1.download_button(
                label="📥 Excel 파일 (.xlsx) 다운로드",
                data=res["excel_bytes"],
                file_name=f"CleanText_Labs_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                type="primary"
            )
            dl_c2.download_button(
                label="📋 TSV (엑셀 붙여넣기용) 복사",
                data=res["tsv_text"],
                file_name=f"CleanText_Labs_{now_str}.tsv",
                mime="text/tab-separated-values",
                width="stretch"
            )
        st.markdown("---")
        
        st.markdown("#### 📊 정량 결과 미리보기")
        for title, group_rows in grouped.items():
            st.markdown(f"#### {title}")
            display_df = rows_to_dataframe(group_rows)[["검사명", "결과값", "단위", "참고치"]]
            st.dataframe(style_lab_df(display_df), width="stretch", hide_index=True)
            st.write("")

        if qual_grouped:
            st.markdown("### 📝 정성 결과 미리보기")
            for title, group_rows in qual_grouped.items():
                st.markdown(f"#### {title}")
                # 스타일링을 위해 전체 DF에 먼저 규칙을 적용한 뒤, Streamlit 렌더링 시 노출할 컬럼만 선택
                full_qdf = qual_rows_to_dataframe(group_rows)
                styled_qdf = style_qual_df(full_qdf)
                st.dataframe(styled_qdf, width="stretch", hide_index=True, column_order=["검사명", "결과값", "단위", "참고치"])
                st.write("")

        with st.expander("🔍 전체 정량 row 테이블 보기", expanded=False):
            st.dataframe(style_lab_df(df), width="stretch", hide_index=True)

        if not qual_df.empty:
            with st.expander("🔍 전체 정성 row 테이블 보기", expanded=False):
                st.dataframe(style_qual_df(qual_df), width="stretch", hide_index=True)

        if report_lines:
            st.info("💡 보고서형 검사(영상/내시경/병리 등)는 텍스트 클리너 사용을 권장합니다.")
            with st.expander("📄 텍스트 클리너로 넘길 보고서형 줄 보기", expanded=False):
                st.code("\n".join(report_lines), language="text")

        if unparsed_lines:
            with st.expander("⚠️ 파싱되지 일반 줄 보기", expanded=False):
                st.code("\n".join(unparsed_lines), language="text")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Raw EMR/lab text -> Excel-friendly TSV")
    p.add_argument("input", nargs="?", help="input text file path. If omitted, read from stdin.")
    p.add_argument("-o", "--output", help="output TSV file path. If omitted, print to stdout.")
    p.add_argument("--no-header", action="store_true", help="omit TSV header row")
    return p


def read_text(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def write_text(path: Optional[str], text: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def main() -> None:
    args = build_argparser().parse_args()
    raw = read_text(args.input)
    rows, _, _, _ = parse_lab_text(raw)
    tsv = rows_to_tsv(rows, include_header=not args.no_header)
    write_text(args.output, tsv)


if __name__ == "__main__":
    main()
