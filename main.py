import streamlit as st
import datetime
from core.ui_theme import inject_custom_css
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
    st.set_page_config(
        page_title="Clean Text | EMR 구조화 솔루션", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 🎨 테마 주입
    inject_custom_css()
    
    # --- [사이드바 메뉴] ---
    with st.sidebar:
        # 🏥 브랜딩 및 로고 대체
        st.markdown(
            """
            <div style='text-align: center; padding: 1.5rem 0;'>
                <h2 style='color: #f1f5f9; margin: 0; font-size: 1.8rem;'>🧼 Clean Text</h2>
                <p style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>EMR 구조화 솔루션</p>
                <div style='height: 2px; width: 40px; background: linear-gradient(90deg, #38bdf8, #818cf8); margin: 1rem auto;'></div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if "menu" not in st.session_state:
            st.session_state.menu = "labexcel"

        # 내비게이션 섹션
        st.markdown("<p style='font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.8rem;'>Navigation</p>", unsafe_allow_html=True)
        
        btn_labexcel_type = "primary" if st.session_state.menu == "labexcel" else "secondary"
        btn_cleaner_type = "primary" if st.session_state.menu == "cleaner" else "secondary"
        btn_qna_type = "primary" if st.session_state.menu == "qna" else "secondary"

        if st.button("🧪 테이블 변환기", type=btn_labexcel_type, width="stretch"):
            st.session_state.menu = "labexcel"
            st.rerun()

        if st.button("🧹 텍스트 클리너", type=btn_cleaner_type, width="stretch"):
            st.session_state.menu = "cleaner"
            st.rerun()

        if st.button("❓ Q&A / 도움말", type=btn_qna_type, width="stretch"):
            st.session_state.menu = "qna"
            st.rerun()

        st.markdown("---")
        # KST 기준 시간 표시
        
        #st.caption(f"🕒 현재 시간: {get_now().strftime('%H:%M')}")
        
        # 하단 푸터 (정보 섹션 + 크레딧 고정)
        st.markdown(
            """
            <div class='sidebar-footer'>
                <div class='status-box'>
                    <p style='font-size: 0.75rem; color: #f1f5f9; font-weight: 600; margin-bottom: 3px;'>Clean Text</p>
                    <p style='font-size: 0.7rem; color: #94a3b8; margin-bottom: 2px;'>버전: 1.2.0 (260409)</p>
                    <p style='font-size: 0.7rem; color: #94a3b8;'>상태: <span style='color: #22c55e;'>● Operational</span></p>
                </div>
                <p style='font-size: 0.7rem; color: #94a3b8;'>Jisong Bang 2026</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        

    # --- [메뉴 1] 텍스트 클리너 ---
    if st.session_state.menu == "labexcel":
        render_lab_to_excel_tool()

    # --- [메뉴 2] Lab → Table 기능 ---
    elif st.session_state.menu == "cleaner":
        render_text_cleaner()

    # --- [메뉴 3] Q&A / 도움말 ---
    elif st.session_state.menu == "qna":
        render_qna()

if __name__ == "__main__":
    main()