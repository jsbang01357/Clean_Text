import streamlit as st
import re
from custom_copy_btn import copy_to_clipboard


# --- 결과 출력 공통 함수 ---
def _render_result(clean_input, cleaned):
    """정리 결과를 화면에 출력합니다."""
    st.markdown("---")
    st.subheader("✨ 정리된 결과")

    orig_len = len(clean_input)
    clean_len = len(cleaned)
    removed = orig_len - clean_len
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("원본 글자수", f"{orig_len}자")
    with col_s2:
        st.metric("정리 후 글자수", f"{clean_len}자")
    with col_s3:
        st.metric("제거된 글자수", f"{removed}자")

    st.text_area("결과 (아래 버튼으로 복사 가능)", value=cleaned, height=250, key="clean_result_area")
    copy_to_clipboard(text=cleaned, before_copy_label="📋 결과 복사하기", after_copy_label="✅ 복사 완료", key="copy_clean_result")


# --- 일반 모드 ---
def _render_general_mode():
    """일반 텍스트 클리너 모드"""
    st.info("입력한 텍스트에서 불필요한 서식을 제거하고 깔끔하게 정리합니다.")

    st.markdown("**정리 옵션**")
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        opt_tab = st.checkbox("탭 문자 제거", value=True)
        opt_multi_space = st.checkbox("연속 공백 → 단일 공백", value=True)
        opt_empty_lines = st.checkbox("연속 빈 줄 → 한 줄로", value=True)
        opt_trim_lines = st.checkbox("각 줄 앞뒤 공백 제거", value=True)
    with col_opt2:
        opt_line_numbers = st.checkbox("줄번호 제거 (예: 1. 또는 1) )", value=False)
        opt_urls = st.checkbox("URL 제거", value=False)
        opt_special_chars = st.checkbox("특수문자 제거 (글자/숫자/공백만 남김)", value=False)
        opt_merge_lines = st.checkbox("모든 줄바꿈 제거 (한 문단으로)", value=False)

    st.markdown("---")
    clean_input = st.text_area("정리할 텍스트를 입력하세요", height=250, placeholder="여기에 내용을 붙여넣으세요...")

    if st.button("깨끗하게 정리하기", type="primary", use_container_width=True):
        if clean_input:
            cleaned = clean_input

            if opt_tab:
                cleaned = cleaned.replace("\t", " ")
            if opt_trim_lines:
                cleaned = "\n".join(line.strip() for line in cleaned.splitlines())
            if opt_multi_space:
                cleaned = "\n".join(
                    " ".join(line.split()) for line in cleaned.splitlines()
                )
            if opt_empty_lines:
                cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
            if opt_line_numbers:
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned, flags=re.MULTILINE)
            if opt_urls:
                cleaned = re.sub(r'https?://\S+', '', cleaned)
            if opt_special_chars:
                cleaned = re.sub(r'[^\w\s가-힣]', '', cleaned)
            if opt_merge_lines:
                cleaned = " ".join(cleaned.splitlines())
                cleaned = " ".join(cleaned.split())

            cleaned = cleaned.strip()
            _render_result(clean_input, cleaned)
        else:
            st.warning("텍스트를 입력해주세요.")


# --- 1. 전각 스페이스 제거 ---

