# Clean Text

의료데이터(EMR) 텍스트를 정제하고 분석 가능한 테이블(Excel, TSV)로 변환하는 도구입니다.

## 🚀 주요 기능
*   **Lab → Excel 변환기**: 정량/정성 검사 결과를 시계열 데이터프레임으로 변환
*   **텍스트 클리너**: EMR 텍스트의 불필요한 공백 제거 및 섹션 정리
*   **Q&A / 도움말**: 사용 가이드 및 자주 묻는 질문 제공

## 📁 프로젝트 구조
*   `core/`: 핵심 로직 (파싱, 클리닝, 엑셀 생성)
*   `test/`: 단위 테스트 및 검증용 샘플 데이터
*   `main.py`: Streamlit 앱 메인 엔트리
*   `lab_to_table.py`, `text_cleaner.py`: UI 렌더링 모듈

## 🛠️ 설치 및 실행
```bash
# 종속성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run main.py
```

## 🧪 테스트 실행
```bash
python -m pytest test/
```
