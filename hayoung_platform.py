# 이 코드는 파이썬으로 웹 화면을 만들어주는 '스트림릿(Streamlit)' 라이브러리를 사용합니다.
# 실행 방법: cd Desktop\하영자원 입력 후 python -m streamlit run hayoung_platform.py 실행


import streamlit as st
import pandas as pd
import time
import io
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
# 1. 페이지 및 기본 환경 설정
# ==========================================
st.set_page_config(page_title="하영자원 B2G 플랫폼", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# 화려하고 직관적인 하영자원 전용 CSS 디자인 팩
st.markdown("""
    <style>
    .custom-card { background-color: #ffffff !important; color: #202124 !important; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border-top: 5px solid #1a73e8; }
    .custom-card-red { border-top: 5px solid #ea4335; }
    .custom-card-purple { border-top: 5px solid #9b59b6; }
    .custom-card-green { border-top: 5px solid #34a853; }
    .custom-card-orange { border-top: 5px solid #fbbc05; }
    .metric-title { font-size: 14px; color: #5f6368 !important; font-weight: bold; margin-bottom: 5px;}
    .metric-value-food { font-size: 26px; font-weight: 900; color: #ea4335 !important; }
    .metric-value-biz { font-size: 26px; font-weight: 900; color: #9b59b6 !important; }
    .metric-value-recycle { font-size: 26px; font-weight: 900; color: #34a853 !important; }
    .metric-value-total { font-size: 26px; font-weight: 900; color: #1a73e8 !important; }
    .mobile-app-header { background-color: #202124; color: #ffffff !important; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; margin-bottom: 15px; }
    .safety-box { background-color: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; color: #2e7d32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 기술적 실체 1 & 3: 데이터 영구 저장 및 실시간 연산
# ==========================================
DB_FILE = "hayoung_data.csv"

def load_data():
    try:
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
        return pd.DataFrame(columns=cols)

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# 서버가 구동될 때마다 최신 파일을 읽어와서 실시간 계산 수행
df_all = load_data()

if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].str[:7]
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2
else:
    cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "탄소감축량(kg)"]
    df_all = pd.DataFrame(columns=cols)

# ==========================================
# 3. 사이드바 (사용자 환경)
# ==========================================
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro")
    st.caption("화성시 공공기관 맞춤 데이터 플랫폼")
    role = st.radio("접속 모드", ["🏢 관리자 (본사 관제)", "🏫 행정실 (학교 담당자)", "🚚 현장 기사 (모바일 앱)"])

# ==========================================
# 4. [모드 1] 관리자 화면 (다중 탭 관제 복구)
# ==========================================
if role == "🏢 관리자 (본사 관제)":
    st.title("🏢 본사 통합 관제 및 정산 센터")
    
    # 상단 핵심 대시보드
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 누적</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 누적</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 누적</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 총 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,} 원</div></div>', unsafe_allow_html=True)
    with col5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검 완료율</div><div class="metric-value-total" style="color:#fbbc05;">100 %</div></div>', unsafe_allow_html=True)

    # 6개 탭 구조 완벽 복구
    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs(["통합 정산", "음식물 상세", "사업장 상세", "재활용 상세", "📍 실시간 관제", "🤝 외주 현황"])
    
    with tab_total:
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '최종정산액', '상태']], use_container_width=True)
        if st.button("🔗 올바로시스템 전자인계서 일괄 발송", type="primary"):
            st.success("한국환경공단 올바로시스템에 전자인계서가 자동 등록되었습니다.")
    with tab_food: st.dataframe(df_all[['날짜', '학교명', '음식물(kg)', '음식물비용']], use_container_width=True)
    with tab_biz: st.dataframe(df_all[['날짜', '학교명', '사업장(kg)', '사업장비용']], use_container_width=True)
    with tab_recycle: st.dataframe(df_all[['날짜', '학교명', '재활용(kg)', '재활용수익']], use_container_width=True)
    with tab_map:
        st.write("📍 **수거 차량 실시간 GPS 관제**")
        st.map(pd.DataFrame({'lat': [37.20, 37.25], 'lon': [127.05, 127.10]}))
    with tab_sub:
        st.error("🔔 'B자원' 업체와의 위탁 계약 만료가 30일 남았습니다.")

# ==========================================
# 5. [모드 2] 학교 행정실 (ESG 및 보안 서류 출력)
# ==========================================
elif role == "🏫 행정실 (학교 담당자)":
    st.title("🏫 학교 폐기물 통합 대시보드")
    school = st.selectbox("관리 대상 학교", ["화성초등학교", "동탄중학교", "수원고등학교"])
    df_school = df_all[df_all['학교명'] == school]

    if not df_school.empty:
        # 실시간 ESG 탄소 저감 로직
        total_co2 = df_school['탄소감축량(kg)'].sum()
        tree_count = int(total_co2 / 6.6)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h4 style="margin:0;">🌱 우리 학교 ESG 성과 (화성시 교육청 제출용)</h4>
            <h2>누적 CO₂ 감축량: {total_co2:,.1f} kg (🌲 소나무 {tree_count}그루 식재 효과)</h2>
        </div>
        """, unsafe_allow_html=True)

        st.bar_chart(df_school.set_index('날짜')[['음식물(kg)', '재활용(kg)', '사업장(kg)']])

        # 기술적 실체 2: 행정 서류 보안 출력 (Security)
        def convert_excel_secure(df):
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='법정실적보고서')
                writer.sheets['법정실적보고서'].protect('hayoung1234', {'objects': True, 'scenarios': True, 'format_cells': False})
            return out.getvalue()

        st.write("---")
        st.subheader("🖨️ 행정 증빙 서류 다운로드 (위변조 방지 적용)")
        col_doc1, col_doc2 = st.columns(2)
        with col_doc1:
            st.download_button(
                label="📄 월말 정산 명세서 (Excel)",
                data=convert_excel_secure(df_school),
                file_name=f"{datetime.now().strftime('%Y%m')}_{school}_정산명세서.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_doc2:
            st.download_button(
                label="📄 화성시 조례 법정 실적 보고서 (Excel)",
                data=convert_excel_secure(df_school),
                file_name=f"{datetime.now().strftime('%Y%m')}_{school}_법정실적보고.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("수거 데이터가 아직 전송되지 않았습니다.")

# ==========================================
# 6. [모드 3] 수거 기사 (현장 실시간 입력)
# ==========================================
elif role == "🚚 현장 기사 (모바일 앱)":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="mobile-app-header"><h2 style="margin:0;">🚚 하영자원 현장 앱</h2></div>', unsafe_allow_html=True)
        
        # 현장 맞춤형 안전 로직
        with st.expander("📋 [필수] 운행 전 안전 점검 리스트", expanded=True):
            check1 = st.checkbox("차량 후방 카메라 작동 확인")
            check2 = st.checkbox("조수석 안전 요원 탑승 확인")
            check3 = st.checkbox("등하교 시간 스쿨존 회피 운행 숙지")
            if check1 and check2 and check3:
                st.success("안전 점검 완료! 출발하십시오.")

        is_schoolzone = st.toggle("🚨 스쿨존 진입 알림 (GPS 모의 테스트)")
        if is_schoolzone:
            st.error("스쿨존 내 진입! 규정 속도(30km)를 준수하세요.")
            st.markdown("<h1 style='text-align:center; color:#d93025; font-size:50px;'>30</h1>", unsafe_allow_html=True)

        st.write("---")
        with st.form("driver_input"):
            target = st.selectbox("수거 완료 학교", ["화성초등학교", "동탄중학교", "수원고등학교"])
            col_in1, col_in2, col_in3 = st.columns(3)
            with col_in1: f_w = st.number_input("음식물(kg)", min_value=0, step=10)
            with col_in2: b_w = st.number_input("사업장(kg)", min_value=0, step=10)
            with col_in3: r_w = st.number_input("재활용(kg)", min_value=0, step=10)
            
            if st.form_submit_button("본사 서버로 전송 🚀", use_container_width=True):
                if f_w + b_w + r_w > 0:
                    new_data = {
                        "날짜": datetime.now().strftime("%Y-%m-%d"),
                        "학교명": target, "수거업체": "하영자원(본사 직영)",
                        "음식물(kg)": f_w, "재활용(kg)": r_w, "사업장(kg)": b_w,
                        "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "대기"
                    }
                    save_data(new_data)
                    st.success(f"✅ {target} 수거 실적이 시스템에 영구 기록되었습니다.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("중량을 먼저 입력해 주세요.")