def _clean_emr_fullwidth_spaces(text, preserve_indent=False):
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
def _classify_line(line):
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
    # 대소문자가 달라도 비교적 안전한 길이가 긴 단어들
    lab_keywords_safe = [
        'HbA1c', 'Glucose', 'Osmol', 'C-Peptide', 'Albumin', 'Protein', 'Bilirubin', 
        'Lipase', 'Amylase', 'Troponin', 'D-dimer', 'Fibrinogen', 'Lactate', 'Ketone', '베타케톤'
    ]
    has_kw_safe = any(re.search(r'\b' + re.escape(kw) + r'\b', stripped, re.IGNORECASE) for kw in lab_keywords_safe)
    
    # 대소문자가 매우 중요한 짧은 약어들 (예: Na가 narrative의 "Na"로 오탐되는 것 방지)
    lab_keywords_strict = [
        'BUN', 'Cr', 'GFR', 'Na', 'K', 'Cl', 'Ca', 'Phos', 'WBC', 'Hb', 'Hgb',
        'Plt', 'PLT', 'AST', 'ALT', 'ALP', 'BNP', 'CRP', 'ESR', 'PCT', 'LDH', 'CPK',
        'PT', 'aPTT', 'INR', 'pH', 'pCO2', 'pO2', 'HCO3', 'BE', 'FENa', 'FEUrea'
    ]
    has_kw_strict = any(re.search(r'\b' + re.escape(kw) + r'\b', stripped) for kw in lab_keywords_strict)
    
    has_lab_keyword = has_kw_safe or has_kw_strict
    
    # E' 패턴 (전해질 약어, 매우 강력한 특수 패턴)
    if re.match(r"^\s*E'\s+[\d\-]+", stripped):
        return 'lab'
    
    # VBGA/ABGA 패턴 (매우 강력한 특수 패턴)
    if re.match(r'^\s*(V|A)BGA\s+[\d\.\-\s]+', stripped):
        return 'lab'
    
    # [핵심 안전성 로직]: 숫자가 존재하고, 위 5개 신호 중 "2개 이상"이 겹쳐야만 Lab으로 강력히 추정.
    # 이전 로직(1개 이상)은 단순 서술문에 'H'가 들어가거나 '~'가 들어갔을 때 Lab으로 파괴시키는 문제가 있었음.
    lab_signals = sum([has_flag, has_unit, has_ref_range, has_lab_prefix, has_lab_keyword])
    if has_number and lab_signals >= 2:
        return 'lab'
    
    # --- 오더 줄 판별 ---
    # 오더 줄: 날짜(8자리)로 시작 + 뒤에 여러 열이 있는 경우
    if re.match(r'^\s*\d{4}[-/.]?\d{2}[-/.]?\d{2}', stripped):
        # 날짜 뒤에 공백으로 구분된 여러 필드가 있으면 order
        parts = stripped.split()
        if len(parts) >= 3:
            return 'order'
    
    return 'narrative'


def _normalize_spaces_for_line(line, line_type):
    """줄 타입에 따라 공백을 다르게 정규화합니다.
    
    - narrative: 연속 공백 2개 이상 → 1개
    - lab/order: 연속 공백 3개 이상 → 탭(구분자)
    - empty/header: 그대로 유지
    """
    if line_type == 'empty' or line_type == 'header':
        return line
    
    if line_type == 'narrative':
        # 줄 앞쪽의 들여쓰기는 보존하고, 본문 내 연속 공백만 축소
        leading = len(line) - len(line.lstrip(' '))
        indent = ' ' * min(leading, 1)  # 들여쓰기는 최대 1칸으로
        body = line.strip()
        body = re.sub(r' {2,}', ' ', body)  # 연속 공백 2+ → 1
        if not body:
            return ''
        return indent + body
    
    if line_type in ('lab', 'order'):
        # 줄 앞 공백은 탭 하나로 통일
        stripped = line.strip()
        if not stripped:
            return ''
        # 연속 공백 3개 이상 → 탭
        normalized = re.sub(r' {3,}', '\t', stripped)
        # 이미 있는 탭 + 공백 조합도 정리
        normalized = re.sub(r'\t +', '\t', normalized)
        normalized = re.sub(r' +\t', '\t', normalized)
        # 연속 탭 → 단일 탭
        normalized = re.sub(r'\t{2,}', '\t', normalized)
        return '\t' + normalized
    
    return line


