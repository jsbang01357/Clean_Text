# Clean Text 🧼

`Clean Text`는 의료진과 의학도를 위한 EMR(Electronic Medical Record) 데이터 정제 및 Lab 결과 구조화 도구입니다. 복잡하고 비구조화된 의무기록 텍스트를 깔끔하게 정리하여 가독성을 높이고, 흩어진 검사 결과를 엑셀 형식의 표로 빠르게 변환할 수 있도록 돕습니다.

## ✨ 주요 기능

### 1. 🧹 텍스트 클리너 (Text Cleaner)
EMR 특유의 서식과 불필요한 요소를 제거하여 가독성을 극대화합니다.
- **전각 스페이스 제거**: EMR에서 흔히 발생하는 `　`(U+3000) 공백을 정규 공백으로 변환.
- **섹션 헤더 표준화**: `Problem>`, `S>`, `O>`, `A>`, `P>` 등 다양한 형태의 헤더를 `[S]`, `[O]` 등으로 통일.
- **기록 블록 자동 분리**: `Progress Note`, `On Duty Note` 등 기록의 시작점을 감지하여 시각적 구분선 삽입.
- **Problem List 불렛화**: `#A.`, `#1.` 등의 기호를 감지하여 체계적인 리스트 형식으로 재구성.
- **정리 단계 설정 (Preset)**: `Safe`, `Standard`, `Aggressive` 3단계 프리셋 제공.

### 2. 🧪 테이블 변환기 (Lab to Table)
텍스트 형태의 검사 결과를 파싱하여 구조화된 시트로 변환합니다.
- **데이터 자동 추출**: 검사명, 결과값, 단위, 참고치를 정밀하게 파싱.
- **지능형 클리닝**: `(응급)`, `‥` 등 불필요한 접두어 제거 및 `▲/▼` 기호를 결과값에 병합.
- **엑셀/TSV 내보내기**: 파싱된 데이터를 엑셀(다중 시트 지원) 또는 TSV 파일로 즉시 다운로드.
- **데이터 분석 지원**: `Grouped_Tables` 시트를 통해 채혈 시간 및 검사 종류별로 정리된 표 제공.

## 🛠 기술 스택
- **언어**: Python 3.9+
- **프레임워크**: Streamlit
- **데이터 처리**: Pandas, Regular Expressions (re)
- **엑셀 엔진**: Openpyxl
- **배포/실행**: Local Streamlit Server

## 🚀 시작하기

### 설치
먼저 필요한 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt
```

### 실행
Streamlit 서버를 구동하여 웹 브라우저에서 사용합니다.
```bash
streamlit run main.py
```

## 📂 프로젝트 구조
- `main.py`: 애플리케이션 엔트리 포인트 및 사이드바 메뉴 구성.
- `text_cleaner.py`: 텍스트 정제 파이프라인 및 EMR 특화 클리닝 로직.
- `lab_to_table.py`: Lab 결과 파싱 및 엑셀/TSV 변환 로직.
- `custom_copy_btn/`: 클립보드 복사를 위한 커스텀 Streamlit 컴포넌트.
- `.streamlit/`: Streamlit 테마 및 서버 설정.

---

## 👨‍💻 개발 및 관리
- **Developer**: Jisong Bang (@Jisong Bang)
- **Version**: 1.0.0 (2026.04.07)
- **License**: 개인 연구 및 실무 보조용 프로젝트
