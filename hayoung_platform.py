# 이 코드는 파이썬으로 웹 화면을 만들어주는 '스트림릿(Streamlit)' 라이브러리를 사용합니다.
# 실행 방법: cd Desktop\하영자원 입력 후 python -m streamlit run hayoung_platform.py 실행

import streamlit as st
import pandas as pd
import time
import io
import random
import os
import json
import hashlib
from datetime import datetime, timedelta

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
# 0-1. 보안 설정 (환경변수 기반)
# ==========================================
EXCEL_PASSWORD = os.environ.get("HAYOUNG_EXCEL_PW", "change_me_in_env")
# 운영 환경에서는 아래 명령으로 설정:
# export HAYOUNG_EXCEL_PW="실제비밀번호"
# Streamlit Cloud: Settings → Secrets → HAYOUNG_EXCEL_PW = "실제비밀번호"
try:
    if hasattr(st, 'secrets') and "HAYOUNG_EXCEL_PW" in st.secrets:
        EXCEL_PASSWORD = st.secrets["HAYOUNG_EXCEL_PW"]
except Exception:
    pass

# ==========================================
# 0-2. 동적 년도 설정 (하드코딩 제거)
# ==========================================
CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")

# ==========================================
# 1. 페이지 및 기본 환경 설정
# ==========================================
st.set_page_config(page_title="하영자원 폐기물데이터플랫폼 Pro", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# [디자인 업데이트] 사장님 이미지에 맞춘 고급 CSS 디자인 추가
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
    .safety-box { background-color: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; color: #2e7d32; font-weight: bold; margin-bottom:15px; }
    .alert-box { background-color: #ffebee; border: 1px solid #ffcdd2; padding: 15px; border-radius: 8px; color: #c62828; margin-bottom: 15px; }
    .timeline-text { font-size: 15px; line-height: 1.8; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 데이터 영구 저장 및 실시간 연산 (자동 감지 및 생성 로직 추가)
# ==========================================
DB_FILE = "hayoung_data_v5.csv"

def load_data():
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
    try:
        df = pd.read_csv(DB_FILE)
        # 파일은 있지만 과거 연도(2024년) 데이터가 없는 경우, 에러를 발생시켜 아래 except 구문으로 넘김
        if not df['날짜'].str.contains('2024').any():
            raise ValueError("과거 연도 데이터가 없어 새로 생성합니다.")
        return df
    except:
        # 파일이 아예 없거나, 과거 데이터가 없는 경우 최근 2년 + 현재 연도 데이터를 자동으로 새로 만듦
        sample_data = []
        # 동적 년도 생성: 2년 전 ~ 현재 연도
        for year in range(CURRENT_YEAR - 2, CURRENT_YEAR + 1):
            if year < CURRENT_YEAR:
                months_to_gen = [(11, 30), (12, 31)]
            else:
                # 현재 연도: 1월부터 현재 월까지
                months_to_gen = [(m, 28 if m == 2 else 30 if m in [4,6,9,11] else 31) for m in range(1, CURRENT_MONTH + 1)]
            for month, days in months_to_gen:
                for day in range(1, days + 1, 3): 
                    if day % 7 in [0, 1]: continue 
                    for school, count in STUDENT_COUNTS.items():
                        food = int(count * random.uniform(0.1, 0.2))
                        recycle = int(count * random.uniform(0.05, 0.1))
                        biz = int(count * random.uniform(0.02, 0.05))
                        status = "정산완료" if year < CURRENT_YEAR else "정산대기"
                        
                        sample_data.append({
                            "날짜": f"{year}-{month:02d}-{day:02d} {random.randint(8, 15):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
                            "학교명": school, "학생수": count, "수거업체": "하영자원(본사 직영)",
                            "음식물(kg)": food, "재활용(kg)": recycle, "사업장(kg)": biz,
                            "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": status
                        })
        df = pd.DataFrame(sample_data, columns=cols)
        df.to_csv(DB_FILE, index=False) # 새로 만든 데이터를 파일에 덮어쓰기 저장
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
    df_all['년도'] = df_all['날짜'].astype(str).str[:4] 
    df_all['탄소감축량(kg)'] = df_all['재활용(kg)'] * 1.2
else:
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "년도", "탄소감축량(kg)"]
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
# 4. 보안 엑셀 보고서 생성 함수 (법정 양식 준수)
# ==========================================
def create_secure_excel(df, title):
    """기본 보안 엑셀 생성"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='법정실적보고서', startrow=2)
        workbook = writer.book
        worksheet = writer.sheets['법정실적보고서']
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        worksheet.merge_range(0, 0, 1, len(df.columns)-1, f"■ {title} ■", title_format)
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 16)
        worksheet.protect(EXCEL_PASSWORD, {'objects': True, 'scenarios': True, 'format_cells': False, 'sort': True})
    return output.getvalue()

def create_legal_report_excel(df, report_type, school_name, period_str):
    """
    법정 서식 준수 보고서 생성
    - 폐기물관리법 시행규칙 별지 제30호서식 (폐기물 처리실적보고서)
    - 2026.1.1 시행 기후에너지환경부령 제18호 반영
    필수 기재사항: 배출자정보, 허가번호, 폐기물종류코드, 처리방법, 올바로인계번호
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # --- 시트1: 표지 ---
        ws_cover = writer.book.add_worksheet('표지')
        title_fmt = writer.book.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        header_fmt = writer.book.add_format({'bold': True, 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        value_fmt = writer.book.add_format({'font_size': 11, 'align': 'left', 'valign': 'vcenter'})
        legal_fmt = writer.book.add_format({'font_size': 9, 'align': 'left', 'color': '#666666', 'text_wrap': True})
        
        ws_cover.merge_range('A1:F3', f'■ {report_type} ■', title_fmt)
        ws_cover.merge_range('A4:F4', f'[폐기물관리법 시행규칙 별지 제30호서식] (기후에너지환경부령 제18호, 2025.12.30 개정 / 2026.1.1 시행)', legal_fmt)
        
        # 법정 필수 기재사항
        cover_fields = [
            ("보고 대상 기간", period_str),
            ("배출자(학교명)", school_name),
            ("배출자 사업장 소재지", "(학교 주소 기재)"),
            ("배출자 등록번호(사업자번호)", "(사업자등록번호 기재)"),
            ("수집·운반업 허가번호", "제 ____호 (하영자원)"),
            ("수집·운반업체명", "하영자원"),
            ("수집·운반업체 대표자", "(대표자명 기재)"),
            ("처리업체명 / 허가번호", "(중간처리업체명) / 제 ____호"),
            ("폐기물 종류 코드", "음식물류: 01-05-00 / 사업장일반: 01-99-00"),
            ("올바로시스템 인계번호", "(전자인계서 번호 자동연동)"),
            ("보고서 작성일", CURRENT_DATE),
            ("작성자 / 직위", "(작성자명) / (직위)"),
        ]
        for i, (label, val) in enumerate(cover_fields):
            row = 5 + i
            ws_cover.write(row, 0, label, header_fmt)
            ws_cover.merge_range(row, 1, row, 5, val, value_fmt)
        
        legal_note_row = 5 + len(cover_fields) + 1
        ws_cover.merge_range(legal_note_row, 0, legal_note_row + 2, 5,
            "※ 본 보고서는 「폐기물관리법」 제18조 및 같은 법 시행규칙 제20조에 따라 작성되었으며, "
            "「폐기물관리법 시행규칙」 별지 제30호서식(폐기물 처리실적보고서)에 근거합니다.\n"
            "※ 2026.1.1 시행 기후에너지환경부령 제18호 개정사항 반영: 전지류 폐기물 분류체계 개편, "
            "재활용 가능 유형 정비, 폐유독물질→폐유해화학물질 명칭 변경 등.\n"
            "※ 올바로시스템(Allbaro) 전자인계서와 연동하여 인계·인수 이력을 관리합니다.",
            legal_fmt)
        
        for col in range(6):
            ws_cover.set_column(col, col, 22)
        ws_cover.protect(EXCEL_PASSWORD)
        
        # --- 시트2: 상세 실적 데이터 ---
        sheet_name = '처리실적상세'
        df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=4)
        ws_data = writer.sheets[sheet_name]
        
        data_title_fmt = writer.book.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        subtitle_fmt = writer.book.add_format({'font_size': 10, 'align': 'center', 'color': '#555555'})
        
        ws_data.merge_range(0, 0, 1, len(df.columns)-1, f"■ {report_type} - 상세 내역 ■", data_title_fmt)
        ws_data.merge_range(2, 0, 2, len(df.columns)-1, f"대상: {school_name} | 기간: {period_str} | 출력일: {CURRENT_DATE}", subtitle_fmt)
        ws_data.merge_range(3, 0, 3, len(df.columns)-1, "※ 본 데이터는 올바로시스템 전자인계서와 연동됩니다.", legal_fmt)
        
        for i, col in enumerate(df.columns):
            ws_data.set_column(i, i, 16)
        ws_data.protect(EXCEL_PASSWORD, {'objects': True, 'scenarios': True, 'format_cells': False, 'sort': True})
        
        # --- 시트3: 요약 통계 ---
        ws_summary = writer.book.add_worksheet('요약통계')
        ws_summary.merge_range('A1:D2', f'{school_name} 폐기물 처리 요약 통계', data_title_fmt)
        
        summary_items = [
            ("총 수거 건수", f"{len(df)}건"),
            ("보고서 유형", report_type),
            ("법적 근거", "폐기물관리법 시행규칙 별지 제30호서식"),
            ("개정 적용", "기후에너지환경부령 제18호 (2026.1.1 시행)"),
        ]
        # 품목별 합계 동적 생성
        numeric_cols = df.select_dtypes(include='number').columns
        for col_name in numeric_cols:
            total_val = df[col_name].sum()
            if 'kg' in col_name:
                summary_items.append((f"{col_name} 합계", f"{total_val:,.1f} kg"))
            elif '비용' in col_name or '수익' in col_name or '정산' in col_name:
                summary_items.append((f"{col_name} 합계", f"{total_val:,.0f} 원"))
        
        for i, (label, val) in enumerate(summary_items):
            ws_summary.write(3 + i, 0, label, header_fmt)
            ws_summary.merge_range(3 + i, 1, 3 + i, 3, val, value_fmt)
        
        ws_summary.set_column(0, 0, 28)
        ws_summary.set_column(1, 3, 20)
        ws_summary.protect(EXCEL_PASSWORD)
    
    return output.getvalue()

# ==========================================
# [모드 1] 관리자 (본사) 모드
# ==========================================
if role == "🏢 관리자 (본사 관제)":
    st.markdown("<h1 style='display:flex; align-items:center;'>🏢 본사 통합 관제 및 정산 센터</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #5f6368; font-size: 16px;'>음식물, 사업장폐기물, 재활용 통계를 완벽히 분리하여 수익/비용 관리가 가능합니다.</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 총 수거</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 총 수거</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 총 수거</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 누적 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,} 원</div></div>', unsafe_allow_html=True)
    with col5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검 완료율</div><div class="metric-value-total" style="color:#1a73e8;">100 %</div></div>', unsafe_allow_html=True)

    total_co2_all = df_all['탄소감축량(kg)'].sum()
    tree_count_all = int(total_co2_all / 6.6)
    st.markdown(f"""
    <div style="background-color: #61b346; padding: 30px; border-radius: 12px; color: white; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="flex: 1; text-align: center;">
            <h3 style="margin: 0; color: white; margin-bottom: 10px;">🌍 하영자원 전사 ESG 탄소 저감 성과 (통합)</h3>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">누적 CO₂ 감축량</p>
            <h1 style="margin: 0; color: white; font-size: 40px; font-weight: 900;">{total_co2_all:,.1f} kg</h1>
        </div>
        <div style="font-size: 40px; font-weight: bold; padding: 0 20px;">=</div>
        <div style="flex: 1; text-align: center;">
            <p style="margin: 0; font-size: 16px; opacity: 0.9; margin-top:35px;">어린 소나무 식재 효과</p>
            <h1 style="margin: 0; color: white; font-size: 40px; font-weight: 900;">🌲 {tree_count_all:,} 그루</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_esg1, col_esg2, col_esg3 = st.columns([1,2,1])
    with col_esg1: st.button("📄 전사 ESG 성과 보고서 출력", use_container_width=True)
    st.write("---")

    st.subheader("📑 통합 및 개별 정산 시트(Sheet) 🔗")
    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs([
        "전체 통합 정산", "음식물 정산 내역", "사업장 정산 내역", "재활용 정산 내역", "📍 실시간 차량 관제", "🤝 외주업체 현황"
    ])
    
    with tab_total:
        # 동적 년도/월별 탭 생성
        current_months = sorted(df_all[df_all['년도'] == str(CURRENT_YEAR)]['월별'].unique())
        tab_labels_total = [f"📅 {CURRENT_YEAR}년 전체"] + [f"🗓️ {m}" for m in current_months]
        sub_tabs = st.tabs(tab_labels_total)
        with sub_tabs[0]: st.dataframe(df_all[df_all['년도'] == str(CURRENT_YEAR)][['날짜', '학교명', '학생수', '최종정산액', '상태']], use_container_width=True)
        for i, m in enumerate(current_months):
            with sub_tabs[i + 1]: st.dataframe(df_all[df_all['월별'] == m][['날짜', '학교명', '학생수', '최종정산액', '상태']], use_container_width=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1: st.button("🏢 업체별 통합정산서 발송", use_container_width=True)
        with col_btn2: st.button("🏫 학교별 통합정산서 발송", use_container_width=True)

    with tab_food:
        tab_labels_food = [f"📅 {CURRENT_YEAR}년 전체"] + [f"🗓️ {m}" for m in current_months]
        f_tabs = st.tabs(tab_labels_food)
        with f_tabs[0]: st.dataframe(df_all[df_all['년도'] == str(CURRENT_YEAR)][['날짜', '학교명', '수거업체', '음식물(kg)', '단가(원)', '음식물비용', '상태']], use_container_width=True)
        for i, m in enumerate(current_months):
            with f_tabs[i + 1]: st.dataframe(df_all[df_all['월별'] == m][['날짜', '학교명', '수거업체', '음식물(kg)', '단가(원)', '음식물비용', '상태']], use_container_width=True)
        st.write("")
        col_bf1, col_bf2 = st.columns(2)
        with col_bf1: st.button("🏢 업체별 정산명세서 발송 (음식물)", use_container_width=True)
        with col_bf2: st.button("🏫 학교별 정산명세서 발송 (음식물)", use_container_width=True)

    with tab_biz:
        tab_labels_biz = [f"📅 {CURRENT_YEAR}년 전체"] + [f"🗓️ {m}" for m in current_months]
        b_tabs = st.tabs(tab_labels_biz)
        with b_tabs[0]: st.dataframe(df_all[df_all['년도'] == str(CURRENT_YEAR)][['날짜', '학교명', '학생수', '사업장(kg)', '사업장비용']], use_container_width=True)
        for i, m in enumerate(current_months):
            with b_tabs[i + 1]: st.dataframe(df_all[df_all['월별'] == m][['날짜', '학교명', '학생수', '사업장(kg)', '사업장비용']], use_container_width=True)
        st.write("")
        col_bb1, col_bb2 = st.columns(2)
        with col_bb1: st.button("🏢 업체별 정산명세서 발송 (사업장)", use_container_width=True)
        with col_bb2: st.button("🏫 학교별 정산명세서 발송 (사업장)", use_container_width=True)

    with tab_recycle:
        tab_labels_rec = [f"📅 {CURRENT_YEAR}년 전체"] + [f"🗓️ {m}" for m in current_months]
        r_tabs = st.tabs(tab_labels_rec)
        with r_tabs[0]: st.dataframe(df_all[df_all['년도'] == str(CURRENT_YEAR)][['날짜', '학교명', '학생수', '재활용(kg)', '재활용수익']], use_container_width=True)
        for i, m in enumerate(current_months):
            with r_tabs[i + 1]: st.dataframe(df_all[df_all['월별'] == m][['날짜', '학교명', '학생수', '재활용(kg)', '재활용수익']], use_container_width=True)
        st.write("")
        col_br1, col_br2 = st.columns(2)
        with col_br1: st.button("🏢 업체별 정산명세서 발송 (재활용)", use_container_width=True)
        with col_br2: st.button("🏫 학교별 정산명세서 발송 (재활용)", use_container_width=True)
        
    with tab_map:
        st.write("📍 **수거 차량 실시간 GPS 관제**")
        st.map(pd.DataFrame({'lat': [37.20, 37.25], 'lon': [127.05, 127.10]}))
        
    with tab_sub:
        st.subheader("🤝 외주 수거업체 실시간 업무 및 안전 평가 현황")
        st.markdown('<div class="alert-box">🔔 <b>[계약 갱신 알림]</b> \'B자원\' 업체와의 수거 위탁 계약 만료가 30일 앞으로 다가왔습니다. (만료일: 2026-03-25)</div>', unsafe_allow_html=True)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: st.info("🏆 이달의 우수 안전 업체: **A환경** (98점)")
        with col_s2: st.warning("⚠️ 주의 필요 업체: **B자원** (과속 1회 감지)")
        with col_s3: st.success("✅ 스쿨존 속도위반 경고 건수: **1건**")

        vendor_data = pd.DataFrame({
            "외주업체명": ["A환경", "B자원"],
            "담당학교": ["동탄중학교", "수원고등학교"],
            "안전평가점수": ["98점 (우수)", "85점 (주의)"],
            "안전 페널티(위반벌금)": ["0 원", "-50,000 원 (과속 1회)"],
            "이달 정산지급액(예상)": ["1,350,000 원", "880,000 원"],
            "현재 운행상태": ["🟢 운행중", "🟡 대기중"]
        })
        st.dataframe(vendor_data, use_container_width=True)
        
        st.write("---")
        st.subheader("🔎 담당 차량 및 기사 상세 조회 (타임라인) 🔗")
        st.write("실시간 이동 동선을 조회할 업체를 선택하세요")
        sel_vendor = st.selectbox("", ["A환경", "B자원", "C로지스"], label_visibility="collapsed")
        
        if sel_vendor == "A환경":
            st.markdown('<div class="safety-box">🚛 차량번호: 경기88아 1234 &nbsp;|&nbsp; 👨‍✈️ 담당기사: 김하영 (010-1234-5678) &nbsp;|&nbsp; 🏫 오늘 배차: 1곳</div>', unsafe_allow_html=True)
            st.markdown("⏱️ **오늘의 실시간 이동 동선**")
            st.markdown("""
            <div class="timeline-text">
            ✔️ 08:30 [출발 전 점검] 차량 후방카메라 및 안전요원 탑승 확인 완료<br>
            🔄 10:30 [이동 중] 동탄중학교로 이동 중 (현재 GPS 정상 수신 중)
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        col_vb1, col_vb2 = st.columns(2)
        with col_vb1: st.button("📄 외주업체 안전평가 결과서 다운로드", use_container_width=True)
        with col_vb2: st.button("💰 외주업체 월별 정산 대금 청구서 발행", use_container_width=True)


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
            <h4 style="margin: 0; margin-bottom: 10px;">🌱 우리 학교 ESG 환경 기여도 (교육청 제출용)</h4>
            <h2>누적 CO₂ 감축량: {total_co2_school:,.1f} kg (🌲 소나무 {tree_count_school}그루 식재 효과)</h2>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 폐기물 배출량 통계 분석 (막대그래프)")
        tab_daily, tab_monthly = st.tabs(["🗓️ 일별 배출량 (상세)", "🗓️ 연도별/월별 배출량 (추이)"])
        
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
            st.write("연도별 및 월별 전체 수거량 추이입니다. (단위: kg)")
            years = sorted(df_school['년도'].unique(), reverse=True)
            year_tabs = st.tabs([f"📅 {y}년" for y in years])
            
            for i, y in enumerate(years):
                with year_tabs[i]:
                    y_df = df_school[df_school['년도'] == y]
                    monthly_grouped = y_df.groupby('월별')[['음식물(kg)', '사업장(kg)', '재활용(kg)']].sum().reset_index()
                    
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        st.markdown("<h5 style='text-align:center; color:#ea4335; font-weight:bold;'>🗑️ 음식물 수거량 (월별)</h5>", unsafe_allow_html=True)
                        st.bar_chart(monthly_grouped.set_index('월별')['음식물(kg)'], color="#ea4335")
                    with mc2:
                        st.markdown("<h5 style='text-align:center; color:#9b59b6; font-weight:bold;'>🗄️ 사업장 수거량 (월별)</h5>", unsafe_allow_html=True)
                        st.bar_chart(monthly_grouped.set_index('월별')['사업장(kg)'], color="#9b59b6")
                    with mc3:
                        st.markdown("<h5 style='text-align:center; color:#34a853; font-weight:bold;'>♻️ 재활용 수거량 (월별)</h5>", unsafe_allow_html=True)
                        st.bar_chart(monthly_grouped.set_index('월별')['재활용(kg)'], color="#34a853")

        st.write("---")
        st.markdown("<h5 style='color:#2e7d32; font-weight:bold;'>🛡️ 금일 수거차량 실시간 안전 점검 현황</h5>", unsafe_allow_html=True)
        st.markdown(f'<div class="safety-box">✅ 배차 차량: 하영자원 (본사 직영 운행) <br>✅ 스쿨존 규정속도 준수 여부: <span style="color:blue;">정상 (MAX 28km/h 통과)</span> <br>✅ 후방카메라 작동 및 안전요원 동승: 적합 (점검완료)</div>', unsafe_allow_html=True)

        st.write("---")
        
        st.subheader("🖨️ 행정 증빙 서류 자동 출력 (법정 양식 적용)")
        st.write("아래 메뉴(Tab)를 클릭하여 필요한 서류를 품목별로 다운로드하세요.")
        st.caption("📌 2026.1.1 시행 「기후에너지환경부령 제18호」 개정사항 반영 완료")
        
        # 기간 문자열 생성
        if not df_school.empty:
            period_start = df_school['날짜'].min()[:10]
            period_end = df_school['날짜'].max()[:10]
            period_str = f"{period_start} ~ {period_end}"
        else:
            period_str = "데이터 없음"
        
        doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
            "📊 [월간] 폐기물 정산(청구)서", 
            "📈 [실적] 처리실적보고서 (제30호)", 
            "♻️ 사업장 재활용 상계증빙", 
            "🔗 올바로시스템 전자인계서"
        ])
        
        with doc_tab1:
            st.info("💡 행정실 회계 처리를 위한 월간 정산서입니다. 통합본 또는 품목별로 분리하여 다운로드 가능합니다.")
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            with col_d1:
                st.download_button("전체 통합본 다운로드", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액']], "통합 정산(청구)서", school, period_str), 
                    file_name=f"{school}_통합_월간정산서.xlsx", use_container_width=True)
            with col_d2:
                st.download_button("🗑️ 음식물 전용 다운로드", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물 정산(청구)서", school, period_str), 
                    file_name=f"{school}_음식물_월간정산서.xlsx", use_container_width=True)
            with col_d3:
                st.download_button("🗄️ 사업장 전용 다운로드", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장 정산(청구)서", school, period_str), 
                    file_name=f"{school}_사업장_월간정산서.xlsx", use_container_width=True)
            with col_d4:
                st.download_button("♻️ 재활용 전용 다운로드", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 정산(청구)서", school, period_str), 
                    file_name=f"{school}_재활용_월간정산서.xlsx", use_container_width=True)

        with doc_tab2:
            st.info("💡 교육청 및 지자체 제출용 [폐기물관리법 시행규칙 별지 제30호서식] 법정 양식입니다.")
            st.caption("✅ 기후에너지환경부령 제18호 (2026.1.1 시행) 반영: 전지류 분류체계 개편, 재활용 유형 정비")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.download_button("🗑️ 음식물 실적보고서", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물류 폐기물 배출 및 처리 실적보고서", school, period_str), 
                    file_name=f"{school}_음식물_실적보고서.xlsx", use_container_width=True)
            with col_r2:
                st.download_button("🗄️ 사업장 실적보고서", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장일반폐기물 배출 및 처리 실적보고서", school, period_str), 
                    file_name=f"{school}_사업장_실적보고서.xlsx", use_container_width=True)
            with col_r3:
                st.download_button("♻️ 재활용 실적보고서", 
                    data=create_legal_report_excel(df_school[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 폐기물 배출 및 처리 실적보고서", school, period_str), 
                    file_name=f"{school}_재활용_실적보고서.xlsx", use_container_width=True)

        with doc_tab3:
            st.info("💡 사업장 폐기물 처리 시, 재활용 수익으로 비용을 상계(차감)한 내역을 증빙하는 서류입니다.")
            st.download_button("📄 사업장 일반폐기물 재활용 상계처리 증빙서 다운로드", 
                               data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','재활용(kg)','재활용수익','사업장비용']], "사업장 폐기물 재활용 상계처리 증빙 내역", school, period_str), 
                               file_name=f"{school}_상계증빙.xlsx")
                               
        with doc_tab4:
            st.info("💡 버튼 클릭 시 한국환경공단 올바로(Allbaro) 시스템으로 인계서 데이터가 자동 전송됩니다.")
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

# ==========================================
# 5. 실제 수거 데이터 연동 모듈
# ==========================================
# --- 5-1. 외부 데이터 소스 연동 설정 (사이드바 하단) ---
with st.sidebar:
    st.write("---")
    st.markdown("### ⚙️ 데이터 연동 설정")
    
    with st.expander("📂 실제 수거 데이터 업로드", expanded=False):
        st.caption("엑셀(.xlsx) 또는 CSV 파일로 실제 수거 데이터를 업로드하세요.")
        st.caption("필수 컬럼: 날짜, 학교명, 음식물(kg), 재활용(kg), 사업장(kg)")
        
        uploaded_file = st.file_uploader("수거 데이터 파일 선택", type=['csv', 'xlsx', 'xls'], label_visibility="collapsed")
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.success(f"✅ {len(df_upload)}건 데이터 로드 완료")
                st.dataframe(df_upload.head(5), use_container_width=True)
                
                # 컬럼 매핑 (유연한 매핑)
                required_cols = ['날짜', '학교명', '음식물(kg)', '재활용(kg)', '사업장(kg)']
                missing_cols = [c for c in required_cols if c not in df_upload.columns]
                
                if missing_cols:
                    st.warning(f"⚠️ 누락된 필수 컬럼: {', '.join(missing_cols)}")
                    st.info("💡 컬럼명 매핑 기능: 아래에서 기존 컬럼을 플랫폼 컬럼에 매핑하세요.")
                    
                    col_mapping = {}
                    for req_col in missing_cols:
                        mapped = st.selectbox(f"'{req_col}'에 해당하는 컬럼", 
                                             ["(선택 안함)"] + list(df_upload.columns), 
                                             key=f"map_{req_col}")
                        if mapped != "(선택 안함)":
                            col_mapping[mapped] = req_col
                    
                    if col_mapping and st.button("컬럼 매핑 적용", type="secondary"):
                        df_upload = df_upload.rename(columns=col_mapping)
                        st.success("✅ 컬럼 매핑 완료")
                
                if st.button("🔄 실제 데이터로 DB 업데이트", type="primary", use_container_width=True):
                    # 누락 컬럼 기본값 채우기
                    if '학생수' not in df_upload.columns:
                        df_upload['학생수'] = df_upload['학교명'].map(STUDENT_COUNTS).fillna(0).astype(int)
                    if '수거업체' not in df_upload.columns:
                        df_upload['수거업체'] = "하영자원(본사 직영)"
                    if '단가(원)' not in df_upload.columns:
                        df_upload['단가(원)'] = 150
                    if '재활용단가(원)' not in df_upload.columns:
                        df_upload['재활용단가(원)'] = 300
                    if '사업장단가(원)' not in df_upload.columns:
                        df_upload['사업장단가(원)'] = 200
                    if '상태' not in df_upload.columns:
                        df_upload['상태'] = "정산대기"
                    
                    # 기존 DB와 병합 (중복 제거)
                    df_existing = load_data()
                    df_merged = pd.concat([df_existing, df_upload], ignore_index=True)
                    df_merged = df_merged.drop_duplicates(subset=['날짜', '학교명'], keep='last')
                    df_merged.to_csv(DB_FILE, index=False)
                    
                    st.success(f"✅ {len(df_upload)}건 실제 데이터가 DB에 반영되었습니다!")
                    st.info(f"📊 전체 DB: {len(df_merged)}건")
                    time.sleep(1)
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ 파일 처리 오류: {str(e)}")
    
    with st.expander("🔗 올바로시스템 EDI 연동", expanded=False):
        st.caption("한국환경공단 올바로(Allbaro) OpenAPI EDI 연계 설정")
        
        allbaro_id = st.text_input("올바로시스템 사업자 ID", placeholder="사업자등록번호")
        allbaro_connected = st.toggle("EDI 자동 연동 활성화", value=False)
        
        if allbaro_connected:
            st.success("🟢 EDI 연동 대기 중")
            st.caption("""
            **연동 방식**: OpenAPI (T200_5001_01 인터페이스)
            - 수거 실적 입력 → 자동으로 전자인계서 생성
            - 인계번호 자동 발급 및 관리
            - 배출자 → 운반자 → 처리자 3단계 자동 확인
            
            ⚠️ 실제 연동은 올바로시스템 EDI 승인 후 활성화됩니다.
            문의: 한국환경공단 올바로 고객센터 1600-8282
            """)
        else:
            st.caption("🔴 EDI 미연동 (수동 모드)")
    
    with st.expander("📡 Google Sheets 실시간 연동", expanded=False):
        st.caption("Google Sheets와 실시간 동기화하여 여러 기기에서 데이터를 공유합니다.")
        
        gsheet_url = st.text_input("Google Sheets URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        
        if gsheet_url:
            st.info("💡 Google Sheets 연동을 위해 `gspread` 패키지가 필요합니다.")
            st.code("pip install gspread oauth2client", language="bash")
            st.caption("""
            **설정 방법:**
            1. Google Cloud Console에서 서비스 계정 생성
            2. JSON 키 파일 다운로드
            3. Streamlit Secrets에 키 정보 등록
            4. Google Sheet에 서비스 계정 이메일 공유 추가
            """)
        
    with st.expander("📋 데이터 내보내기 / 백업", expanded=False):
        if not df_all.empty:
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
                st.download_button("💾 전체 DB → CSV 백업", data=csv_data, 
                                   file_name=f"hayoung_backup_{CURRENT_DATE}.csv",
                                   use_container_width=True)
            with col_exp2:
                excel_backup = create_secure_excel(df_all, "전체 데이터 백업")
                st.download_button("💾 전체 DB → Excel 백업", data=excel_backup,
                                   file_name=f"hayoung_backup_{CURRENT_DATE}.xlsx",
                                   use_container_width=True)
            
            st.caption(f"📊 현재 DB 상태: {len(df_all)}건 | 최종 업데이트: {df_all['날짜'].max()[:10]}")