def _clean_emr_normalize_spaces(text):
    """2. 연속 공백 정규화 (줄 타입별 분기 처리)
    
    줄마다 타입을 분류한 뒤:
    - narrative 줄: 연속 공백 2개 이상 → 1개로 축소
    - lab/order 줄: 연속 공백 3개 이상 → 탭(구분자)으로 변환
    - empty/header 줄: 그대로 유지
    """
    lines = text.splitlines()
    result = []
    
    for line in lines:
        line_type = _classify_line(line)
        normalized = _normalize_spaces_for_line(line, line_type)
        result.append(normalized)
    
    return "\n".join(result)



# --- 3. 기록 블록 분리 ---
# 기록 시작을 나타내는 패턴들 (문서 segmentation)
RECORD_STARTERS = [
    '타과회신', '타과의뢰', 
    'On Duty Note', 'Off Duty Note', 'Progress Note',
    '입원초진기록', '입원경과기록',
    '응급경과기록', '응급초진기록',
    '전문의기록', '전공의기록', '수련의기록',
    '퇴원요약', '수술기록', '시술기록',
    '간호기록', '영양상담기록',
]

def _clean_emr_block_separator(text):
    """3. 기록 블록 분리
    
    하나의 텍스트 안에 여러 기록(타과회신, On Duty Note, 입원초진기록 등)이 
    이어붙여져 있을 때, 각 기록의 경계를 시각적으로 분리합니다.
    
    record starter 패턴을 감지하여:
    - 구분선(===)을 삽입하고
    - 헤더 메타데이터(작성자, 확정/임시, 날짜)를 파싱하여 정리합니다.
    """
    # record starter를 regex OR 패턴으로 합침
    starters_pattern = '|'.join(re.escape(s) for s in RECORD_STARTERS)
    
    # 패턴: "기록유형  /작성자(상태)  [기록일:날짜]  날짜 시간 수정>날짜 시간"
    # 또는: "기록유형  /작성자(상태)  [기록일:날짜]  날짜 시간"
    record_header_pattern = re.compile(
        r'^(?P<type>' + starters_pattern + r')\s*/\s*'
        r'(?P<author>[^(]+)\((?P<status>[^)]+)\)\s*'
        r'\[기록일:\s*(?P<date>\S+)\]\s*'
        r'(?P<created>\S+\s+\S+)'
        r'(?:\s*수정>\s*(?P<modified>\S+\s+\S+))?'
    )
    
    # 처방 패턴: "이름 처방" 또는 "이름 처방 [기록일:...]"
    order_pattern = re.compile(
        r'^(?P<author>\S+)\s+처방\s*(?:\[기록일:\s*(?P<date>\S+)\])?\s*(?P<rest>.*)'
    )
    
    lines = text.splitlines()
    result = []
    is_first_block = True
    
    for line in lines:
        # 기록 헤더 패턴 매칭
        match = record_header_pattern.match(line.strip())
        if match:
            record_type = match.group('type')
            author = match.group('author').strip()
            status = match.group('status').strip()
            date = match.group('date').strip()
            created = match.group('created').strip()
            modified = match.group('modified')
            
            # 구분선 추가 (첫 블록 제외)
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
        
        # 처방 패턴 매칭
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


# --- 4. 섹션 헤더 표준화 ---
# canonical section name 매핑 딕셔너리
SECTION_CANONICAL_MAP = {
    # 기본 정보 계열
    '기본정보': '기본정보',
    '진단정보': '진단정보',
    '의뢰내용': '의뢰내용',
    '회신내용': '회신내용',
    
    # 병력 계열
    '주호소': '주호소',
    'CC': '주호소',
    '현병력': '현병력',
    'HPI': '현병력',
    '과거력': '과거력',
    'PMH': '과거력',
    '가족력': '가족력',
    'FHx': '가족력',
    '사회력': '사회력',
    'SHx': '사회력',
    '복용약물': '복용약물',
    
    # SOAP 계열
    'Problem': 'Problem',
    'S': 'S',
    'Subjective': 'S',
    'O': 'O',
    'Objective': 'O',
    'A': 'A',
    'Assessment': 'A',
    'P': 'Plan',
    'Plan': 'Plan',
    'P(Care plan)': 'Plan',
    'Care plan': 'Plan',
    '계획': 'Plan',
    
    # 신체검진
    '신체검진': '신체검진',
    'PE': '신체검진',
    'Physical Exam': '신체검진',
    'V/S': 'V/S',
    'Vital Signs': 'V/S',
    
    # 기타
    '검사소견': '검사소견',
    '영상소견': '영상소견',
    '경과': '경과',
}

