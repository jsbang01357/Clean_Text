from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

SKIP_EXACT = {"[소견]", "[의뢰의사 Comment]", "Antibiotic", "[판정]", ".", "신속)", "tate)", "종)", "fraction)", "tion)"}
SECTION_HEADER_RE = re.compile(r"^\s*\[(진검|핵의학|병리과|수혈의학|진단검사의학과|건강의학센터|병리|영상의학과|심장혈관센터|재활의학과|호흡기센터|내분비대사내과|이비인후-두경부외과|이비인후-두경부센터|내분비내과)\]\s*(.+?)\s*$")
META_LINE_RE = re.compile(r"(채혈:|접수:|보고:|IM[NI]\()")
COLUMN_HEADER_RE = re.compile(r"^\s*검사명\s+결과값\s+단위\s+참고치\s*$")
COMMENT_LINE_RE = re.compile(r"^\s*(\[소견\]|\[의뢰의사 Comment\]|\[판독의\]|\[판정\]|판독의:)")
MARKDOWN_HEADER_RE = re.compile(r"^\s*\|\s*Test\s*\|\s*Value\s*\|", re.I)
MARKDOWN_RULE_RE = re.compile(r"^\s*\|\s*-{2,}")
BULLET_PREFIX_RE = re.compile(r"^[\s\.·‥∙⋅•ㆍ]+")
EMERGENCY_PREFIX_RE = re.compile(r"^\((?:응급|응급뇨|응급면역|뇨)\)\s*")
DRAW_TIME_RE = re.compile(r"채혈:\s*(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})")
RANGE_LIKE_NAME_RE = re.compile(r"^\s*(?:[<>≤≥]\s*\d|\d+(?:\.\d+)?\s*[~-]\s*\d+(?:\.\d+)?)")
CONTINUATION_REF_START_RE = re.compile(r"^\s*(?:[<>≤≥]\s*\d|\d+(?:\.\d+)?\s*~\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*이상|\d+(?:\.\d+)?\s*이하)")
CONTINUATION_REF_KEYWORD_RE = re.compile(r"(경계치|높음|낮음|정상|이상지질혈증|대사증후군|신부전|경도감소|고도감소)")

SECTION_TITLE_BLACKLIST = {
    "CBC with diff count & ESR", "WBC differential count", "Admission/Electro Battery(24",
    "종)", "Routine U/A with Microscope", "Gram Stain & Cul & Sensi", "Urine Microscopy",
    "ABGA ,Ca++,electrolyte", "CBC with diff & Reti", "ABGA (Lactate 포함)",
    "Prothrombin Time", "Cardiac Marker", "Electrolyte(3종)", "Calculated LDL Cholesterol",
    "PB morphology", "SUMMARY", "Comment", "normal in No.", "relative eosinophilia",
    "All items of ABGA", "IPF (Immature platelet frac", "IRF (immature reticulocyte",
    "Routine U/A (10종)", "ABO/Rh type & screening", "normocytic normochromic RBCs"
}

QUAL_SECTION_KEYWORDS = ("미생물", "혈액은행")
REPORT_SECTION_KEYWORDS = (
    "영상", "소화기병센터", "내시경", "병리", "심장혈관", "재활", "호흡기", "이비인후", "내분비", "Sarcopenia", "PTA", 
    "PTsec", "PFT", "Spine", "Abdomen", "Chest", "MRI", "CT", "Ultrasound", "초음파", "Audiometry", "composition",
    "PB morphology", "Thromboelastometry"
)
FORCE_QUANTITATIVE_KEYWORDS = ("핵의학",)
QUAL_SKIP_EXACT = {"Gram Stain & Cul & Sensi", "Blood culture", "Antibiotic", "[OCR결과/장비결과] Interface 용 서식지"}

UNIT_ALIASES = {"㎕": "uL", "μL": "uL", "µL": "uL", "μIU": "uIU", "µIU": "uIU", "㎗": "dL"}

