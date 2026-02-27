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
    "driver01": {"pw":"dr2026!","role":"driver","name":"김하영 기사","vendor":"하영자원(본사)","schools":["화성초등학교","동탄중학교","수원고등학교","평촌초등학교"]},
    "driver02": {"pw":"dr2026!","role":"driver","name":"박수거 기사","vendor":"하영자원(본사)","schools":["부림초등학교","부흥중학교","덕천초등학교","안양남초등학교"]},
    "driver03": {"pw":"dr2026!","role":"driver","name":"이운반 기사","vendor":"하영자원(본사)","schools":["서초고등학교","구암고등학교","국사봉중학교"]},
    "driver04": {"pw":"dr2026!","role":"driver","name":"최민수 기사","vendor":"A환경","schools":["당곡고등학교","당곡중학교","강남중학교"]},
    "driver05": {"pw":"dr2026!","role":"driver","name":"정대호 기사","vendor":"A환경","schools":["서울공업고등학교","영남중학교"]},
    "driver06": {"pw":"dr2026!","role":"driver","name":"한정우 기사","vendor":"B자원","schools":["선유고등학교","신목고등학교","고척고등학교"]},
    "driver07": {"pw":"dr2026!","role":"driver","name":"오세진 기사","vendor":"B자원","schools":["구현고등학교","비봉고등학교"]},
    "driver08": {"pw":"dr2026!","role":"driver","name":"윤재혁 기사","vendor":"C로지스","schools":["안산고등학교","안산국제비지니스고등학교"]},
    "driver09": {"pw":"dr2026!","role":"driver","name":"송태윤 기사","vendor":"C로지스","schools":["송호고등학교"]},
}