def _clean_emr_section_headers(text):
    """4. 섹션 헤더 표준화
    
    EMR 내 섹션 헤더(Problem>, S>, O>, A>, P(Care plan)>, 기본정보> 등)를 
    canonical name으로 통일하고 형식을 정리합니다.
    
    매핑 예시:
    - P(Care plan)> → [Plan]
    - 계획> → [Plan]
    - 주호소> → [주호소]
    - S> → [S]
    """
    lines = text.splitlines()
    result = []
    
    # 섹션 헤더 후보 패턴:
    # "텍스트>" 또는 "텍스트(부가정보)>" 형태 (줄 전체가 헤더인 경우)
    section_pattern = re.compile(r'^\s*(.+?)\s*>\s*$')
    
    for line in lines:
        match = section_pattern.match(line)
        if match:
            raw_section = match.group(1).strip()
            
            # canonical name 찾기
            canonical = SECTION_CANONICAL_MAP.get(raw_section)
            
            if canonical:
                result.append(f"\n[{canonical}]")
                continue
            
            # 정확한 매치가 없으면 부분 매칭 시도
            # 예: "P(Care plan)" → key "P(Care plan)" → "Plan"
            found = False
            for key, value in SECTION_CANONICAL_MAP.items():
                if key in raw_section or raw_section in key:
                    result.append(f"\n[{value}]")
                    found = True
                    break
            
            if not found:
                # 매핑에 없는 섹션이라도 형식은 통일
                result.append(f"\n[{raw_section}]")
                continue
        else:
            result.append(line)
    
    return "\n".join(result)



def _clean_emr_empty_lines(text):
    """연속 빈 줄을 한 줄로 줄입니다."""
    return re.sub(r'\n{3,}', '\n\n', text)


# --- 5. Problem List Bullet화 ---
def _clean_emr_problem_list(text):
    """5. Problem List Bullet화
    
    #A., #B., #C. 같은 문자 태그 → Active Issues (현재 주요 문제)
    #1., #2., #3. 같은 숫자 태그 → PMH / Comorbidity (과거력/동반질환)
    
    변환 예:
        #A. DKA c newly-diagnosed DM
        #B. AKI
        #1. NSCLC
        #2. HTN
    →
        [Active Issues]
         - A. DKA c newly-diagnosed DM
         - B. AKI
        [Past History / Comorbidity]
         - 1. NSCLC
         - 2. HTN
    """
    lines = text.splitlines()
    result = []
    
    alpha_pattern = re.compile(r'^\s*#([A-Z])\.\s+(.+)')    # #A. ...
    num_pattern = re.compile(r'^\s*#(\d+)\.\s+(.+)')         # #1. ...
    sub_item_pattern = re.compile(r'^\s{2,}(.+)')             # 하위 항목 (들여쓰기)
    
    active_issues = []       # #A, #B, #C ...
    pmh_items = []           # #1, #2, #3 ...
    current_list = None      # 현재 수집 중인 리스트
    current_item_subs = []   # 현재 아이템의 하위 줄들
    
    def flush_lists():
        """수집된 리스트를 result에 출력"""
        nonlocal active_issues, pmh_items
        
        if active_issues:
            result.append("\t[Active Issues]")
            for item in active_issues:
                result.append(item)
            active_issues = []
        
        if pmh_items:
            result.append("\t[Past History / Comorbidity]")
            for item in pmh_items:
                result.append(item)
            pmh_items = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        alpha_match = alpha_pattern.match(line)
        num_match = num_pattern.match(line)
        
        if alpha_match:
            tag = alpha_match.group(1)
            content = alpha_match.group(2).strip()
            bullet_line = f"\t - {tag}. {content}"
            
            # 다음 줄이 하위 항목(들여쓰기)이면 같이 수집
            j = i + 1
            while j < len(lines):
                sub_match = sub_item_pattern.match(lines[j])
                # 다음 # 항목이 아니고 들여쓰기/탭으로 시작하는 줄이면 하위 항목
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
            # # 항목이 아닌 줄 → 수집 중인 리스트가 있으면 flush
            if active_issues or pmh_items:
                flush_lists()
                current_list = None
            result.append(line)
        
        i += 1
    
    # 마지막 남은 리스트 flush
    flush_lists()
    
    return "\n".join(result)


