# 이 코드는 파이썬으로 웹 화면을 만들어주는 '스트림릿(Streamlit)' 라이브러리를 사용합니다.
# 실행 방법: cd Desktop\하영자원 입력 후 python -m streamlit run hayoung_platform.py 실행


import streamlit as st
import pandas as pd
import time
import io
import random
from datetime import datetime

# ==========================================
# 0. 관리 대상 학교 목록 및 실제 학생 수 (검색 데이터 기반)
# ==========================================
STUDENT_COUNTS = {
    "화성초등학교": 309, "동탄중학교": 1033, "수원고등학교": 884, "안양남초등학교": 486,
    "평촌초등학교": 1126, "부림초등학교": 782, "부흥중학교": 512, "덕천초등학교": 859,
    "서초고등학교": 831, "구암고등학교": 547, "국사봉중학교": 346, "당곡고등학교": 746,
    "당곡중학교": 512, "서울공업고등학교": 735, "강남중학교": 265, "영남중학교": 409,
    "선유고등학교": 580, "신목고등학교": 1099, "고척고등학교": 782, "구현고등학교": 771,
    "안산국제비지니스고등학교": 660, "안산고등학교": 745, "송호고등학교": 879, "비봉고등학교": 734
}
SCHOOL_LIST = sorted(list(STUDENT_COUNTS.keys()))