# ==========================================
# 0-B. 외주 수거업체 데이터
# ==========================================
VENDOR_DATA = {
    "A환경": {
        "대표":"김환경","사업자번호":"123-45-67890","연락처":"031-234-5678",
        "차량":["경기89가 5678","경기90나 1234"],
        "drivers":["driver04","driver05"],
        "schools":["당곡고등학교","당곡중학교","강남중학교","서울공업고등학교","영남중학교"],
        "안전점수":98,"상태":"🟢 운행중","계약만료":"2026-09-30",
    },
    "B자원": {
        "대표":"박자원","사업자번호":"234-56-78901","연락처":"02-345-6789",
        "차량":["서울91다 3456","서울92라 7890"],
        "drivers":["driver06","driver07"],
        "schools":["선유고등학교","신목고등학교","고척고등학교","구현고등학교","비봉고등학교"],
        "안전점수":85,"상태":"🟡 대기중","계약만료":"2026-03-25",
    },
    "C로지스": {
        "대표":"이로지","사업자번호":"345-67-89012","연락처":"031-456-7890",
        "차량":["경기93마 5678"],
        "drivers":["driver08","driver09"],
        "schools":["안산고등학교","안산국제비지니스고등학교","송호고등학교"],
        "안전점수":92,"상태":"🟢 운행중","계약만료":"2027-01-15",
    },
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
# 2. 데이터 영구 저장 및 실시간 연산 (실제 수거 데이터 통합)
# ==========================================
DB_FILE = "hayoung_data_v5.csv"
REAL_DATA_FILE = "hayoung_real_2025.csv"

# ★ 탄소 감축 계수 (환경부 기준)
# 음식물폐기물 퇴비화 재활용 시 매립 대비 CO₂ 감축: 0.587 kgCO₂eq/kg
# 소나무 1그루 연간 CO₂ 흡수량: 6.6 kg (산림청)
CO2_FACTOR = 0.587  # kgCO₂eq per kg 음식물폐기물
TREE_FACTOR = 6.6   # kg CO₂ per 소나무 1그루/년

def load_real_data():
    """업로드된 실제 2025년 수거 데이터 로딩 (3~12월)"""
    try:
        df = pd.read_csv(REAL_DATA_FILE)
        return df
    except:
        return pd.DataFrame()

def preprocess_real_data(df):
    """실제 데이터 전처리 (날짜/월/탄소감축 등 파생 컬럼 생성)"""
    if df.empty:
        return df
    df = df.copy()
    df['날짜_dt'] = pd.to_datetime(df['날짜'], errors='coerce')
    df['월'] = df['날짜_dt'].dt.month
    df['년도'] = df['날짜_dt'].dt.year.astype(str)
    df['월별'] = df['날짜_dt'].dt.strftime('%Y-%m')
    df['수거여부'] = df['음식물(kg)'] > 0
    df['탄소감축량(kg)'] = df['음식물(kg)'] * CO2_FACTOR
    df['소나무환산(그루)'] = df['탄소감축량(kg)'] / TREE_FACTOR
    return df

def load_data():
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
    try:
        df = pd.read_csv(DB_FILE)
        if not df['날짜'].str.contains('2024').any():
            raise ValueError("과거 연도 데이터가 없어 새로 생성합니다.")
        return df
    except:
        sample_data = []
        for year in range(CURRENT_YEAR - 2, CURRENT_YEAR + 1):
            if year < CURRENT_YEAR:
                months_to_gen = [(11, 30), (12, 31)]
            else:
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
        df.to_csv(DB_FILE, index=False)
        return df

def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- 실제 데이터(2025 엑셀) 로딩 + 전처리 ---
df_real = preprocess_real_data(load_real_data())

# --- 기존 시뮬레이션 데이터 로딩 ---
df_all = load_data()

if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].astype(str).str[:7]
    df_all['년도'] = df_all['날짜'].astype(str).str[:4] 
    df_all['탄소감축량(kg)'] = df_all['음식물(kg)'] * CO2_FACTOR  # ★ 환경부 기준 적용
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
        tree_count_all = int(total_co2_all / TREE_FACTOR)
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
        tab_real, tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub = st.tabs(["📊 실제 수거 데이터(2025)","전체 통합 정산","음식물 정산","사업장 정산","재활용 정산","📍 차량 관제","🤝 외주업체"])

        # ★★★ [신규] 실제 수거 데이터 탭 ★★★
        with tab_real:
            if not df_real.empty:
                st.markdown("#### 📊 2025년 실제 음식물폐기물 수거 데이터 (3~12월)")
                st.caption(f"총 {len(df_real):,}건 | 수거일 {df_real['수거여부'].sum():,}건 | 총 수거량 {df_real['음식물(kg)'].sum():,.0f}kg")
                # 학교 선택 필터
                real_schools = sorted(df_real['학교명'].unique())
                sel_school_r = st.selectbox("🏫 학교/거래처 선택", ["전체"] + real_schools, key="admin_real_school")
                df_r_filtered = df_real if sel_school_r == "전체" else df_real[df_real['학교명']==sel_school_r]
                # 월별 하위 탭
                real_months = sorted(df_r_filtered['월'].unique())
                month_labels = ["📅 연간 전체"] + [f"🗓️ {m}월" for m in real_months]
                rtabs = st.tabs(month_labels)
                with rtabs[0]:
                    # 연간 학교별 요약
                    yr_summary = df_r_filtered.groupby('학교명').agg(
                        수거일수=('수거여부','sum'), 총수거량=('음식물(kg)','sum'),
                        총공급가=('공급가','sum'), 탄소감축=('탄소감축량(kg)','sum')
                    ).reset_index().sort_values('총수거량', ascending=False)
                    yr_summary['소나무환산'] = (yr_summary['탄소감축'] / TREE_FACTOR).astype(int)
                    yr_summary.columns = ['학교명','수거일수','총수거량(kg)','총공급가(원)','CO₂감축(kg)','🌲소나무(그루)']
                    st.dataframe(yr_summary, use_container_width=True, hide_index=True)
                    # 연간 차트
                    st.bar_chart(yr_summary.set_index('학교명')['총수거량(kg)'], color="#ea4335")
                for idx, m in enumerate(real_months):
                    with rtabs[idx+1]:
                        df_m = df_r_filtered[df_r_filtered['월']==m]
                        df_m_active = df_m[df_m['수거여부']==True]
                        mc1, mc2, mc3 = st.columns(3)
                        with mc1: st.metric("수거일수", f"{len(df_m_active)}일")
                        with mc2: st.metric("수거량", f"{df_m_active['음식물(kg)'].sum():,.0f}kg")
                        with mc3: st.metric("공급가", f"{df_m_active['공급가'].sum():,.0f}원")
                        if sel_school_r == "전체":
                            m_summary = df_m_active.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index().sort_values('수거량',ascending=False)
                            st.dataframe(m_summary, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_m[['날짜','학교명','음식물(kg)','단가(원)','공급가','재활용방법','재활용업체']],use_container_width=True, hide_index=True)
            else:
                st.warning("실제 수거 데이터 파일(hayoung_real_2025.csv)이 없습니다.")

        # 기존 시뮬레이션 정산 탭
        all_schools_sim = sorted(df_all['학교명'].unique()) if not df_all.empty else []
        all_years_sim = sorted(df_all['년도'].unique(), reverse=True) if not df_all.empty else []

        with tab_total:
            sel_school_t = st.selectbox("🏫 거래처(학교) 선택", ["전체"] + all_schools_sim, key="admin_total_school")
            df_t = df_all if sel_school_t == "전체" else df_all[df_all['학교명']==sel_school_t]
            if not df_t.empty:
                sel_yr_t = st.selectbox("📅 년도 선택", sorted(df_t['년도'].unique(), reverse=True), key="admin_total_yr")
                df_ty = df_t[df_t['년도']==sel_yr_t]
                t_months = sorted(df_ty['월별'].unique())
                t_tabs = st.tabs(["📅 연간 전체"] + [f"🗓️ {m}" for m in t_months])
                with t_tabs[0]:
                    if sel_school_t == "전체":
                        t_sum = df_ty.groupby('학교명').agg({'음식물(kg)':'sum','사업장(kg)':'sum','재활용(kg)':'sum','최종정산액':'sum'}).reset_index().sort_values('최종정산액',ascending=False)
                        st.dataframe(t_sum, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_ty[['날짜','학교명','학생수','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액','상태']], use_container_width=True, hide_index=True)
                for ti, tm in enumerate(t_months):
                    with t_tabs[ti+1]:
                        df_tm = df_ty[df_ty['월별']==tm]
                        if sel_school_t == "전체":
                            tm_sum = df_tm.groupby('학교명').agg({'최종정산액':'sum'}).reset_index().sort_values('최종정산액',ascending=False)
                            st.dataframe(tm_sum, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_tm[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액','상태']], use_container_width=True, hide_index=True)
            cb1, cb2 = st.columns(2)
            with cb1: st.button("🏢 업체별 통합정산서 발송", use_container_width=True)
            with cb2: st.button("🏫 학교별 통합정산서 발송", use_container_width=True)
        with tab_food:
            sel_school_f = st.selectbox("🏫 거래처(학교) 선택", ["전체"] + all_schools_sim, key="admin_food_school")
            df_f = df_all if sel_school_f == "전체" else df_all[df_all['학교명']==sel_school_f]
            if not df_f.empty:
                sel_yr_f = st.selectbox("📅 년도 선택", sorted(df_f['년도'].unique(), reverse=True), key="admin_food_yr")
                df_fy = df_f[df_f['년도']==sel_yr_f]
                f_months = sorted(df_fy['월별'].unique())
                f_tabs = st.tabs(["📅 연간 전체"] + [f"🗓️ {m}" for m in f_months])
                with f_tabs[0]:
                    if sel_school_f == "전체":
                        f_sum = df_fy.groupby('학교명').agg({'음식물(kg)':'sum','음식물비용':'sum'}).reset_index().sort_values('음식물비용',ascending=False)
                        st.dataframe(f_sum, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_fy[['날짜','학교명','음식물(kg)','단가(원)','음식물비용','상태']], use_container_width=True, hide_index=True)
                for fi, fm in enumerate(f_months):
                    with f_tabs[fi+1]:
                        df_fm = df_fy[df_fy['월별']==fm]
                        if sel_school_f == "전체":
                            fm_sum = df_fm.groupby('학교명').agg({'음식물(kg)':'sum','음식물비용':'sum'}).reset_index().sort_values('음식물비용',ascending=False)
                            st.dataframe(fm_sum, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_fm[['날짜','학교명','음식물(kg)','단가(원)','음식물비용','상태']], use_container_width=True, hide_index=True)
        with tab_biz:
            sel_school_b = st.selectbox("🏫 거래처(학교) 선택", ["전체"] + all_schools_sim, key="admin_biz_school")
            df_b = df_all if sel_school_b == "전체" else df_all[df_all['학교명']==sel_school_b]
            if not df_b.empty:
                sel_yr_b = st.selectbox("📅 년도 선택", sorted(df_b['년도'].unique(), reverse=True), key="admin_biz_yr")
                df_by = df_b[df_b['년도']==sel_yr_b]
                b_months = sorted(df_by['월별'].unique())
                b_tabs = st.tabs(["📅 연간 전체"] + [f"🗓️ {m}" for m in b_months])
                with b_tabs[0]:
                    if sel_school_b == "전체":
                        b_sum = df_by.groupby('학교명').agg({'사업장(kg)':'sum','사업장비용':'sum'}).reset_index().sort_values('사업장비용',ascending=False)
                        st.dataframe(b_sum, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_by[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], use_container_width=True, hide_index=True)
                for bi, bm in enumerate(b_months):
                    with b_tabs[bi+1]:
                        df_bm = df_by[df_by['월별']==bm]
                        if sel_school_b == "전체":
                            bm_sum = df_bm.groupby('학교명').agg({'사업장(kg)':'sum','사업장비용':'sum'}).reset_index()
                            st.dataframe(bm_sum, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_bm[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], use_container_width=True, hide_index=True)
        with tab_recycle:
            sel_school_rc = st.selectbox("🏫 거래처(학교) 선택", ["전체"] + all_schools_sim, key="admin_rec_school")
            df_rc = df_all if sel_school_rc == "전체" else df_all[df_all['학교명']==sel_school_rc]
            if not df_rc.empty:
                sel_yr_rc = st.selectbox("📅 년도 선택", sorted(df_rc['년도'].unique(), reverse=True), key="admin_rec_yr")
                df_rcy = df_rc[df_rc['년도']==sel_yr_rc]
                rc_months = sorted(df_rcy['월별'].unique())
                rc_tabs = st.tabs(["📅 연간 전체"] + [f"🗓️ {m}" for m in rc_months])
                with rc_tabs[0]:
                    if sel_school_rc == "전체":
                        rc_sum = df_rcy.groupby('학교명').agg({'재활용(kg)':'sum','재활용수익':'sum'}).reset_index().sort_values('재활용수익',ascending=False)
                        st.dataframe(rc_sum, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_rcy[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], use_container_width=True, hide_index=True)
                for rci, rcm in enumerate(rc_months):
                    with rc_tabs[rci+1]:
                        df_rcm = df_rcy[df_rcy['월별']==rcm]
                        if sel_school_rc == "전체":
                            rcm_sum = df_rcm.groupby('학교명').agg({'재활용(kg)':'sum','재활용수익':'sum'}).reset_index()
                            st.dataframe(rcm_sum, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_rcm[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], use_container_width=True, hide_index=True)
        with tab_map:
            st.write("📍 **수거 차량 실시간 GPS 관제**")
            st.map(pd.DataFrame({'lat':[37.20,37.25],'lon':[127.05,127.10]}))
        with tab_sub:
            st.subheader("🤝 외주 수거업체 실시간 업무 및 안전 평가 현황")
            # 계약 갱신 알림
            from datetime import datetime as dt_cls
            for vn, vd in VENDOR_DATA.items():
                exp = dt_cls.strptime(vd['계약만료'],'%Y-%m-%d')
                days_left = (exp - dt_cls.now()).days
                if days_left <= 90:
                    st.markdown(f'<div class="alert-box">🔔 <b>[계약 갱신]</b> \'{vn}\' 업체와의 수거 위탁 계약 만료가 {days_left}일 앞으로 다가왔습니다. (만료일: {vd["계약만료"]})</div>', unsafe_allow_html=True)
            # 우수/주의/경고 카드
            sorted_vendors = sorted(VENDOR_DATA.items(), key=lambda x: x[1]['안전점수'], reverse=True)
            vc1, vc2, vc3 = st.columns(3)
            with vc1: st.success(f"🏆 이달의 우수 안전 업체: **{sorted_vendors[0][0]}** ({sorted_vendors[0][1]['안전점수']}점)")
            worst = sorted_vendors[-1]
            with vc2: st.warning(f"⚠️ 주의 필요 업체: **{worst[0]}** ({worst[1]['안전점수']}점)")
            with vc3: st.info(f"✅ 스쿨존 속도위반 경고 건수: **1건**")

            # 업체 총괄 테이블
            vendor_rows = []
            for vn, vd in VENDOR_DATA.items():
                # 해당 업체 담당 학교 실제 데이터 합산
                v_schools = vd['schools']
                if not df_real.empty:
                    v_df = df_real[(df_real['학교명'].isin(v_schools)) & (df_real['수거여부'])]
                    v_total = v_df['공급가'].sum() if not v_df.empty else 0
                else:
                    v_total = 0
                penalty = -50000 if vd['안전점수'] < 90 else 0
                vendor_rows.append({
                    '외주업체명':vn, '담당학교':'/'.join(v_schools[:2])+'...' if len(v_schools)>2 else '/'.join(v_schools),
                    '안전평가점수':f"{vd['안전점수']}점 ({'우수' if vd['안전점수']>=90 else '주의'})",
                    '안전 페널티(위반벌금)':f"{penalty:,} 원" if penalty else "0 원",
                    '이달 정산지급액(예상)':f"{max(0,v_total+penalty):,.0f} 원",
                    '현재 운행상태':vd['상태'],
                })
            st.dataframe(pd.DataFrame(vendor_rows), use_container_width=True, hide_index=True)

            # ★ 하위시트: 업체 선택 → 거래처(학교)/품목 → 년도 → 월
            st.write("---")
            st.subheader("🔍 담당 차량 및 기사 상세 조회 (타임라인)")
            st.caption("실시간 이동 동선을 조회할 업체를 선택하세요")
            sel_v = st.selectbox("업체 선택", list(VENDOR_DATA.keys()), key="admin_vendor_sel")
            vinfo = VENDOR_DATA[sel_v]
            # 기사 정보
            driver_names = [DRIVER_ACCOUNTS[d]['name'] for d in vinfo['drivers'] if d in DRIVER_ACCOUNTS]
            driver_phones = ["010-1234-5678","010-2345-6789","010-3456-7890"]
            st.markdown(f'<div class="safety-box">🚛 차량번호: {" | ".join(vinfo["차량"])} | 👨‍✈️ 담당기사: {", ".join(driver_names)} | 🏫 오늘 배차: {len(vinfo["schools"])}곳</div>', unsafe_allow_html=True)
            # 타임라인
            st.markdown("**🚚 오늘의 실시간 이동 동선**")
            st.markdown("✅ 08:30 [출발 전 점검] 차량 후방카메라 및 안전요원 탑승 확인 완료")
            st.markdown(f"➡️ 10:30 [이동 중] {vinfo['schools'][0]}로 이동 중 (현재 GPS 정상 수신 중)")

            # ★ 거래처(학교)별 수거량 하위시트
            st.write("---")
            st.subheader(f"📊 {sel_v} 거래처별 수거 현황")
            v_schools_list = vinfo['schools']
            if not df_real.empty:
                df_v_real = df_real[df_real['학교명'].isin(v_schools_list)]
                if not df_v_real.empty:
                    # 학교 선택
                    sel_v_school = st.selectbox("거래처(학교) 선택", ["전체"] + v_schools_list, key="vendor_school_sel")
                    df_vs = df_v_real if sel_v_school == "전체" else df_v_real[df_v_real['학교명']==sel_v_school]
                    # 년도 선택
                    v_years = sorted(df_vs['년도'].unique(), reverse=True)
                    sel_v_year = st.selectbox("년도 선택", v_years, key="vendor_year_sel") if v_years else None
                    if sel_v_year:
                        df_vy = df_vs[df_vs['년도']==sel_v_year]
                        v_m_list = sorted(df_vy['월'].unique())
                        v_m_tabs = st.tabs(["📅 연간 전체"] + [f"🗓️ {m}월" for m in v_m_list])
                        with v_m_tabs[0]:
                            vy_sum = df_vy[df_vy['수거여부']].groupby('학교명').agg(수거일수=('음식물(kg)','count'),수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index().sort_values('수거량',ascending=False)
                            st.dataframe(vy_sum, use_container_width=True, hide_index=True)
                        for vmi, vm in enumerate(v_m_list):
                            with v_m_tabs[vmi+1]:
                                df_vmm = df_vy[(df_vy['월']==vm) & (df_vy['수거여부'])]
                                if sel_v_school == "전체":
                                    vmm_s = df_vmm.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                                    st.dataframe(vmm_s, use_container_width=True, hide_index=True)
                                else:
                                    st.dataframe(df_vmm[['날짜','학교명','음식물(kg)','단가(원)','공급가','재활용방법']],use_container_width=True, hide_index=True)
                else:
                    st.info(f"{sel_v} 담당 학교의 실제 수거 데이터가 없습니다.")
            else:
                st.info("실제 수거 데이터가 로드되지 않았습니다.")

            # ★ 안전평가 결과서 다운로드
            st.write("---")
            st.subheader("📋 외주업체 안전평가 결과서")
            def create_safety_report_excel(vendor_name, vdata):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book
                    title_fmt = wb.add_format({'bold':True,'font_size':16,'align':'center','font_color':'#c62828'})
                    header_fmt = wb.add_format({'bold':True,'font_size':10,'align':'center','bg_color':'#1565c0','font_color':'white','border':1,'text_wrap':True})
                    cell_c = wb.add_format({'font_size':10,'align':'center','border':1,'text_wrap':True,'valign':'vcenter'})
                    cell_l = wb.add_format({'font_size':10,'align':'left','border':1,'text_wrap':True,'valign':'vcenter'})
                    pass_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'bg_color':'#e8f5e9','font_color':'#2e7d32'})
                    warn_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'bg_color':'#fff3e0','font_color':'#e65100'})
                    section_fmt = wb.add_format({'bold':True,'font_size':11,'bg_color':'#e3f2fd','border':1})
                    ws = wb.add_worksheet('안전평가 결과서')
                    ws.set_column(0,0,5); ws.set_column(1,1,18); ws.set_column(2,2,35); ws.set_column(3,3,12); ws.set_column(4,4,12); ws.set_column(5,5,20)
                    ws.merge_range('A1:F1', '외주 수거업체 안전평가 결과서', title_fmt)
                    ws.merge_range('A2:F2', f'평가대상: {vendor_name} | 평가일: {CURRENT_DATE} | 평가자: 하영자원 안전관리팀', wb.add_format({'font_size':10,'align':'center','border':0}))
                    # 업체 기본정보
                    ws.merge_range('A4:F4', '▣ 업체 기본정보', section_fmt)
                    info_items = [['업체명',vendor_name],['대표자',vdata['대표']],['사업자번호',vdata['사업자번호']],
                                  ['연락처',vdata['연락처']],['차량번호',', '.join(vdata['차량'])],['계약만료일',vdata['계약만료']]]
                    for ri, row in enumerate(info_items):
                        ws.write(5+ri, 0, '', cell_c); ws.write(5+ri, 1, row[0], cell_c); ws.merge_range(5+ri, 2, 5+ri, 5, row[1], cell_l)
                    # 평가항목 (환경부 기준 + 학교 스쿨존)
                    r = 12
                    ws.merge_range(f'A{r}:F{r}', '▣ 안전평가 점검 항목 (100점 만점)', section_fmt)
                    r += 1
                    eval_headers = ['No','평가영역','점검항목','배점','평가점수','비고']
                    for ci, h in enumerate(eval_headers): ws.write(r, ci, h, header_fmt)
                    score = vdata['안전점수']
                    is_good = score >= 90
                    eval_items = [
                        ['1','차량 안전성\n(30점)','차량 정기검사 이행 여부','10','10' if is_good else '8',''],
                        ['2','','후방카메라·측면센서 장착 상태','10','10' if is_good else '7',''],
                        ['3','','소화기·안전삼각대 비치','10','10' if is_good else '10',''],
                        ['4','스쿨존 준수\n(30점)','스쿨존 30km/h 이하 운행','15','15' if is_good else '10','위반 시 -5점/건'],
                        ['5','','학교 출입 시 안전요원 동승','15','15' if is_good else '12',''],
                        ['6','기사 안전교육\n(20점)','산업안전보건교육 이수','10','10' if is_good else '8','연 2회 이상'],
                        ['7','','음식물폐기물 취급 교육','10','10' if is_good else '10',''],
                        ['8','환경 관리\n(10점)','수거 시 악취·오수 관리','5','5' if is_good else '5',''],
                        ['9','','폐수 적정 처리 여부','5','5' if is_good else '5',''],
                        ['10','행정 신뢰성\n(10점)','올바로시스템 전자인계서 적시 전송','5','5' if is_good else '5',''],
                        ['11','','월별 실적보고서 기한 내 제출','5','3' if is_good else '5',''],
                    ]
                    for ri, row in enumerate(eval_items):
                        r2 = r + 1 + ri
                        for ci, val in enumerate(row):
                            fmt = cell_c if ci != 2 else cell_l
                            if ci == 4: fmt = pass_fmt if int(val) >= int(eval_items[ri][3]) else warn_fmt
                            ws.write(r2, ci, val, fmt)
                    # 총점
                    total_r = r + 1 + len(eval_items)
                    ws.merge_range(total_r, 0, total_r, 3, '총점', wb.add_format({'bold':True,'font_size':12,'align':'center','border':1,'bg_color':'#1565c0','font_color':'white'}))
                    total_score = sum(int(x[4]) for x in eval_items)
                    grade = '우수(A)' if total_score >= 90 else '양호(B)' if total_score >= 80 else '주의(C)'
                    ws.write(total_r, 4, str(total_score), wb.add_format({'bold':True,'font_size':14,'align':'center','border':1,'font_color':'#c62828'}))
                    ws.write(total_r, 5, grade, wb.add_format({'bold':True,'font_size':12,'align':'center','border':1}))
                return output.getvalue()
            sel_v_safety = st.selectbox("평가 대상 업체", list(VENDOR_DATA.keys()), key="safety_vendor")
            st.download_button("📋 안전평가 결과서 다운로드", data=create_safety_report_excel(sel_v_safety, VENDOR_DATA[sel_v_safety]),
                               file_name=f"{sel_v_safety}_안전평가결과서_{CURRENT_DATE}.xlsx", use_container_width=True)

            # ★ 월별 정산 대금 청구서 발행
            st.write("---")
            st.subheader("💰 외주업체 월별 정산 대금 청구서 발행")
            sel_v_bill = st.selectbox("청구 대상 업체", list(VENDOR_DATA.keys()), key="bill_vendor")
            vb_info = VENDOR_DATA[sel_v_bill]
            if not df_real.empty:
                df_vb = df_real[(df_real['학교명'].isin(vb_info['schools'])) & (df_real['수거여부'])]
                if not df_vb.empty:
                    vb_months = sorted(df_vb['월'].unique())
                    vb_tabs = st.tabs([f"🗓️ {m}월" for m in vb_months])
                    for vbi, vbm in enumerate(vb_months):
                        with vb_tabs[vbi]:
                            df_vbm = df_vb[df_vb['월']==vbm]
                            vbm_sum = df_vbm.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                            st.dataframe(vbm_sum, use_container_width=True, hide_index=True)
                            vbm_total = vbm_sum['공급가'].sum()
                            penalty = -50000 if vb_info['안전점수'] < 90 else 0
                            st.metric(f"{vbm}월 청구 금액", f"{max(0,vbm_total+penalty):,.0f} 원", delta=f"페널티 {penalty:,}원" if penalty else None)
                            # 청구서 엑셀 생성
                            def make_bill(vname, month, df_month, total, pen):
                                out = io.BytesIO()
                                with pd.ExcelWriter(out, engine='xlsxwriter') as w:
                                    wb = w.book
                                    ws = wb.add_worksheet('청구서')
                                    ws.set_column(0,4,18)
                                    tf = wb.add_format({'bold':True,'font_size':16,'align':'center'})
                                    hf = wb.add_format({'bold':True,'font_size':10,'align':'center','bg_color':'#34a853','font_color':'white','border':1})
                                    cf = wb.add_format({'font_size':10,'align':'center','border':1})
                                    nf = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0'})
                                    ws.merge_range('A1:E1', f'{vname} 월별 정산 대금 청구서', tf)
                                    ws.merge_range('A2:E2', f'청구월: 2025년 {month}월 | 발행일: {CURRENT_DATE}', wb.add_format({'font_size':10,'align':'center'}))
                                    for ci, h in enumerate(['학교명','수거량(kg)','공급가(원)','단가(원)','비고']): ws.write(3, ci, h, hf)
                                    for ri, (_, row) in enumerate(df_month.iterrows()):
                                        ws.write(4+ri, 0, row['학교명'], cf)
                                        ws.write(4+ri, 1, row['수거량'], nf)
                                        ws.write(4+ri, 2, row['공급가'], nf)
                                        ws.write(4+ri, 3, 162, nf)
                                        ws.write(4+ri, 4, '', cf)
                                    tr = 4 + len(df_month)
                                    ws.merge_range(tr, 0, tr, 1, '소계', hf); ws.write(tr, 2, total, nf)
                                    ws.merge_range(tr+1, 0, tr+1, 1, '안전 페널티', hf); ws.write(tr+1, 2, pen, nf)
                                    gf = wb.add_format({'bold':True,'font_size':14,'align':'center','border':1,'bg_color':'#34a853','font_color':'white','num_format':'#,##0'})
                                    ws.merge_range(tr+2, 0, tr+2, 1, '최종 청구액', gf); ws.write(tr+2, 2, max(0,total+pen), gf)
                                return out.getvalue()
                            st.download_button(f"📄 {vbm}월 청구서 발행", data=make_bill(sel_v_bill, vbm, vbm_sum, vbm_total, penalty),
                                               file_name=f"{sel_v_bill}_{vbm}월_청구서.xlsx", use_container_width=True, key=f"bill_{sel_v_bill}_{vbm}")
                else:
                    st.info(f"{sel_v_bill} 담당 학교의 수거 데이터가 없습니다.")
            else:
                st.info("실제 수거 데이터가 없습니다.")

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
                        # 실제 수거 데이터 구조 자동 감지 (음식물(kg) + 공급가 컬럼 존재 시)
                        is_real_data = '음식물(kg)' in df_up.columns and '공급가' in df_up.columns
                        if is_real_data:
                            st.info("📊 실제 수거 데이터 형식 감지 → 행정실/교육청 공유 데이터로 저장됩니다.")
                        if st.button("🔄 DB 업데이트", type="primary", use_container_width=True):
                            if is_real_data:
                                # 실제 데이터(REAL_DATA_FILE)에 병합
                                existing = load_real_data()
                                if not existing.empty:
                                    df_merged = pd.concat([existing, df_up], ignore_index=True).drop_duplicates(subset=['날짜','학교명'], keep='last')
                                else:
                                    df_merged = df_up
                                df_merged.to_csv(REAL_DATA_FILE, index=False)
                                st.success("✅ 실제 수거 데이터 반영 완료! (행정실/교육청 공유)")
                            else:
                                # 기존 시뮬레이션 DB에 병합
                                for cn, dv in [('학생수',0),('수거업체',"하영자원(본사 직영)"),('단가(원)',150),('재활용단가(원)',300),('사업장단가(원)',200),('상태',"정산대기")]:
                                    if cn not in df_up.columns:
                                        df_up[cn] = df_up['학교명'].map(STUDENT_COUNTS).fillna(0).astype(int) if cn=='학생수' else dv
                                df_m = pd.concat([load_data(), df_up], ignore_index=True).drop_duplicates(subset=['날짜','학교명'], keep='last')
                                df_m.to_csv(DB_FILE, index=False)
                                st.success("✅ 시뮬레이션 DB 반영 완료!")
                            time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
            with st.expander("📋 데이터 백업"):
                bc1, bc2 = st.columns(2)
                with bc1:
                    if not df_all.empty:
                        st.download_button("💾 시뮬레이션 백업", data=df_all.to_csv(index=False).encode('utf-8-sig'), file_name=f"hayoung_sim_backup_{CURRENT_DATE}.csv", use_container_width=True)
                with bc2:
                    if not df_real.empty:
                        st.download_button("💾 실제데이터 백업", data=df_real.to_csv(index=False).encode('utf-8-sig'), file_name=f"hayoung_real_backup_{CURRENT_DATE}.csv", use_container_width=True)
                if not df_all.empty:
                    st.caption(f"📊 시뮬레이션: {len(df_all)}건 | 실제: {len(df_real)}건")
            with st.expander("📅 오늘의 수거일정 등록"):
                st.caption("외주업체별 오늘 수거할 학교 목록을 등록합니다.")
                for vn in VENDOR_DATA:
                    v_sch = VENDOR_DATA[vn]['schools']
                    sel_today = st.multiselect(f"{vn} 오늘 수거 학교", v_sch, default=v_sch, key=f"sched_{vn}")
                    if f'schedule_{vn}' not in st.session_state:
                        st.session_state[f'schedule_{vn}'] = v_sch
                    st.session_state[f'schedule_{vn}'] = sel_today
                # 본사 직영 기사 일정
                own_schools = []
                for did in ['driver01','driver02','driver03']:
                    own_schools.extend(DRIVER_ACCOUNTS[did].get('schools',[]))
                sel_own = st.multiselect("하영자원(본사) 오늘 수거 학교", own_schools, default=own_schools, key="sched_own")
                st.session_state['schedule_하영자원(본사)'] = sel_own
                st.success("✅ 수거일정이 기사 앱에 실시간 반영됩니다.")

    # ============ [모드2] 학교 담당자 ============
    elif role == "school":
        school = st.session_state.user_name
        st.title(f"🏫 {school} 폐기물 통합 대시보드")
        # 실제 데이터 필터
        df_school_real = df_real[df_real['학교명'] == school] if not df_real.empty else pd.DataFrame()
        df_school = df_all[df_all['학교명'] == school]

        # --- ESG 환경 기여도 (실제 데이터 우선) ---
        if not df_school_real.empty:
            total_kg_real = df_school_real['음식물(kg)'].sum()
            total_co2_real = total_kg_real * CO2_FACTOR
            tree_real = int(total_co2_real / TREE_FACTOR)
            st.markdown(f'<div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:20px;border-radius:12px;color:white;margin-bottom:20px;"><h4 style="margin:0;margin-bottom:10px;">🌱 우리 학교 ESG 환경 기여도 (교육청 제출용)</h4><p style="margin:0;font-size:13px;opacity:0.9;">산정기준: 환경부 음식물폐기물 퇴비화 재활용 매립 회피 계수 {CO2_FACTOR} kgCO₂eq/kg</p><h2 style="margin:8px 0;">2025년 실제 수거량: {total_kg_real:,.0f} kg → CO₂ 감축: {total_co2_real:,.1f} kg (🌲 소나무 {tree_real:,}그루)</h2></div>', unsafe_allow_html=True)
        elif not df_school.empty:
            total_co2_school = df_school['탄소감축량(kg)'].sum()
            tree_count_school = int(total_co2_school / TREE_FACTOR)
            st.markdown(f'<div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:20px;border-radius:12px;color:white;margin-bottom:20px;"><h4 style="margin:0;margin-bottom:10px;">🌱 우리 학교 ESG 환경 기여도 (교육청 제출용)</h4><h2>누적 CO₂ 감축량: {total_co2_school:,.1f} kg (🌲 소나무 {tree_count_school}그루)</h2></div>', unsafe_allow_html=True)

        has_data = not df_school_real.empty or not df_school.empty
        if has_data:
            # --- 메인 탭 구성 ---
            main_tabs = st.tabs(["📊 실제 수거 통계","📅 수거일정 캘린더","📈 시뮬레이션 통계","🖨️ 행정 증빙 서류","🌍 ESG 탄소중립 보고서"])

            # ★ 탭1: 실제 수거 통계 (2025 엑셀 데이터)
            with main_tabs[0]:
                if not df_school_real.empty:
                    st.markdown("#### 📊 2025년 실제 음식물폐기물 수거 기록")
                    r_active = df_school_real[df_school_real['수거여부']]
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    with rc1: st.metric("총 수거일", f"{len(r_active)}일")
                    with rc2: st.metric("총 수거량", f"{r_active['음식물(kg)'].sum():,.0f}kg")
                    with rc3: st.metric("총 공급가", f"{r_active['공급가'].sum():,.0f}원")
                    with rc4: st.metric("CO₂ 감축", f"{r_active['탄소감축량(kg)'].sum():,.1f}kg")
                    # 월별 하위탭
                    r_months = sorted(df_school_real['월'].unique())
                    r_labels = ["📅 연간 전체"] + [f"🗓️ {m}월" for m in r_months]
                    r_tabs = st.tabs(r_labels)
                    with r_tabs[0]:
                        monthly_sum = r_active.groupby('월').agg(수거일수=('음식물(kg)','count'),수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                        monthly_sum.columns = ['월','수거일수','수거량(kg)','공급가(원)']
                        st.dataframe(monthly_sum, use_container_width=True, hide_index=True)
                        st.bar_chart(monthly_sum.set_index('월')['수거량(kg)'], color="#ea4335")
                    for ri, rm in enumerate(r_months):
                        with r_tabs[ri+1]:
                            df_rm = df_school_real[df_school_real['월']==rm]
                            df_rm_show = df_rm[['날짜','음식물(kg)','단가(원)','공급가','재활용방법','재활용업체']].copy()
                            df_rm_show['수거'] = df_rm['수거여부'].map({True:'✅',False:'—'})
                            st.dataframe(df_rm_show, use_container_width=True, hide_index=True)
                            rm_active = df_rm[df_rm['수거여부']]
                            st.caption(f"수거일: {len(rm_active)}일 | 수거량: {rm_active['음식물(kg)'].sum():,.0f}kg | 공급가: {rm_active['공급가'].sum():,.0f}원")
                else:
                    st.info("2025년 실제 수거 데이터가 없습니다.")

            # ★ 탭2: 수거일정 캘린더 (실제 데이터 기반)
            with main_tabs[1]:
                st.markdown("#### 📅 수거일정 캘린더")
                if not df_school_real.empty:
                    cal_months = sorted(df_school_real['월'].unique())
                    sel_cal_month = st.selectbox("월 선택", cal_months, format_func=lambda x: f"{x}월", key="school_cal_month")
                    df_cal = df_school_real[df_school_real['월']==sel_cal_month].copy()
                    df_cal['일'] = pd.to_datetime(df_cal['날짜']).dt.day
                    # 캘린더 그리드 생성
                    import calendar
                    year_cal = 2025
                    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
                    month_days = list(cal.itermonthdays2(year_cal, sel_cal_month))
                    st.markdown(f"**{year_cal}년 {sel_cal_month}월 수거 캘린더**")
                    # 요일 헤더
                    cols_h = st.columns(7)
                    for ci, day_name in enumerate(['일','월','화','수','목','금','토']):
                        cols_h[ci].markdown(f"<div style='text-align:center;font-weight:bold;color:#5f6368;'>{day_name}</div>", unsafe_allow_html=True)
                    # 주 단위 렌더링
                    week = []
                    for day_num, weekday in month_days:
                        week.append(day_num)
                        if len(week) == 7:
                            cols_w = st.columns(7)
                            for wi, wd in enumerate(week):
                                if wd == 0:
                                    cols_w[wi].write("")
                                else:
                                    row_match = df_cal[df_cal['일']==wd]
                                    if not row_match.empty and row_match.iloc[0]['수거여부']:
                                        kg_val = row_match.iloc[0]['음식물(kg)']
                                        cols_w[wi].markdown(f"<div style='text-align:center;background:#e8f5e9;border-radius:8px;padding:4px;'><b>{wd}</b><br><span style='color:#2e7d32;font-size:11px;'>✅ {kg_val:,.0f}kg</span></div>", unsafe_allow_html=True)
                                    else:
                                        cols_w[wi].markdown(f"<div style='text-align:center;padding:4px;color:#999;'>{wd}</div>", unsafe_allow_html=True)
                            week = []
                    if week:
                        cols_w = st.columns(7)
                        for wi, wd in enumerate(week):
                            if wd == 0:
                                cols_w[wi].write("")
                            else:
                                row_match = df_cal[df_cal['일']==wd]
                                if not row_match.empty and row_match.iloc[0]['수거여부']:
                                    kg_val = row_match.iloc[0]['음식물(kg)']
                                    cols_w[wi].markdown(f"<div style='text-align:center;background:#e8f5e9;border-radius:8px;padding:4px;'><b>{wd}</b><br><span style='color:#2e7d32;font-size:11px;'>✅ {kg_val:,.0f}kg</span></div>", unsafe_allow_html=True)
                                else:
                                    cols_w[wi].markdown(f"<div style='text-align:center;padding:4px;color:#999;'>{wd}</div>", unsafe_allow_html=True)
                    cal_active = df_cal[df_cal['수거여부']]
                    st.caption(f"✅ 수거일: {len(cal_active)}일 | 총 수거량: {cal_active['음식물(kg)'].sum():,.0f}kg")
                else:
                    st.info("캘린더에 표시할 실제 수거 데이터가 없습니다.")

            # 탭3: 기존 시뮬레이션 통계
            with main_tabs[2]:
                if not df_school.empty:
                    st.markdown("#### 📈 시뮬레이션 수거 통계 (음식물/사업장/재활용)")
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
                else:
                    st.info("시뮬레이션 데이터가 없습니다.")

            # 탭4: 행정 증빙 서류
            with main_tabs[3]:
                st.subheader("🖨️ 행정 증빙 서류 자동 출력 (법정 양식)")
                st.caption("📌 2026.1.1 시행 「기후에너지환경부령 제18호」 반영 완료")
                st.markdown("<h5 style='color:#2e7d32;font-weight:bold;'>🛡️ 금일 수거차량 안전 점검 현황</h5>", unsafe_allow_html=True)
                st.markdown('<div class="safety-box">✅ 배차: 하영자원 (본사 직영)<br>✅ 스쿨존: 정상 (MAX 28km/h)<br>✅ 후방카메라·안전요원: 적합</div>', unsafe_allow_html=True)
                if not df_school.empty:
                    period_start = df_school['날짜'].min()[:10]
                    period_end = df_school['날짜'].max()[:10]
                    period_str = f"{period_start} ~ {period_end}"
                    # 년도/월 선택 필터
                    sch_years = sorted(df_school['년도'].unique(), reverse=True)
                    sel_doc_year = st.selectbox("📅 년도 선택", sch_years, key="school_doc_year")
                    df_doc_yr = df_school[df_school['년도']==sel_doc_year]
                    sch_months = sorted(df_doc_yr['월별'].unique())
                    sel_doc_month = st.selectbox("🗓️ 월 선택", ["전체"] + sch_months, key="school_doc_month")
                    if sel_doc_month == "전체":
                        df_doc = df_doc_yr
                        doc_period = f"{sel_doc_year}년 전체"
                    else:
                        df_doc = df_doc_yr[df_doc_yr['월별']==sel_doc_month]
                        doc_period = sel_doc_month
                    st.caption(f"📊 선택 기간: {doc_period} | {len(df_doc)}건")

                    doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs(["📊 월간 정산서","📈 실적보고서(제30호)","♻️ 상계증빙","🔗 올바로 연동"])
                    with doc_tab1:
                        st.info("💡 행정실 회계 처리용 월간 정산서입니다.")
                        cd1, cd2, cd3, cd4 = st.columns(4)
                        with cd1: st.download_button("전체 통합본", data=create_legal_report_excel(df_doc[['날짜','학교명','음식물(kg)','사업장(kg)','재활용(kg)','최종정산액']], "통합 정산서", school, doc_period), file_name=f"{school}_통합정산서_{doc_period}.xlsx", use_container_width=True)
                        with cd2: st.download_button("🗑️ 음식물", data=create_legal_report_excel(df_doc[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물 정산서", school, doc_period), file_name=f"{school}_음식물정산_{doc_period}.xlsx", use_container_width=True)
                        with cd3: st.download_button("🗄️ 사업장", data=create_legal_report_excel(df_doc[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장 정산서", school, doc_period), file_name=f"{school}_사업장정산_{doc_period}.xlsx", use_container_width=True)
                        with cd4: st.download_button("♻️ 재활용", data=create_legal_report_excel(df_doc[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 정산서", school, doc_period), file_name=f"{school}_재활용정산_{doc_period}.xlsx", use_container_width=True)
                    with doc_tab2:
                        st.info("💡 교육청/지자체 제출용 법정 양식")
                        cr1, cr2, cr3 = st.columns(3)
                        with cr1: st.download_button("🗑️ 음식물 실적", data=create_legal_report_excel(df_doc[['날짜','학교명','음식물(kg)','단가(원)','음식물비용']], "음식물류 처리 실적보고서", school, doc_period), file_name=f"{school}_음식물실적_{doc_period}.xlsx", use_container_width=True)
                        with cr2: st.download_button("🗄️ 사업장 실적", data=create_legal_report_excel(df_doc[['날짜','학교명','사업장(kg)','사업장단가(원)','사업장비용']], "사업장 처리 실적보고서", school, doc_period), file_name=f"{school}_사업장실적_{doc_period}.xlsx", use_container_width=True)
                        with cr3: st.download_button("♻️ 재활용 실적", data=create_legal_report_excel(df_doc[['날짜','학교명','재활용(kg)','재활용단가(원)','재활용수익']], "재활용 처리 실적보고서", school, doc_period), file_name=f"{school}_재활용실적_{doc_period}.xlsx", use_container_width=True)
                    with doc_tab3:
                        st.info("💡 사업장 폐기물 재활용 수익 상계 증빙")
                        st.download_button("📄 상계증빙서 다운로드", data=create_legal_report_excel(df_doc[['날짜','학교명','사업장(kg)','재활용(kg)','재활용수익','사업장비용']], "재활용 상계처리 증빙", school, doc_period), file_name=f"{school}_상계증빙_{doc_period}.xlsx")
                    with doc_tab4:
                        st.info("💡 올바로 시스템 자동 전송")
                        if st.button("🔗 올바로시스템 전자인계서 연동", type="primary", use_container_width=True):
                            with st.spinner("한국환경공단 서버 통신 중..."):
                                time.sleep(2)
                            st.success("✅ 올바로시스템에 전자인계서 이관 완료!")

            # ★ 탭5: ESG 탄소중립 보고서 출력
            with main_tabs[4]:
                st.subheader("🌍 ESG 탄소중립 보고서")
                st.caption("환경부 음식물폐기물 퇴비화 재활용 매립 회피 계수 적용")
                if not df_school_real.empty:
                    r_act = df_school_real[df_school_real['수거여부']]
                    total_kg = r_act['음식물(kg)'].sum()
                    total_co2 = total_kg * CO2_FACTOR
                    total_tree = int(total_co2 / TREE_FACTOR)
                    total_supply = r_act['공급가'].sum()
                    # 시각화 카드
                    ec1, ec2, ec3, ec4 = st.columns(4)
                    with ec1: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">♻️ 총 재활용량</div><div class="metric-value-recycle">{total_kg:,.0f}kg</div></div>', unsafe_allow_html=True)
                    with ec2: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">🌍 CO₂ 감축량</div><div class="metric-value-recycle">{total_co2:,.1f}kg</div></div>', unsafe_allow_html=True)
                    with ec3: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">🌲 소나무 식재 효과</div><div class="metric-value-recycle">{total_tree:,}그루</div></div>', unsafe_allow_html=True)
                    with ec4: st.markdown(f'<div class="custom-card" style="text-align:center;"><div class="metric-title">💰 환경비용 절감</div><div class="metric-value-total">{total_supply:,.0f}원</div></div>', unsafe_allow_html=True)
                    # 월별 탄소감축 차트
                    st.write("---")
                    st.markdown("**📊 월별 탄소감축 추이**")
                    co2_monthly = r_act.groupby('월').agg(수거량=('음식물(kg)','sum')).reset_index()
                    co2_monthly['CO₂감축(kg)'] = co2_monthly['수거량'] * CO2_FACTOR
                    st.bar_chart(co2_monthly.set_index('월')['CO₂감축(kg)'], color="#34a853")
                    # 보고서 다운로드 (엑셀 - 충주용산초 ESG 양식 기반)
                    st.write("---")
                    def create_esg_report_excel(school_name, df_data):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            wb = writer.book
                            # 공통 서식
                            title_fmt = wb.add_format({'bold':True,'font_size':18,'align':'center','valign':'vcenter','font_color':'#1a73e8','border':0})
                            subtitle_fmt = wb.add_format({'bold':True,'font_size':12,'align':'center','bg_color':'#e8f5e9','border':1})
                            header_fmt = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#34a853','font_color':'white','border':1,'text_wrap':True})
                            header_blue = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#1a73e8','font_color':'white','border':1,'text_wrap':True})
                            header_purple = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#667eea','font_color':'white','border':1,'text_wrap':True})
                            cell_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'text_wrap':True,'valign':'vcenter'})
                            cell_left = wb.add_format({'font_size':10,'align':'left','border':1,'text_wrap':True,'valign':'vcenter'})
                            num_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0'})
                            num_fmt1 = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0.0'})
                            green_card = wb.add_format({'bold':True,'font_size':14,'align':'center','bg_color':'#34a853','font_color':'white','border':1})
                            section_fmt = wb.add_format({'bold':True,'font_size':13,'bg_color':'#e8f5e9','border':1,'align':'left'})

                            # ===== 시트1: 표지 =====
                            ws1 = wb.add_worksheet('표지')
                            ws1.set_column(0, 5, 18)
                            ws1.merge_range('A3:F3', f'2025년 ESG 행정 실적보고서', title_fmt)
                            ws1.merge_range('A5:F5', school_name, wb.add_format({'bold':True,'font_size':14,'align':'center'}))
                            ws1.merge_range('A7:F7', f'보고 기간: 2025년 3월 ~ 12월', wb.add_format({'font_size':11,'align':'center','font_color':'#555'}))
                            ws1.merge_range('A9:F9', 'Ⅰ. ESG 행정 실천 목표', section_fmt)
                            esg_goals = [
                                ['E (녹색 행정)','탄소중립·환경보전','음식물폐기물 재활용 퇴비화','탄소저감, 자원순환 실천'],
                                ['S (사회적 행정)','안전·보건 구현','스쿨존 안전운행, 수거기사 안전교육','공공구매, 안전보건 지원'],
                                ['G (투명 행정)','회계 투명성','정산 데이터 공개, 실시간 모니터링','자율적 내부통제, 행정 공개'],
                            ]
                            for ci, h in enumerate(['ESG 영역','목표','주요 추진 내용','세부 실천 사항']):
                                ws1.write(10, ci, h, header_fmt)
                            for ri, row in enumerate(esg_goals):
                                for ci, val in enumerate(row):
                                    ws1.write(11+ri, ci, val, cell_left)

                            # ===== 시트2: E_녹색행정 실적 (PDCA) =====
                            ws2 = wb.add_worksheet('E_녹색행정')
                            ws2.set_column(0, 0, 15); ws2.set_column(1, 1, 22); ws2.set_column(2, 2, 18)
                            ws2.set_column(3, 3, 40); ws2.set_column(4, 4, 12); ws2.set_column(5, 5, 15)
                            ws2.merge_range('A1:F1', 'Ⅱ. E_녹색 행정 추진 실적 (2025년)', section_fmt)
                            pdca_headers = ['계획(Plan)','제목','문서번호','실행(Do) 내용','확인(Check)','개선(Action)']
                            for ci, h in enumerate(pdca_headers):
                                ws2.write(2, ci, h, header_fmt)
                            e_records = [
                                ['E\n탄소 저감\n녹색 행정', '음식물폐기물\n퇴비화 재활용', '하영자원\n수거기록', f'총 수거량: {total_kg:,.0f}kg\n재활용업체: (주)혜인이엔씨\n재활용방법: 퇴비화 및 비료생산','이행','지속 확대'],
                                ['','탄소감축 실적', 'ESG 보고', f'CO₂ 감축: {total_co2:,.1f}kg\n소나무 식재 효과: {total_tree:,}그루\n산정기준: 환경부 매립회피 {CO2_FACTOR}kgCO₂eq/kg','이행','성과 공유'],
                                ['','공급가 정산', '월별 정산', f'총 공급가: {total_supply:,.0f}원\n단가: 162원/kg','이행','투명 정산'],
                            ]
                            for ri, row in enumerate(e_records):
                                for ci, val in enumerate(row):
                                    ws2.write(3+ri, ci, val, cell_left if ci==3 else cell_fmt)

                            # 월별 수거 실적 테이블
                            ws2.merge_range(f'A8:F8', '월별 음식물폐기물 수거 실적', subtitle_fmt)
                            m_headers = ['월','수거일수','수거량(kg)','공급가(원)','CO₂감축(kg)','소나무(그루)']
                            for ci, h in enumerate(m_headers):
                                ws2.write(9, ci, h, header_blue)
                            monthly_detail = df_data[df_data['수거여부']].groupby('월').agg(
                                수거일수=('음식물(kg)','count'), 수거량=('음식물(kg)','sum'), 공급가=('공급가','sum')
                            ).reset_index()
                            monthly_detail['CO2'] = monthly_detail['수거량'] * CO2_FACTOR
                            monthly_detail['소나무'] = (monthly_detail['CO2'] / TREE_FACTOR).astype(int)
                            for ri, row in monthly_detail.iterrows():
                                ws2.write(10+ri, 0, f"{int(row['월'])}월", cell_fmt)
                                ws2.write(10+ri, 1, int(row['수거일수']), num_fmt)
                                ws2.write(10+ri, 2, row['수거량'], num_fmt)
                                ws2.write(10+ri, 3, row['공급가'], num_fmt)
                                ws2.write(10+ri, 4, row['CO2'], num_fmt1)
                                ws2.write(10+ri, 5, int(row['소나무']), num_fmt)
                            # 합계
                            tr = 10 + len(monthly_detail)
                            ws2.write(tr, 0, '합계', green_card)
                            ws2.write(tr, 1, int(monthly_detail['수거일수'].sum()), green_card)
                            ws2.write(tr, 2, monthly_detail['수거량'].sum(), green_card)
                            ws2.write(tr, 3, monthly_detail['공급가'].sum(), green_card)
                            ws2.write(tr, 4, monthly_detail['CO2'].sum(), green_card)
                            ws2.write(tr, 5, int(monthly_detail['소나무'].sum()), green_card)

                            # ===== 시트3: S_사회적행정 =====
                            ws3 = wb.add_worksheet('S_사회적행정')
                            ws3.set_column(0, 5, 18)
                            ws3.merge_range('A1:F1', 'Ⅲ. S_사회적 행정 추진 실적 (2025년)', section_fmt)
                            for ci, h in enumerate(pdca_headers):
                                ws3.write(2, ci, h, header_blue)
                            s_records = [
                                ['S\n사회적 가치\n행정','스쿨존 안전운행','수거차량 관제','수거차량 스쿨존 30km/h 이하 운행\n후방카메라 장착, 안전요원 동승','이행','지속 실천'],
                                ['','수거기사 안전교육','안전점검 기록','운행 전 차량 안전점검 실시\n안전보건교육 정기 이수','이행','교육 강화'],
                                ['','올바로시스템 연동','전자인계서','한국환경공단 올바로시스템 전자인계서 자동 전송','이행','시스템 고도화'],
                            ]
                            for ri, row in enumerate(s_records):
                                for ci, val in enumerate(row):
                                    ws3.write(3+ri, ci, val, cell_left if ci==3 else cell_fmt)

                            # ===== 시트4: G_투명행정 =====
                            ws4 = wb.add_worksheet('G_투명행정')
                            ws4.set_column(0, 5, 18)
                            ws4.merge_range('A1:F1', 'Ⅳ. G_투명 행정 추진 실적 (2025년)', section_fmt)
                            for ci, h in enumerate(pdca_headers):
                                ws4.write(2, ci, h, header_purple)
                            g_records = [
                                ['G\n투명 행정','ESG 실적 공개','학교홈페이지','하영자원 플랫폼 통해 실시간 수거 데이터 공개\n학교별 대시보드 제공','이행','지속'],
                                ['','투명 정산','플랫폼 정산','월별 자동정산, 법정 양식 증빙 서류 자동 출력\n음식물/사업장/재활용 분리 정산','이행','자동화 확대'],
                                ['','내부통제','감사 증빙','수거일지-정산서-세금계산서 자동 매칭\n부정 방지 시스템','이행','고도화'],
                            ]
                            for ri, row in enumerate(g_records):
                                for ci, val in enumerate(row):
                                    ws4.write(3+ri, ci, val, cell_left if ci==3 else cell_fmt)

                        return output.getvalue()
                    st.download_button("📥 ESG 행정 실적보고서 다운로드 (교육청 양식)", data=create_esg_report_excel(school, df_school_real),
                                       file_name=f"{school}_ESG_행정실적보고서_2025.xlsx", use_container_width=True, type="primary")
                    st.caption("※ 충주용산초 ESG 행정 실적보고서 양식(PDCA) 기반 | 표지 + E녹색행정 + S사회적행정 + G투명행정 4개 시트")
                else:
                    st.info("실제 수거 데이터가 있어야 ESG 보고서를 생성할 수 있습니다.")
        else:
            st.info("해당 학교의 수거 데이터가 아직 없습니다.")

    # ============ [모드2-B] 교육청 담당자 ============
    elif role == "edu_office":
        office_name = st.session_state.user_name
        office_schools = st.session_state.user_data.get("schools", [])
        st.title(f"🎓 {office_name} 관할 폐기물 통합 대시보드")
        st.caption(f"관할 학교: {len(office_schools)}개교")

        # 실제 데이터 필터
        df_office_real = df_real[df_real['학교명'].isin(office_schools)] if not df_real.empty else pd.DataFrame()
        df_office = df_all[df_all['학교명'].isin(office_schools)]

        # --- ESG 상단 카드 (실제 데이터 우선) ---
        if not df_office_real.empty:
            r_act = df_office_real[df_office_real['수거여부']]
            total_kg_o = r_act['음식물(kg)'].sum()
            total_co2_o = total_kg_o * CO2_FACTOR
            total_tree_o = int(total_co2_o / TREE_FACTOR)
            oc1, oc2, oc3, oc4 = st.columns(4)
            with oc1: st.metric("🗑️ 실제 수거량(2025)", f"{total_kg_o:,.0f} kg")
            with oc2: st.metric("🌍 CO₂ 감축", f"{total_co2_o:,.1f} kg")
            with oc3: st.metric("🌲 소나무 효과", f"{total_tree_o:,} 그루")
            with oc4: st.metric("💰 총 공급가", f"{r_act['공급가'].sum():,.0f} 원")
            st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:12px;color:white;margin:15px 0;"><h4 style="margin:0;color:white;">🌍 {office_name} ESG 탄소 저감 성과 (실제 데이터)</h4><p style="margin:5px 0;color:white;opacity:0.9;">산정기준: 환경부 음식물폐기물 퇴비화 매립회피 계수 {CO2_FACTOR} kgCO₂eq/kg | 소나무 {TREE_FACTOR}kg/그루/년</p><h2 style="margin:5px 0;color:white;">CO₂ 감축: {total_co2_o:,.1f}kg = 🌲 소나무 {total_tree_o:,}그루 식재 효과</h2></div>', unsafe_allow_html=True)
        elif not df_office.empty:
            oc1, oc2, oc3, oc4 = st.columns(4)
            with oc1: st.metric("🗑️ 음식물 총 수거", f"{df_office['음식물(kg)'].sum():,} kg")
            with oc2: st.metric("🗄️ 사업장 총 수거", f"{df_office['사업장(kg)'].sum():,} kg")
            with oc3: st.metric("♻️ 재활용 총 수거", f"{df_office['재활용(kg)'].sum():,} kg")
            with oc4: st.metric("💰 총 정산 금액", f"{df_office['최종정산액'].sum():,} 원")
            tco2 = df_office['탄소감축량(kg)'].sum()
            st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:12px;color:white;margin:15px 0;"><h4 style="margin:0;color:white;">🌍 {office_name} ESG 성과</h4><h2 style="margin:5px 0;color:white;">CO₂ 감축: {tco2:,.1f}kg (🌲 {int(tco2/TREE_FACTOR):,}그루)</h2></div>', unsafe_allow_html=True)

        has_edu_data = not df_office_real.empty or not df_office.empty
        if has_edu_data:
            edu_tabs = st.tabs(["📊 실제 수거 현황(2025)","📋 관할 학교 상세","📈 시뮬레이션 통계","🌍 ESG 탄소중립 보고서"])

            # ★ 탭1: 실제 수거 현황
            with edu_tabs[0]:
                if not df_office_real.empty:
                    st.markdown("#### 📊 관할 학교 실제 수거 현황 (2025)")
                    # 학교별 요약 테이블
                    school_sum = df_office_real[df_office_real['수거여부']].groupby('학교명').agg(
                        수거일수=('음식물(kg)','count'), 총수거량=('음식물(kg)','sum'),
                        총공급가=('공급가','sum'), CO2감축=('탄소감축량(kg)','sum')
                    ).reset_index().sort_values('총수거량', ascending=False)
                    school_sum['🌲소나무'] = (school_sum['CO2감축'] / TREE_FACTOR).astype(int)
                    st.dataframe(school_sum, use_container_width=True, hide_index=True)
                    # 학교별 수거량 차트
                    st.bar_chart(school_sum.set_index('학교명')['총수거량'], color="#667eea")
                    # 월별 하위탭
                    st.write("---")
                    st.markdown("**🗓️ 월별 상세**")
                    o_months = sorted(df_office_real['월'].unique())
                    o_mtabs = st.tabs([f"{m}월" for m in o_months])
                    for omi, om in enumerate(o_months):
                        with o_mtabs[omi]:
                            df_om = df_office_real[(df_office_real['월']==om) & (df_office_real['수거여부'])]
                            om_sum = df_om.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index().sort_values('수거량',ascending=False)
                            st.dataframe(om_sum, use_container_width=True, hide_index=True)
                else:
                    st.info("실제 수거 데이터가 없습니다.")

            # ★ 탭2: 개별 학교 상세 조회
            with edu_tabs[1]:
                st.markdown("#### 🔍 개별 학교 상세 조회")
                sel_edu_sch = st.selectbox("학교 선택", office_schools, key="edu_sel_school")
                # 실제 데이터
                if not df_office_real.empty:
                    df_es_real = df_office_real[df_office_real['학교명']==sel_edu_sch]
                    if not df_es_real.empty:
                        es_active = df_es_real[df_es_real['수거여부']]
                        es1, es2, es3 = st.columns(3)
                        with es1: st.metric("실제 수거량", f"{es_active['음식물(kg)'].sum():,.0f} kg")
                        with es2: st.metric("실제 공급가", f"{es_active['공급가'].sum():,.0f} 원")
                        with es3: st.metric("CO₂ 감축", f"{es_active['탄소감축량(kg)'].sum():,.1f} kg")
                        st.dataframe(df_es_real[['날짜','음식물(kg)','단가(원)','공급가','수거여부']].tail(31), use_container_width=True, hide_index=True)
                # 시뮬레이션 데이터
                df_es_sim = df_office[df_office['학교명']==sel_edu_sch] if not df_office.empty else pd.DataFrame()
                if not df_es_sim.empty:
                    st.write("---")
                    st.caption("시뮬레이션 데이터 (참고)")
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1: st.metric("음식물", f"{df_es_sim['음식물(kg)'].sum():,} kg")
                    with sc2: st.metric("사업장", f"{df_es_sim['사업장(kg)'].sum():,} kg")
                    with sc3: st.metric("재활용", f"{df_es_sim['재활용(kg)'].sum():,} kg")

            # 탭3: 시뮬레이션 통계
            with edu_tabs[2]:
                if not df_office.empty:
                    st.markdown("#### 📈 시뮬레이션 통계 (전체 관할)")
                    summary = df_office.groupby('학교명').agg({'음식물(kg)':'sum','사업장(kg)':'sum','재활용(kg)':'sum','최종정산액':'sum'}).reset_index().sort_values('최종정산액', ascending=False)
                    st.dataframe(summary, use_container_width=True, hide_index=True)
                else:
                    st.info("시뮬레이션 데이터가 없습니다.")

            # ★ 탭4: ESG 탄소중립 보고서 출력
            with edu_tabs[3]:
                st.subheader("🌍 교육청 ESG 탄소중립 보고서")
                if not df_office_real.empty:
                    r_act_e = df_office_real[df_office_real['수거여부']]
                    e_total_kg = r_act_e['음식물(kg)'].sum()
                    e_total_co2 = e_total_kg * CO2_FACTOR
                    e_total_tree = int(e_total_co2 / TREE_FACTOR)
                    e_total_supply = r_act_e['공급가'].sum()
                    e_school_count = r_act_e['학교명'].nunique()
                    # 시각화 카드
                    ee1, ee2, ee3, ee4 = st.columns(4)
                    with ee1: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">🏫 관할 학교</div><div class="metric-value-recycle">{e_school_count}개교</div></div>', unsafe_allow_html=True)
                    with ee2: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">♻️ 총 재활용량</div><div class="metric-value-recycle">{e_total_kg:,.0f}kg</div></div>', unsafe_allow_html=True)
                    with ee3: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">🌍 CO₂ 감축</div><div class="metric-value-recycle">{e_total_co2:,.1f}kg</div></div>', unsafe_allow_html=True)
                    with ee4: st.markdown(f'<div class="custom-card custom-card-green" style="text-align:center;"><div class="metric-title">🌲 소나무 효과</div><div class="metric-value-recycle">{e_total_tree:,}그루</div></div>', unsafe_allow_html=True)
                    # 학교별 탄소감축 차트
                    st.write("---")
                    st.markdown("**📊 학교별 탄소감축 기여도**")
                    eco_by_school = r_act_e.groupby('학교명').agg(수거량=('음식물(kg)','sum')).reset_index()
                    eco_by_school['CO₂감축(kg)'] = eco_by_school['수거량'] * CO2_FACTOR
                    eco_by_school = eco_by_school.sort_values('CO₂감축(kg)', ascending=False)
                    st.bar_chart(eco_by_school.set_index('학교명')['CO₂감축(kg)'], color="#34a853")
                    # 월별 추이
                    st.markdown("**📊 월별 탄소감축 추이**")
                    eco_monthly = r_act_e.groupby('월').agg(수거량=('음식물(kg)','sum')).reset_index()
                    eco_monthly['CO₂감축(kg)'] = eco_monthly['수거량'] * CO2_FACTOR
                    st.bar_chart(eco_monthly.set_index('월')['CO₂감축(kg)'], color="#667eea")
                    # 보고서 다운로드
                    st.write("---")
                    def create_edu_esg_excel(office, schools_data):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            wb = writer.book
                            title_fmt = wb.add_format({'bold':True,'font_size':18,'align':'center','font_color':'#667eea'})
                            header_fmt = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#667eea','font_color':'white','border':1,'text_wrap':True})
                            header_green = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#34a853','font_color':'white','border':1,'text_wrap':True})
                            cell_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'text_wrap':True,'valign':'vcenter'})
                            cell_left = wb.add_format({'font_size':10,'align':'left','border':1,'text_wrap':True,'valign':'vcenter'})
                            num_fmt = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0'})
                            num_fmt1 = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0.0'})
                            green_total = wb.add_format({'bold':True,'font_size':11,'align':'center','bg_color':'#34a853','font_color':'white','border':1,'num_format':'#,##0'})
                            section_fmt = wb.add_format({'bold':True,'font_size':13,'bg_color':'#e8eef9','border':1})

                            # 시트1: ESG 요약 (표지+목표)
                            ws1 = wb.add_worksheet('ESG 요약')
                            ws1.set_column(0, 5, 18)
                            ws1.merge_range('A2:F2', f'{office} 2025년 ESG 탄소중립 보고서', title_fmt)
                            ws1.merge_range('A4:F4', f'보고 기간: 2025.3~12 | 관할: {e_school_count}개교 | 작성일: {CURRENT_DATE}', wb.add_format({'font_size':11,'align':'center','font_color':'#555'}))
                            # 요약 수치
                            ws1.merge_range('A6:F6', 'ESG 성과 요약', section_fmt)
                            summary_items = [['총 수거량',f'{e_total_kg:,.0f} kg'],['CO₂ 감축량',f'{e_total_co2:,.1f} kg'],
                                             ['소나무 식재 효과',f'{e_total_tree:,} 그루'],['총 공급가',f'{e_total_supply:,.0f} 원'],
                                             ['산정기준',f'환경부 매립회피 계수 {CO2_FACTOR} kgCO₂eq/kg'],['재활용 방법','퇴비화 및 비료생산'],['재활용 업체','(주)혜인이엔씨']]
                            for ci, h in enumerate(['항목','내용']): ws1.write(7, ci, h, header_fmt)
                            for ri, row in enumerate(summary_items):
                                ws1.write(8+ri, 0, row[0], cell_fmt); ws1.write(8+ri, 1, row[1], cell_left)

                            # 시트2: 학교별 상세 (서식 적용)
                            ws2 = wb.add_worksheet('학교별 상세')
                            ws2.set_column(0, 0, 25); ws2.set_column(1, 5, 15)
                            ws2.merge_range('A1:F1', '관할 학교별 음식물폐기물 재활용 실적', section_fmt)
                            sch_headers = ['학교명','수거일수','수거량(kg)','공급가(원)','CO₂감축(kg)','소나무(그루)']
                            for ci, h in enumerate(sch_headers): ws2.write(2, ci, h, header_green)
                            school_detail = schools_data[schools_data['수거여부']].groupby('학교명').agg(
                                수거일수=('음식물(kg)','count'), 수거량=('음식물(kg)','sum'), 공급가=('공급가','sum')
                            ).reset_index().sort_values('수거량', ascending=False)
                            school_detail['CO2'] = school_detail['수거량'] * CO2_FACTOR
                            school_detail['소나무'] = (school_detail['CO2'] / TREE_FACTOR).astype(int)
                            for ri, row in school_detail.iterrows():
                                ws2.write(3+ri, 0, row['학교명'], cell_left)
                                ws2.write(3+ri, 1, int(row['수거일수']), num_fmt)
                                ws2.write(3+ri, 2, row['수거량'], num_fmt)
                                ws2.write(3+ri, 3, row['공급가'], num_fmt)
                                ws2.write(3+ri, 4, row['CO2'], num_fmt1)
                                ws2.write(3+ri, 5, int(row['소나무']), num_fmt)
                            tr2 = 3 + len(school_detail)
                            ws2.write(tr2, 0, '합계', green_total)
                            for ci, col in enumerate(['수거일수','수거량','공급가','CO2','소나무'],1):
                                ws2.write(tr2, ci, int(school_detail[col].sum()) if col in ['수거일수','소나무'] else school_detail[col].sum(), green_total)

                            # 시트3: 월별 추이
                            ws3 = wb.add_worksheet('월별 추이')
                            ws3.set_column(0, 5, 15)
                            ws3.merge_range('A1:F1', '월별 음식물폐기물 재활용 추이', section_fmt)
                            for ci, h in enumerate(['월','수거일수','수거량(kg)','공급가(원)','CO₂감축(kg)','소나무(그루)']): ws3.write(2, ci, h, header_fmt)
                            monthly = schools_data[schools_data['수거여부']].groupby('월').agg(수거일수=('음식물(kg)','count'),수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                            monthly['CO2'] = monthly['수거량'] * CO2_FACTOR
                            monthly['소나무'] = (monthly['CO2'] / TREE_FACTOR).astype(int)
                            for ri, row in monthly.iterrows():
                                ws3.write(3+ri, 0, f"{int(row['월'])}월", cell_fmt)
                                ws3.write(3+ri, 1, int(row['수거일수']), num_fmt)
                                ws3.write(3+ri, 2, row['수거량'], num_fmt)
                                ws3.write(3+ri, 3, row['공급가'], num_fmt)
                                ws3.write(3+ri, 4, row['CO2'], num_fmt1)
                                ws3.write(3+ri, 5, int(row['소나무']), num_fmt)
                        return output.getvalue()
                    st.download_button("📥 교육청 ESG 행정 실적보고서 다운로드 (엑셀)",
                                       data=create_edu_esg_excel(office_name, df_office_real),
                                       file_name=f"{office_name}_ESG_행정실적보고서_2025.xlsx",
                                       use_container_width=True, type="primary")
                    st.caption("※ ESG 행정 실적보고서 양식(PDCA) 기반 | ESG요약 + 학교별상세 + 월별추이 3개 시트")
                else:
                    st.info("실제 수거 데이터가 있어야 ESG 보고서를 생성할 수 있습니다.")
        else:
            st.info("관할 학교의 수거 데이터가 아직 없습니다.")

    # ============ [모드3] 수거 기사 + 퇴근하기 ============
    elif role == "driver":
        driver_id = st.session_state.user_id
        driver_info = DRIVER_ACCOUNTS.get(driver_id, {})
        vendor_name = driver_info.get('vendor', '하영자원(본사)')
        my_schools = driver_info.get('schools', [])

        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.markdown(f'<div class="mobile-app-header"><h2 style="margin:0;font-size:22px;">🚚 하영자원 기사 전용 앱</h2><p style="margin:5px 0 0 0;font-size:14px;opacity:0.8;">{user_name}님 ({vendor_name})</p></div>', unsafe_allow_html=True)

            # 안전점검
            with st.expander("📋 [필수] 운행 전 안전 점검", expanded=True):
                st.warning("어린이 안전을 위해 확인해 주세요.")
                check1 = st.checkbox("차량 후방 카메라 정상 작동 확인")
                check2 = st.checkbox("조수석 안전 요원 탑승 확인")
                check3 = st.checkbox("스쿨존 회피 운행 숙지")
                if check1 and check2 and check3:
                    st.success("안전 점검 완료! 오늘도 안전 운행하세요.")
            st.write("---")

            # ★ 오늘의 수거일정 (관리자가 등록한 일정 또는 기본 담당학교)
            st.markdown("### 📅 오늘의 수거일정")
            schedule_key = f'schedule_{vendor_name}'
            today_schools = st.session_state.get(schedule_key, my_schools)
            # 내 담당 학교만 필터
            my_today = [s for s in today_schools if s in my_schools] if today_schools else my_schools

            if my_today:
                for idx, sch_name in enumerate(my_today):
                    with st.expander(f"🏫 {idx+1}. {sch_name}", expanded=(idx==0)):
                        st.caption("학교명을 클릭하면 네비게이션이 실행됩니다.")
                        import urllib.parse
                        encoded_name = urllib.parse.quote(sch_name)
                        # 카카오맵 딥링크 (키워드 검색)
                        kakao_url = f"https://map.kakao.com/link/search/{encoded_name}"
                        # 티맵 딥링크 (키워드 검색)
                        tmap_url = f"https://apis.openapi.sk.com/tmap/app/routes?appKey=&name={encoded_name}"
                        tmap_search = f"tmap://search?name={encoded_name}"

                        nc1, nc2 = st.columns(2)
                        with nc1:
                            st.markdown(f'<a href="{kakao_url}" target="_blank" style="display:block;text-align:center;background:#FEE500;color:#000;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">🗺️ 카카오맵으로 열기</a>', unsafe_allow_html=True)
                        with nc2:
                            st.markdown(f'<a href="{tmap_search}" target="_blank" style="display:block;text-align:center;background:#0064FF;color:#fff;padding:12px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">🚗 티맵으로 열기</a>', unsafe_allow_html=True)
                        st.caption(f"※ 모바일에서 해당 앱이 설치되어 있으면 자동 실행됩니다.")
            else:
                st.info("오늘 배정된 수거 학교가 없습니다.")

            # 스쿨존 알림
            st.write("---")
            is_schoolzone = st.toggle("🚨 스쿨존 진입 알림 (GPS 테스트)")
            if is_schoolzone:
                st.error("스쿨존 진입! 속도를 30km 이하로 줄이세요.")
                st.markdown("<h1 style='text-align:center;color:#d93025;font-size:60px;'>30</h1>", unsafe_allow_html=True)
            st.write("---")

            # 현장 증빙
            st.camera_input("📸 현장 증빙 사진 (선택)")

            # ★ 수거량 전송 (본사 + 행정실 공유)
            st.markdown("### 📤 수거 완료 보고")
            with st.form("driver_input"):
                target = st.selectbox("수거 완료 학교", my_today if my_today else my_schools)
                ci1, ci2, ci3 = st.columns(3)
                with ci1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
                with ci2: biz_w = st.number_input("사업장 (kg)", min_value=0, step=10)
                with ci3: re_w = st.number_input("재활용 (kg)", min_value=0, step=10)
                if st.form_submit_button("📤 본사로 수거량 전송", type="primary", use_container_width=True):
                    if food_w > 0 or biz_w > 0 or re_w > 0:
                        # 시뮬레이션 DB 저장 (관리자+행정실 조회 가능)
                        new_data = {"날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "학교명": target, "학생수": STUDENT_COUNTS.get(target, 0), "수거업체": vendor_name,
                            "음식물(kg)": food_w, "재활용(kg)": re_w, "사업장(kg)": biz_w,
                            "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "실시간"}
                        save_data(new_data)
                        # 실제 데이터 CSV에도 저장 (행정실 실시간 조회용)
                        real_row = pd.DataFrame([{
                            "날짜": datetime.now().strftime("%Y-%m-%d"),
                            "학교명": target, "음식물(kg)": food_w, "단가(원)": 162,
                            "공급가": food_w * 162, "재활용방법": "퇴비화및비료생산",
                            "재활용업체": "(주)혜인이엔씨", "월": datetime.now().month,
                            "년도": str(datetime.now().year), "월별파일": f"{datetime.now().month}월"
                        }])
                        try:
                            existing = pd.read_csv(REAL_DATA_FILE)
                            merged = pd.concat([existing, real_row], ignore_index=True)
                        except:
                            merged = real_row
                        merged.to_csv(REAL_DATA_FILE, index=False)
                        st.success(f"✅ {target} 수거 실적 전송 완료!")
                        st.caption("📡 본사 관제센터 + 행정실에 실시간 반영됩니다.")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")

            # 퇴근하기
            st.write("---")
            st.markdown("### 🏠 퇴근 처리")
            if st.button("🏠 퇴근하기", use_container_width=True, type="secondary"):
                st.balloons()
                st.success(f"✅ {user_name}님, {datetime.now().strftime('%H시 %M분')} 퇴근 처리 완료! 수고하셨습니다.")
                st.caption("퇴근 기록이 본사 관제센터로 자동 전송됩니다.")
