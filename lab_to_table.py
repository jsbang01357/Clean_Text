#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional

import streamlit as st

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

def render_lab_to_excel_tool() -> None:
    """Streamlit 도구 화면 렌더링"""
    st.title("🧪 Lab → Excel 변환기")
    st.caption("정량/정성 검사를 표로 정리한 뒤, 엑셀 파일로 다운로드합니다.")
    st.info(
        "보고서형 검사(영상/내시경/병리)는 표 변환 대신 Text Cleaner 사용을 권장합니다. "
        "정량은 기존 방식대로, 정성은 결과/참고치 비교로 판정합니다."
    )
    
    default_sample = (
        "[진검]  응급혈액[WB, EDTA]\n"
        "　채혈: 2026-04-05 17:48  접수: 2026-04-06 13:45  IMN(조영일)  보고: 2026-04-06 14:04  -\n"
        "　검사명                               결과값       단위         참고치\n"
        "　　(응급)WBC                          9.13         ×10³/㎕    4~10\n"
        "　　(응급)RBC                          3.27  ▼     ×10^6/㎕    4.2~6.3\n"
        "　　(응급)Protein                      2+ (65~200mg/dl)          Negative\n"
    )

    with st.expander("예시 데이터 넣기", expanded=False):
        if st.button("샘플 입력", use_container_width=True):
            st.session_state["lab_excel_input"] = default_sample
            st.rerun()

    raw_text = st.text_area(
        "Lab / EMR 원문 붙여넣기", 
        key="lab_excel_input", 
        height=360, 
        placeholder="여기에 검사 결과 원문을 붙여넣으세요..."
    )
    
    c1, c2 = st.columns(2)
    run = c1.button("표 만들기", type="primary", use_container_width=True)
    clear = c2.button("입력 지우기", use_container_width=True)
    
    if clear:
        st.session_state["lab_excel_input"] = ""
        st.session_state["lab_results"] = None
        st.rerun()

    # --- 데이터 처리 로직 ---
    if run:
        if not raw_text.strip():
            st.warning("원문을 먼저 붙여넣어 주세요.")
            st.session_state["lab_results"] = None
        else:
            rows, qual_rows, unparsed_lines, report_lines = parse_lab_text(raw_text)
            
            st.session_state["lab_results"] = {
                "rows": rows,
                "qual_rows": qual_rows,
                "unparsed_lines": unparsed_lines,
                "report_lines": report_lines,
                "df": rows_to_dataframe(rows),
                "qual_df": qual_rows_to_dataframe(qual_rows),
                "excel_bytes": build_excel_bytes(rows, qual_rows, raw_text, unparsed_lines, report_lines),
                "tsv_text": rows_to_tsv(rows),
                "grouped": rows_grouped(rows),
                "qual_grouped": qual_rows_grouped(qual_rows),
            }

    # --- 결과 렌더링 로직 ---
    if st.session_state.get("lab_results") is not None:
        res = st.session_state["lab_results"]
        rows, qual_rows = res["rows"], res["qual_rows"]
        unparsed_lines, report_lines = res["unparsed_lines"], res["report_lines"]
        df, qual_df = res["df"], res["qual_df"]
        grouped, qual_grouped = res["grouped"], res["qual_grouped"]

        st.success(f"정량 {len(rows)}개 row, 정성 {len(qual_rows)}개 row를 추출했습니다.")
        
        cols = st.columns(6)
        cols[0].metric("정량 row", len(rows))
        cols[1].metric("정성 row", len(qual_rows))
        cols[2].metric("정량 표 수", len(grouped))
        cols[3].metric("미파싱 줄", len(unparsed_lines))
        cols[4].metric("보고서 줄", len(report_lines))
        cols[5].metric("원문 줄 수", len(raw_text.splitlines()))

        now_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d_%H%M")
        dl_c1, dl_c2 = st.columns(2)
        dl_c1.download_button(
            "📥 엑셀 다운로드", 
            data=res["excel_bytes"], 
            file_name=f"table_{now_str}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True
        )
        dl_c2.download_button(
            "📥 TSV 다운로드", 
            data=res["tsv_text"], 
            file_name=f"table_{now_str}.tsv", 
            mime="text/tab-separated-values", 
            use_container_width=True
        )

        st.markdown("---")
        
        st.markdown("### 📊 정량 결과 미리보기")
        for title, group_rows in grouped.items():
            st.markdown(f"#### {title}")
            display_df = rows_to_dataframe(group_rows)[["검사명", "결과값", "단위", "참고치"]]
            st.dataframe(style_lab_df(display_df), use_container_width=True, hide_index=True)
            st.write("")

        if qual_grouped:
            st.markdown("### 📝 정성 결과 미리보기")
            for title, group_rows in qual_grouped.items():
                st.markdown(f"#### {title}")
                display_qdf = qual_rows_to_dataframe(group_rows)[["항목", "결과", "참고치", "판정", "비고"]]
                st.dataframe(style_qual_df(display_qdf), use_container_width=True, hide_index=True)
                st.write("")

        with st.expander("🔍 전체 정량 row 테이블 보기", expanded=False):
            st.dataframe(style_lab_df(df), use_container_width=True, hide_index=True)

        if not qual_df.empty:
            with st.expander("🔍 전체 정성 row 테이블 보기", expanded=False):
                st.dataframe(style_qual_df(qual_df), use_container_width=True, hide_index=True)

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
