import re
from config.constants import RECORD_STARTERS, SECTION_CANONICAL_MAP

# --- 1. 전각 스페이스 제거 ---
def clean_emr_fullwidth_spaces(text, preserve_indent=False):
    """1. 전각 스페이스(U+3000, 　) 제거
    
    파이프라인 제일 앞에 위치해야 합니다.
    후속 기능(공백 정규화, 섹션 파싱 등)이 전부 여기에 의존합니다.
    
    Args:
        text: 원본 텍스트
        preserve_indent: True면 전각 공백을 4칸 공백으로 변환하여 
                         시각적 들여쓰기를 일부 유지. False면 1칸으로 치환.
    """
    if preserve_indent:
        return text.replace('\u3000', '    ')
    return text.replace('\u3000', ' ')

# --- 줄 분류기 (Line Classifier) ---
def classify_line(line):
    """줄 유형을 분류합니다.
    
    Returns:
        'lab'       - 검사값 줄 (숫자 + 단위 + 화살표 등)
        'order'     - 처방/오더 줄 (날짜로 시작 + 여러 열)
        'narrative' - 일반 서술문 (현병력, S/O/A/P 텍스트 등)
        'empty'     - 빈 줄
        'header'    - 섹션 헤더 줄
    """
    stripped = line.strip()
    
    if not stripped:
        return 'empty'
    
    # 섹션 헤더: Problem>, S>, O>, A>, P(Care plan)> 등
    if re.match(r'^(Problem|S|O|A|P(?:\(.*?\))?|기본정보|진단정보|의뢰내용|회신내용|주호소|현병력|과거력|계획)\s*>?\s*$', stripped):
        return 'header'
    
    # --- Lab 줄 판별 기준 (보수적 접근: False Positive 최소화) ---
    has_number = bool(re.search(r'\d+\.?\d*', stripped))
    
    # 1. 플래그: H, L은 단독 알파벳일 때만, 나머지는 명확한 특수기호
    has_flag = bool(re.search(r'[▲▼↑↓★]|(?<!\w)[HL](?!\w)', stripped))
    
    # 2. 단위: 의료 특화된 복합 단위 명시적 허용
    has_unit = bool(re.search(r'(?:mg/dL|mmol/L|mEq/L|g/dL|U/L|μmol/L|pg/mL|ng/mL|cells/μL|mm/hr|IU/L|ng/L|mcg/L)\b|%', stripped, re.IGNORECASE))
    
    # 3. 참고범위: 형태가 "숫자~숫자" 인 경우만 엄격하게 매칭하여, 일반 문장 내의 '~' 오탐 방지
    has_ref_range = bool(re.search(r'\b\d+\.?\d*\s*[~–\-]\s*\d+\.?\d*\b', stripped))
    
    # 4. 검사 그룹 prefix: EMR 특유의 괄호 묶음
    has_lab_prefix = bool(re.match(r'^\s*\((혈액|응급|일반|화학|뇨|면역|미생물|분자|진단|수탁)\)', stripped))
    
    # 5. 주요 검사명 키워드
    lab_keywords_safe = [
        'HbA1c', 'Glucose', 'Osmol', 'C-Peptide', 'Albumin', 'Protein', 'Bilirubin', 
        'Lipase', 'Amylase', 'Troponin', 'D-dimer', 'Fibrinogen', 'Lactate', 'Ketone', '베타케톤'
    ]
    has_kw_safe = any(re.search(r'\b' + re.escape(kw) + r'\b', stripped, re.IGNORECASE) for kw in lab_keywords_safe)
    
    lab_keywords_strict = [
        'BUN', 'Cr', 'GFR', 'Na', 'K', 'Cl', 'Ca', 'Phos', 'WBC', 'Hb', 'Hgb',
        'Plt', 'PLT', 'AST', 'ALT', 'ALP', 'BNP', 'CRP', 'ESR', 'PCT', 'LDH', 'CPK',
        'PT', 'aPTT', 'INR', 'pH', 'pCO2', 'pO2', 'HCO3', 'BE', 'FENa', 'FEUrea'
    ]
    has_kw_strict = any(re.search(r'\b' + re.escape(kw) + r'\b', stripped) for kw in lab_keywords_strict)
    
    has_lab_keyword = has_kw_safe or has_kw_strict
    
    if re.match(r"^\s*E'\s+[\d\-]+", stripped):
        return 'lab'
    if re.match(r'^\s*(V|A)BGA\s+[\d\.\-\s]+', stripped):
        return 'lab'
    
    lab_signals = 0
    if has_flag: lab_signals += 1
    if has_unit: lab_signals += 1
    if has_ref_range: lab_signals += 2
    if has_lab_prefix: lab_signals += 1
    if has_lab_keyword: lab_signals += 2
    
    if has_number and lab_signals >= 2:
        return 'lab'
    
    if re.match(r'^\s*\d{4}[-/.]?\d{2}[-/.]?\d{2}', stripped):
        parts = stripped.split()
        if len(parts) >= 3:
            return 'order'
    
    return 'narrative'

def normalize_spaces_for_line(line, line_type):
    if line_type == 'empty' or line_type == 'header':
        return line
    if line_type == 'narrative':
        leading = len(line) - len(line.lstrip(' '))
        indent = ' ' * min(leading, 1)  # 들여쓰기는 최대 1칸으로
        body = line.strip()
        body = re.sub(r' {2,}', ' ', body)  # 연속 공백 2+ → 1
        if not body:
            return ''
        return indent + body
    if line_type in ('lab', 'order'):
        stripped = line.strip()
        if not stripped:
            return ''
        normalized = re.sub(r' {3,}', '\t', stripped)
        normalized = re.sub(r'\t +', '\t', normalized)
        normalized = re.sub(r' +\t', '\t', normalized)
        normalized = re.sub(r'\t{2,}', '\t', normalized)
        return '\t' + normalized
    return line

