#!/usr/bin/env python3
"""
lab_to_table.py

EMR / lab raw text -> Streamlit table + Excel export + TSV converter

핵심 기능
- raw lab text에서 검사 결과 row 추출
- 검사명 정리: (응급), (응급뇨), 앞쪽 들여쓰기 기호(‥, .. 등) 제거
- 이상표시(▲/▼)는 결과값 오른쪽에 붙임
- 여러 검사 블록을 section + 채혈일 기준으로 그룹화
- Streamlit UI에서 표 미리보기 + Excel 다운로드
- CLI에서는 TSV 출력 유지
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Tuple

# ===== Parser constants =====

SKIP_EXACT = {
    "[소견]",
    "[의뢰의사 Comment]",
    "Antibiotic",
}

SECTION_HEADER_RE = re.compile(r"^\s*\[진검\]\s*(.+?)\s*$")
META_LINE_RE = re.compile(r"(채혈:|접수:|보고:|IMN\()")
COLUMN_HEADER_RE = re.compile(r"^\s*검사명\s+결과값\s+단위\s+참고치\s*$")
COMMENT_LINE_RE = re.compile(r"^\s*(\[소견\]|\[의뢰의사 Comment\]|\[판독의\])")
MARKDOWN_HEADER_RE = re.compile(r"^\s*\|\s*Test\s*\|\s*Value\s*\|", re.I)
MARKDOWN_RULE_RE = re.compile(r"^\s*\|\s*-{2,}")
BULLET_PREFIX_RE = re.compile(r"^[\s\.·‥∙⋅•ㆍ]+")
EMERGENCY_PREFIX_RE = re.compile(r"^\((?:응급|응급뇨)\)\s*")
DRAW_TIME_RE = re.compile(r"채혈:\s*(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})")

UNIT_PATTERNS = [
    r"×10\^?\d+/[^\s]+",
    r"×10³/[^\s]+",
    r"×10\^6/[^\s]+",
    r"mL/min/1\.73m²",
    r"cells/HPF",
    r"/LPF",
    r"mg/dl",
    r"g/dl",
    r"g/㎗",
    r"IU/L",
    r"mmol/L",
    r"mm/h",
    r"fL",
    r"pg",
    r"%",
]
UNIT_RE = re.compile(r"^(?:" + "|".join(UNIT_PATTERNS) + r")$", re.I)
FLAG_RE = re.compile(r"^[▲▼]$")
RANGE_HINT_RE = re.compile(r"[~<>≤≥]|\b경계치\b|\b높음\b|\b정상\b|\b이상지질혈증\b|\b신부전\b|\b감소\b")

SECTION_TITLE_BLACKLIST = {
    "CBC with diff count & ESR",
    "WBC differential count",
    "Admission/Electro Battery(24",
    "종)",
    "Routine U/A with Microscope",
    "Gram Stain & Cul & Sensi",
    "Urine Microscopy",
}


# ===== Data model =====

@dataclass
class LabRow:
    name: str
    value: str
    unit: str = ""
    ref: str = ""
    raw_line: str = ""
    section: str = ""
    draw_time: str = ""
    table_title: str = ""


# ===== Utility =====

def normalize_line(line: str) -> str:
    line = line.replace("\u3000", " ")
    line = line.replace("\t", " ")
    line = line.rstrip()
    line = re.sub(r" {2,}", "  ", line)
    return line


def split_columns(line: str) -> List[str]:
    parts = [p.strip() for p in re.split(r" {2,}", line.strip())]
    return [p for p in parts if p]


def clean_test_name(name: str) -> str:
    name = BULLET_PREFIX_RE.sub("", name)
    while True:
        new = EMERGENCY_PREFIX_RE.sub("", name)
        new = BULLET_PREFIX_RE.sub("", new)
        if new == name:
            break
        name = new
    name = re.sub(r"\s+", " ", name).strip()
    return name


def clean_section_name(section: str) -> str:
    section = section.strip()
    section = re.sub(r"\[[^\]]+\]", "", section)
    section = re.sub(r"\s+", " ", section).strip(" -")
    return section


def extract_section_name(line: str) -> str:
    m = SECTION_HEADER_RE.match(line.strip())
    if not m:
        return "Unknown"
    return clean_section_name(m.group(1)) or "Unknown"


def extract_draw_time(line: str) -> str:
    m = DRAW_TIME_RE.search(line)
    if not m:
        return ""
    return f"{m.group(1)} {m.group(2)}"


def format_title(section: str, draw_time: str) -> str:
    if draw_time:
        try:
            dt = datetime.strptime(draw_time, "%Y-%m-%d %H:%M")
            return f"{section}_{dt.year}_{dt.month:02d}_{dt.day:02d}"
        except ValueError:
            pass
    return section


def is_skip_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if s in SKIP_EXACT:
        return True
    if SECTION_HEADER_RE.match(s):
        return True
    if COLUMN_HEADER_RE.match(s):
        return True
    if COMMENT_LINE_RE.match(s):
        return True
    if MARKDOWN_HEADER_RE.match(s) or MARKDOWN_RULE_RE.match(s):
        return True
    if META_LINE_RE.search(s):
        return True
    if s.startswith("- "):
        return True
    return False


def looks_like_continuation_ref(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if is_skip_line(s):
        return False
    if RANGE_HINT_RE.search(s):
        return True
    if s.startswith("Total cholesterol -"):
        return True
    return False


def append_ref(old_ref: str, extra: str) -> str:
    extra = re.sub(r"\s+", " ", extra).strip()
    if not old_ref:
        return extra
    return f"{old_ref}; {extra}"


def compose_value(value: str, flag: str = "") -> str:
    value = value.strip()
    flag = flag.strip()
    if value and flag:
        return f"{value} {flag}"
    return value or flag


def value_flag(value: str) -> str:
    if value.endswith("▲"):
        return "up"
    if value.endswith("▼"):
        return "down"
    return ""


# ===== Parsing =====

def parse_candidate_row(line: str, section: str = "", draw_time: str = "") -> Optional[LabRow]:
    parts = split_columns(line)
    if len(parts) < 2:
        return None

    name = ""
    value = ""
    flag = ""
    unit = ""
    ref = ""

    if len(parts) >= 4:
        name = parts[0]
        value = parts[1]
        idx = 2

        if idx < len(parts) and FLAG_RE.match(parts[idx]):
            flag = parts[idx]
            idx += 1

        if idx < len(parts) and UNIT_RE.match(parts[idx]):
            unit = parts[idx]
            idx += 1

        if idx < len(parts):
            ref = " ".join(parts[idx:]).strip()

        if not unit and ref and UNIT_RE.match(ref):
            unit, ref = ref, ""

    elif len(parts) == 3:
        name, second, third = parts
        m = re.match(r"^(.*?)(?:\s*([▲▼]))?$", second)
        if m:
            value = m.group(1).strip()
            flag = (m.group(2) or "").strip()

        if UNIT_RE.match(third):
            unit = third
        else:
            ref = third

    else:  # len(parts) == 2
        name, second = parts
        m = re.match(r"^(.*?)(?:\s*([▲▼]))?$", second)
        if m:
            value = m.group(1).strip()
            flag = (m.group(2) or "").strip()

    name = clean_test_name(name)

    if not name:
        return None
    if name in SECTION_TITLE_BLACKLIST:
        return None

    m2 = re.match(r"^(.*?)(?:\s*([▲▼]))$", value)
    if m2 and not flag:
        value = m2.group(1).strip()
        flag = m2.group(2)

    if name in {"검사명", "Test"} or value in {"결과값", "Value"}:
        return None
    if not value:
        return None

    value = re.sub(r"\s+", " ", value).strip()
    unit = re.sub(r"\s+", " ", unit).strip()
    ref = re.sub(r"\s+", " ", ref).strip()

    return LabRow(
        name=name,
        value=compose_value(value, flag),
        unit=unit,
        ref=ref,
        raw_line=line,
        section=section,
        draw_time=draw_time,
        table_title=format_title(section or "Unknown", draw_time),
    )


def parse_lab_text(text: str) -> Tuple[List[LabRow], List[str]]:
    rows: List[LabRow] = []
    unparsed_lines: List[str] = []
    last_row: Optional[LabRow] = None
    in_comment_block = False
    current_section = "Unknown"
    current_draw_time = ""

    for raw in text.splitlines():
        line = normalize_line(raw)
        stripped = line.strip()

        if not stripped:
            continue

        if SECTION_HEADER_RE.match(stripped):
            current_section = extract_section_name(stripped)
            current_draw_time = ""
            in_comment_block = False
            last_row = None
            continue

        draw_time = extract_draw_time(stripped)
        if draw_time:
            current_draw_time = draw_time
            continue

        if is_skip_line(stripped):
            if stripped in {"[소견]", "[의뢰의사 Comment]"}:
                in_comment_block = True
            continue

        if in_comment_block:
            if SECTION_HEADER_RE.match(stripped):
                in_comment_block = False
            else:
                continue

        row = parse_candidate_row(stripped, section=current_section, draw_time=current_draw_time)
        if row:
            rows.append(row)
            last_row = row
            continue

        if last_row and looks_like_continuation_ref(stripped):
            last_row.ref = append_ref(last_row.ref, stripped)
            continue

        if stripped not in SECTION_TITLE_BLACKLIST:
            unparsed_lines.append(stripped)

    return rows, unparsed_lines


# ===== Export helpers =====

def rows_to_tsv(rows: Iterable[LabRow], include_header: bool = True) -> str:
    out_lines: List[str] = []
    if include_header:
        out_lines.append("\t".join(["제목", "검사명", "결과값", "단위", "참고치"]))
    for row in rows:
        out_lines.append("\t".join([row.table_title, row.name, row.value, row.unit, row.ref]))
    return "\n".join(out_lines)


def rows_to_dataframe(rows: List[LabRow]):
    import pandas as pd

    return pd.DataFrame(
        [
            {
                "제목": r.table_title,
                "검사명": r.name,
                "결과값": r.value,
                "단위": r.unit,
                "참고치": r.ref,
                "검사종류": r.section,
                "채혈시각": r.draw_time,
            }
            for r in rows
        ]
    )


def rows_grouped(rows: List[LabRow]) -> Dict[str, List[LabRow]]:
    grouped: Dict[str, List[LabRow]] = {}
    for row in rows:
        grouped.setdefault(row.table_title or "Unknown", []).append(row)
    return grouped


def build_excel_bytes(rows: List[LabRow], raw_text: str, unparsed_lines: List[str]) -> BytesIO:
    import pandas as pd
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    parsed_df = rows_to_dataframe(rows)
    raw_df = pd.DataFrame({"원문": raw_text.splitlines()})
    unparsed_df = pd.DataFrame({"파싱되지 않은 줄": unparsed_lines})
    grouped = rows_grouped(rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        parsed_df.to_excel(writer, index=False, sheet_name="Parsed_Labs")
        raw_df.to_excel(writer, index=False, sheet_name="Original_Text")
        unparsed_df.to_excel(writer, index=False, sheet_name="Unparsed")

        wb = writer.book
        ws_group = wb.create_sheet("Grouped_Tables")

        title_fill = PatternFill(fill_type="solid", fgColor="D9EAF7")
        header_fill = PatternFill(fill_type="solid", fgColor="F3F4F6")
        title_font = Font(bold=True, size=12)
        header_font = Font(bold=True)
        red_font = Font(color="C62828")
        blue_font = Font(color="1565C0")

        current_row = 1
        headers = ["검사명", "결과값", "단위", "참고치"]

        for title, group_rows in grouped.items():
            ws_group.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
            cell = ws_group.cell(row=current_row, column=1, value=title)
            cell.font = title_font
            cell.fill = title_fill
            cell.alignment = Alignment(horizontal="left")
            current_row += 1

            for idx, header in enumerate(headers, start=1):
                c = ws_group.cell(row=current_row, column=idx, value=header)
                c.font = header_font
                c.fill = header_fill
            current_row += 1

            for r in group_rows:
                ws_group.cell(row=current_row, column=1, value=r.name)
                value_cell = ws_group.cell(row=current_row, column=2, value=r.value)
                ws_group.cell(row=current_row, column=3, value=r.unit)
                ws_group.cell(row=current_row, column=4, value=r.ref)

                flag = value_flag(r.value)
                if flag == "up":
                    value_cell.font = red_font
                elif flag == "down":
                    value_cell.font = blue_font
                current_row += 1

            current_row += 2

        for sheet_name, df in {
            "Parsed_Labs": parsed_df,
            "Original_Text": raw_df,
            "Unparsed": unparsed_df,
        }.items():
            ws = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns, start=1):
                max_len = max([len(str(col))] + [len(str(v)) for v in df[col].fillna("")]) if not df.empty else len(str(col))
                ws.column_dimensions[get_column_letter(idx)].width = min(max(max_len + 2, 12), 60)

            if sheet_name == "Parsed_Labs" and not df.empty:
                for row_idx in range(2, len(df) + 2):
                    cell = ws.cell(row=row_idx, column=3)  # 결과값
                    val = str(cell.value or "")
                    flag = value_flag(val)
                    if flag == "up":
                        cell.font = red_font
                    elif flag == "down":
                        cell.font = blue_font

        for idx, width in {1: 28, 2: 16, 3: 14, 4: 50}.items():
            ws_group.column_dimensions[get_column_letter(idx)].width = width

    output.seek(0)
    return output


# ===== Streamlit UI =====

def render_lab_to_excel_tool() -> None:
    import streamlit as st

    st.title("🧪 Lab → Excel 변환기")
    st.caption("검사 결과 행을 표로 정리한 뒤, 엑셀 파일로 바로 다운로드합니다.")
    st.info(
        "원문에서 검사명 / 결과값 / 단위 / 참고치를 추출합니다. "
        "검사명 앞의 (응급), (응급뇨), ‥ 같은 표시는 제거하고, ▲/▼는 결과값 오른쪽에 붙입니다. "
        "검사 블록이 바뀌면 엑셀 Grouped_Tables 시트에서 별도 표로 분리됩니다."
    )

    default_sample = """[진검]  응급혈액[WB, EDTA]\n　채혈: 2026-04-05 17:48  접수: 2026-04-06 13:45  IMN(조영일)  보고: 2026-04-06 14:04  -\n　검사명                               결과값       단위         참고치\n　　(응급)WBC                          9.13         ×10³/㎕    4~10\n　　(응급)RBC                          3.27  ▼     ×10^6/㎕    4.2~6.3\n　　‥(응급)RDW                        15.9  ▲     %            11.5~14.5\n[진검]  응급화학[Plasma, PST]\n　채혈: 2026-04-05 17:48  접수: 2026-04-06 14:11  IMN(조영일)  보고: 2026-04-06 14:28  -\n　검사명                               결과값       단위         참고치\n　　(응급)Glucose                      177  ▲      mg/dl        70~99\n　　(응급)Albumin                      2.6  ▼      g/dl         3.8~5.3\n"""

    with st.expander("예시 데이터 넣기", expanded=False):
        if st.button("샘플 입력", use_container_width=True):
            st.session_state["lab_excel_input"] = default_sample

    raw_text = st.text_area(
        "Lab / EMR 원문 붙여넣기",
        key="lab_excel_input",
        height=360,
        placeholder="여기에 검사 결과 원문을 붙여넣으세요...",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        run = st.button("표 만들기", type="primary", use_container_width=True)
    with col2:
        clear = st.button("입력 지우기", use_container_width=True)

    if clear:
        st.session_state["lab_excel_input"] = ""
        st.rerun()

    if run:
        if not raw_text.strip():
            st.warning("원문을 먼저 붙여넣어 주세요.")
            return

        rows, unparsed_lines = parse_lab_text(raw_text)
        df = rows_to_dataframe(rows)
        excel_bytes = build_excel_bytes(rows, raw_text, unparsed_lines)
        tsv_text = rows_to_tsv(rows)
        grouped = rows_grouped(rows)

        st.success(f"{len(rows)}개 row를 추출했습니다.")
        metric_cols = st.columns(4)
        metric_cols[0].metric("파싱된 row", len(rows))
        metric_cols[1].metric("검사 표 수", len(grouped))
        metric_cols[2].metric("미파싱 줄", len(unparsed_lines))
        metric_cols[3].metric("원문 줄 수", len(raw_text.splitlines()))

        st.markdown("### 표 미리보기")
        for title, group_rows in grouped.items():
            st.markdown(f"#### {title}")
            group_df = rows_to_dataframe(group_rows)[["검사명", "결과값", "단위", "참고치"]]
            st.dataframe(group_df, use_container_width=True, hide_index=True)
            st.write("")

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📥 엑셀 다운로드",
                data=excel_bytes,
                file_name="lab_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                label="📥 TSV 다운로드",
                data=tsv_text,
                file_name="lab_analysis.tsv",
                mime="text/tab-separated-values",
                use_container_width=True,
            )

        with st.expander("전체 row 테이블 보기", expanded=False):
            st.dataframe(df, use_container_width=True, hide_index=True)

        if unparsed_lines:
            with st.expander("파싱되지 않은 줄 보기", expanded=False):
                st.code("\n".join(unparsed_lines), language="text")


# ===== CLI =====

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
    rows, _ = parse_lab_text(raw)
    tsv = rows_to_tsv(rows, include_header=not args.no_header)
    write_text(args.output, tsv)


if __name__ == "__main__":
    main()
