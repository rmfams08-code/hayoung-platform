# 이 코드는 파이썬으로 웹 화면을 만들어주는 '스트림릿(Streamlit)' 라이브러리를 사용합니다.
# 실행 방법: cd Desktop\하영자원 입력 후 python -m streamlit run hayoung_platform.py 실행


import streamlit as st
import pandas as pd
import time
import io
import random
from datetime import datetime

# ==========================================
# 0. 관리 대상 학교 목록 (가나다순 자동 정렬 적용)
# ==========================================
SCHOOL_LIST = sorted([
    "화성초등학교", "동탄중학교", "수원고등학교", "안양남초등학교", "평촌초등학교", 
    "부림초등학교", "부흥중학교", "덕천초등학교", "서초고등학교", "구암고등학교", 
    "국사봉중학교", "당곡고등학교", "당곡중학교", "서울공업고등학교", "강남중학교", 
    "영남중학교", "선유고등학교", "신목고등학교", "고척고등학교", "구현고등학교", 
    "안산국제비지니스고등학교", "안산고등학교", "송호고등학교", "비봉고등학교"
])

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
    .mobile-app-header { background-color: #202124; color: #ffffff !important; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; }
    .safety-box { background-color: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; color: #2e7d32; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 데이터 영구 저장 및 실시간 연산 (26년 1월 일일 데이터 자동 생성)
# ==========================================
DB_FILE = "hayoung_data_v3.csv" # 파일명을 바꿔서 새 파일을 강제로 생성합니다.

def load_data():
    try:
        return pd.read_csv(DB_FILE)
    except FileNotFoundError:
        cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
        sample_data = []
        # 26년 1월 1일부터 31일까지 매일 데이터 생성 (주말 제외 등 현실적인 로직 반영)
        for day in range(1, 32):
            if day % 7 in [3, 4]: continue # 임의로 주말 휴무 처리
            for school in ["화성초등학교", "동탄중학교", "강남중학교", "안양남초등학교"]:
                hour = random.randint(8, 15)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                sample_data.append({
                    "날짜": f"2026-01-{day:02d} {hour:02d}:{minute:02d}:{second:02d}",
                    "학교명": school, "수거업체": "하영자원(본사 직영)",
                    "음식물(kg)": random.randint(50, 180), "재활용(kg)": random.randint(20, 80), "사업장(kg)": random.randint(10, 50),
                    "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "정산완료"
                })
        df = pd.DataFrame(sample_data, columns=cols)
        df.to_csv(DB_FILE, index=False)
        return df

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

df_all = load_data()

# 실시간 단가 및 ESG 계산 연동
if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].astype(str).str[:7]
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2
else:
    cols = ["날짜", "학교명", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "탄소감축량(kg)"]
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
    st.info("💡 **데이터 동기화 (Sync) 완벽 지원**\n\n모든 정보는 실시간으로 공유됩니다.")

# ==========================================
# 4. 보안 엑셀 보고서 생성 함수 (전문가 양식 적용)
# ==========================================
def create_secure_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 데이터는 3번째 줄부터 쓰기
        df.to_excel(writer, index=False, sheet_name='실적보고서', startrow=2)
        workbook = writer.book
        worksheet = writer.sheets['실적보고서']
        
        # 실무 양식처럼 상단에 굵고 큰 제목 추가
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        worksheet.merge_range(0, 0, 1, len(df.columns)-1, f"■ {title} ■", title_format)
        
        # 컬럼 너비 자동 조절
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 15)
            
        # [핵심 보안] 엑셀 시트 보호 (비밀번호 설정)
        worksheet.protect('hayoung1234', {'objects': True, 'scenarios': True, 'format_cells': False, 'sort': True})
    return output.getvalue()

