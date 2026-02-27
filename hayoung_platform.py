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
# 0-A. 계정 데이터베이스 (로그인 시스템)
# ==========================================
SCHOOL_ACCOUNTS = {
    "kn12": {"pw":"1234","role":"school","name":"강남중학교"},
    "hs01": {"pw":"1234","role":"school","name":"화성초등학교"},
    "dt02": {"pw":"1234","role":"school","name":"동탄중학교"},
    "sw03": {"pw":"1234","role":"school","name":"수원고등학교"},
    "an04": {"pw":"1234","role":"school","name":"안양남초등학교"},
    "pc05": {"pw":"1234","role":"school","name":"평촌초등학교"},
    "br06": {"pw":"1234","role":"school","name":"부림초등학교"},
    "bh07": {"pw":"1234","role":"school","name":"부흥중학교"},
    "dc08": {"pw":"1234","role":"school","name":"덕천초등학교"},
    "sc09": {"pw":"1234","role":"school","name":"서초고등학교"},
    "ga10": {"pw":"1234","role":"school","name":"구암고등학교"},
    "gs11": {"pw":"1234","role":"school","name":"국사봉중학교"},
    "dg13": {"pw":"1234","role":"school","name":"당곡고등학교"},
    "dg14": {"pw":"1234","role":"school","name":"당곡중학교"},
    "sg15": {"pw":"1234","role":"school","name":"서울공업고등학교"},
    "yn16": {"pw":"1234","role":"school","name":"영남중학교"},
    "sy17": {"pw":"1234","role":"school","name":"선유고등학교"},
    "sm18": {"pw":"1234","role":"school","name":"신목고등학교"},
    "gc19": {"pw":"1234","role":"school","name":"고척고등학교"},
    "gh20": {"pw":"1234","role":"school","name":"구현고등학교"},
    "as21": {"pw":"1234","role":"school","name":"안산국제비지니스고등학교"},
    "as22": {"pw":"1234","role":"school","name":"안산고등학교"},
    "sh23": {"pw":"1234","role":"school","name":"송호고등학교"},
    "bb24": {"pw":"1234","role":"school","name":"비봉고등학교"},
}
EDU_OFFICE_ACCOUNTS = {
    "edu_hw": {"pw":"edu2026!","role":"edu_office","name":"화성오산교육지원청",
               "schools":["화성초등학교","동탄중학교","수원고등학교","안양남초등학교","평촌초등학교",
                           "부림초등학교","부흥중학교","덕천초등학교","비봉고등학교","안산고등학교",
                           "안산국제비지니스고등학교","송호고등학교"]},
    "edu_sw": {"pw":"edu2026!","role":"edu_office","name":"서울남부교육지원청",
               "schools":["서초고등학교","구암고등학교","국사봉중학교","당곡고등학교","당곡중학교",
                           "서울공업고등학교","강남중학교","영남중학교","선유고등학교","신목고등학교",
                           "고척고등학교","구현고등학교"]},
}
DRIVER_ACCOUNTS = {
    "driver01": {"pw":"dr2026!","role":"driver","name":"김하영 기사"},
    "driver02": {"pw":"dr2026!","role":"driver","name":"박수거 기사"},
    "driver03": {"pw":"dr2026!","role":"driver","name":"이운반 기사"},
}
ADMIN_ACCOUNTS = {
    "admin": {"pw":"hayoung2026!","role":"admin","name":"하영자원 본사 관리자"},
}
ALL_ACCOUNTS = {}
ALL_ACCOUNTS.update(SCHOOL_ACCOUNTS)
ALL_ACCOUNTS.update(EDU_OFFICE_ACCOUNTS)
ALL_ACCOUNTS.update(DRIVER_ACCOUNTS)
ALL_ACCOUNTS.update(ADMIN_ACCOUNTS)

def authenticate(user_id, password):
    if user_id in ALL_ACCOUNTS and str(ALL_ACCOUNTS[user_id]["pw"]) == str(password):
        return ALL_ACCOUNTS[user_id]
    return None

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

