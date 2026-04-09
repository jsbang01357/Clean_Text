# --- 기록 블록 분리용 패턴 모음 ---
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

# --- 섹션 헤더 표준화용 매핑 ---
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