SPECIAL_UNIT_PATTERNS = [r"mL/min/1\.73m²", r"mOsm/kg H2O", r"mmHg", r"mm/h", r"sec", r"fL", r"pg", r"%"]
COUNT_UNIT_PATTERNS = [r"×10[⁰¹²³⁴⁵⁶⁷⁸⁹]+/(?:uL|[^\s]+)", r"×10\^?\d+/(?:uL|[^\s]+)", r"cells/HPF", r"/LPF"]
CONCENTRATION_UNIT_PATTERNS = [r"(?:mg|g|ug|ng|pg)/(?:dL|L|mL)", r"(?:IU|U|uIU)/(?:L|mL)", r"mmol/L", r"mEq/L", r"g/L", r"mg/mL"]
RATIO_UNIT_PATTERNS = [r"mmol/mol", r"mL/dL"]
UNIT_PATTERNS = SPECIAL_UNIT_PATTERNS + COUNT_UNIT_PATTERNS + CONCENTRATION_UNIT_PATTERNS + RATIO_UNIT_PATTERNS
UNIT_RE = re.compile(r"^(?:" + "|".join(f"(?:{p})" for p in UNIT_PATTERNS) + r")$", re.I)
UNIT_REF_SPLIT_RE = re.compile(r"^(?P<unit>(?:" + "|".join(f"(?:{p})" for p in UNIT_PATTERNS) + r"))\s+(?P<ref>.+)$", re.I)
FLAG_RE = re.compile(r"^[▲▼]$")

QUAL_WORDS = ["negative", "positive", "trace", "not found", "none", "some", "many", "few", "present", "absent", "no growth"]
NORMAL_WORDS = ["negative", "not found", "none", "absent", "normal", "non-reactive", "undetected", "no growth"]
ABNORMAL_WORDS = ["positive", "trace", "1+", "2+", "3+", "4+", "some", "many", "present", "reactive", "detected"]
PLUS_PATTERN = re.compile(r"^\s*\d\+(?:[^\w]|$)")
PURE_NUM_PATTERN = re.compile(r"^\s*[+-]?\d+(?:\.\d+)?\s*(?:[▲▼])?\s*$")
RANGE_NUM_PATTERN = re.compile(r"^\s*[+-]?\d+(?:\.\d+)?\s*~\s*[+-]?\d+(?:\.\d+)?")
THRESHOLD_PATTERN = re.compile(r"^\s*[+-]?\d+(?:\.\d+)?\s*(?:이상|이하)")
SKIP_CONTAIN = {"[OCR결과/장비결과] Interface 용 서식지", "상기 체성분 분석 검사", "【 Image Interface 】", "종합검증 보고서", "보고자:"}
NUMERIC_REF_PATTERN = re.compile(r"(<|>|<=|>=|~|이상|이하|\d)")


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

@dataclass
class QualRow:
    item: str
    result: str
    unit: str = ""
    ref: str = ""
    status: str = "unknown"
    note: str = ""
    raw_line: str = ""
    section: str = ""
    draw_time: str = ""
    table_title: str = ""

def normalize_line(line: str) -> str:
    line = line.replace("\u3000", "  ").replace("\t", "  ").rstrip()
    return re.sub(r" {2,}", "  ", line)

def split_columns(line: str) -> List[str]:
    return [p.strip() for p in re.split(r" {2,}", line.strip()) if p.strip()]

def normalize_unit_token(s: str) -> str:
    s = s.strip()
    for src, dst in UNIT_ALIASES.items():
        s = s.replace(src, dst)
    superscript_map = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    s = re.sub(r"\^(\d+)", lambda m: "".join(superscript_map.get(d, d) for d in m.group(1)), s)
    s = re.sub(r"/dl\b", "/dL", s, flags=re.I)
    s = re.sub(r"/ml\b", "/mL", s, flags=re.I)
    s = re.sub(r"/ul\b", "/uL", s, flags=re.I)
    s = re.sub(r"\bmg/dl\b", "mg/dL", s, flags=re.I)
    s = re.sub(r"\bg/dl\b", "g/dL", s, flags=re.I)
    s = re.sub(r"\bug/ml\b", "ug/mL", s, flags=re.I)
    s = re.sub(r"\bng/ml\b", "ng/mL", s, flags=re.I)
    s = re.sub(r"\bpg/ml\b", "pg/mL", s, flags=re.I)
    s = re.sub(r"\bug/dl\b", "ug/dL", s, flags=re.I)
    return s

def clean_test_name(name: str) -> str:
    name = BULLET_PREFIX_RE.sub("", name)
    while True:
        new = EMERGENCY_PREFIX_RE.sub("", name)
        new = BULLET_PREFIX_RE.sub("", new)
        if new == name:
            break
        name = new
    return re.sub(r"\s+", " ", name).strip()

def clean_section_name(section: str) -> str:
    return re.sub(r"\[[^\]]+\]", "", section.strip()).strip(" -")