# --- 세션 상태 초기화 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.session_state.user_data = None
    st.session_state.login_group = None

# [디자인] 기존 CSS + 랜딩페이지 CSS
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
    .landing-header { background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf9 50%, #e0f0e3 100%); padding: 50px 20px 30px 20px; text-align: center; border-radius: 0 0 20px 20px; margin: -1rem -1rem 30px -1rem; }
    .landing-header h1 { font-size: 36px; font-weight: 900; color: #1a1a2e; margin-bottom: 8px; }
    .landing-header .subtitle { font-size: 18px; color: #555; }
    .landing-header .brand { font-size: 28px; font-weight: 800; color: #1a73e8; margin-bottom: 15px; }
    .role-card { background: #fff; border: 2px solid #e8eaed; border-radius: 16px; padding: 35px 20px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); min-height: 280px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .role-card .icon { font-size: 64px; margin-bottom: 15px; }
    .role-card .title { font-size: 22px; font-weight: 800; color: #202124; margin-bottom: 8px; }
    .role-card .desc { font-size: 14px; color: #5f6368; line-height: 1.5; }
    .role-card .arrow { font-size: 24px; color: #1a73e8; margin-top: 12px; }
    .footer-info { text-align: center; padding: 20px; color: #777; font-size: 13px; margin-top: 30px; border-top: 1px solid #e8eaed; }
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
# ★ 화면 라우팅: 로그인 전→랜딩 / 로그인 후→역할별 대시보드
# ==========================================

if not st.session_state.logged_in:
    # ===== 랜딩 페이지 (S2B 스타일) =====
    st.markdown("""
    <div class="landing-header">
        <div class="brand">♻️ 하영자원 폐기물데이터플랫폼</div>
        <h1>투명하고 스마트한 폐기물 관리,</h1>
        <p class="subtitle">하영자원 데이터플랫폼이 여러분과 함께합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown('<div class="role-card"><div class="icon">🏢</div><div class="title">관리자</div><div class="desc">하영자원 본사 관리자<br>통합 관제 및 정산 센터</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("관리자 로그인", key="btn_admin", use_container_width=True, type="primary"):
            st.session_state.login_group = "admin"; st.rerun()
    with col2:
        st.markdown('<div class="role-card"><div class="icon">🏫</div><div class="title">교육청 / 학교</div><div class="desc">교육지원청 담당자<br>학교 행정실 담당자</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("교육청/학교 로그인", key="btn_edu", use_container_width=True, type="primary"):
            st.session_state.login_group = "edu_school"; st.rerun()
    with col3:
        st.markdown('<div class="role-card"><div class="icon">🚚</div><div class="title">수거업체</div><div class="desc">수거 기사 현장 앱<br>업체 관리자</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("수거업체 로그인", key="btn_driver", use_container_width=True, type="primary"):
            st.session_state.login_group = "driver"; st.rerun()

    if st.session_state.login_group:
        st.write("---")
        group = st.session_state.login_group
        labels = {"admin":("🏢 관리자 로그인","#1a73e8"),"edu_school":("🏫 교육청/학교 로그인","#34a853"),"driver":("🚚 수거업체 로그인","#ea4335")}
        label, color = labels[group]
        _, login_col, _ = st.columns([1,2,1])
        with login_col:
            st.markdown(f"<h3 style='text-align:center;color:{color};'>{label}</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                uid = st.text_input("아이디 (ID)", placeholder="아이디를 입력하세요")
                upw = st.text_input("비밀번호 (PW)", type="password", placeholder="비밀번호를 입력하세요")
                lc, bc = st.columns(2)
                with lc: submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")
                with bc: go_back = st.form_submit_button("← 돌아가기", use_container_width=True)
                if submitted:
                    account = authenticate(uid.strip(), upw.strip())
                    if account:
                        valid = (group=="admin" and account["role"]=="admin") or \
                                (group=="edu_school" and account["role"] in ("school","edu_office")) or \
                                (group=="driver" and account["role"]=="driver")
                        if valid:
                            st.session_state.logged_in = True
                            st.session_state.user_role = account["role"]
                            st.session_state.user_name = account["name"]
                            st.session_state.user_id = uid.strip()
                            st.session_state.user_data = account
                            st.session_state.login_group = None
                            st.rerun()
                        else:
                            st.error("⚠️ 이 계정은 선택하신 그룹에 속하지 않습니다.")
                    else:
                        st.error("❌ 아이디 또는 비밀번호가 일치하지 않습니다.")
                if go_back:
                    st.session_state.login_group = None; st.rerun()
    st.markdown('<div class="footer-info">하영자원 | 경기도 화성시 | 고객센터: 031-XXX-XXXX (평일 09~18시)</div>', unsafe_allow_html=True)

else:
    # ===== 로그인 후: 사이드바 + 역할별 대시보드 =====
    role = st.session_state.user_role
    user_name = st.session_state.user_name
    with st.sidebar:
        st.markdown("## ♻️ 하영자원 Pro")
        st.caption("공공기관(B2G) 맞춤 데이터 플랫폼")
        st.write("---")
        emojis = {"admin":"🏢","school":"🏫","edu_office":"🎓","driver":"🚚"}
        rlabels = {"admin":"관리자","school":"학교 담당자","edu_office":"교육청 담당자","driver":"수거 기사"}
        st.markdown(f"### {emojis.get(role,'👤')} 로그인 정보")
        st.markdown(f"**이름:** {user_name}")
        st.markdown(f"**역할:** {rlabels.get(role, role)}")
        st.markdown(f"**계정:** {st.session_state.user_id}")
        st.caption(f"접속: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write("---")
        if st.button("🔓 로그아웃", use_container_width=True, type="secondary"):
            for k in ['logged_in','user_role','user_name','user_id','user_data','login_group']:
                st.session_state[k] = None if k != 'logged_in' else False
            st.rerun()
        st.write("---")
        st.info("💡 **데이터 실시간 동기화 완벽 지원**")

    # ============ [모드1] 관리자 ============
    if role == "admin":
        st.markdown("<h1 style='display:flex; align-items:center;'>🏢 본사 통합 관제 및 정산 센터</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #5f6368; font-size: 16px;'>음식물, 사업장폐기물, 재활용 통계를 완벽히 분리하여 수익/비용 관리가 가능합니다.</p>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 총 수거</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 총 수거</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 총 수거</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,} kg</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 누적 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,} 원</div></div>', unsafe_allow_html=True)
        with col5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검</div><div class="metric-value-total" style="color:#1a73e8;">100%</div></div>', unsafe_allow_html=True)

        total_co2_all = df_all['탄소감축량(kg)'].sum()
        tree_count_all = int(total_co2_all / 6.6)
        st.markdown(f'<div style="background-color:#61b346;padding:30px;border-radius:12px;color:white;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;"><div style="flex:1;text-align:center;"><h3 style="margin:0;color:white;">🌍 전사 ESG 탄소 저감 성과</h3><p style="margin:0;font-size:16px;opacity:0.9;">누적 CO₂ 감축량</p><h1 style="margin:0;color:white;font-size:40px;font-weight:900;">{total_co2_all:,.1f} kg</h1></div><div style="font-size:40px;font-weight:bold;padding:0 20px;">=</div><div style="flex:1;text-align:center;"><p style="margin:0;font-size:16px;opacity:0.9;margin-top:35px;">소나무 식재 효과</p><h1 style="margin:0;color:white;font-size:40px;font-weight:900;">🌲 {tree_count_all:,} 그루</h1></div></div>', unsafe_allow_html=True)

        col_esg1, col_esg2, col_esg3 = st.columns([1,2,1])
        with col_esg1: st.button("📄 전사 ESG 성과 보고서 출력", use_container_width=True)
        st.write("---")

        # ★ 이번 달 우수 수거 기사
        st.subheader("🏆 이번 달 우수 수거 기사")
        bc1, bc2, bc3 = st.columns(3)
        with bc1: st.markdown('<div class="custom-card" style="border-top:5px solid #FFD700;text-align:center;"><div style="font-size:40px;">🥇</div><div style="font-size:18px;font-weight:800;margin:8px 0;">김하영 기사</div><div style="color:#5f6368;">수거량: 12,450kg | 안전: 100점</div><div style="color:#34a853;font-weight:bold;">무사고 365일</div></div>', unsafe_allow_html=True)
        with bc2: st.markdown('<div class="custom-card" style="border-top:5px solid #C0C0C0;text-align:center;"><div style="font-size:40px;">🥈</div><div style="font-size:18px;font-weight:800;margin:8px 0;">박수거 기사</div><div style="color:#5f6368;">수거량: 11,200kg | 안전: 98점</div><div style="color:#34a853;font-weight:bold;">무사고 280일</div></div>', unsafe_allow_html=True)
        with bc3: st.markdown('<div class="custom-card" style="border-top:5px solid #CD7F32;text-align:center;"><div style="font-size:40px;">🥉</div><div style="font-size:18px;font-weight:800;margin:8px 0;">이운반 기사</div><div style="color:#5f6368;">수거량: 10,800kg | 안전: 95점</div><div style="color:#34a853;font-weight:bold;">무사고 190일</div></div>', unsafe_allow_html=True)
        st.write("---")

        st.subheader("📑 통합 및 개별 정산 시트 🔗")
        tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs(["전체 통합 정산","음식물 정산","사업장 정산","재활용 정산","📍 차량 관제","🤝 외주업체"])
        current_months = sorted(df_all[df_all['년도']==str(CURRENT_YEAR)]['월별'].unique())
        with tab_total:
            stabs = st.tabs([f"📅 {CURRENT_YEAR}년 전체"]+[f"🗓️ {m}" for m in current_months])
            with stabs[0]: st.dataframe(df_all[df_all['년도']==str(CURRENT_YEAR)][['날짜','학교명','학생수','최종정산액','상태']], use_container_width=True)
            for i, m in enumerate(current_months):
                with stabs[i+1]: st.dataframe(df_all[df_all['월별']==m][['날짜','학교명','학생수','최종정산액','상태']], use_container_width=True)
            cb1, cb2 = st.columns(2)
            with cb1: st.button("🏢 업체별 통합정산서 발송", use_container_width=True)
            with cb2: st.button("🏫 학교별 통합정산서 발송", use_container_width=True)
        with tab_food:
            ftabs = st.tabs([f"📅 {CURRENT_YEAR}년 전체"]+[f"🗓️ {m}" for m in current_months])
            with ftabs[0]: st.dataframe(df_all[df_all['년도']==str(CURRENT_YEAR)][['날짜','학교명','음식물(kg)','단가(원)','음식물비용','상태']], use_container_width=True)
            for i, m in enumerate(current_months):
                with ftabs[i+1]: st.dataframe(df_all[df_all['월별']==m][['날짜','학교명','음식물(kg)','단가(원)','음식물비용','상태']], use_container_width=True)
        with tab_biz:
            btabs = st.tabs([f"📅 {CURRENT_YEAR}년 전체"]+[f"🗓️ {m}" for m in current_months])
            with btabs[0]: st.dataframe(df_all[df_all['년도']==str(CURRENT_YEAR)][['날짜','학교명','사업장(kg)','사업장비용']], use_container_width=True)
            for i, m in enumerate(current_months):
                with btabs[i+1]: st.dataframe(df_all[df_all['월별']==m][['날짜','학교명','사업장(kg)','사업장비용']], use_container_width=True)
        with tab_recycle:
            rtabs = st.tabs([f"📅 {CURRENT_YEAR}년 전체"]+[f"🗓️ {m}" for m in current_months])
            with rtabs[0]: st.dataframe(df_all[df_all['년도']==str(CURRENT_YEAR)][['날짜','학교명','재활용(kg)','재활용수익']], use_container_width=True)
            for i, m in enumerate(current_months):
                with rtabs[i+1]: st.dataframe(df_all[df_all['월별']==m][['날짜','학교명','재활용(kg)','재활용수익']], use_container_width=True)
        with tab_map:
            st.write("📍 **수거 차량 실시간 GPS 관제**")
            st.map(pd.DataFrame({'lat':[37.20,37.25],'lon':[127.05,127.10]}))
        with tab_sub:
            st.subheader("🤝 외주 수거업체 현황")
            st.markdown('<div class="alert-box">🔔 <b>[계약 갱신]</b> B자원 계약 만료 30일 전 (2026-03-25)</div>', unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns(3)
            with cs1: st.info("🏆 우수: **A환경** (98점)")
            with cs2: st.warning("⚠️ 주의: **B자원** (과속 1회)")
            with cs3: st.success("✅ 스쿨존 위반: **1건**")
            vendor_data = pd.DataFrame({"외주업체명":["A환경","B자원"],"담당학교":["동탄중학교","수원고등학교"],"안전평가":["98점(우수)","85점(주의)"],"운행상태":["🟢 운행중","🟡 대기중"]})
            st.dataframe(vendor_data, use_container_width=True)
            st.write("---")
            st.subheader("🔎 기사 상세 조회")
            sel_vendor = st.selectbox("업체 선택", ["A환경","B자원","C로지스"])
            if sel_vendor == "A환경":
                st.markdown('<div class="safety-box">🚛 경기88아 1234 | 👨‍✈️ 김하영 | 🏫 오늘 배차 1곳</div>', unsafe_allow_html=True)

        # 관리자 사이드바 - 데이터 업로드/백업
        with st.sidebar:
            st.write("---")
            st.markdown("### ⚙️ 데이터 연동")
            with st.expander("📂 수거 데이터 업로드"):
                uploaded_file = st.file_uploader("파일 선택", type=['csv','xlsx','xls'], label_visibility="collapsed")
                if uploaded_file:
                    try:
                        df_up = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                        st.success(f"✅ {len(df_up)}건 로드")
                        if st.button("🔄 DB 업데이트", type="primary", use_container_width=True):
                            for cn, dv in [('학생수',0),('수거업체',"하영자원(본사 직영)"),('단가(원)',150),('재활용단가(원)',300),('사업장단가(원)',200),('상태',"정산대기")]:
                                if cn not in df_up.columns:
                                    df_up[cn] = df_up['학교명'].map(STUDENT_COUNTS).fillna(0).astype(int) if cn=='학생수' else dv
                            df_m = pd.concat([load_data(), df_up], ignore_index=True).drop_duplicates(subset=['날짜','학교명'], keep='last')
                            df_m.to_csv(DB_FILE, index=False)
                            st.success("✅ 반영 완료!"); time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
            with st.expander("📋 데이터 백업"):
                if not df_all.empty:
                    st.download_button("💾 CSV 백업", data=df_all.to_csv(index=False).encode('utf-8-sig'), file_name=f"hayoung_backup_{CURRENT_DATE}.csv", use_container_width=True)
                    st.caption(f"📊 DB: {len(df_all)}건 | 최종: {df_all['날짜'].max()[:10]}")

    # ============ [모드2] 학교 담당자 ============
    elif role == "school":
        school = st.session_state.user_name
        st.title(f"🏫 {school} 폐기물 통합 대시보드")
        df_school = df_all[df_all['학교명'] == school]
        if not df_school.empty:
            total_co2_school = df_school['탄소감축량(kg)'].sum()
            tree_count_school = int(total_co2_school / 6.6)
            st.markdown(f'<div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:20px;border-radius:12px;color:white;margin-bottom:20px;"><h4 style="margin:0;margin-bottom:10px;">🌱 우리 학교 ESG 환경 기여도 (교육청 제출용)</h4><h2>누적 CO₂ 감축량: {total_co2_school:,.1f} kg (🌲 소나무 {tree_count_school}그루 식재 효과)</h2></div>', unsafe_allow_html=True)
            st.subheader("📊 폐기물 배출량 통계 분석")
            tab_daily, tab_monthly = st.tabs(["🗓️ 일별 배출량","🗓️ 월별 배출량"])
            with tab_daily:
                daily_df = df_school.copy()
                daily_df['일자'] = daily_df['날짜'].astype(str).str[:10]
                daily_grouped = daily_df.groupby('일자')[['음식물(kg)','사업장(kg)','재활용(kg)']].sum().reset_index()
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    st.markdown("<h5 style='text-align:center;color:#ea4335;'>🗑️ 음식물</h5>", unsafe_allow_html=True)
                    st.bar_chart(daily_grouped.set_index('일자')['음식물(kg)'], color="#ea4335")
                with cc2:
                    st.markdown("<h5 style='text-align:center;color:#9b59b6;'>🗄️ 사업장</h5>", unsafe_allow_html=True)
                    st.bar_chart(daily_grouped.set_index('일자')['사업장(kg)'], color="#9b59b6")
                with cc3:
                    st.markdown("<h5 style='text-align:center;color:#34a853;'>♻️ 재활용</h5>", unsafe_allow_html=True)
                    st.bar_chart(daily_grouped.set_index('일자')['재활용(kg)'], color="#34a853")
            with tab_monthly:
                years = sorted(df_school['년도'].unique(), reverse=True)
                year_tabs = st.tabs([f"📅 {y}년" for y in years])
                for yi, y in enumerate(years):
                    with year_tabs[yi]:
                        y_df = df_school[df_school['년도']==y]
                        mg = y_df.groupby('월별')[['음식물(kg)','사업장(kg)','재활용(kg)']].sum().reset_index()
                        mc1, mc2, mc3 = st.columns(3)
                        with mc1:
                            st.markdown("<h5 style='text-align:center;color:#ea4335;'>🗑️ 음식물(월별)</h5>", unsafe_allow_html=True)
                            st.bar_chart(mg.set_index('월별')['음식물(kg)'], color="#ea4335")
                        with mc2:
                            st.markdown("<h5 style='text-align:center;color:#9b59b6;'>🗄️ 사업장(월별)</h5>", unsafe_allow_html=True)
                            st.bar_chart(mg.set_index('월별')['사업장(kg)'], color="#9b59b6")
                        with mc3:
                            st.markdown("<h5 style='text-align:center;color:#34a853;'>♻️ 재활용(월별)</h5>", unsafe_allow_html=True)
                            st.bar_chart(mg.set_index('월별')['재활용(kg)'], color="#34a853")
            st.write("---")
            st.markdown("<h5 style='color:#2e7d32;font-weight:bold;'>🛡️ 금일 수거차량 안전 점검 현황</h5>", unsafe_allow_html=True)
            st.markdown('<div class="safety-box">✅ 배차: 하영자원 (본사 직영)<br>✅ 스쿨존: 정상 (MAX 28km/h)<br>✅ 후방카메라·안전요원: 적합</div>', unsafe_allow_html=True)
            st.write("---")
            st.subheader("🖨️ 행정 증빙 서류 자동 출력 (법정 양식)")
            st.caption("📌 2026.1.1 시행 「기후에너지환경부령 제18호」 반영 완료")
            period_start = df_school['날짜'].min()[:10]
            period_end = df_school['날짜'].max()[:10]
            period_str = f"{period_start} ~ {period_end}"
            doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs(["📊 월간 정산서","📈 실적보고서(제30호)","♻️ 상계증빙","🔗 올바로 연동"])
            with doc_tab1:
                st.info("💡 행정실 회계 처리용 월간 정산서입니다.")
                cd1, cd2, cd3, cd4 = st.columns(4)
                with cd1: st.download_button("전체 통합본", data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액']], "통합 정산서", school, period_str), file_name=f"{school}_통합_정산서.xlsx", use_container_width=True)
                with cd2: st.download_button("🗑️ 음식물", data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물 정산서", school, period_str), file_name=f"{school}_음식물_정산서.xlsx", use_container_width=True)
                with cd3: st.download_button("🗄️ 사업장", data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장 정산서", school, period_str), file_name=f"{school}_사업장_정산서.xlsx", use_container_width=True)
                with cd4: st.download_button("♻️ 재활용", data=create_legal_report_excel(df_school[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 정산서", school, period_str), file_name=f"{school}_재활용_정산서.xlsx", use_container_width=True)
            with doc_tab2:
                st.info("💡 교육청/지자체 제출용 법정 양식")
                cr1, cr2, cr3 = st.columns(3)
                with cr1: st.download_button("🗑️ 음식물 실적", data=create_legal_report_excel(df_school[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물류 처리 실적보고서", school, period_str), file_name=f"{school}_음식물_실적.xlsx", use_container_width=True)
                with cr2: st.download_button("🗄️ 사업장 실적", data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장 처리 실적보고서", school, period_str), file_name=f"{school}_사업장_실적.xlsx", use_container_width=True)
                with cr3: st.download_button("♻️ 재활용 실적", data=create_legal_report_excel(df_school[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 처리 실적보고서", school, period_str), file_name=f"{school}_재활용_실적.xlsx", use_container_width=True)
            with doc_tab3:
                st.info("💡 사업장 폐기물 재활용 수익 상계 증빙")
                st.download_button("📄 상계증빙서 다운로드", data=create_legal_report_excel(df_school[['날짜','학교명','사업장(kg)','재활용(kg)','재활용수익','사업장비용']], "재활용 상계처리 증빙", school, period_str), file_name=f"{school}_상계증빙.xlsx")
            with doc_tab4:
                st.info("💡 올바로 시스템 자동 전송")
                if st.button("🔗 올바로시스템 전자인계서 연동", type="primary", use_container_width=True):
                    with st.spinner("한국환경공단 서버 통신 중..."):
                        time.sleep(2)
                    st.success("✅ 올바로시스템에 전자인계서 이관 완료!")
        else:
            st.info("해당 학교의 수거 데이터가 아직 없습니다.")

    # ============ [모드2-B] 교육청 담당자 ============
    elif role == "edu_office":
        office_name = st.session_state.user_name
        office_schools = st.session_state.user_data.get("schools", [])
        st.title(f"🎓 {office_name} 관할 폐기물 통합 대시보드")
        st.caption(f"관할 학교: {len(office_schools)}개교")
        df_office = df_all[df_all['학교명'].isin(office_schools)]
        if not df_office.empty:
            oc1, oc2, oc3, oc4 = st.columns(4)
            with oc1: st.metric("🗑️ 음식물 총 수거", f"{df_office['음식물(kg)'].sum():,} kg")
            with oc2: st.metric("🗄️ 사업장 총 수거", f"{df_office['사업장(kg)'].sum():,} kg")
            with oc3: st.metric("♻️ 재활용 총 수거", f"{df_office['재활용(kg)'].sum():,} kg")
            with oc4: st.metric("💰 총 정산 금액", f"{df_office['최종정산액'].sum():,} 원")
            tco2 = df_office['탄소감축량(kg)'].sum()
            st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:12px;color:white;margin:15px 0;"><h4 style="margin:0;color:white;">🌍 {office_name} ESG 성과</h4><h2 style="margin:5px 0;color:white;">CO₂ 감축: {tco2:,.1f}kg (🌲 {int(tco2/6.6):,}그루)</h2></div>', unsafe_allow_html=True)
            st.write("---")
            st.subheader("📊 관할 학교별 배출 현황")
            summary = df_office.groupby('학교명').agg({'음식물(kg)':'sum','사업장(kg)':'sum','재활용(kg)':'sum','최종정산액':'sum'}).reset_index().sort_values('최종정산액', ascending=False)
            st.dataframe(summary, use_container_width=True)
            st.write("---")
            st.subheader("🔍 개별 학교 상세")
            sel_sch = st.selectbox("학교 선택", office_schools)
            df_sel = df_office[df_office['학교명']==sel_sch]
            if not df_sel.empty:
                sc1, sc2, sc3 = st.columns(3)
                with sc1: st.metric("음식물", f"{df_sel['음식물(kg)'].sum():,} kg")
                with sc2: st.metric("사업장", f"{df_sel['사업장(kg)'].sum():,} kg")
                with sc3: st.metric("재활용", f"{df_sel['재활용(kg)'].sum():,} kg")
                st.dataframe(df_sel[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액','상태']].tail(20), use_container_width=True)
        else:
            st.info("관할 학교의 수거 데이터가 아직 없습니다.")

    # ============ [모드3] 수거 기사 + 퇴근하기 ============
    elif role == "driver":
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.markdown(f'<div class="mobile-app-header"><h2 style="margin:0;font-size:22px;">🚚 하영자원 기사 전용 앱</h2><p style="margin:5px 0 0 0;font-size:14px;opacity:0.8;">{user_name}님 환영합니다</p></div>', unsafe_allow_html=True)
            with st.expander("📋 [필수] 운행 전 안전 점검", expanded=True):
                st.warning("어린이 안전을 위해 확인해 주세요.")
                check1 = st.checkbox("차량 후방 카메라 정상 작동 확인")
                check2 = st.checkbox("조수석 안전 요원 탑승 확인")
                check3 = st.checkbox("스쿨존 회피 운행 숙지")
                if check1 and check2 and check3:
                    st.success("안전 점검 완료! 오늘도 안전 운행하세요.")
            st.write("---")
            is_schoolzone = st.toggle("🚨 스쿨존 진입 알림 (GPS 테스트)")
            if is_schoolzone:
                st.error("스쿨존 진입! 속도를 30km 이하로 줄이세요.")
                st.markdown("<h1 style='text-align:center;color:#d93025;font-size:60px;'>30</h1>", unsafe_allow_html=True)
            st.write("---")
            st.camera_input("📸 현장 증빙 사진 (선택)")
            with st.form("driver_input"):
                target = st.selectbox("수거 완료 학교", SCHOOL_LIST)
                ci1, ci2, ci3 = st.columns(3)
                with ci1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
                with ci2: biz_w = st.number_input("사업장 (kg)", min_value=0, step=10)
                with ci3: re_w = st.number_input("재활용 (kg)", min_value=0, step=10)
                if st.form_submit_button("본사로 수거량 전송", type="primary", use_container_width=True):
                    if food_w > 0 or biz_w > 0 or re_w > 0:
                        new_data = {"날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "학교명": target, "학생수": STUDENT_COUNTS[target], "수거업체": "하영자원(본사 직영)",
                            "음식물(kg)": food_w, "재활용(kg)": re_w, "사업장(kg)": biz_w,
                            "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "대기"}
                        save_data(new_data)
                        st.success(f"✅ {target} 수거 실적 기록 완료!")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")
            # ★ 퇴근하기 버튼
            st.write("---")
            st.markdown("### 🏠 퇴근 처리")
            if st.button("🏠 퇴근하기", use_container_width=True, type="secondary"):
                st.balloons()
                st.success(f"✅ {user_name}님, {datetime.now().strftime('%H시 %M분')} 퇴근 처리 완료! 수고하셨습니다.")
                st.caption("퇴근 기록이 본사 관제센터로 자동 전송됩니다.")