# --- 6. Lab 결과 줄 정렬 ---
# 플래그 문자를 읽기 쉬운 화살표로 변환
FLAG_MAP = {
    '▲': '↑', 'H': '↑', '△': '↑',
    '▼': '↓', 'L': '↓', '▽': '↓',
}

def _parse_lab_line(line):
    """Lab 줄을 5개 필드로 파싱합니다.
    
    Returns:
        dict with keys: test_name, value, flag, unit, ref_range
        또는 None (파싱 실패)
    """
    stripped = line.strip()
    if not stripped:
        return None
    
    # (응급) 또는 (혈액) 같은 prefix 제거 후 검사명에 포함
    prefix = ''
    prefix_match = re.match(r'^(\([^)]+\))\s*', stripped)
    if prefix_match:
        prefix = prefix_match.group(1)
        stripped = stripped[prefix_match.end():]
    
    # 패턴: 검사명 + 구분자(공백/탭) + 값 + [플래그] + [단위] + [참고범위]
    # 탭으로 이미 구분된 경우
    if '\t' in stripped:
        parts = [p.strip() for p in stripped.split('\t') if p.strip()]
    else:
        # 공백 기반 분리 (연속 공백 2+ 를 구분자로)
        parts = [p.strip() for p in re.split(r'\s{2,}', stripped) if p.strip()]
    
    if len(parts) < 2:
        return None
    
    test_name = prefix + parts[0]
    
    # 나머지 parts에서 value, flag, unit, ref_range 추출
    value = ''
    flag = ''
    unit = ''
    ref_range = ''
    
    remaining = parts[1:]
    
    for part in remaining:
        # 참고범위: ~ 포함
        if '~' in part or '–' in part or '−' in part:
            ref_range = part
        # 플래그: ▲, ▼, H, L (단독)
        elif part in ('▲', '▼', '△', '▽', 'H', 'L', '★'):
            flag = FLAG_MAP.get(part, part)
        # 단위: 알파벳/기호 조합 (숫자 없음)
        elif re.match(r'^[a-zA-Zμ%/×]+(?:[/\s][a-zA-Zμ]+)*$', part) and not re.search(r'\d', part):
            unit = part
        # 숫자값
        elif re.search(r'\d', part) and not value:
            value = part
        elif not value:
            value = part
        else:
            # 나머지는 참고범위에 추가
            if ref_range:
                ref_range += ' ' + part
            else:
                ref_range = part
    
    if not value:
        return None
    
    return {
        'test_name': test_name,
        'value': value,
        'flag': flag,
        'unit': unit,
        'ref_range': ref_range,
    }


