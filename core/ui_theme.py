import streamlit as st

def inject_custom_css():
    """앱에 커스텀 CSS를 주입하여 프리미엄 미학을 적용합니다."""
    st.markdown(
        """
        <style>
        /* 1. 글로벌 타이포그래피 (Google Fonts Inter) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* 2. 메인 배경 및 레이아웃 */
        .main {
            background-color: transparent;
        }
        
        /* 3. 사이드바 스타일링 (Fixed Dark for Premium Look) */
        [data-testid="stSidebar"] {
            background-image: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        [data-testid="stSidebar"] .stButton button {
            background-color: rgba(255, 255, 255, 0.02);
            color: #f1f5f9; /* 제목과 동일한 밝은 색상 적용 */
            border: 1px solid rgba(255, 255, 255, 0.08); /* 세련된 반투명 테두리 */
            transition: all 0.3s ease;
            text-align: left;
            padding: 0.6rem 1rem;
            font-weight: 500;
            border-radius: 8px; /* 버튼 모서리 둥글게 */
            margin-bottom: 4px;
        }
        
        [data-testid="stSidebar"] .stButton button:hover {
            background-color: rgba(255, 255, 255, 0.05);
            color: #38bdf8;
            border-color: rgba(56, 189, 248, 0.3); /* 호버 시 사이언 색상 강조 */
            transform: translateX(2px); /* 호버 시 미세한 움직임 효과 */
        }
        
        /* 4. 헤더 및 포인트 컬러 (Emoji Color Preservation) */
        h1, h2, h3 {
            color: #f8fafc;
            font-weight: 700;
        }

        /* 5. 버튼 스타일링 */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #0284c7, #4f46e5);
            border: none;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        .stButton>button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0369a1, #4338ca);
            transform: translateY(-1px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        /* 6. 메트릭 보드 스타일링 */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.02);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        /* 7. 데이터프레임 컨테이너 */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* 8. 익스팬더 스타일링 */
        .stExpander {
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            background-color: rgba(255, 255, 255, 0.01) !important;
        }

        /* 9. 입력 필드 커스텀 */
        .stTextArea textarea {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background-color: rgba(0, 0, 0, 0.1);
        }

        .stTextArea textarea:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }

        /* 11. 사이드바 하단 고정 푸터 (Adaptive Width) */
        .sidebar-footer {
            position: fixed;
            bottom: 20px;
            left: 0;
            width: 100%;
            padding: 0 1.25rem; /* 버튼 패딩과 일치하도록 조정 */
            z-index: 99;
        }
        
        @media (min-width: 576px) {
            .sidebar-footer {
                width: 300px; /* 사이드바 기본 너비 */
            }
        }
        
        .sidebar-footer .status-box {
            background-color: rgba(255, 255, 255, 0.03);
            padding: 0.8rem 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 10px;
            box-sizing: border-box;
        }
        
        .sidebar-footer p {
            font-size: 0.75rem;
            color: #f1f5f9 !important;
            margin: 0;
            line-height: 1.4;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def ui_card(title: str, content: str = "", footer: str = ""):
    """공통 카드 컴포넌트 스타일링"""
    st.markdown(
        f"""
        <div style="
            padding: 1.5rem;
            border-radius: 16px;
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        ">
            <h4 style="margin-top: 0; color: var(--text-color);">{title}</h4>
            <div style="color: var(--secondary-text-color); font-size: 0.95rem; line-height: 1.6;">{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