def extract_section_name(line: str) -> str:
    m = SECTION_HEADER_RE.match(line.strip())
    if m:
        return clean_section_name(m.group(2))
    return "Unknown"

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
    if any(k in s for k in SKIP_CONTAIN):
        return True
    return False

def is_qualitative_section(section: str) -> bool:
    return any(k in (section or "") for k in QUAL_SECTION_KEYWORDS)

def is_report_section(section: str, line: str = "") -> bool:
    return any(k in (section or "") for k in REPORT_SECTION_KEYWORDS) or \
           any(k in (line or "") for k in REPORT_SECTION_KEYWORDS)

def is_qual_skip_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if s in QUAL_SKIP_EXACT:
        return True
    if COLUMN_HEADER_RE.match(s):
        return True
    if COMMENT_LINE_RE.match(s):
        return True
    if META_LINE_RE.search(s):
        return True
    return False

def is_section_title_like(line: str) -> bool:
    cleaned = clean_test_name(line)
    return any(cleaned.startswith(k) for k in SECTION_TITLE_BLACKLIST)

def looks_like_continuation_ref(line: str) -> bool:
    s = line.strip()
    if not s or is_skip_line(s):
        return False
    parts = split_columns(s)
    if len(parts) >= 3 and not RANGE_LIKE_NAME_RE.match(parts[0]):
        return False
    if CONTINUATION_REF_START_RE.search(s) or CONTINUATION_REF_KEYWORD_RE.search(s) or s.startswith("Total cholesterol -") or "참고치" in s:
        return True
    if len(parts) == 1 and bool(re.match(r'^[-\*\(\[a-zA-Z가-힣]', s)):
        if is_section_title_like(s):
            return False
        if "microscopy" in s.lower() or s.endswith("종)"):
            return False
        return True
    return False

def append_ref(old_ref: str, extra: str) -> str:
    extra = re.sub(r"\s+", " ", extra).strip()
    if not old_ref:
        return extra
    return old_ref.strip() + "; " + extra

def compose_value(value: str, flag: str = "") -> str:
    v = value.strip()
    f = flag.strip()
    if v and f:
        return f"{v} {f}"
    return v or f

def value_flag(value: str) -> str:
    s_val = str(value)
    if s_val.endswith("▲"):
        return "up"
    if s_val.endswith("▼"):
        return "down"
    return ""

def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u3000", " ")).strip().lower()

def classify_row_type(result: str, ref: str = "", unit: str = "") -> str:
    r, refn, unitn = (result or "").strip().lower(), (ref or "").strip().lower(), (unit or "").strip()
    if any(w in r for w in QUAL_WORDS):
        return "qualitative"
    if PLUS_PATTERN.search(r):
        return "qualitative"
    if "cells/hpf" in r or "/lpf" in r or "cells/hpf" in refn or "/lpf" in refn:
        return "qualitative"
    if PURE_NUM_PATTERN.match(r) and unitn:
        return "quantitative"
    if PURE_NUM_PATTERN.match(r) and NUMERIC_REF_PATTERN.search(refn):
        return "quantitative"
    if RANGE_NUM_PATTERN.search(r) or THRESHOLD_PATTERN.search(r):
        return "qualitative"
    return "unknown"

def _first_num(s: str) -> Optional[float]:
    if not s:
        return None
    s_clean = s.replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s_clean)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None

def _check_keyword_status(result: str, ref: str) -> str:
    res, r = result.lower(), ref.lower()
    
    # 1. 참고치 자체가 'Trace' 등 이상 단어를 포함하고, 결과값도 동일한 이상 단어를 가질 경우 정상(normal)으로 처리
    # 예: Urobilinogen 결과가 Trace이고 참고치도 Trace인 경우
    for w in ABNORMAL_WORDS:
        if w in res and w in r:
            return "normal"

    # Check if result directly says abnormal
    if any(w in res for w in ABNORMAL_WORDS) and not any(w in res for w in ["false positive", "false-positive"]):
        return "abnormal"
        
    # Check if result directly says normal
    if any(w in res for w in NORMAL_WORDS) and not any(w in res for w in ABNORMAL_WORDS):
        return "normal"
        
    # Check ref context (original logic fallback)
    if any(w in r for w in NORMAL_WORDS):
        if any(w in res for w in ABNORMAL_WORDS):
            return "abnormal"
        if any(w in res for w in NORMAL_WORDS):
            return "normal"
            
    return "unknown"