# ==========================================
# 1. 페이지 및 기본 환경 설정 (기존 유지)
# ==========================================
st.set_page_config(page_title="하영자원 데이터 플랫폼 Pro", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

st.markdown("""
    <style>
    .custom-card { background-color: #ffffff !important; color: #202124 !important; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border-top: 5px solid #1a73e8; }
    .custom-card-green { border-top: 5px solid #34a853; }
    .custom-card-orange { border-top: 5px solid #fbbc05; }
    .custom-card-red { border-top: 5px solid #ea4335; }
    .custom-card-purple { border-top: 5px solid #9b59b6; }
    .metric-title { font-size: 14px; color: #5f6368 !important; font-weight: bold; margin-bottom: 5px;}
    .metric-value-food { font-size: 26px; font-weight: 900; color: #ea4335 !important; }
    .metric-value-recycle { font-size: 26px; font-weight: 900; color: #34a853 !important; }
    .metric-value-biz { font-size: 26px; font-weight: 900; color: #9b59b6 !important; }
    .metric-value-total { font-size: 26px; font-weight: 900; color: #1a73e8 !important; }
    .mobile-app-header { background-color: #202124; color: #ffffff !important; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; margin-bottom: 15px; }
    .safety-box { background-color: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; color: #2e7d32; font-weight: bold; }
    .penalty-box { background-color: #ffebee; border: 1px solid #ffcdd2; padding: 15px; border-radius: 8px; color: #c62828; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 데이터 영구 저장 및 실시간 연산 (V5: 학생수 비례 고도화 로직)
# ==========================================
DB_FILE = "hayoung_data_v5.csv"

def load_data():
    try:
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
        sample_data = []
        
        # 1월, 2월 데이터를 모든 학교 대상으로 생성
        for month, days in [(1, 31), (2, 25)]:
            for day in range(1, days + 1):
                if day % 7 in [0, 1]: continue # 주말 제외
                for school, count in STUDENT_COUNTS.items():
                    # AI 고도화 추론: 학생 1인당 배출량 기준 산정
                    food = int(count * random.uniform(0.1, 0.2))
                    recycle = int(count * random.uniform(0.05, 0.1))
                    biz = int(count * random.uniform(0.02, 0.05))
                    status = "정산완료" if month == 1 else "정산대기"
                    
                    sample_data.append({
                        "날짜": f"2026-{month:02d}-{day:02d} {random.randint(8, 15):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
                        "학교명": school, "학생수": count, "수거업체": "하영자원(본사 직영)",
                        "음식물(kg)": food, "재활용(kg)": recycle, "사업장(kg)": biz,
                        "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": status
                    })
        df = pd.DataFrame(sample_data, columns=cols)
        df.to_csv(DB_FILE, index=False)
        return df

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

df_all = load_data()

if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].astype(str).str[:7]
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2
else:
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "탄소감축량(kg)"]
    df_all = pd.DataFrame(columns=cols)

# ==========================================
# 3. 사이드바 (왼쪽 메뉴)
# ==========================================
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro")
    st.caption("공공기관(B2G) 맞춤 데이터 플랫폼")
    st.write("---")
    role = st.radio("사용자 환경(모드) 선택", ["🏢 관리자 (본사 관제)", "🏫 학교 담당자 (행정실)", "🚚 수거 기사 (현장 앱)"])
    st.write("---")
    st.info("💡 **데이터 실시간 동기화 완벽 지원**")

# ==========================================
# 4. 보안 엑셀 보고서 생성 함수
# ==========================================
def create_secure_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='법정실적보고서', startrow=2)
        workbook = writer.book
        worksheet = writer.sheets['법정실적보고서']
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        worksheet.merge_range(0, 0, 1, len(df.columns)-1, f"■ {title} ■", title_format)
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 16)
        worksheet.protect('hayoung1234', {'objects': True, 'scenarios': True, 'format_cells': False, 'sort': True})
    return output.getvalue()

# ==========================================
# [모드 1] 관리자 (본사) 모드
# ==========================================
if role == "🏢 관리자 (본사 관제)":
    st.title("🏢 본사 통합 관제 및 정산 센터")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 누적</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 누적</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 누적</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 총 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,} 원</div></div>', unsafe_allow_html=True)
    with col5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 평균 안전 점수</div><div class="metric-value-total" style="color:#fbbc05;">96 점</div></div>', unsafe_allow_html=True)

    # 사장님이 주신 이미지 구조 완벽 반영 (하위 탭 생성)
    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs([
        "전체 통합 정산", "음식물 정산 내역", "사업장 정산 내역", "재활용 정산 내역", "📍 실시간 차량 관제", "🤝 외주업체 현황"
    ])
    
    with tab_total:
        st.subheader("📑 연도별/월별 통합 정산 시트")
        st.write("💡 **AI 추론 요약:** 학생 1인당 평균 정산 단가를 추적하여 과다 배출 학교를 모니터링합니다.")
        sub_all, sub_1, sub_2 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with sub_all: st.dataframe(df_all[['날짜', '학교명', '학생수', '최종정산액', '상태']], use_container_width=True)
        with sub_1: st.dataframe(df_all[df_all['월별']=='2026-01'][['날짜', '학교명', '학생수', '최종정산액', '상태']], use_container_width=True)
        with sub_2: st.dataframe(df_all[df_all['월별']=='2026-02'][['날짜', '학교명', '학생수', '최종정산액', '상태']], use_container_width=True)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1: st.button("🚀 통합 세금계산서 일괄 전송", type="primary", use_container_width=True)
        with col_t2: st.button("🔗 올바로시스템 전자인계서 일괄발송", type="primary", use_container_width=True)

    with tab_food:
        st.subheader("🗑️ 연도별/월별 음식물 정산 시트")
        st.write("💡 **AI 추론 요약:** 학교별 급식 인원(학생수)에 비례한 잔반 배출 계수(평균 0.15kg/인) 적용 내역입니다.")
        f_all, f_1, f_2 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with f_all: st.dataframe(df_all[['날짜', '학교명', '학생수', '음식물(kg)', '음식물비용']], use_container_width=True)
        with f_1: st.dataframe(df_all[df_all['월별']=='2026-01'][['날짜', '학교명', '학생수', '음식물(kg)', '음식물비용']], use_container_width=True)
        with f_2: st.dataframe(df_all[df_all['월별']=='2026-02'][['날짜', '학교명', '학생수', '음식물(kg)', '음식물비용']], use_container_width=True)

    with tab_biz:
        st.subheader("🗄️ 연도별/월별 사업장 정산 시트")
        st.write("💡 **AI 추론 요약:** 행정실 및 교실 교보재 폐기물 발생량(평균 0.04kg/인) 분석 내역입니다.")
        b_all, b_1, b_2 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with b_all: st.dataframe(df_all[['날짜', '학교명', '학생수', '사업장(kg)', '사업장비용']], use_container_width=True)
        with b_1: st.dataframe(df_all[df_all['월별']=='2026-01'][['날짜', '학교명', '학생수', '사업장(kg)', '사업장비용']], use_container_width=True)
        with b_2: st.dataframe(df_all[df_all['월별']=='2026-02'][['날짜', '학교명', '학생수', '사업장(kg)', '사업장비용']], use_container_width=True)

    with tab_recycle:
        st.subheader("♻️ 연도별/월별 재활용 정산 시트")
        st.write("💡 **AI 추론 요약:** 종이, 플라스틱 분리수거를 통한 자원순환 상계처리(수익) 분석 내역입니다.")
        r_all, r_1, r_2 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with r_all: st.dataframe(df_all[['날짜', '학교명', '학생수', '재활용(kg)', '재활용수익']], use_container_width=True)
        with r_1: st.dataframe(df_all[df_all['월별']=='2026-01'][['날짜', '학교명', '학생수', '재활용(kg)', '재활용수익']], use_container_width=True)
        with r_2: st.dataframe(df_all[df_all['월별']=='2026-02'][['날짜', '학교명', '학생수', '재활용(kg)', '재활용수익']], use_container_width=True)
        
    with tab_map:
        st.write("📍 **수거 차량 실시간 GPS 관제**")
        st.map(pd.DataFrame({'lat': [37.20, 37.25], 'lon': [127.05, 127.10]}))
        
    with tab_sub:
        st.write("🚚 **위탁 외주업체 수거 현황 및 안전관리 평가표**")
        vendor_data = pd.DataFrame({
            "위탁업체명": ["A환경", "B자원", "C로지스"],
            "담당 기사": ["김철수", "이영희", "박민수"],
            "차량 번호": ["경기80자1234", "서울90바5678", "화성70가9012"],
            "누적수거량(kg)": [8500, 6200, 4100],
            "계약 만료일": ["2026-12-31", "2026-03-15", "2027-06-30"],
            "안전 점수": ["98점 (우수)", "75점 (경고)", "95점 (양호)"]
        })
        st.dataframe(vendor_data, use_container_width=True)
        st.markdown('<div class="penalty-box">⚠️ [경고] B자원(서울90바5678): 2월 14일 스쿨존 규정속도 1회 위반 감지 <br> - 조치: 안전점수 25점 삭감 및 위약 패널티 50,000원 청구 예정</div>', unsafe_allow_html=True)

# ==========================================
# [모드 2] 학교 책임자 (행정실) 모드
# ==========================================
elif role == "🏫 학교 담당자 (행정실)":
    st.title("🏫 학교 폐기물 통합 대시보드")
    school = st.selectbox("관리 대상 학교", SCHOOL_LIST)
    df_school = df_all[df_all['학교명'] == school]

    if not df_school.empty:
        total_co2_school = df_school['탄소감축량(kg)'].sum()
        tree_count_school = int(total_co2_school / 6.6)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h4 style="margin: 0; margin-bottom: 10px;">🌱 우리 학교 ESG 환경 기여도 (탄소배출 저감)</h4>
            <h2>누적 CO₂ 감축량: {total_co2_school:,.1f} kg (🌲 소나무 {tree_count_school}그루 식재 효과)</h2>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 폐기물 배출량 통계 분석 (막대그래프)")
        tab_daily, tab_monthly = st.tabs(["🗓️ 일별 배출량 (상세)", "🗓️ 월별 배출량 (추이)"])
        
        with tab_daily:
            st.write("해당 월의 일자별 수거량입니다. (단위: kg)")
            daily_df = df_school.copy()
            daily_df['일자'] = daily_df['날짜'].astype(str).str[:10]
            daily_grouped = daily_df.groupby('일자')[['음식물(kg)', '사업장(kg)', '재활용(kg)']].sum().reset_index()
            
            col_chart1, col_chart2, col_chart3 = st.columns(3)
            with col_chart1:
                st.markdown("<h5 style='text-align:center; color:#ea4335; font-weight:bold;'>🗑️ 음식물 수거량</h5>", unsafe_allow_html=True)
                st.bar_chart(daily_grouped.set_index('일자')['음식물(kg)'], color="#ea4335")
            with col_chart2:
                st.markdown("<h5 style='text-align:center; color:#9b59b6; font-weight:bold;'>🗄️ 사업장 수거량</h5>", unsafe_allow_html=True)
                st.bar_chart(daily_grouped.set_index('일자')['사업장(kg)'], color="#9b59b6")
            with col_chart3:
                st.markdown("<h5 style='text-align:center; color:#34a853; font-weight:bold;'>♻️ 재활용 수거량</h5>", unsafe_allow_html=True)
                st.bar_chart(daily_grouped.set_index('일자')['재활용(kg)'], color="#34a853")

        with tab_monthly:
            st.write("월별 전체 수거량 추이입니다. (단위: kg)")
            monthly_df_school = df_school.groupby('월별')[['음식물(kg)', '사업장(kg)', '재활용(kg)']].sum()
            st.bar_chart(monthly_df_school)

        st.write("---")
        st.markdown("<h5 style='color:#2e7d32; font-weight:bold;'>🛡️ 금일 수거차량 실시간 안전 점검 현황</h5>", unsafe_allow_html=True)
        st.markdown(f'<div class="safety-box">✅ 배차 차량: 하영자원 (본사 직영 운행) <br>✅ 스쿨존 규정속도 준수 여부: <span style="color:blue;">정상 (MAX 28km/h 통과)</span> <br>✅ 후방카메라 작동 및 안전요원 동승: 적합 (점검완료)</div>', unsafe_allow_html=True)

        st.write("---")
        st.subheader("🖨️ 행정 증빙 서류 자동 출력 (관공서 법정 양식 적용)")
        col_doc1, col_doc2 = st.columns(2)
        with col_doc1:
            st.download_button("📄 [월간] 폐기물 위탁처리 정산(청구)서 다운로드", 
                               data=create_secure_excel(df_school[['날짜','학교명','음식물(kg)','사업장(kg)','최종정산액']], "폐기물 위탁처리 정산(청구)서"), 
                               file_name=f"{school}_월간정산서.xlsx", use_container_width=True)
        with col_doc2:
            st.download_button("📄 [실적] 폐기물 배출 및 처리실적보고서 (법정 제30호서식)", 
                               data=create_secure_excel(df_school[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)']], "[폐기물관리법 시행규칙 별지 제30호서식] 폐기물 배출 및 처리 실적보고"), 
                               file_name=f"{school}_실적보고서.xlsx", use_container_width=True)

        st.write("") 
        col_doc3, col_doc4 = st.columns(2)
        with col_doc3:
            st.download_button("📄 사업장 일반폐기물 재활용 상계처리 증빙서", 
                               data=create_secure_excel(df_school[['날짜','학교명','재활용(kg)','재활용수익']], "사업장 폐기물 재활용 상계처리 증빙 내역"), 
                               file_name=f"{school}_상계증빙.xlsx", use_container_width=True)
        with col_doc4:
            if st.button("🔗 올바로시스템 전자인계서 연동 및 자동결재", type="primary", use_container_width=True):
                with st.spinner("한국환경공단 서버와 통신 중..."):
                    time.sleep(2)
                st.success("올바로시스템에 전자인계서가 성공적으로 이관 및 결재되었습니다!")
    else:
        st.info("해당 학교의 수거 데이터가 아직 전송되지 않았습니다.")

# ==========================================
# [모드 3] 수거 기사님 (현장용) 앱
# ==========================================
elif role == "🚚 수거 기사 (현장 앱)":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="mobile-app-header"><h2 style="margin: 0; font-size: 22px;">🚚 하영자원 기사 전용 앱</h2></div>', unsafe_allow_html=True)
        
        with st.expander("📋 [필수] 운행 전 안전 점검 리스트", expanded=True):
            st.warning("어린이 안전을 위해 아래 항목을 확인해 주세요.")
            check1 = st.checkbox("차량 후방 카메라 정상 작동 확인")
            check2 = st.checkbox("조수석 안전 요원 탑승 여부 확인")
            check3 = st.checkbox("스쿨존 회피 운행 숙지")
            if check1 and check2 and check3:
                st.success("안전 점검 완료! 오늘도 안전 운행하세요.")
        
        st.write("---")
        is_schoolzone = st.toggle("🚨 스쿨존 진입 알림 (GPS 모의 테스트)")
        if is_schoolzone:
            st.error("스쿨존 진입! 속도를 30km 이하로 줄이세요.")
            st.markdown("<h1 style='text-align:center; color:#d93025; font-size:60px;'>30</h1>", unsafe_allow_html=True)

        st.write("---")
        st.camera_input("📸 현장 증빙 사진 촬영 (선택사항)")
        
        with st.form("driver_input"):
            target = st.selectbox("수거 완료한 학교", SCHOOL_LIST)
            col_in1, col_in2, col_in3 = st.columns(3)
            with col_in1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
            with col_in2: biz_w = st.number_input("사업장 (kg)", min_value=0, step=10)
            with col_in3: re_w = st.number_input("재활용 (kg)", min_value=0, step=10)
            
            if st.form_submit_button("본사로 수거량 전송하기", type="primary", use_container_width=True):
                if food_w > 0 or biz_w > 0 or re_w > 0:
                    new_data = {
                        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "학교명": target, "학생수": STUDENT_COUNTS[target], "수거업체": "하영자원(본사 직영)",
                        "음식물(kg)": food_w, "재활용(kg)": re_w, "사업장(kg)": biz_w,
                        "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "대기"
                    }
                    save_data(new_data)
                    st.success(f"✅ {target} 수거 실적이 초단위 시간과 함께 기록되었습니다.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")