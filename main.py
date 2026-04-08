import streamlit as st
import datetime
from text_cleaner import render_text_cleaner
from lab_to_table import render_lab_to_excel_tool
from qna import render_qna

# 한국 시간(KST) 타임존 정의 (UTC+9)
KST = datetime.timezone(datetime.timedelta(hours=9))

def get_now():
    """현재 시간을 KST 기준으로 반환합니다."""
    return datetime.datetime.now(KST)

# --- 메인 함수 ---
def main():
    st.set_page_config(page_title="Clean Text", layout="wide")
    
    # --- [사이드바 메뉴] ---
    st.sidebar.title("🧼 Clean Text")
    
    if "menu" not in st.session_state:
        st.session_state.menu = "cleaner"

    btn_cleaner_type = "primary" if st.session_state.menu == "cleaner" else "secondary"
    btn_labexcel_type = "primary" if st.session_state.menu == "labexcel" else "secondary"
    btn_qna_type = "primary" if st.session_state.menu == "qna" else "secondary"

    if st.sidebar.button("🧪 테이블 변환기", type=btn_labexcel_type, use_container_width=True):
        st.session_state.menu = "labexcel"
        st.rerun()

    if st.sidebar.button("🧹 텍스트 클리너", type=btn_cleaner_type, use_container_width=True):
        st.session_state.menu = "cleaner"
        st.rerun()

    if st.sidebar.button("❓ Q&A / 도움말", type=btn_qna_type, use_container_width=True):
        st.session_state.menu = "qna"
        st.rerun()

    st.sidebar.markdown("---")
    # KST 기준 시간 표시
    st.sidebar.caption(f"🕒 현재 시간: {get_now().strftime('%H:%M')}")
    st.sidebar.markdown("---")
    st.sidebar.caption("V 1.0.0 2026.04.07") 
    st.sidebar.caption("@Jisong Bang 2026") 

    # --- [메뉴 1] 텍스트 클리너 ---
    if st.session_state.menu == "cleaner":
        render_text_cleaner()

    # --- [메뉴 2] Lab → Table 기능 ---
    elif st.session_state.menu == "labexcel":
        render_lab_to_excel_tool()

    # --- [메뉴 3] Q&A / 도움말 ---
    elif st.session_state.menu == "qna":
        render_qna()

if __name__ == "__main__":
    main()