def _check_range_status(result: str, ref: str) -> str:
    rm = re.search(r"(-?\d+(?:\.\d+)?)\s*~\s*(-?\d+(?:\.\d+)?)", result)
    refm = re.search(r"(-?\d+(?:\.\d+)?)\s*~\s*(-?\d+(?:\.\d+)?)", ref)
    if rm and refm:
        r_low, r_high = float(rm.group(1)), float(rm.group(2))
        ref_low, ref_high = float(refm.group(1)), float(refm.group(2))
        if r_high < ref_low:
            return "low"
        if r_low > ref_high:
            return "high"
        return "normal"
    return "unknown"

def _check_threshold_status(result: str, ref: str) -> str:
    m_re = re.search(r"(-?\d+(?:\.\d+)?)\s*이상", result)
    refm = re.search(r"(-?\d+(?:\.\d+)?)\s*~\s*(-?\d+(?:\.\d+)?)", ref)
    if m_re and refm and float(m_re.group(1)) > float(refm.group(2)):
        return "high"

    m_le = re.search(r"(-?\d+(?:\.\d+)?)\s*이하", result)
    if m_le and refm and float(m_le.group(1)) < float(refm.group(1)):
        return "low"

    rv, xv = _first_num(result), _first_num(ref)
    if rv is None or xv is None:
        return "unknown"

    if ref.startswith("<") or "이하" in ref:
        return "high" if rv > xv else "normal"
    if ref.startswith(">") or "이상" in ref:
        return "low" if rv < xv else "normal"

    return "unknown"

def classify_qual_status(result: str, ref: str = "") -> str:
    res_norm, ref_norm = norm_text(result), norm_text(ref)
    if not res_norm:
        return "unknown"
    status = _check_keyword_status(res_norm, ref_norm)
    if status != "unknown": return status
    status = _check_range_status(res_norm, ref_norm)
    if status != "unknown": return status
    status = _check_threshold_status(res_norm, ref_norm)
    if status != "unknown": return status
    return "unknown"

def parse_candidate_row(line: str, section: str = "", draw_time: str = "") -> Optional[LabRow]:
    line = normalize_line(line)
    if RANGE_LIKE_NAME_RE.match(line):
        return None
    
    parts = split_columns(line)
    if len(parts) < 2:
        return None

    name = value = flag = unit = ref = ""
    
    if len(parts) >= 4:
        name, value = parts[0], parts[1]
        idx = 2
        if idx < len(parts) and FLAG_RE.match(parts[idx]):
            flag = parts[idx]
            idx += 1
        if idx < len(parts):
            pnorm = normalize_unit_token(parts[idx])
            if UNIT_RE.match(pnorm):
                unit = pnorm
                idx += 1
        if idx < len(parts):
            ref = " ".join(parts[idx:]).strip()
        if not unit and ref:
            ref_norm = normalize_unit_token(ref)
            if UNIT_RE.match(ref_norm):
                unit, ref = ref_norm, ""
    elif len(parts) == 3:
        name, second, third = parts
        m = re.match(r"^(.*?)(?:\s*([▲▼]))?$", second)
        if m:
            value, flag = m.group(1).strip(), (m.group(2) or "").strip()
        third_norm = normalize_unit_token(third.strip())
        if UNIT_RE.match(third_norm):
            unit = third_norm
        else:
            m_ur = UNIT_REF_SPLIT_RE.match(third_norm)
            if m_ur:
                unit, ref = m_ur.group("unit").strip(), m_ur.group("ref").strip()
            else:
                m_fallback = re.match(r"^([^\d<>\~]+?)\s+([\d<>\~].*|Negative.*|Positive.*)$", third_norm, re.I)
                if m_fallback and not re.search(r'\s', m_fallback.group(1).strip()):
                    unit, ref = m_fallback.group(1).strip(), m_fallback.group(2).strip()
                else:
                    ref = third.strip()
    else:
        name, second = parts
        m = re.match(r"^(.*?)(?:\s*([▲▼]))?$", second)
        if m:
            value, flag = m.group(1).strip(), (m.group(2) or "").strip()

    name = clean_test_name(name)
    if not name or name in SECTION_TITLE_BLACKLIST or name in {"검사명", "Test"} or not value:
        return None

    if not flag:
        m2 = re.match(r"^(.*?)(?:\s*([▲▼]))$", value)
        if m2:
            value, flag = m2.group(1).strip(), m2.group(2)

    return LabRow(
        name=name,
        value=compose_value(value, flag),
        unit=re.sub(r"\s+", " ", unit).strip(),
        ref=re.sub(r"\s+", " ", ref).strip(),
        raw_line=line,
        section=section,
        draw_time=draw_time,
        table_title=format_title(section or "Unknown", draw_time)
    )

