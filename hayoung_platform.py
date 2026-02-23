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

# --- 3. 데이터베이스 로직 (CSV 파일 저장 방식) ---
DB_FILE = "hayoung_data.csv"

def load_data():
    try:
        # 파일이 있으면 읽어오고
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        # 파일이 없으면 빈 틀을 만듭니다.
        columns = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", 
                   "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
        return pd.DataFrame(columns=columns)

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# [수정된 핵심 줄] 이제 세션 상태가 아니라 함수에서 데이터를 직접 가져옵니다.
df_all = load_data()

# 데이터가 비어있지 않을 때만 계산 실행
if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].str[:7]
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2

# 현재 데이터 상태를 세션(메모리)에 동기화
st.session_state.df_all = load_data()
df_all = st.session_state.df_all

# 데이터프레임(엑셀표)으로 변환 및 계산식 추가
df_all = pd.DataFrame(st.session_state.MOCK_DATA)
df_all['월별'] = df_all['날짜'].str[:7] 
df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2

# --- 4. 사이드바 (왼쪽 메뉴) ---
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro")
    st.caption("공공기관(B2G) 맞춤 데이터 플랫폼")
    st.write("---")
    
    role = st.radio(
        "사용자 환경(모드) 선택",
        ["🏢 관리자 (본사 관제)", "🏫 학교 담당자 (행정실)", "🚚 수거 기사 (현장 앱)"],
        index=0 
    )
    st.write("---")
    st.info("💡 **데이터 동기화 (Sync) 완벽 지원**\n\n모든 정보는 실시간으로 공유됩니다.")

