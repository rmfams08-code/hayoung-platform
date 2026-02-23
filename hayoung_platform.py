# 이 코드는 파이썬으로 웹 화면을 만들어주는 '스트림릿(Streamlit)' 라이브러리를 사용합니다.
# 실행 방법: cd Desktop\하영자원 입력 후 python -m streamlit run hayoung_platform.py 실행


import streamlit as st
import pandas as pd
import time
from datetime import datetime
import streamlit.components.v1 as components
import io  # [추가] 메모리 안에서 파일을 만들기 위한 도구

# --- 1. 페이지 및 기본 설정 ---
st.set_page_config(
    page_title="하영자원 데이터 플랫폼 Pro",
    page_icon="♻️",
    layout="wide", # 화면 넓게 쓰기
    initial_sidebar_state="expanded"
)

# --- [추가된 부분] 구글 애널리틱스 (방문자 통계) 연동 코드 시작 ---
# 파이썬(Streamlit) 환경에서 구글 애널리틱스 센서가 정상적으로 작동하도록 변환한 코드입니다.
ga_code = """
<script>
    // 구글 애널리틱스 외부 스크립트 불러오기 (부모 창에 적용)
    var script = window.parent.document.createElement('script');
    script.src = "https://www.googletagmanager.com/gtag/js?id=G-DNFFMVMQLT";
    script.async = true;
    window.parent.document.head.appendChild(script);

    // 구글 애널리틱스 설정 코드 실행
    var script2 = window.parent.document.createElement('script');
    script2.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-DNFFMVMQLT');
    `;
    window.parent.document.head.appendChild(script2);
</script>
"""
# 변환된 코드를 화면에 보이지 않게(크기 0) 백그라운드에서 실행시킵니다.
components.html(ga_code, width=0, height=0)
# --- 구글 애널리틱스 연동 코드 끝 ---

# --- 구글 크롬 자동 번역 방지 명령어 ---
# 브라우저가 멋대로 이상한 한글로 번역하는 것을 막아줍니다.
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# --- 2. 고급 디자인 (CSS: 화면 꾸미기 명령어) ---
st.markdown("""
    <style>
    /* 카드(네모 박스) 디자인 - 배경은 흰색, 글씨는 검은색으로 고정 */
    .custom-card {
        background-color: #ffffff !important;
        color: #202124 !important; 
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-top: 5px solid #1a73e8; /* 위쪽 파란색 포인트 줄 */
    }
    .custom-card-green { border-top: 5px solid #34a853; }
    .custom-card-orange { border-top: 5px solid #fbbc05; }
    .custom-card-red { border-top: 5px solid #ea4335; }
    .custom-card-purple { border-top: 5px solid #9b59b6; } /* 사업장폐기물용 보라색 포인트 줄 추가 */
    
    /* 글자 크기 및 색상 */
    .metric-title { font-size: 14px; color: #5f6368 !important; font-weight: bold; margin-bottom: 5px;}
    .metric-value-food { font-size: 26px; font-weight: 900; color: #ea4335 !important; } /* 음식물은 빨간색 강조 */
    .metric-value-recycle { font-size: 26px; font-weight: 900; color: #34a853 !important; } /* 재활용은 초록색 강조 */
    .metric-value-biz { font-size: 26px; font-weight: 900; color: #9b59b6 !important; } /* 사업장폐기물 보라색 강조 */
    .metric-value-total { font-size: 26px; font-weight: 900; color: #1a73e8 !important; } /* 통합은 파란색 강조 */
    
    /* 기사님 앱 전용 디자인 */
    .mobile-app-header {
        background-color: #202124; 
        color: #ffffff !important; 
        padding: 15px; 
        border-radius: 10px 10px 0 0; 
        text-align: center;
    }
    
    /* 안전관리 현황 박스 */
    .safety-box {
        background-color: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; color: #2e7d32; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 진짜 데이터 저장소 (CSV) 로직 ---
DB_FILE = "hayoung_data.csv"

def load_data():
    try:
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        # 파일이 처음엔 없으므로 틀을 만듭니다.
        cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
        return pd.DataFrame(columns=cols)

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- 데이터 불러오기 및 자동 계산 부분 수정 ---
df_all = load_data()

# 데이터가 비어있지 않을 때만 계산 실행
if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].str[:7]
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2
else:
    # [중요] 데이터가 아예 없을 때 에러 방지용 빈 표(컬럼) 만들기
    cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "탄소감축량(kg)"]
    df_all = pd.DataFrame(columns=cols)

# --- 3. 사이드바 메뉴 ---
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro")
    role = st.radio("사용자 모드", ["🏢 본사 관리자", "🏫 학교 행정실", "🚚 수거 기사님"])

# --- 4. [모드 1] 관리자 화면 ---
if role == "🏢 본사 관리자":
    st.title("🏢 본사 통합 관제")
    if not df_all.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🗑️ 음식물 합계", f"{df_all['음식물(kg)'].sum():,} kg")
        c2.metric("🗄️ 사업장 합계", f"{df_all['사업장(kg)'].sum():,} kg")
        c3.metric("♻️ 재활용 합계", f"{df_all['재활용(kg)'].sum():,} kg")
        c4.metric("💰 누적 정산액", f"{df_all['최종정산액'].sum():,} 원")
        st.dataframe(df_all, use_container_width=True)
    else:
        st.info("아직 수거 데이터가 없습니다.")

# --- 5. [모드 2] 학교 행정실 화면 ---
elif role == "🏫 학교 행정실":
    st.title("🏫 학교 데이터 대시보드")
    school_name = st.selectbox("학교 선택", ["화성초등학교", "동탄중학교", "수원고등학교"])
    df_school = df_all[df_all['학교명'] == school_name]

    if not df_school.empty:
        st.subheader("📊 수거량 통계")
        st.bar_chart(df_school.set_index('날짜')[['음식물(kg)', '재활용(kg)']])
        
        # 엑셀 다운로드 (시트 보호 포함)
        def convert_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='실적보고서')
                writer.sheets['실적보고서'].protect('hayoung1234')
            return output.getvalue()

        st.download_button(
            label="📄 실적보고서(엑셀) 다운로드",
            data=convert_excel(df_school),
            file_name=f"{school_name}_실적보고서.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("해당 학교의 데이터가 없습니다.")

# --- 6. [모드 3] 수거 기사님 화면 ---
elif role == "🚚 수거 기사님":
    st.title("🚚 현장 수거량 입력")
    with st.form("input_form"):
        target = st.selectbox("방문 학교", ["화성초등학교", "동탄중학교", "수원고등학교"])
        f_w = st.number_input("음식물 (kg)", min_value=0)
        r_w = st.number_input("재활용 (kg)", min_value=0)
        b_w = st.number_input("사업장 (kg)", min_value=0)
        
        if st.form_submit_button("본사로 전송"):
            new_data = {
                "날짜": datetime.now().strftime("%Y-%m-%d"),
                "학교명": target, "수거업체": "하영자원",
                "음식물(kg)": f_w, "재활용(kg)": r_w, "사업장(kg)": b_w,
                "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "대기"
            }
            save_data(new_data)
            st.success("✅ 저장되었습니다! 화면을 새로고침합니다.")
            time.sleep(1)
            st.rerun()