def _clean_emr_lab_format(text, mode='compact'):
    """6. Lab 결과 줄 정렬
    
    Lab 줄(줄 분류기가 'lab'으로 판정한 줄)을 파싱하여 
    구조화된 형태로 변환합니다.
    
    Args:
        text: 원본 텍스트
        mode: 출력 형식
            'compact' - "HbA1c 10.8% ↑" (간결한 텍스트)
            'table'   - "| Test | Value | Unit | Flag | Ref |" (테이블)
    """
    lines = text.splitlines()
    result = []
    lab_buffer = []  # 연속 lab 줄을 모아두는 버퍼
    
    def flush_lab_buffer():
        """수집된 lab 줄들을 포맷팅하여 result에 추가"""
        nonlocal lab_buffer
        if not lab_buffer:
            return
        
        if mode == 'table' and len(lab_buffer) >= 1:
            result.append("\t| Test | Value | Unit | Flag | Ref |")
            result.append("\t|---|---:|---|---|---|")
            for parsed in lab_buffer:
                flag_str = parsed['flag'] if parsed['flag'] else ''
                unit_str = parsed['unit'] if parsed['unit'] else ''
                ref_str = parsed['ref_range'] if parsed['ref_range'] else ''
                result.append(f"\t| {parsed['test_name']} | {parsed['value']} | {unit_str} | {flag_str} | {ref_str} |")
        else:  # compact mode
            for parsed in lab_buffer:
                parts = [f"\t{parsed['test_name']}: {parsed['value']}"]
                if parsed['unit']:
                    parts[0] += f" {parsed['unit']}"
                if parsed['flag']:
                    parts[0] += f" {parsed['flag']}"
                if parsed['ref_range']:
                    parts[0] += f" (ref {parsed['ref_range']})"
                result.append(parts[0])
        
        lab_buffer = []
    
    for line in lines:
        line_type = _classify_line(line)
        
        if line_type == 'lab':
            parsed = _parse_lab_line(line)
            if parsed:
                lab_buffer.append(parsed)
            else:
                # 파싱 실패 시 원본 유지
                flush_lab_buffer()
                result.append(line)
        else:
            # lab이 아닌 줄을 만나면 버퍼 flush
            flush_lab_buffer()
            result.append(line)
    
    # 마지막 남은 lab 버퍼
    flush_lab_buffer()
    
    return "\n".join(result)


def _clean_emr_special_markers(text):
    """EMR 특수 마커(★, ▲, △ 등)를 제거합니다."""
    return re.sub(r'[★▲△▼▽●○◆◇■□]', '', text)