# ==========================================
# [모드 1] 관리자 (본사) 모드
# ==========================================
if role == "🏢 관리자 (본사 관제)":
    st.title("🏢 본사 통합 관제 및 정산 센터")
    st.write("음식물, 사업장폐기물, 재활용 통계를 완벽히 분리하여 수익/비용 관리가 가능합니다.")

    # 1. 상단 대시보드
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 총 수거</div><div class="metric-value-food">{df_all['음식물(kg)'].sum():,} kg</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 총 수거</div><div class="metric-value-biz">{df_all['사업장(kg)'].sum():,} kg</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 총 수거</div><div class="metric-value-recycle">{df_all['재활용(kg)'].sum():,} kg</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="custom-card"><div class="metric-title">💰 누적 청구 금액</div><div class="metric-value-total">{df_all['최종정산액'].sum():,} 원</div></div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검 완료율</div><div class="metric-value-total" style="color:#fbbc05 !important;">100 %</div></div>""", unsafe_allow_html=True)

    # ESG 탄소 저감 대시보드
    total_co2_admin = df_all['탄소감축량(kg)'].sum()
    tree_count_admin = int(total_co2_admin / 6.6)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #00b09b, #96c93d); padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,176,155,0.2);">
        <h3 style="color: white; margin-top: 0;">🌍 하영자원 전사 ESG 탄소 저감 성과 (통합)</h3>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div><div style="font-size: 16px; opacity: 0.9;">누적 CO₂ 감축량</div><div style="font-size: 36px; font-weight: 900;">{total_co2_admin:,.1f} kg</div></div>
            <div style="font-size: 40px; font-weight: bold; opacity: 0.5;">=</div>
            <div><div style="font-size: 16px; opacity: 0.9;">어린 소나무 식재 효과</div><div style="font-size: 36px; font-weight: 900;">🌲 {tree_count_admin} 그루</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_esg1, col_esg2 = st.columns([1, 4])
    with col_esg1:
        if st.button("📄 전사 ESG 성과 보고서 출력", type="secondary"):
            st.success("전체 학교 대상 ESG 보고서 다운로드가 완료되었습니다.")

    # 2. 항목별 분리 정산 탭 (외주업체 탭 포함)
    st.subheader("📑 통합 및 개별 정산 시트(Sheet)")
    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_subcontractor = st.tabs([
        "전체 통합 정산", "음식물 정산 내역", "사업장 정산 내역", "재활용 정산 내역", "📍 실시간 차량 관제", "🤝 외주업체 현황"
    ])
    
    with tab_total:
        st.write("✅ **통합 상계처리 명세서** (음식물비용 + 사업장비용 - 재활용수익)")
        # 수거업체명 포함하여 출력
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '음식물비용', '사업장비용', '재활용수익', '최종정산액', '상태']], use_container_width=True)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("🚀 통합 세금계산서 일괄 전송 (국세청 홈택스)", type="primary", use_container_width=True):
                st.success("모든 거래처에 통합 세금계산서 발행이 완료되었습니다.")
        with col_t2:
            if st.button("🔗 올바로시스템 전자인계서 자동등록 및 일괄발송", type="primary", use_container_width=True):
                with st.spinner("한국환경공단 올바로시스템 API와 데이터 연동 중..."):
                    time.sleep(2)
                st.success("모든 내역이 올바로시스템에 전자인계서로 자동 등록 및 발송 처리되었습니다!")

    with tab_food:
        st.write("🗑️ **음식물 폐기물 처리비용 상세 시트**")
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '음식물(kg)', '단가(원)', '음식물비용', '상태']], use_container_width=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("🏢 업체별 정산명세서 발송 (음식물)", key="btn_food_company", use_container_width=True):
                st.success("각 수거업체(본사/외주)로 음식물 정산명세서가 발송되었습니다.")
        with col_f2:
            if st.button("🏫 학교별 정산명세서 발송 (음식물)", key="btn_food_school", use_container_width=True):
                st.success("각 학교 행정실로 음식물 정산명세서가 발송되었습니다.")

    with tab_biz:
        st.write("🗄️ **사업장 폐기물 처리비용 상세 시트**")
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '사업장(kg)', '사업장단가(원)', '사업장비용', '상태']], use_container_width=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🏢 업체별 정산명세서 발송 (사업장)", key="btn_biz_company", use_container_width=True):
                st.success("각 수거업체(본사/외주)로 사업장폐기물 정산명세서가 발송되었습니다.")
        with col_b2:
            if st.button("🏫 학교별 정산명세서 발송 (사업장)", key="btn_biz_school", use_container_width=True):
                st.success("각 학교 행정실로 사업장폐기물 정산명세서가 발송되었습니다.")

    with tab_recycle:
        st.write("♻️ **재활용 매입/수익 상세 시트**")
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '재활용(kg)', '재활용단가(원)', '재활용수익', '상태']], use_container_width=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("🏢 업체별 매입명세서 발송 (재활용)", key="btn_re_company", use_container_width=True):
                st.success("각 수거업체(본사/외주)로 재활용 매입명세서가 발송되었습니다.")
        with col_r2:
            if st.button("🏫 학교별 수익명세서 발송 (재활용)", key="btn_re_school", use_container_width=True):
                st.success("각 학교 행정실로 재활용 수익명세서가 발송되었습니다.")

    with tab_map:
        st.write("📍 **차량 실시간 위치 관제 (GPS)**")
        st.map(pd.DataFrame({'lat': [37.20, 37.25, 37.18], 'lon': [127.05, 127.10, 127.02]}))
        
    with tab_subcontractor:
        st.write("🤝 **외주 수거업체 실시간 업무 및 안전 평가 현황**")
        st.error("🔔 **[계약 갱신 알림]** 'B자원' 업체와의 수거 위탁 계약 만료가 30일 앞으로 다가왔습니다. (만료일: 2026-03-25)")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.info("🏆 이달의 우수 안전 업체: **A환경** (98점)")
        with col_s2:
            st.warning("⚠️ 주의 필요 업체: **B자원** (과속 1회 감지)") 
        with col_s3:
            st.success("✅ 스쿨존 속도위반 경고 건수: **1건**")
            
        st.write("---")
        mock_sub_data = pd.DataFrame({
            "외주업체명": ["A환경", "B자원"],
            "담당학교": ["동탄중학교", "수원고등학교"],
            "안전평가점수": ["98점 (우수)", "85점 (주의)"],
            "안전 페널티(위반벌금)": ["0 원", "-50,000 원 (과속 1회)"], 
            "이달 정산지급액(예상)": ["1,350,000 원", "880,000 원"], 
            "현재 운행상태": ["🟢 운행중", "🟡 대기중"]
        })
        st.dataframe(mock_sub_data, use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("🔎 담당 차량 및 기사 상세 조회 (타임라인)")
        selected_sub = st.selectbox("실시간 이동 동선을 조회할 업체를 선택하세요", ["A환경", "B자원"])

        if selected_sub == "A환경":
            st.markdown("<div class='safety-box'>🚛 <b>차량번호:</b> 경기88아 1234 &nbsp;|&nbsp; 👨‍✈️ <b>담당기사:</b> 김하영 (010-1234-5678) &nbsp;|&nbsp; 🏫 <b>오늘 배차:</b> 1곳</div>", unsafe_allow_html=True)
            st.write("⏱️ **오늘의 실시간 이동 동선**")
            st.write("✔️ 08:30 [출발 전 점검] 차량 후방카메라 및 안전요원 탑승 확인 완료")
            st.write("🔄 10:30 [이동 중] 동탄중학교로 이동 중 (현재 GPS 정상 수신 중)")
        elif selected_sub == "B자원":
            st.markdown("<div class='safety-box' style='background-color:#fff3e0; border-color:#ffe0b2; color:#e65100;'>🚛 <b>차량번호:</b> 서울99바 5678 &nbsp;|&nbsp; 👨‍✈️ <b>담당기사:</b> 이자원 (010-9876-5432) &nbsp;|&nbsp; 🏫 <b>오늘 배차:</b> 1곳</div>", unsafe_allow_html=True)
            st.write("⏱️ **오늘의 실시간 이동 동선**")
            st.write("✔️ 09:00 [출발 전 점검] 안전요원 탑승 확인 완료")
            st.write("❌ 09:45 [경고 발생] 수원고등학교 인근 스쿨존 진입 시 38km/h 과속 감지 (안전 점수 차감 및 페널티 부여)")

        st.write("---")
        col_sub_btn1, col_sub_btn2 = st.columns(2)
        with col_sub_btn1:
            if st.button("📄 외주업체 안전평가 결과서 다운로드"):
                st.success("안전평가 결과서 다운로드가 완료되었습니다.")
        with col_sub_btn2:
            if st.button("💰 외주업체 월별 정산 대금 청구서 발행"):
                st.success("외주업체에 정산 대금 지급 내역이 전송되었습니다.")

# ==========================================
# [모드 2] 학교 책임자 (행정실) 모드
# ==========================================
elif role == "🏫 학교 담당자 (행정실)":
    st.title("🏫 화성초등학교 폐기물 통합 대시보드")
    
    df_school = df_all[df_all['학교명'] == '화성초등학교']
    
    # 1. 상단 대시보드
    st.subheader("🔍 실시간 수거 현황 및 안전 준수율")
    col_rt1, col_rt2, col_rt3, col_rt4 = st.columns(4)
    
    today_data = df_school.iloc[-1] 
    month_data_sum = df_school[df_school['월별'] == '2026-02'].sum(numeric_only=True)
    
    with col_rt1:
        st.markdown(f"""
        <div class="custom-card custom-card-red">
            <div class="metric-title">🗑️ 음식물 수거량 (실시간/누적)</div>
            <div style="font-size: 16px;">오늘: <strong style="color:#ea4335;">{today_data['음식물(kg)']} kg</strong></div>
            <div style="font-size: 16px;">금월: <strong>{month_data_sum['음식물(kg)']} kg</strong></div>
        </div>""", unsafe_allow_html=True)
    with col_rt2:
        st.markdown(f"""
        <div class="custom-card custom-card-purple">
            <div class="metric-title">🗄️ 사업장 수거량 (실시간/누적)</div>
            <div style="font-size: 16px;">오늘: <strong style="color:#9b59b6;">{today_data['사업장(kg)']} kg</strong></div>
            <div style="font-size: 16px;">금월: <strong>{month_data_sum['사업장(kg)']} kg</strong></div>
        </div>""", unsafe_allow_html=True)
    with col_rt3:
        st.markdown(f"""
        <div class="custom-card custom-card-green">
            <div class="metric-title">♻️ 재활용 수거량 (실시간/누적)</div>
            <div style="font-size: 16px;">오늘: <strong style="color:#34a853;">{today_data['재활용(kg)']} kg</strong></div>
            <div style="font-size: 16px;">금월: <strong>{month_data_sum['재활용(kg)']} kg</strong></div>
        </div>""", unsafe_allow_html=True)
    with col_rt4:
        st.markdown("""
        <div class="custom-card custom-card-orange">
            <div class="metric-title">🛡️ 수거업체 안전 준수</div>
            <div class="safety-box" style="padding: 10px; font-size:13px;">✓ 담당: 하영자원(본사 직영)</div>
            <div class="safety-box" style="margin-top: 5px; padding: 10px; font-size:13px;">✓ 스쿨존 규정 100% 준수</div>
        </div>""", unsafe_allow_html=True)

    # ESG 대시보드
    total_co2_school = df_school['탄소감축량(kg)'].sum()
    tree_count_school = int(total_co2_school / 6.6)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 20px; border-radius: 12px; color: white; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 8px 15px rgba(17,153,142,0.2);">
        <h4 style="color: white; margin-top: 0; margin-bottom: 15px;">🌱 우리 학교 ESG 환경 기여도 (탄소배출 저감 효과)</h4>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div><span style="font-size: 14px; opacity: 0.9;">누적 CO₂ 감축량</span><br><span style="font-size: 28px; font-weight: 900;">{total_co2_school:,.1f} kg</span></div>
            <div style="font-size: 30px; font-weight: bold; opacity: 0.5;">=</div>
            <div><span style="font-size: 14px; opacity: 0.9;">어린 소나무 심은 효과</span><br><span style="font-size: 28px; font-weight: 900;">🌲 {tree_count_school} 그루</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 일별/월별 막대그래프 
    st.write("---")
    st.subheader("📊 폐기물 배출량 통계 분석 (막대그래프)")
    tab_daily, tab_monthly = st.tabs(["📅 일별 배출량 (상세)", "🗓️ 월별 배출량 (추이)"])
    
    with tab_daily:
        st.write("해당 월의 일자별 수거량입니다. (단위: kg)")
        col_chart1, col_chart2, col_chart3 = st.columns(3)
        with col_chart1:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#ea4335;'>🗑️ 음식물 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(df_school.set_index('날짜')['음식물(kg)'], color="#ea4335")
        with col_chart2:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#9b59b6;'>🗄️ 사업장 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(df_school.set_index('날짜')['사업장(kg)'], color="#9b59b6")
        with col_chart3:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#34a853;'>♻️ 재활용 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(df_school.set_index('날짜')['재활용(kg)'], color="#34a853")
        
    with tab_monthly:
        st.write("월별 총 누적 수거량 비교입니다. (단위: kg)")
        chart_df_monthly = df_school.groupby('월별')[['음식물(kg)', '사업장(kg)', '재활용(kg)']].sum()
        col_chart4, col_chart5, col_chart6 = st.columns(3)
        with col_chart4:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#ea4335;'>🗑️ 음식물 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(chart_df_monthly['음식물(kg)'], color="#ea4335")
        with col_chart5:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#9b59b6;'>🗄️ 사업장 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(chart_df_monthly['사업장(kg)'], color="#9b59b6")
        with col_chart6:
            st.markdown("<div style='text-align:center; font-weight:bold; color:#34a853;'>♻️ 재활용 수거량</div>", unsafe_allow_html=True)
            st.bar_chart(chart_df_monthly['재활용(kg)'], color="#34a853")

    # --- 수정된 행정 서류 출력 부분 ---
    st.write("---")
    st.subheader("🖨️ 행정 증빙 서류 자동 출력 및 올바로시스템 연동")
    
    # 엑셀 파일로 변환하는 함수 (빠른 모드용 핵심 로직)
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='실적보고서')
        return output.getvalue()

    excel_data = convert_df_to_excel(df_school)

    col_doc1, col_doc2, col_doc3 = st.columns(3)
    with col_doc1:
        # [수정] 일반 버튼에서 다운로드 버튼으로 변경
        st.download_button(
            label="📄 음식물/사업장 실적보고서",
            data=excel_data,
            file_name=f"{datetime.now().strftime('%Y%m%d')}_화성초_실적보고서.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_doc2:
        if st.button("📄 재활용 수익 상계처리 증빙서", use_container_width=True):
            st.success("감사 대비용 상계증빙서 다운로드 완료!")
    with col_doc3:
        if st.button("📄 수거업체 안전관리 점검결과표", use_container_width=True):
            st.success("안전관리 현황 보고서 다운로드 완료!")
            
    # 2번째 줄: 통계, 연말 결산, ESG
    st.write("") 
    col_doc4, col_doc5, col_doc6 = st.columns(3)
    with col_doc4:
        if st.button("📄 월별 수거량 통계 (항목별 분리)", use_container_width=True):
            st.success("월별 통계 보고서 다운로드 완료!")
    with col_doc5:
        if st.button("📄 [연말 결산] 교육청 제출용 종합 보고서", use_container_width=True):
            st.success("교육청 제출용 종합 보고서 다운로드 완료!")
    with col_doc6:
        if st.button("📄 [ESG] 탄소배출 저감 성과 보고서", use_container_width=True):
            st.success("교육청 제출용 ESG 성과 보고서 다운로드 완료!")

    # 3번째 줄: [추가요청] 품목별 정산명세서 다운로드 및 올바로 전자인계서 자동화
    st.write("")
    st.markdown("<h5 style='color:#1a73e8; font-weight:bold;'>⚡ 데이터 플랫폼 특화 기능 (자동화)</h5>", unsafe_allow_html=True)
    col_doc7, col_doc8 = st.columns(2)
    with col_doc7:
        if st.button("📥 품목별 정산명세서 (음식물/사업장/재활용) 일괄 다운로드", use_container_width=True):
            st.success("음식물, 사업장, 재활용으로 분류된 상세 정산명세서(PDF)가 내 컴퓨터에 저장되었습니다.")
    with col_doc8:
        if st.button("🔗 올바로시스템 전자인계서 연동 및 자동결재", type="primary", use_container_width=True):
            with st.spinner("한국환경공단 서버와 통신하며 전자인계서 전자서명(결재)을 진행 중입니다..."):
                time.sleep(2)
            st.success("올바로시스템에 전자인계서가 성공적으로 이관 및 자동 결재되었습니다!")

# ==========================================
# [모드 3] 수거 기사님 (현장용) 앱
# ==========================================
elif role == "🚚 수거 기사 (현장 앱)":
    _, mid, _ = st.columns([1, 2, 1])
    
    with mid:
        st.markdown("""
            <div class="mobile-app-header">
                <h2 style="margin: 0; font-size: 22px;">🚚 하영자원 기사 전용 앱</h2>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 [필수] 운행 전 안전 점검 리스트 (클릭하여 열기)", expanded=True):
            st.warning("어린이 안전을 위해 아래 항목을 모두 확인 후 체크해 주세요.")
            check1 = st.checkbox("차량 후방 카메라 및 후진 경고음 정상 작동 확인")
            check2 = st.checkbox("조수석 안전 요원 탑승 여부 확인")
            check3 = st.checkbox("등하교 시간 (오전 8시~9시 / 오후 2시~3시) 회피 운행 숙지")
            
            if check1 and check2 and check3:
                st.success("안전 점검 완료! 오늘도 안전 운행하세요.")
        
        st.write("---")
        st.subheader("📍 현재 주행 상태")
        is_schoolzone = st.toggle("차량이 스쿨존(반경 300m 이내)에 진입함 (GPS 가상 테스트)")
        
        if is_schoolzone:
            st.error("🚨 **스쿨존 진입! 속도를 30km 이하로 줄이세요.**")
            st.markdown("<h1 style='text-align:center; color:#d93025; font-size:60px;'>30</h1>", unsafe_allow_html=True)
        else:
            st.info("🟢 스쿨존 밖 정상 주행 중입니다.")

        st.write("---")
        st.subheader("📝 현장 수거량 입력")
        target = st.selectbox("수거 완료한 학교를 선택하세요", ["화성초등학교", "동탄중학교", "수원고등학교"])
        
        col_input1, col_input2, col_input3 = st.columns(3)
        with col_input1:
            food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
        with col_input2:
            biz_w = st.number_input("사업장 (kg)", min_value=0, step=10)
        with col_input3:
            re_w = st.number_input("재활용 (kg)", min_value=0, step=10)
            
        st.camera_input("📸 현장 증빙 사진 촬영 (선택사항)", label_visibility="collapsed")
        
       # [모드 3] 수거 기사 (현장 앱) 부분의 버튼 수정
if st.button("본사로 수거량 전송하기", type="primary", use_container_width=True):
    if food_w > 0 or biz_w > 0 or re_w > 0:
        # 새로운 데이터 한 줄 생성
        new_entry = {
            "날짜": datetime.now().strftime("%Y-%m-%d"),
            "학교명": target,
            "수거업체": "하영자원(본사)",
            "음식물(kg)": food_w,
            "재활용(kg)": re_w,
            "사업장(kg)": biz_w,
            "단가(원)": 150,
            "재활용단가(원)": 300,
            "사업장단가(원)": 200,
            "상태": "대기중"
        }
        # 파일에 저장
        save_data(new_entry)
        st.success("✅ 본사 서버로 전송 및 영구 기록 완료!")
        time.sleep(1)
        st.rerun() # 화면 새로고침하여 대시보드 반영
    else:
        st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")