# ==========================================
# [모드 1] 관리자 (본사) 모드
# ==========================================
if role == "🏢 관리자 (본사 관제)":
    st.title("🏢 본사 통합 관제 및 정산 센터")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 총 수거</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 총 수거</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 총 수거</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 누적 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,} 원</div></div>', unsafe_allow_html=True)
    with col5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검 완료율</div><div class="metric-value-total" style="color:#fbbc05;">100 %</div></div>', unsafe_allow_html=True)

    # 학교별 조회 탭이 추가된 7개 탭
    st.subheader("📑 통합 및 개별 정산 시트")
    tab_total, tab_school_view, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs([
        "전체 통합 정산", "🏫 학교별 상세조회", "음식물 내역", "사업장 내역", "재활용 내역", "📍 실시간 관제", "🤝 외주업체 현황"
    ])
    
    with tab_total:
        st.dataframe(df_all[['날짜', '학교명', '수거업체', '최종정산액', '상태']], use_container_width=True)
        col_t1, col_t2 = st.columns(2)
        with col_t1: st.button("🚀 통합 세금계산서 일괄 전송", type="primary", use_container_width=True)
        with col_t2: st.button("🔗 올바로시스템 전자인계서 일괄발송", type="primary", use_container_width=True)
        
    with tab_school_view:
        st.write("🔎 **특정 학교의 누적 실적을 필터링하여 조회합니다.**")
        admin_target_school = st.selectbox("조회할 학교를 선택하세요", ["전체보기"] + SCHOOL_LIST)
        if admin_target_school == "전체보기":
            st.dataframe(df_all, use_container_width=True)
        else:
            filtered_df = df_all[df_all['학교명'] == admin_target_school]
            st.dataframe(filtered_df, use_container_width=True)
            if not filtered_df.empty:
                st.bar_chart(filtered_df.set_index('날짜')[['음식물(kg)', '재활용(kg)', '사업장(kg)']])
                
    with tab_food: st.dataframe(df_all[['날짜', '학교명', '음식물(kg)', '음식물비용']], use_container_width=True)
    with tab_biz: st.dataframe(df_all[['날짜', '학교명', '사업장(kg)', '사업장비용']], use_container_width=True)
    with tab_recycle: st.dataframe(df_all[['날짜', '학교명', '재활용(kg)', '재활용수익']], use_container_width=True)
    with tab_map: st.map(pd.DataFrame({'lat': [37.20, 37.25], 'lon': [127.05, 127.10]}))
    with tab_sub: st.error("🔔 'B자원' 업체와의 수거 위탁 계약 만료가 30일 앞으로 다가왔습니다.")

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
            <h4 style="margin: 0; margin-bottom: 10px;">🌱 우리 학교 ESG 환경 기여도 (탄소배출 저감 효과)</h4>
            <h2>누적 CO₂ 감축량: {total_co2_school:,.1f} kg (🌲 소나무 {tree_count_school}그루 식재 효과)</h2>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 폐기물 배출량 통계 분석")
        st.bar_chart(df_school.set_index('날짜')[['음식물(kg)', '사업장(kg)', '재활용(kg)']])

        st.write("---")
        st.subheader("🖨️ 행정 증빙 서류 자동 출력 및 올바로시스템 연동 (위변조 방지 엑셀)")
        
        # 다운로드 버튼들 실제 작동화
        col_doc1, col_doc2, col_doc3 = st.columns(3)
        with col_doc1:
            st.download_button("📄 음식물/사업장 실적보고서 다운로드", data=create_secure_excel(df_school[['날짜','학교명','음식물(kg)','사업장(kg)','상태']], "폐기물 실적보고서(법정양식)"), file_name=f"{school}_실적보고서.xlsx", use_container_width=True)
        with col_doc2:
            st.download_button("📄 재활용 수익 상계처리 증빙서", data=create_secure_excel(df_school[['날짜','학교명','재활용(kg)','재활용수익','상태']], "재활용 상계처리 증빙서류"), file_name=f"{school}_상계증빙.xlsx", use_container_width=True)
        with col_doc3:
            st.button("📄 수거업체 안전관리 점검결과표 (PDF)", use_container_width=True) # 안전관리는 엑셀보단 PDF 폼 유지

        st.write("") 
        col_doc4, col_doc5, col_doc6 = st.columns(3)
        # 월별 통계 그룹화 데이터
        monthly_df = df_school.groupby('월별')[['음식물(kg)', '사업장(kg)', '재활용(kg)']].sum().reset_index()
        with col_doc4:
            st.download_button("📄 월별 수거량 통계 (항목별 분리)", data=create_secure_excel(monthly_df, "월별 수거량 통계 분석표"), file_name=f"{school}_월별통계.xlsx", use_container_width=True)
        with col_doc5:
            st.download_button("📄 [연말 결산] 교육청 제출용 종합 보고서", data=create_secure_excel(df_school, "연말 결산 종합 보고서(교육청 제출용)"), file_name=f"{school}_연말결산.xlsx", use_container_width=True)
        with col_doc6:
            st.download_button("📄 [ESG] 탄소배출 저감 성과 보고서", data=create_secure_excel(df_school[['날짜', '학교명', '재활용(kg)', '탄소감축량(kg)']], "ESG 탄소저감 환경성과 보고서"), file_name=f"{school}_ESG성과.xlsx", use_container_width=True)

        st.write("")
        st.markdown("<h5 style='color:#1a73e8; font-weight:bold;'>⚡ 데이터 플랫폼 특화 기능 (자동화)</h5>", unsafe_allow_html=True)
        col_doc7, col_doc8 = st.columns(2)
        with col_doc7:
            st.download_button("📥 품목별 정산명세서 일괄 다운로드", data=create_secure_excel(df_school, "품목별 통합 정산명세서"), file_name=f"{school}_통합정산.xlsx", use_container_width=True)
        with col_doc8:
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
                        # [핵심] 초정밀 시간 기록
                        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "학교명": target, "수거업체": "하영자원(본사 직영)",
                        "음식물(kg)": food_w, "재활용(kg)": re_w, "사업장(kg)": biz_w,
                        "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "대기"
                    }
                    save_data(new_data)
                    st.success(f"✅ {target} 수거 실적이 초단위 시간과 함께 기록되었습니다.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")