def _render_emr_mode():
    """KUMC EMR 모드"""
    # 4. 짧은 설명 문구 추가
    st.info(
        "💡 **안내**\n"
        "- 이 도구는 붙여넣은 EMR 텍스트의 가독성을 높이는 용도입니다.\n"
        "- 완전한 parser가 아니며, 원본의 입력 포맷에 따라 결과가 달라질 수 있습니다.\n"
        "- 의료적 의미나 내용의 정확성을 검증하는 도구는 아니므로, 중요 정보의 누락이 없는지 원문과 대조를 권장합니다."
    )

    # 1 & 2. 빠른 정리 / 고급 정리 및 프리셋 도입
    preset = st.radio(
        "정리 수준 선택 (Preset)",
        ["Safe (안전한 정리 - 기본값)", "Standard (표준 정리)", "Aggressive (적극적 구조화)"],
        horizontal=True,
        help="단계를 높일수록 구조화(강제 줄바꿈 및 포맷팅)가 적극적으로 적용됩니다."
    )

    # Preset에 따른 기본 Option 결정 (보수적 접근)
    emr_fw = True
    emr_norm = True
    emr_empty = True
    emr_block = True
    emr_sec = False
    emr_prob = False
    emr_lab = False
    emr_markers = False
    default_lab_mode = 'compact'

    if "Standard" in preset:
        emr_sec = True
    elif "Aggressive" in preset:
        emr_sec = True
        emr_prob = True
        emr_lab = True

    # 고급 옵션 (Advanced)은 Expander 안에 숨김
    with st.expander("🛠️ 고급 정리 옵션 (직접 설정)"):
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            st.caption("전처리")
            emr_fullwidth = st.checkbox("전각 스페이스(　) 제거", value=emr_fw)
            emr_preserve_indent = st.checkbox("┗ 들여쓰기 시각적 유지 (4칸 변환)", value=False)
            emr_normalize = st.checkbox("연속 공백 정규화 (보수적)", value=emr_norm)
            emr_empty_lines = st.checkbox("연속 빈 줄 한 줄로 축소", value=emr_empty)
        with col_opt2:
            st.caption("구조 정리")
            emr_block_check = st.checkbox("명백한 기록 블록 분리", value=emr_block)
            emr_section_check = st.checkbox("섹션 헤더 표준화", value=emr_sec)
            emr_problem_check = st.checkbox("Problem List 재구성 (위험)", value=emr_prob)
            emr_lab_check = st.checkbox("Lab 결과 포맷팅 (위험)", value=emr_lab)
            emr_markers_check = st.checkbox("특수 마커 제거 (★, ▲ 등)", value=emr_markers)

        lab_mode = default_lab_mode
        if emr_lab_check:
            lab_mode_sel = st.radio(
                "Lab 출력 형식",
                ['compact', 'table'],
                format_func=lambda x: '📝 Compact (텍스트 한 줄)' if x == 'compact' else '📊 Table (마크다운 표)',
                horizontal=True
            )
            lab_mode = lab_mode_sel

    st.markdown("---")

    # 3. 원문과 정리 결과 나란히 보기 (Side-by-side)
    col_in, col_out = st.columns(2)

    with col_in:
        st.write("##### 📥 원본 EMR 텍스트")
        emr_input = st.text_area(
            "원문 입력",
            height=450,
            placeholder="On Duty Note, Progress Note 등을 여기에 붙여넣으세요...",
            label_visibility="collapsed",
            key="emr_input"
        )
        # 5. 제품다운 버튼 이름 변경
        run_btn = st.button("✨ EMR 가독성 개선 실행", type="primary", use_container_width=True)

    with col_out:
        st.write("##### 📤 정리된 결과")
        if run_btn and emr_input:
            cleaned = emr_input
            
            # 파이프라인 적용
            if emr_fullwidth:
                cleaned = _clean_emr_fullwidth_spaces(cleaned, preserve_indent=emr_preserve_indent)
            if emr_normalize:
                cleaned = _clean_emr_normalize_spaces(cleaned)
            if emr_block_check:
                cleaned = _clean_emr_block_separator(cleaned)
            if emr_section_check:
                cleaned = _clean_emr_section_headers(cleaned)
            if emr_problem_check:
                cleaned = _clean_emr_problem_list(cleaned)
            if emr_lab_check:
                cleaned = _clean_emr_lab_format(cleaned, mode=lab_mode)
            if emr_empty_lines:
                cleaned = _clean_emr_empty_lines(cleaned)
            if emr_markers_check:
                cleaned = _clean_emr_special_markers(cleaned)
            
            cleaned = cleaned.strip()
            
            st.text_area("결과 출력", value=cleaned, height=450, label_visibility="collapsed", key="cleaned_result")
            copy_to_clipboard(text=cleaned, before_copy_label="📋 결과 복사하기", after_copy_label="✅ 복사 완료")
            
            orig_len = len(emr_input)
            clean_len = len(cleaned)
            removed = orig_len - clean_len
            st.caption(f"통계: 원본 {orig_len}자 ➔ 정리 후 {clean_len}자 (총 {removed}자 정리됨)")
        else:
            st.text_area("결과 대기", value="", height=450, disabled=True, label_visibility="collapsed", placeholder="왼쪽에서 텍스트를 입력하고 '개선 실행' 버튼을 누르면 결과가 나타납니다.")



# --- 메인 렌더 함수 ---
def render_text_cleaner():
    """텍스트 클리너 페이지를 렌더링합니다."""
    st.title("🧹 텍스트 클리너")

    mode = st.radio(
        "모드 선택",
        ["🏥 KUMC EMR 모드", "📝 일반 모드"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    if mode == "🏥 KUMC EMR 모드":
        _render_emr_mode()
    elif mode == "📝 일반 모드":
        _render_general_mode()