def clean_emr_normalize_spaces(text):
    """2. 연속 공백 정규화"""
    lines = text.splitlines()
    result = []
    for line in lines:
        line_type = classify_line(line)
        normalized = normalize_spaces_for_line(line, line_type)
        result.append(normalized)
    return "\n".join(result)

def clean_emr_block_separator(text):
    """3. 기록 블록 분리"""
    starters_pattern = '|'.join(re.escape(s) for s in RECORD_STARTERS)
    
    record_header_pattern = re.compile(
        r'^(?P<type>' + starters_pattern + r')\s*/\s*'
        r'(?P<author>[^(]+)\((?P<status>[^)]+)\)\s*'
        r'\[기록일:\s*(?P<date>\S+)\]\s*'
        r'(?P<created>\S+\s+\S+)'
        r'(?:\s*수정>\s*(?P<modified>\S+\s+\S+))?'
    )
    
    order_pattern = re.compile(
        r'^(?P<author>\S+)\s+처방\s*(?:\[기록일:\s*(?P<date>\S+)\])?\s*(?P<rest>.*)'
    )
    
    lines = text.splitlines()
    result = []
    is_first_block = True
    
    for line in lines:
        match = record_header_pattern.match(line.strip())
        if match:
            record_type = match.group('type')
            author = match.group('author').strip()
            status = match.group('status').strip()
            date = match.group('date').strip()
            created = match.group('created').strip()
            modified = match.group('modified')
            
            if not is_first_block:
                result.append('')
            
            header = f"{'=' * 50}"
            result.append(header)
            
            meta = f"{record_type} | {author} | {status} | {date} {created}"
            if modified:
                meta += f" | 수정: {modified}"
            result.append(meta)
            result.append(header)
            
            is_first_block = False
            continue
        
        order_match = order_pattern.match(line.strip())
        if order_match and '처방' in line:
            author = order_match.group('author')
            date = order_match.group('date') or ''
            
            if not is_first_block:
                result.append('')
            
            header = f"{'=' * 50}"
            result.append(header)
            meta = f"처방 | {author}"
            if date:
                meta += f" | {date}"
            result.append(meta)
            result.append(header)
            
            is_first_block = False
            continue
        
        result.append(line)
    
    return "\n".join(result)

def clean_emr_section_headers(text):
    """4. 섹션 헤더 표준화"""
    lines = text.splitlines()
    result = []
    
    section_pattern = re.compile(r'^\s*(.+?)\s*>\s*$')
    for line in lines:
        match = section_pattern.match(line)
        if match:
            raw_section = match.group(1).strip()
            canonical = SECTION_CANONICAL_MAP.get(raw_section)
            
            if canonical:
                result.append(f"\n[{canonical}]")
                continue
            
            found = False
            for key, value in SECTION_CANONICAL_MAP.items():
                if key in raw_section or raw_section in key:
                    result.append(f"\n[{value}]")
                    found = True
                    break
            
            if not found:
                result.append(f"\n[{raw_section}]")
                continue
        else:
            result.append(line)
    
    return "\n".join(result)

def clean_emr_empty_lines(text):
    """연속 빈 줄을 한 줄로 줄입니다."""
    return re.sub(r'\n{3,}', '\n\n', text)

def clean_emr_problem_list(text):
    """5. Problem List Bullet화"""
    lines = text.splitlines()
    result = []
    
    alpha_pattern = re.compile(r'^\s*#([A-Z])\.\s+(.+)')
    num_pattern = re.compile(r'^\s*#(\d+)\.\s+(.+)')
    sub_item_pattern = re.compile(r'^\s{2,}(.+)')
    
    active_issues = []
    pmh_items = []
    current_list = None
    
    def flush_lists():
        if active_issues:
            result.append("\t[Active Issues]")
            for item in active_issues:
                result.append(item)
            active_issues.clear()
        
        if pmh_items:
            result.append("\t[Past History / Comorbidity]")
            for item in pmh_items:
                result.append(item)
            pmh_items.clear()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        alpha_match = alpha_pattern.match(line)
        num_match = num_pattern.match(line)
        
        if alpha_match:
            tag = alpha_match.group(1)
            content = alpha_match.group(2).strip()
            bullet_line = f"\t - {tag}. {content}"
            
            j = i + 1
            while j < len(lines):
                sub_match = sub_item_pattern.match(lines[j])
                if sub_match and not alpha_pattern.match(lines[j]) and not num_pattern.match(lines[j]):
                    bullet_line += "\n\t\t" + lines[j].strip()
                    j += 1
                else:
                    break
            active_issues.append(bullet_line)
            current_list = 'alpha'
            i = j
            continue
            
        elif num_match:
            tag = num_match.group(1)
            content = num_match.group(2).strip()
            bullet_line = f"\t - {tag}. {content}"
            
            j = i + 1
            while j < len(lines):
                sub_match = sub_item_pattern.match(lines[j])
                if sub_match and not alpha_pattern.match(lines[j]) and not num_pattern.match(lines[j]):
                    bullet_line += "\n\t\t" + lines[j].strip()
                    j += 1
                else:
                    break
            pmh_items.append(bullet_line)
            current_list = 'num'
            i = j
            continue
        else:
            if active_issues or pmh_items:
                flush_lists()
                current_list = None
            result.append(line)
        i += 1
    
    flush_lists()
    return "\n".join(result)

def clean_emr_special_markers(text):
    """EMR 특수 마커(★, ▲, △ 등)를 제거합니다."""
    return re.sub(r'[★▲△▼▽●○◆◇■□]', '', text)