def parse_qualitative_row(line: str, section: str = "", draw_time: str = "") -> Optional[QualRow]:
    line = normalize_line(line)
    if not line or is_skip_line(line) or is_qual_skip_line(line) or is_section_title_like(line):
        return None

    parts = split_columns(line)
    if len(parts) >= 3:
        item, result, ref = clean_test_name(parts[0]), parts[1].strip(), parts[2].strip()
        note = " ".join(parts[3:]).strip() if len(parts) > 3 else ""
    elif len(parts) == 2:
        item, result, ref, note = clean_test_name(parts[0]), parts[1].strip(), "", ""
    else:
        return None

    if not item or item in {"검사명", "Test"}:
        return None

    return QualRow(
        item=item,
        result=re.sub(r"\s+", " ", result).strip(),
        unit="", # 기본 정성 파싱에서는 단위를 빈 값으로 시작 (필요 시 확장)
        ref=re.sub(r"\s+", " ", ref).strip(),
        status=classify_qual_status(result, ref),
        note=re.sub(r"\s+", " ", note).strip(),
        raw_line=line,
        section=section,
        draw_time=draw_time,
        table_title=format_title(section or "Unknown", draw_time)
    )

def parse_lab_text(text: str) -> Tuple[List[LabRow], List[QualRow], List[str], List[str]]:
    rows: List[LabRow] = []
    qual_rows: List[QualRow] = []
    unparsed_lines: List[str] = []
    report_lines: List[str] = []
    
    last_row: Optional[LabRow] = None
    last_qual_row: Optional[QualRow] = None
    in_comment_block = False
    current_section, current_draw_time = "Unknown", ""

    for raw in text.splitlines():
        line = normalize_line(raw)
        stripped = line.strip()
        if not stripped:
            continue

        if SECTION_HEADER_RE.match(stripped):
            current_section, current_draw_time = extract_section_name(stripped), ""
            in_comment_block = False
            last_row = last_qual_row = None
            continue

        draw_time = extract_draw_time(stripped)
        if draw_time:
            current_draw_time = draw_time
            continue

        if is_report_section(current_section, stripped) or SECTION_HEADER_RE.match(stripped):
            if not is_skip_line(stripped):
                report_lines.append(stripped)
            continue

        if is_skip_line(stripped):
            if stripped in {"[소견]", "[의뢰의사 Comment]"}:
                in_comment_block = True
            continue

        if in_comment_block:
            continue

        if is_qualitative_section(current_section):
            qrow = parse_qualitative_row(stripped, section=current_section, draw_time=current_draw_time)
            if qrow:
                qual_rows.append(qrow)
                last_qual_row = qrow
                last_row = None
                continue
            
            if last_qual_row and len(split_columns(stripped)) == 1:
                extra = re.sub(r"\s+", " ", stripped).strip()
                if not last_qual_row.ref:
                    last_qual_row.ref = extra
                    last_qual_row.status = classify_qual_status(last_qual_row.result, last_qual_row.ref)
                else:
                    last_qual_row.note = append_ref(last_qual_row.note, extra)
                continue
                
            if not is_section_title_like(stripped) and not is_qual_skip_line(stripped):
                unparsed_lines.append(stripped)
            continue

        if last_row and looks_like_continuation_ref(stripped):
            last_row.ref = append_ref(last_row.ref, stripped)
            continue

        row = parse_candidate_row(stripped, section=current_section, draw_time=current_draw_time)
        if row:
            row_type = classify_row_type(row.value, row.ref, row.unit)
            
            if any(k in current_section for k in FORCE_QUANTITATIVE_KEYWORDS):
                row_type = "quantitative"

            if row_type == "qualitative":
                q_row = QualRow(
                    item=row.name,
                    result=row.value,
                    unit=row.unit,
                    ref=row.ref,
                    status=classify_qual_status(row.value, row.ref),
                    raw_line=row.raw_line,
                    section=row.section,
                    draw_time=row.draw_time,
                    table_title=row.table_title
                )
                qual_rows.append(q_row)
                last_qual_row = q_row
                last_row = None
            else:
                rows.append(row)
                last_row = row
                last_qual_row = None
            continue

        if not is_section_title_like(stripped) and not any(k in stripped for k in SKIP_CONTAIN) and not RANGE_LIKE_NAME_RE.match(stripped):
            unparsed_lines.append(stripped)

    return rows, qual_rows, unparsed_lines, report_lines
