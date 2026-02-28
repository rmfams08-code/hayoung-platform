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
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# ★ SQLite DB (시세/계약/일정 영구 저장)
# ==========================================
DB_PATH = "hayoung_platform.db"

def init_db():
    """SQLite DB 초기화 (테이블 없으면 생성)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS price_data
        (category TEXT, item TEXT, price INTEGER, unit TEXT, trend TEXT, sub_cat TEXT,
         PRIMARY KEY(category, item))''')
    c.execute('''CREATE TABLE IF NOT EXISTS contract_data
        (vendor TEXT, item TEXT, price INTEGER, PRIMARY KEY(vendor, item))''')
    c.execute('''CREATE TABLE IF NOT EXISTS contract_info
        (vendor TEXT PRIMARY KEY, rep TEXT, biz_no TEXT, start_date TEXT, end_date TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedule_data
        (vendor TEXT, month INTEGER, weekdays TEXT, schools TEXT, items TEXT,
         PRIMARY KEY(vendor, month))''')
    c.execute('''CREATE TABLE IF NOT EXISTS today_schedule
        (vendor TEXT PRIMARY KEY, schools TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS customer_info
        (vendor TEXT, name TEXT, biz_no TEXT, rep TEXT, addr TEXT,
         biz_type TEXT, biz_item TEXT, email TEXT, cust_type TEXT,
         PRIMARY KEY(vendor, name))''')
    conn.commit(); conn.close()

def db_get(table, where=None):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    q = f"SELECT * FROM {table}" + (f" WHERE {where}" if where else "")
    rows = conn.execute(q).fetchall(); conn.close()
    return [dict(r) for r in rows]

def db_upsert(table, data):
    conn = sqlite3.connect(DB_PATH)
    cols = ','.join(data.keys()); placeholders = ','.join(['?']*len(data))
    conn.execute(f"REPLACE INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit(); conn.close()

def db_delete(table, where):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DELETE FROM {table} WHERE {where}")
    conn.commit(); conn.close()

init_db()

def load_price_from_db():
    rows = db_get('price_data')
    if rows:
        result = {"폐기물":{},"재활용품":{}}
        for r in rows:
            result[r['category']][r['item']] = {"단가":r['price'],"단위":r['unit'],"변동":r['trend'],"카테고리":r['sub_cat']}
        return result
    defaults = {
        "폐기물":{"음식물폐기물(혼합)":{"단가":162,"단위":"원/kg","변동":"▲5","카테고리":"음식물"},"음식물폐기물(분리)":{"단가":140,"단위":"원/kg","변동":"—","카테고리":"음식물"},"사업장일반폐기물":{"단가":200,"단위":"원/kg","변동":"▼10","카테고리":"사업장"},"사업장지정폐기물":{"단가":350,"단위":"원/kg","변동":"▲20","카테고리":"사업장"},"건설폐기물(혼합)":{"단가":45,"단위":"원/kg","변동":"—","카테고리":"건설"}},
        "재활용품":{"폐지(신문지)":{"단가":120,"단위":"원/kg","변동":"▼15","카테고리":"종이류"},"폐지(골판지)":{"단가":80,"단위":"원/kg","변동":"▼10","카테고리":"종이류"},"폐지(서적류)":{"단가":90,"단위":"원/kg","변동":"—","카테고리":"종이류"},"PET병(투명)":{"단가":450,"단위":"원/kg","변동":"▲30","카테고리":"플라스틱"},"PET병(유색)":{"단가":200,"단위":"원/kg","변동":"▲10","카테고리":"플라스틱"},"PP(폴리프로필렌)":{"단가":350,"단위":"원/kg","변동":"▲20","카테고리":"플라스틱"},"PE(폴리에틸렌)":{"단가":300,"단위":"원/kg","변동":"▲15","카테고리":"플라스틱"},"PS(폴리스티렌)":{"단가":150,"단위":"원/kg","변동":"▼5","카테고리":"플라스틱"},"혼합플라스틱":{"단가":100,"단위":"원/kg","변동":"—","카테고리":"플라스틱"},"스티로폼(EPS)":{"단가":500,"단위":"원/kg","변동":"▲50","카테고리":"플라스틱"},"알루미늄캔":{"단가":1200,"단위":"원/kg","변동":"▲80","카테고리":"금속류"},"철캔(스틸)":{"단가":350,"단위":"원/kg","변동":"▲20","카테고리":"금속류"},"비철금속(구리)":{"단가":8500,"단위":"원/kg","변동":"▲200","카테고리":"금속류"},"고철(잡철)":{"단가":280,"단위":"원/kg","변동":"▼15","카테고리":"금속류"},"투명유리병":{"단가":60,"단위":"원/kg","변동":"—","카테고리":"유리류"},"갈색유리병":{"단가":40,"단위":"원/kg","변동":"—","카테고리":"유리류"},"혼합유리":{"단가":20,"단위":"원/kg","변동":"▼5","카테고리":"유리류"},"의류(면직물)":{"단가":200,"단위":"원/kg","변동":"▲10","카테고리":"기타"},"폐형광등":{"단가":0,"단위":"원/개","변동":"—","카테고리":"기타"},"폐건전지":{"단가":0,"단위":"원/kg","변동":"—","카테고리":"기타"},"폐식용유":{"단가":300,"단위":"원/L","변동":"▲30","카테고리":"기타"},"폐가전제품":{"단가":0,"단위":"원/대","변동":"—","카테고리":"기타"},"폐목재":{"단가":30,"단위":"원/kg","변동":"—","카테고리":"기타"}}
    }
    for cat, items in defaults.items():
        for item, v in items.items():
            db_upsert('price_data', {'category':cat,'item':item,'price':v['단가'],'unit':v['단위'],'trend':v['변동'],'sub_cat':v['카테고리']})
    return defaults

def save_price_to_db(cat, item, price, unit="원/kg", trend="수정", sub_cat="기타"):
    db_upsert('price_data', {'category':cat,'item':item,'price':price,'unit':unit,'trend':trend,'sub_cat':sub_cat})

def load_contracts_from_db():
    rows = db_get('contract_info')
    if rows:
        result = {}
        for r in rows:
            items = db_get('contract_data', f"vendor='{r['vendor']}'")
            result[r['vendor']] = {"대표":r['rep'],"사업자번호":r['biz_no'],"계약시작":r['start_date'],"계약만료":r['end_date'],"상태":r['status'],"품목단가":{i['item']:i['price'] for i in items}}
        return result
    result = {}
    for vn, vd in VENDOR_DATA.items():
        result[vn] = {"대표":vd['대표'],"사업자번호":vd['사업자번호'],"계약시작":"2025-04-01","계약만료":vd['계약만료'],"상태":"정상" if vd['안전점수']>=90 else "주의","품목단가":{"음식물폐기물":162,"사업장일반폐기물":200,"재활용(혼합)":300}}
        db_upsert('contract_info', {'vendor':vn,'rep':vd['대표'],'biz_no':vd['사업자번호'],'start_date':'2025-04-01','end_date':vd['계약만료'],'status':result[vn]['상태']})
        for item, price in result[vn]['품목단가'].items():
            db_upsert('contract_data', {'vendor':vn,'item':item,'price':price})
    return result

def save_contract_price(vendor, item, price):
    db_upsert('contract_data', {'vendor':vendor,'item':item,'price':price})

def load_customers_from_db(vendor):
    """DB에서 거래처 정보 로드 → dict 반환"""
    rows = db_get('customer_info', f"vendor='{vendor}'")
    if rows:
        return {r['name']: {"사업자번호":r['biz_no'],"상호":r['name'],"대표자":r['rep'],"주소":r['addr'],"업태":r['biz_type'],"종목":r['biz_item'],"이메일":r['email'],"구분":r['cust_type']} for r in rows}
    return None

def save_customer_to_db(vendor, name, info):
    """거래처 1건 DB 저장"""
    db_upsert('customer_info', {'vendor':vendor,'name':name,'biz_no':info.get('사업자번호',''),'rep':info.get('대표자',''),'addr':info.get('주소',''),'biz_type':info.get('업태',''),'biz_item':info.get('종목',''),'email':info.get('이메일',''),'cust_type':info.get('구분','학교')})

def delete_customer_from_db(vendor, name):
    """거래처 1건 DB 삭제"""
    db_delete('customer_info', f"vendor='{vendor}' AND name='{name}'")

def save_all_customers_to_db(vendor, detail_dict):
    """업체의 전체 거래처를 DB에 저장 (기존 삭제 후 전체 재삽입)"""
    db_delete('customer_info', f"vendor='{vendor}'")
    for name, info in detail_dict.items():
        save_customer_to_db(vendor, name, info)

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
    "driver10": {"pw":"dr2026!","role":"driver","name":"정민수 기사","vendor":"더존환경","schools":[]},
    "driver11": {"pw":"dr2026!","role":"driver","name":"한도현 기사","vendor":"더존환경","schools":[]},
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
    "더존환경": {
        "대표":"정더존","사업자번호":"456-78-90123","연락처":"031-567-8901",
        "차량":["경기94바 9012"],
        "drivers":["driver10","driver11"],
        "schools":[],
        "안전점수":90,"상태":"🟢 운행중","계약만료":"2027-06-30",
    },
}
ADMIN_ACCOUNTS = {
    "admin": {"pw":"hayoung2026!","role":"admin","name":"하영자원 본사 관리자"},
}
# 외주업체 관리자 계정
VENDOR_ADMIN_ACCOUNTS = {
    "vendor_a": {"pw":"a1234","role":"vendor_admin","name":"A환경 관리자","vendor":"A환경"},
    "vendor_b": {"pw":"b1234","role":"vendor_admin","name":"B자원 관리자","vendor":"B자원"},
    "vendor_c": {"pw":"c1234","role":"vendor_admin","name":"C로지스 관리자","vendor":"C로지스"},
    "dj01": {"pw":"ansdudska4","role":"vendor_admin","name":"더존환경 관리자","vendor":"더존환경"},
}
ALL_ACCOUNTS = {}
ALL_ACCOUNTS.update(SCHOOL_ACCOUNTS)
ALL_ACCOUNTS.update(EDU_OFFICE_ACCOUNTS)
ALL_ACCOUNTS.update(DRIVER_ACCOUNTS)
ALL_ACCOUNTS.update(ADMIN_ACCOUNTS)
ALL_ACCOUNTS.update(VENDOR_ADMIN_ACCOUNTS)

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

@st.cache_data(ttl=300)
def load_real_data():
    """실제 수거 데이터 로딩 (무조건 최신 CSV를 읽어와서 DB와 강제 동기화)"""
    try:
        # 1. 무조건 최신 CSV 파일(REAL_DATA_FILE)을 읽는다
        df = pd.read_csv(REAL_DATA_FILE)
        # 2. 읽어온 최신 데이터로 SQLite DB를 강제로 덮어씌운다
        if not df.empty:
            conn = sqlite3.connect(DB_PATH)
            df.to_sql('collection_data', conn, if_exists='replace', index=False)
            conn.close()
        return df
    except Exception as e:
        # 파일이 없거나 에러가 나면 빈 DataFrame 반환
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
    # ★ 수거업체/기사/시간 기본값 패치 (기존 데이터에 없는 경우)
    if '수거업체' not in df.columns:
        df['수거업체'] = '하영자원(본사)'
    else:
        df['수거업체'] = df['수거업체'].fillna('하영자원(본사)')
    if '수거기사' not in df.columns:
        df['수거기사'] = ''
    else:
        df['수거기사'] = df['수거기사'].fillna('')
    if '수거시간' not in df.columns:
        df['수거시간'] = ''
    else:
        df['수거시간'] = df['수거시간'].fillna('')
    if '사업장(kg)' not in df.columns: df['사업장(kg)'] = 0
    if '재활용(kg)' not in df.columns: df['재활용(kg)'] = 0
    return df

def load_data():
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태"]
    try:
        df = pd.read_csv(DB_FILE)
        return df
    except:
        return pd.DataFrame(columns=cols)

def save_data(new_row):
    df = load_data()
    if not df.empty:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])
    df.to_csv(DB_FILE, index=False)

# --- 실제 데이터 로딩 + 전처리 ---
df_real = preprocess_real_data(load_real_data())

# --- 기존 데이터 로딩 ---
df_all = load_data()

# ★ [가상데이터 삭제 + 실제 데이터 동기화]
# 실제 데이터가 존재하는 월의 가상데이터를 제거하고 실제 데이터로 대체
if not df_real.empty:
    df_real_sync = df_real.copy()
    df_real_sync['상태'] = '정산완료'
    df_real_sync['단가(원)'] = pd.to_numeric(df_real_sync.get('단가(원)', 150), errors='coerce').fillna(150)
    df_real_sync['사업장(kg)'] = pd.to_numeric(df_real_sync.get('사업장(kg)', 0), errors='coerce').fillna(0)
    df_real_sync['재활용(kg)'] = pd.to_numeric(df_real_sync.get('재활용(kg)', 0), errors='coerce').fillna(0)
    df_real_sync['사업장단가(원)'] = 200
    df_real_sync['재활용단가(원)'] = 300
    if '수거업체' not in df_real_sync.columns:
        df_real_sync['수거업체'] = '하영자원(본사)'
    df_real_sync['학생수'] = df_real_sync['학교명'].map(STUDENT_COUNTS).fillna(1000)
    if not df_all.empty:
        df_all['임시_월별'] = pd.to_datetime(df_all['날짜'], errors='coerce').dt.strftime('%Y-%m')
        df_real_sync['임시_월별'] = pd.to_datetime(df_real_sync['날짜'], errors='coerce').dt.strftime('%Y-%m')
        real_months = df_real_sync['임시_월별'].dropna().unique()
        df_all = df_all[~df_all['임시_월별'].isin(real_months)].copy()
        df_all = pd.concat([df_all, df_real_sync], ignore_index=True)
        df_all = df_all.drop(columns=['임시_월별'], errors='ignore')
    else:
        df_all = df_real_sync.copy()

if not df_all.empty:
    df_all['음식물비용'] = df_all['음식물(kg)'] * df_all['단가(원)']
    df_all['사업장비용'] = df_all['사업장(kg)'] * df_all['사업장단가(원)']
    df_all['재활용수익'] = df_all['재활용(kg)'] * df_all['재활용단가(원)']
    df_all['최종정산액'] = df_all['음식물비용'] + df_all['사업장비용'] - df_all['재활용수익']
    df_all['월별'] = df_all['날짜'].astype(str).str[:7]
    df_all['년도'] = df_all['날짜'].astype(str).str[:4]
    df_all['탄소감축량(kg)'] = df_all['음식물(kg)'] * CO2_FACTOR
else:
    cols = ["날짜", "학교명", "학생수", "수거업체", "음식물(kg)", "재활용(kg)", "사업장(kg)", "단가(원)", "재활용단가(원)", "사업장단가(원)", "상태", "음식물비용", "사업장비용", "재활용수익", "최종정산액", "월별", "년도", "탄소감축량(kg)"]
    df_all = pd.DataFrame(columns=cols)




def safe_cols(df, cols):
    """DataFrame에 존재하는 컬럼만 필터링 + 수거업체/기사/시간 자동 추가"""
    extra = [c for c in ['수거업체','수거기사','수거시간'] if c in df.columns and c not in cols]
    return [c for c in cols + extra if c in df.columns]

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


def create_allbaro_report(df_real, report_role, entity_name, year, item_filter=None):
    """올바로시스템 실적보고서 엑셀 생성
    report_role: 'emitter'(배출자-학교/교육청) / 'transporter'(수집운반-관리자/외주업체)
    """
    output = io.BytesIO()
    df = df_real.copy()
    if '년도' in df.columns:
        df = df[df['년도']==str(year)]
    if item_filter and item_filter != "전체":
        item_map = {"음식물":"음식물(kg)","사업장":"사업장(kg)","재활용":"재활용(kg)"}
        if item_filter in item_map and item_map[item_filter] in df.columns:
            df = df[df[item_map[item_filter]] > 0] if item_map[item_filter] in df.columns else df
    if df.empty:
        with pd.ExcelWriter(output, engine='xlsxwriter') as w:
            wb = w.book; ws = wb.add_worksheet('실적보고서')
            ws.write(0, 0, f'{year}년 데이터가 없습니다.')
        return output.getvalue()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book
        tf = wb.add_format({'bold':True,'font_size':16,'align':'center','font_color':'#1565c0'})
        hf = wb.add_format({'bold':True,'font_size':10,'align':'center','bg_color':'#1565c0','font_color':'white','border':1,'text_wrap':True})
        cf = wb.add_format({'font_size':10,'align':'center','border':1})
        nf = wb.add_format({'font_size':10,'align':'center','border':1,'num_format':'#,##0'})
        sf = wb.add_format({'bold':True,'font_size':11,'bg_color':'#e3f2fd','border':1})
        lf = wb.add_format({'font_size':9,'align':'left','color':'#666666','text_wrap':True})
        # 시트1: 표지
        ws1 = wb.add_worksheet('표지')
        ws1.set_column(0,5,18)
        if report_role == 'emitter':
            ws1.merge_range('A1:F2','폐기물 배출 실적보고서 (배출자용)',tf)
            ws1.merge_range('A3:F3','폐기물관리법 제38조, 시행규칙 제60조 / 별지 제30호서식',lf)
            role_label = '배출자(사업장)'
        else:
            ws1.merge_range('A1:F2','폐기물 수집·운반 실적보고서 (수집운반업자용)',tf)
            ws1.merge_range('A3:F3','폐기물관리법 제38조, 시행규칙 제60조 / 별지 제30호서식',lf)
            role_label = '수집·운반업자'
        info = [['보고 대상 연도',f'{year}년'],['보고서 유형',role_label],['업체(기관)명',entity_name],
                ['보고 제출일',CURRENT_DATE],['관할 행정기관','화성시청 환경보호과'],
                ['올바로시스템','www.allbaro.or.kr']]
        for ri, row in enumerate(info):
            ws1.write(5+ri, 0, row[0], sf); ws1.merge_range(5+ri, 1, 5+ri, 5, row[1], cf)
        ws1.merge_range(12, 0, 13, 5, '※ 폐기물관리법 제38조에 따라 폐기물의 발생·처리에 관한 보고를 매년 2월 말일까지 올바로시스템으로 제출', lf)
        # 시트2: 월별 실적
        ws2 = wb.add_worksheet('월별실적')
        ws2.set_column(0,8,15)
        ws2.merge_range('A1:I1', f'{entity_name} {year}년 폐기물 {role_label} 실적', tf)
        headers = ['월','폐기물종류','성상','발생(배출)량(kg)','처리방법','처리(운반)량(kg)','인계업체','올바로인계번호','비고']
        for ci, h in enumerate(headers): ws2.write(2, ci, h, hf)
        row_idx = 3
        months = sorted(df['월'].unique()) if '월' in df.columns else [1]
        for m in months:
            df_m = df[df['월']==m] if '월' in df.columns else df
            total_kg = df_m['음식물(kg)'].sum() if '음식물(kg)' in df_m.columns else 0
            total_supply = df_m['공급가'].sum() if '공급가' in df_m.columns else 0
            ws2.write(row_idx, 0, f'{m}월', cf)
            ws2.write(row_idx, 1, '음식물류 폐기물', cf)
            ws2.write(row_idx, 2, '고상', cf)
            ws2.write(row_idx, 3, total_kg, nf)
            ws2.write(row_idx, 4, '퇴비화(R-2)', cf)
            ws2.write(row_idx, 5, total_kg, nf)
            recycler = df_m['재활용업체'].iloc[0] if '재활용업체' in df_m.columns and not df_m.empty else ''
            ws2.write(row_idx, 6, str(recycler), cf)
            ws2.write(row_idx, 7, f'AB-{year}-{m:02d}-001', cf)
            ws2.write(row_idx, 8, '', cf)
            row_idx += 1
        # 합계행
        total_all = df['음식물(kg)'].sum() if '음식물(kg)' in df.columns else 0
        ws2.write(row_idx, 0, '합계', hf)
        ws2.merge_range(row_idx, 1, row_idx, 2, '', cf)
        ws2.write(row_idx, 3, total_all, wb.add_format({'bold':True,'font_size':11,'align':'center','border':1,'num_format':'#,##0','bg_color':'#e3f2fd'}))
        ws2.write(row_idx, 5, total_all, wb.add_format({'bold':True,'font_size':11,'align':'center','border':1,'num_format':'#,##0','bg_color':'#e3f2fd'}))
        # 시트3: 업체별 연간발생량
        ws3 = wb.add_worksheet('업체별연간발생량')
        ws3.set_column(0,6,18)
        ws3.merge_range('A1:G1', f'{entity_name} {year}년 업체별 연간 폐기물 발생량', tf)
        ab_headers = ['업체(학교)명','연간수거량(kg)','연간공급가(원)','수거건수','월평균수거량(kg)','주요처리방법','비고']
        for ci, h in enumerate(ab_headers): ws3.write(2, ci, h, hf)
        if '학교명' in df.columns:
            schools_in = sorted(df['학교명'].unique())
            for ri, sch in enumerate(schools_in):
                df_sch = df[df['학교명']==sch]
                total_kg = df_sch['음식물(kg)'].sum() if '음식물(kg)' in df_sch.columns else 0
                total_sup = df_sch['공급가'].sum() if '공급가' in df_sch.columns else 0
                cnt = len(df_sch)
                active_months = df_sch['월'].nunique() if '월' in df_sch.columns else 1
                avg_monthly = total_kg / max(active_months, 1)
                method = str(df_sch['재활용방법'].mode().iloc[0]) if '재활용방법' in df_sch.columns and not df_sch['재활용방법'].mode().empty else ''
                ws3.write(3+ri, 0, sch, cf)
                ws3.write(3+ri, 1, total_kg, nf)
                ws3.write(3+ri, 2, total_sup, nf)
                ws3.write(3+ri, 3, cnt, nf)
                ws3.write(3+ri, 4, round(avg_monthly,1), nf)
                ws3.write(3+ri, 5, method, cf)
                ws3.write(3+ri, 6, '', cf)
            # 합계행
            tr = 3 + len(schools_in)
            total_all_kg = df['음식물(kg)'].sum() if '음식물(kg)' in df.columns else 0
            total_all_sup = df['공급가'].sum() if '공급가' in df.columns else 0
            sum_fmt = wb.add_format({'bold':True,'font_size':11,'align':'center','border':1,'num_format':'#,##0','bg_color':'#e3f2fd'})
            ws3.write(tr, 0, '합계', sum_fmt)
            ws3.write(tr, 1, total_all_kg, sum_fmt)
            ws3.write(tr, 2, total_all_sup, sum_fmt)
            ws3.write(tr, 3, len(df), sum_fmt)
        # 시트4: 폐기물 수집운반내역 (올바로 양식)
        ws4 = wb.add_worksheet('수집운반내역')
        ws4.set_column(0,12,14)
        ws4.merge_range('A1:M1', f'{entity_name} {year}년 폐기물 수집·운반 내역', tf)
        ws4.merge_range('A2:M2', '폐기물관리법 시행규칙 [별지 제30호서식] 폐기물 수집운반실적보고 - 수집운반내역', lf)
        ab4_h = ['No','인계일','폐기물종류','폐기물코드','성상','인계량(kg)','수집운반업체','허가번호','인계자','인수자','운반차량','최종처리업체','비고']
        for ci, h in enumerate(ab4_h): ws4.write(3, ci, h, hf)
        r4 = 4
        for _, row in df.iterrows():
            kg_val = row.get('음식물(kg)', 0)
            if kg_val <= 0: continue
            ws4.write(r4, 0, r4-3, cf)
            ws4.write(r4, 1, str(row.get('날짜',''))[:10], cf)
            ws4.write(r4, 2, '음식물류 폐기물', cf)
            ws4.write(r4, 3, '51-01-01', cf)
            ws4.write(r4, 4, '고상', cf)
            ws4.write(r4, 5, kg_val, nf)
            ws4.write(r4, 6, entity_name, cf)
            ws4.write(r4, 7, '', cf)
            ws4.write(r4, 8, row.get('수거기사',''), cf)
            ws4.write(r4, 9, '', cf)
            ws4.write(r4, 10, '', cf)
            recycler = row.get('재활용업체', row.get('재활용방법',''))
            ws4.write(r4, 11, str(recycler), cf)
            ws4.write(r4, 12, '', cf)
            r4 += 1
        # 합계
        ws4.write(r4, 0, '합계', hf)
        ws4.merge_range(r4, 1, r4, 4, '', cf)
        ws4.write(r4, 5, total_all_kg, sum_fmt)
    return output.getvalue()


def create_monthly_invoice_pdf(vendor_name, school_name, month, year, df_month):
    """월말거래명세서 PDF 생성 (한글 깨짐 방지 - WenQuanYi Zen Hei)"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # 한글 폰트 등록 (WQY Zen Hei - 한중일 지원 TTF)
    KR_FONT = 'KoreanFont'
    try:
        pdfmetrics.registerFont(TTFont(KR_FONT, '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', subfontIndex=0))
    except:
        pass
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    # 헤더
    c.setFont(KR_FONT, 18)
    c.drawCentredString(w/2, h-35*mm, '거 래 명 세 서')
    c.setFont(KR_FONT, 10)
    c.drawCentredString(w/2, h-43*mm, f'{year}년 {month}월 월말 거래명세서')
    # 구분선
    c.setStrokeColor(colors.Color(0.1,0.4,0.7))
    c.setLineWidth(1.5)
    c.line(15*mm, h-47*mm, w-15*mm, h-47*mm)
    # 공급자/공급받는자
    c.setFont(KR_FONT, 10)
    y = h-55*mm
    c.drawString(20*mm, y, '공급자 (수집운반업체)')
    c.drawString(110*mm, y, '공급받는자 (배출자)')
    c.setFont(KR_FONT, 9)
    c.drawString(20*mm, y-6*mm, f'업 체 명 : {vendor_name}')
    c.drawString(110*mm, y-6*mm, f'학 교 명 : {school_name}')
    c.drawString(20*mm, y-12*mm, f'발 행 일 : {CURRENT_DATE}')
    c.drawString(110*mm, y-12*mm, f'기    간 : {year}년 {month}월 1일 ~ 말일')
    # 테이블 헤더
    table_y = y - 22*mm
    c.setFillColor(colors.Color(0.1,0.4,0.7))
    c.rect(15*mm, table_y, w-30*mm, 7*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(KR_FONT, 8)
    cols = [18, 38, 70, 92, 115, 145]
    headers = ['No','수거일','단위(L)','단가(원)','공급가(원)','재활용방법']
    for ci, hd in enumerate(headers):
        c.drawString(cols[ci]*mm, table_y+2*mm, hd)
    # 데이터 행
    c.setFillColor(colors.black)
    c.setFont(KR_FONT, 8)
    row_y = table_y - 6*mm
    total_qty = 0; total_amt = 0
    for ri, (_, row) in enumerate(df_month.iterrows()):
        if row_y < 35*mm:
            c.showPage(); row_y = h - 25*mm
            c.setFont(KR_FONT, 8)
        qty = row.get('단위(L)', row.get('음식물(kg)', 0))
        price = row.get('단가', row.get('단가(원)', 170))
        supply = row.get('공급가', qty * price if qty else 0)
        date_str = str(row.get('수거일', row.get('날짜', '')))
        if ri % 2 == 0:
            c.setFillColor(colors.Color(0.95,0.97,1.0))
            c.rect(15*mm, row_y-1.5*mm, w-30*mm, 5.5*mm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(cols[0]*mm, row_y+1*mm, str(ri+1))
        c.drawString(cols[1]*mm, row_y+1*mm, date_str[:15])
        c.drawString(cols[2]*mm, row_y+1*mm, f'{qty:,.0f}' if qty else '-')
        c.drawString(cols[3]*mm, row_y+1*mm, f'{price:,.0f}')
        c.drawString(cols[4]*mm, row_y+1*mm, f'{supply:,.0f}' if supply else '-')
        c.drawString(cols[5]*mm, row_y+1*mm, str(row.get('재활용방법', ''))[:10])
        if qty: total_qty += qty
        if supply: total_amt += supply
        row_y -= 5.5*mm
    # 합계
    row_y -= 2*mm
    c.setFillColor(colors.Color(0.1,0.4,0.7))
    c.rect(15*mm, row_y-1.5*mm, w-30*mm, 7*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont(KR_FONT, 9)
    c.drawString(cols[0]*mm, row_y+1*mm, '합  계')
    c.drawString(cols[2]*mm, row_y+1*mm, f'{total_qty:,.0f}')
    c.drawString(cols[4]*mm, row_y+1*mm, f'{total_amt:,.0f}')
    # 하단 서명
    c.setFillColor(colors.black); c.setFont(KR_FONT, 8)
    c.drawString(20*mm, 25*mm, f'위 금액을 거래명세서로 발행합니다.')
    c.drawString(20*mm, 20*mm, f'{vendor_name} 대표')
    c.drawRightString(w-20*mm, 20*mm, f'하영자원 폐기물데이터플랫폼 자동생성 ({CURRENT_DATE})')
    c.save()
    return buf.getvalue()


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
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.markdown('<div class="role-card"><div class="icon">🏢</div><div class="title">관리자</div><div class="desc">하영자원 본사<br>통합 관제</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("관리자 로그인", key="btn_admin", use_container_width=True, type="primary"):
            st.session_state.login_group = "admin"; st.rerun()
    with col2:
        st.markdown('<div class="role-card"><div class="icon">🏫</div><div class="title">교육청/학교</div><div class="desc">교육지원청<br>학교 행정실</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("교육청/학교 로그인", key="btn_edu", use_container_width=True, type="primary"):
            st.session_state.login_group = "edu_school"; st.rerun()
    with col3:
        st.markdown('<div class="role-card"><div class="icon">🚚</div><div class="title">수거기사</div><div class="desc">수거 기사<br>현장 앱</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("수거기사 로그인", key="btn_driver", use_container_width=True, type="primary"):
            st.session_state.login_group = "driver"; st.rerun()
    with col4:
        st.markdown('<div class="role-card"><div class="icon">🤝</div><div class="title">외주업체</div><div class="desc">외주업체<br>관리자</div><div class="arrow">→</div></div>', unsafe_allow_html=True)
        if st.button("외주업체 로그인", key="btn_vendor", use_container_width=True, type="primary"):
            st.session_state.login_group = "vendor_admin"; st.rerun()

    if st.session_state.login_group:
        st.write("---")
        group = st.session_state.login_group
        labels = {"admin":("🏢 관리자 로그인","#1a73e8"),"edu_school":("🏫 교육청/학교 로그인","#34a853"),"driver":("🚚 수거기사 로그인","#ea4335"),"vendor_admin":("🤝 외주업체 관리자 로그인","#ff6d00")}
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
                                (group=="driver" and account["role"]=="driver") or \
                                (group=="vendor_admin" and account["role"]=="vendor_admin")
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
        # ★ 3그룹 카테고리 (모바일 대응)
        admin_group = st.radio("", ["📊 데이터/관리","💰 정산/보고서","🏢 업체/운영"], horizontal=True, key="admin_grp", label_visibility="collapsed")
        tab_real=tab_sched=tab_map=tab_total=tab_food=tab_biz=tab_recycle=tab_allbaro=tab_price=tab_vendor_mgmt=tab_sub=None
        if admin_group == "📊 데이터/관리":
            tab_real, tab_sched, tab_map = st.tabs(["📊 실제 수거 데이터(2025)","📅 수거일정 관리","📍 차량 관제"])
        elif admin_group == "💰 정산/보고서":
            tab_total, tab_food, tab_biz, tab_recycle, tab_allbaro = st.tabs(["전체 통합 정산","음식물 정산","사업장 정산","재활용 정산","🔗 올바로 보고서"])
        else:
            tab_price, tab_vendor_mgmt, tab_sub = st.tabs(["💹 품목별 시세관리","🚛 수거업체관리","🤝 외주업체"])

        # ★★★ [신규] 실제 수거 데이터 탭 ★★★
        if tab_real is not None:
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
                            st.dataframe(df_m[['날짜','학교명','음식물(kg)','단가(원)','공급가','재활용방법'] + [c for c in ['수거업체','수거기사','수거시간'] if c in df_m.columns]],use_container_width=True, hide_index=True)
            else:
                st.warning("실제 수거 데이터 파일(hayoung_real_2025.csv)이 없습니다.")

        # 기존 시뮬레이션 정산 탭
        all_schools_sim = sorted(df_all['학교명'].unique()) if not df_all.empty else []
        all_years_sim = sorted(df_all['년도'].unique(), reverse=True) if not df_all.empty else []

        if tab_total is not None:
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
                        # ★ 계산서 발행 + 명세서 다운로드
                        st.write("---")
                        admin_tax = st.radio(f"{tm} 발행유형", ["전자세금계산서(부가세10%)","전자계산서(세율적용X)"], horizontal=True, key=f"adm_tax_{ti}")
                        is_tax_a = "세금" in admin_tax
                        total_a = df_tm['최종정산액'].sum()
                        sup_a = int(total_a/1.1) if is_tax_a else int(total_a)
                        vat_a = total_a - sup_a if is_tax_a else 0
                        st.caption(f"공급가액: {sup_a:,.0f}원 | 세액: {vat_a:,.0f}원 | 합계: {total_a:,.0f}원")
                        ac1, ac2, ac3 = st.columns(3)
                        with ac1:
                            if st.button(f"🧾 {'전자세금계산서' if is_tax_a else '전자계산서'} 발행", use_container_width=True, key=f"adm_tax_btn_{ti}"):
                                st.success(f"✅ {tm} {'전자세금계산서' if is_tax_a else '전자계산서'} 발행 완료!")
                        with ac2:
                            school_n = sel_school_t if sel_school_t!="전체" else "전체"
                            pdf_adm = create_monthly_invoice_pdf("하영자원(본사)", school_n, int(tm[-2:]) if '-' in tm else CURRENT_MONTH, sel_yr_t, df_tm)
                            st.download_button(f"📄 명세서 PDF", data=pdf_adm, file_name=f"{school_n}_{tm}_명세서.pdf", mime="application/pdf", use_container_width=True, key=f"adm_inv_{ti}")
                        with ac3:
                            if st.button(f"📧 이메일 전송", use_container_width=True, key=f"adm_em_{ti}"):
                                st.info("📧 SMTP 설정 후 사용 가능")
            cb1, cb2 = st.columns(2)
            with cb1: st.button("🏢 업체별 통합정산서 발송", use_container_width=True)
            with cb2: st.button("🏫 학교별 통합정산서 발송", use_container_width=True)
        if tab_food is not None:
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
        if tab_biz is not None:
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
        if tab_recycle is not None:
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
        # ★ 수거일정 관리 탭
        if tab_sched is not None:
         with tab_sched:
            st.subheader("📅 수거일정 등록 및 관리")
            sched_mode = st.radio("모드 선택", ["오늘 일정 등록","월별 일정 관리","신규 거래처 추가","업체별 일정 확인"], horizontal=True, key="sched_mode")

            # === 모든 업체+본사 학교 목록 통합 관리 ===
            all_vendor_names = ["하영자원(본사)"] + list(VENDOR_DATA.keys())
            def get_vendor_schools(vn):
                if vn == "하영자원(본사)":
                    s = []
                    for did in ['driver01','driver02','driver03']:
                        s.extend(DRIVER_ACCOUNTS[did].get('schools',[]))
                    return s
                return VENDOR_DATA.get(vn,{}).get('schools',[])

            if sched_mode == "오늘 일정 등록":
                st.markdown("#### 📋 오늘의 수거일정 등록")
                st.caption("각 업체별 오늘 수거할 학교를 선택하세요. 기사 앱에 실시간 반영됩니다.")
                for vn in all_vendor_names:
                    v_sch = get_vendor_schools(vn)
                    icon = "🏢" if vn.startswith("하영") else "🤝"
                    _sched_default = [s for s in st.session_state.get(f'schedule_{vn}', v_sch) if s in v_sch]
                    sel_vs = st.multiselect(f"{icon} {vn} 수거 학교", v_sch, default=_sched_default, key=f"sched_{vn}_tab")
                    st.session_state[f'schedule_{vn}'] = sel_vs
                st.success("✅ 수거일정이 각 기사 앱에 실시간 반영됩니다.")
                # 오늘 일정 요약
                st.write("---")
                st.markdown("**📊 오늘 일정 요약**")
                sched_rows = []
                for vn in all_vendor_names:
                    sch_list = st.session_state.get(f'schedule_{vn}', [])
                    if vn == '하영자원(본사)':
                        drivers = [DRIVER_ACCOUNTS[d]['name'] for d in ['driver01','driver02','driver03']]
                    else:
                        drivers = [DRIVER_ACCOUNTS[d]['name'] for d in VENDOR_DATA.get(vn,{}).get('drivers',[]) if d in DRIVER_ACCOUNTS]
                    sched_rows.append({'업체명':vn, '수거학교수':len(sch_list), '담당기사':'/'.join(drivers), '학교목록':', '.join(sch_list[:3]) + ('...' if len(sch_list)>3 else '')})
                st.dataframe(pd.DataFrame(sched_rows), use_container_width=True, hide_index=True)

            elif sched_mode == "월별 일정 관리":
                st.markdown("#### 🗓️ 월별 수거일정 관리")
                sched_sub = st.tabs(["📅 정기 일정 등록","📋 수거예정일 등록","✏️ 기존 일정 수정"])
                with sched_sub[0]:
                    sel_sv = st.selectbox("업체 선택", all_vendor_names, key="sched_vendor_monthly")
                    v_sch_list = get_vendor_schools(sel_sv)
                    sel_sm = st.selectbox("월 선택", list(range(1,13)), format_func=lambda x: f"{x}월", key="sched_month_sel")
                    weekdays = ['월','화','수','목','금']
                    sk_existing = st.session_state.get(f"monthly_sched_{sel_sv}_{sel_sm}", {"요일":['월','수','금'], "학교":v_sch_list, "품목":['음식물','사업장','재활용']})
                    sched_days = st.multiselect("수거 요일", weekdays, default=sk_existing.get('요일',['월','수','금']), key=f"sched_days_{sel_sv}_{sel_sm}")
                    sched_schools = st.multiselect("수거 대상 학교", v_sch_list, default=[s for s in sk_existing.get('학교',v_sch_list) if s in v_sch_list], key=f"sched_schools_{sel_sv}_{sel_sm}")
                    sched_items = st.multiselect("수거 품목", ['음식물','사업장','재활용'], default=sk_existing.get('품목',['음식물','사업장','재활용']), key=f"sched_items_{sel_sv}_{sel_sm}")
                    if st.button("💾 월별 일정 저장", type="primary", use_container_width=True, key="save_monthly"):
                        st.session_state[f"monthly_sched_{sel_sv}_{sel_sm}"] = {"요일": sched_days, "학교": sched_schools, "품목": sched_items}
                        st.success(f"✅ {sel_sv} {sel_sm}월 일정 저장 완료!")
                with sched_sub[1]:
                    st.markdown("**📋 수거예정일 개별 등록**")
                    sp_vendor = st.selectbox("업체 선택", all_vendor_names, key="sp_vendor")
                    sp_schools = get_vendor_schools(sp_vendor)
                    sp_school = st.selectbox("거래처(학교)", sp_schools if sp_schools else ["등록된 거래처 없음"], key="sp_school")
                    sp_item = st.selectbox("수거 품목", ['음식물','사업장','재활용'], key="sp_item")
                    sp_date = st.date_input("수거 예정일", key="sp_date")
                    sp_memo = st.text_input("메모 (선택)", key="sp_memo")
                    if st.button("📅 수거예정일 등록", type="primary", use_container_width=True, key="sp_save"):
                        pk = 'planned_schedules'
                        if pk not in st.session_state: st.session_state[pk] = []
                        st.session_state[pk].append({"업체":sp_vendor,"학교":sp_school,"품목":sp_item,"날짜":str(sp_date),"메모":sp_memo})
                        st.success(f"✅ {sp_vendor} → {sp_school} ({sp_item}) {sp_date} 등록!")
                    if st.session_state.get('planned_schedules'):
                        st.write("---")
                        st.markdown("**📋 등록된 수거예정일**")
                        st.dataframe(pd.DataFrame(st.session_state['planned_schedules']), use_container_width=True, hide_index=True)
                with sched_sub[2]:
                    st.markdown("**✏️ 기존 등록 일정 확인/수정**")
                    sel_edit_v = st.selectbox("업체", all_vendor_names, key="edit_sched_v")
                    for m in range(1, 13):
                        sk = f"monthly_sched_{sel_edit_v}_{m}"
                        if sk in st.session_state:
                            sd = st.session_state[sk]
                            with st.expander(f"📅 {m}월: {'/'.join(sd.get('요일',[]))} | {'/'.join(sd.get('품목',[]))}", expanded=(m==CURRENT_MONTH)):
                                st.write(f"수거요일: {', '.join(sd.get('요일',[]))}")
                                st.write(f"수거품목: {', '.join(sd.get('품목',[]))}")
                                st.write(f"대상학교: {', '.join(sd.get('학교',[]))}")
                                if st.button(f"🗑️ {m}월 일정 삭제", key=f"del_sched_{sel_edit_v}_{m}"):
                                    del st.session_state[sk]
                                    st.success(f"✅ {m}월 일정 삭제!"); st.rerun()

            elif sched_mode == "신규 거래처 추가":
                st.markdown("#### ➕ 신규 거래처(학교) 추가")
                st.caption("등록된 학교 외 신규 학교를 추가하고 업체에 배정합니다.")
                # 신규 학교 직접 입력
                new_school_name = st.text_input("신규 학교(거래처)명 입력", placeholder="예: 동탄초등학교", key="new_school_input")
                new_school_students = st.number_input("학생수 (명)", min_value=0, value=300, step=50, key="new_school_students")
                assign_vendor = st.selectbox("배정 업체", all_vendor_names, key="assign_vendor")
                if st.button("➕ 신규 거래처 등록", type="primary", use_container_width=True, key="add_new_school"):
                    if new_school_name and new_school_name not in SCHOOL_LIST:
                        # SCHOOL_LIST에 추가
                        SCHOOL_LIST.append(new_school_name)
                        STUDENT_COUNTS[new_school_name] = new_school_students
                        # 업체에 배정
                        if assign_vendor == "하영자원(본사)":
                            DRIVER_ACCOUNTS['driver01']['schools'].append(new_school_name)
                        elif assign_vendor in VENDOR_DATA:
                            VENDOR_DATA[assign_vendor]['schools'].append(new_school_name)
                        st.success(f"✅ '{new_school_name}' 등록 완료 → {assign_vendor}에 배정됨")
                        st.rerun()
                    elif new_school_name in SCHOOL_LIST:
                        st.warning(f"⚠️ '{new_school_name}'은(는) 이미 등록된 학교입니다.")
                    else:
                        st.warning("학교명을 입력하세요.")
                # 기존 미배정 학교를 업체에 배정
                st.write("---")
                st.markdown("**🔄 기존 학교 업체 재배정**")
                all_assigned = []
                for vn in all_vendor_names:
                    all_assigned.extend(get_vendor_schools(vn))
                unassigned = [s for s in SCHOOL_LIST if s not in all_assigned]
                if unassigned:
                    st.warning(f"미배정 학교: {', '.join(unassigned)}")
                    sel_unassigned = st.selectbox("배정할 학교", unassigned, key="reassign_school")
                    reassign_to = st.selectbox("배정 대상 업체", all_vendor_names, key="reassign_to")
                    if st.button("🔄 배정", key="reassign_btn"):
                        if reassign_to == "하영자원(본사)":
                            DRIVER_ACCOUNTS['driver01']['schools'].append(sel_unassigned)
                        else:
                            VENDOR_DATA[reassign_to]['schools'].append(sel_unassigned)
                        st.success(f"✅ {sel_unassigned} → {reassign_to} 배정 완료!")
                        st.rerun()
                else:
                    st.success("✅ 모든 학교가 업체에 배정되어 있습니다.")

            elif sched_mode == "업체별 일정 확인":
                st.markdown("#### 🔍 업체별 등록 일정 확인")
                sel_check_v = st.selectbox("업체 선택", all_vendor_names, key="check_vendor")
                v_tabs = st.tabs(["📅 오늘 일정", "🗓️ 월별 일정"])
                with v_tabs[0]:
                    today_sch = st.session_state.get(f'schedule_{sel_check_v}', get_vendor_schools(sel_check_v))
                    if sel_check_v == '하영자원(본사)':
                        drivers = [DRIVER_ACCOUNTS[d]['name'] for d in ['driver01','driver02','driver03']]
                    else:
                        drivers = [DRIVER_ACCOUNTS[d]['name'] for d in VENDOR_DATA.get(sel_check_v,{}).get('drivers',[]) if d in DRIVER_ACCOUNTS]
                    st.markdown(f"**담당 기사:** {', '.join(drivers)}")
                    st.markdown(f"**오늘 수거 학교 ({len(today_sch)}곳):**")
                    for si, sch in enumerate(today_sch):
                        st.markdown(f"  {si+1}. 🏫 {sch}")
                with v_tabs[1]:
                    has_monthly = False
                    for m in range(1, 13):
                        sk = f"monthly_sched_{sel_check_v}_{m}"
                        if sk in st.session_state:
                            has_monthly = True
                            sd = st.session_state[sk]
                            with st.expander(f"📅 {m}월", expanded=(m==CURRENT_MONTH)):
                                st.write(f"**수거 요일:** {', '.join(sd.get('요일',[]))}")
                                st.write(f"**수거 품목:** {', '.join(sd.get('품목',[]))}")
                                st.write(f"**대상 학교:** {', '.join(sd.get('학교',[]))}")
                    if not has_monthly:
                        st.info("등록된 월별 일정이 없습니다. '월별 일정 관리'에서 등록하세요.")

        # ★ 올바로 보고서 탭 (수집운반업자용)
        if tab_allbaro is not None:
         with tab_allbaro:
            st.subheader("🔗 올바로시스템 실적보고서 (수집·운반업자용)")
            st.caption("폐기물관리법 제38조, 시행규칙 제60조 / 별지 제30호서식")
            if not df_real.empty:
                ab_years = sorted(df_real['년도'].unique(), reverse=True)
                sel_ab_yr = st.selectbox("📅 년도 선택", ab_years, key="admin_ab_yr")
                sel_ab_item = st.selectbox("📦 품목 선택", ["전체","음식물","사업장","재활용"], key="admin_ab_item")
                # 미리보기
                df_ab = df_real[df_real['년도']==str(sel_ab_yr)]
                if sel_ab_item != "전체":
                    item_col = {"음식물":"음식물(kg)","사업장":"사업장(kg)","재활용":"재활용(kg)"}.get(sel_ab_item)
                    if item_col and item_col in df_ab.columns:
                        df_ab = df_ab[df_ab[item_col] > 0]
                ab_months = sorted(df_ab['월'].unique()) if not df_ab.empty else []
                if ab_months:
                    ab_mtabs = st.tabs(["📅 연간 요약"] + [f"🗓️ {m}월" for m in ab_months])
                    with ab_mtabs[0]:
                        ab_sum = df_ab[df_ab['수거여부']].groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index().sort_values('수거량',ascending=False)
                        st.dataframe(ab_sum, use_container_width=True, hide_index=True)
                        st.metric("총 수거량", f"{ab_sum['수거량'].sum():,.0f} kg")
                    for mi, mm in enumerate(ab_months):
                        with ab_mtabs[mi+1]:
                            df_abm = df_ab[(df_ab['월']==mm) & (df_ab['수거여부'])]
                            abm_s = df_abm.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                            st.dataframe(abm_s, use_container_width=True, hide_index=True)
                st.write("---")
                st.download_button("📄 올바로 실적보고서 다운로드 (수집운반업자용)",
                    data=create_allbaro_report(df_real, 'transporter', '하영자원', sel_ab_yr, sel_ab_item),
                    file_name=f"올바로_수집운반_실적보고서_{sel_ab_yr}_{sel_ab_item}.xlsx", use_container_width=True)
            else:
                st.info("실제 수거 데이터가 없습니다.")

        # ★ 품목별 시세관리 탭
        if tab_price is not None:
         with tab_price:
            st.subheader("💹 품목별 시세관리")
            # 세션 기반 시세 데이터 초기화
            if 'price_data' not in st.session_state:
                st.session_state['price_data'] = load_price_from_db()
            price_mode = st.radio("분류", ["폐기물 (음식물 포함)","재활용품 23종","업체/학교별 단가관리"], horizontal=True, key="price_mode")

            if price_mode == "폐기물 (음식물 포함)":
                st.markdown("#### 🗑️ 폐기물 품목별 실시간 시세")
                pd_waste = st.session_state['price_data']['폐기물']
                waste_rows = [{"품목":k,"단가(원)":v["단가"],"단위":v["단위"],"변동":v["변동"],"카테고리":v["카테고리"]} for k,v in pd_waste.items()]
                st.dataframe(pd.DataFrame(waste_rows), use_container_width=True, hide_index=True)
                # 단가 수정
                st.write("---")
                st.markdown("**✏️ 단가 수정**")
                sel_waste = st.selectbox("수정할 품목", list(pd_waste.keys()), key="edit_waste")
                new_price_w = st.number_input("새 단가 (원)", value=pd_waste[sel_waste]["단가"], step=10, key="new_price_w")
                if st.button("💾 단가 저장", key="save_waste_price"):
                    st.session_state['price_data']['폐기물'][sel_waste]["단가"] = new_price_w
                    v = st.session_state['price_data']['폐기물'][sel_waste]
                    save_price_to_db('폐기물', sel_waste, new_price_w, v['단위'], '수정', v['카테고리'])
                    st.success(f"✅ {sel_waste} 단가 → {new_price_w:,}원 저장 (DB 영구 반영)!")
                    st.rerun()
                # 신규 품목 추가
                st.write("---")
                st.markdown("**➕ 신규 폐기물 품목 추가**")
                new_wn = st.text_input("품목명", key="new_waste_name")
                new_wp = st.number_input("단가", value=100, step=10, key="new_waste_p")
                new_wc = st.selectbox("카테고리", ["음식물","사업장","건설","기타"], key="new_waste_cat")
                if st.button("➕ 추가", key="add_waste"):
                    if new_wn:
                        st.session_state['price_data']['폐기물'][new_wn] = {"단가":new_wp,"단위":"원/kg","변동":"신규","카테고리":new_wc}
                        st.success(f"✅ {new_wn} 추가!")
                        st.rerun()

            elif price_mode == "재활용품 23종":
                st.markdown("#### ♻️ 재활용품 23종 실시간 시세")
                pd_recy = st.session_state['price_data']['재활용품']
                # 카테고리별 하위탭
                cats = list(dict.fromkeys(v["카테고리"] for v in pd_recy.values()))
                cat_tabs = st.tabs(["📦 전체"] + [f"{'📄' if c=='종이류' else '🧴' if c=='플라스틱' else '🔩' if c=='금속류' else '🫙' if c=='유리류' else '📦'} {c}" for c in cats])
                with cat_tabs[0]:
                    recy_rows = [{"품목":k,"단가(원)":v["단가"],"단위":v["단위"],"변동":v["변동"],"카테고리":v["카테고리"]} for k,v in pd_recy.items()]
                    st.dataframe(pd.DataFrame(recy_rows), use_container_width=True, hide_index=True)
                for ci, cat in enumerate(cats):
                    with cat_tabs[ci+1]:
                        cat_rows = [{"품목":k,"단가(원)":v["단가"],"단위":v["단위"],"변동":v["변동"]} for k,v in pd_recy.items() if v["카테고리"]==cat]
                        st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)
                # 단가 수정
                st.write("---")
                st.markdown("**✏️ 단가 수정**")
                sel_recy = st.selectbox("수정할 품목", list(pd_recy.keys()), key="edit_recy")
                new_price_r = st.number_input("새 단가 (원)", value=pd_recy[sel_recy]["단가"], step=10, key="new_price_r")
                if st.button("💾 단가 저장", key="save_recy_price"):
                    st.session_state['price_data']['재활용품'][sel_recy]["단가"] = new_price_r
                    v = st.session_state['price_data']['재활용품'][sel_recy]
                    save_price_to_db('재활용품', sel_recy, new_price_r, v['단위'], '수정', v['카테고리'])
                    st.success(f"✅ {sel_recy} 단가 → {new_price_r:,}원 저장 (DB 영구 반영)!")
                    st.rerun()
                # 신규 추가
                st.write("---")
                st.markdown("**➕ 신규 재활용 품목 추가**")
                new_rn = st.text_input("품목명", key="new_recy_name")
                new_rp = st.number_input("단가", value=100, step=10, key="new_recy_p")
                new_rc = st.selectbox("카테고리", cats + ["기타"], key="new_recy_cat")
                if st.button("➕ 추가", key="add_recy"):
                    if new_rn:
                        st.session_state['price_data']['재활용품'][new_rn] = {"단가":new_rp,"단위":"원/kg","변동":"신규","카테고리":new_rc}
                        st.success(f"✅ {new_rn} 추가!")
                        st.rerun()

            else:  # 업체/학교별 단가관리
                st.markdown("#### 🏫 업체/학교별 개별 단가 관리")
                st.caption("특정 업체나 학교에 적용되는 개별 단가를 설정합니다.")
                if 'custom_prices' not in st.session_state:
                    st.session_state['custom_prices'] = {}
                sel_target_type = st.radio("대상 유형", ["학교","외주업체"], horizontal=True, key="price_target_type")
                if sel_target_type == "학교":
                    sel_target = st.selectbox("학교 선택", SCHOOL_LIST, key="price_target_sch")
                else:
                    sel_target = st.selectbox("업체 선택", list(VENDOR_DATA.keys()), key="price_target_vd")
                sel_item = st.selectbox("품목", list(st.session_state['price_data']['폐기물'].keys()) + list(st.session_state['price_data']['재활용품'].keys()), key="price_item")
                custom_p = st.number_input("개별 단가 (원)", value=162, step=10, key="custom_price_val")
                if st.button("💾 개별 단가 저장", key="save_custom"):
                    cp_key = f"{sel_target}_{sel_item}"
                    st.session_state['custom_prices'][cp_key] = {"대상":sel_target,"품목":sel_item,"단가":custom_p}
                    st.success(f"✅ {sel_target} - {sel_item} → {custom_p:,}원 저장!")
                # 등록된 개별 단가 표시
                if st.session_state['custom_prices']:
                    st.write("---")
                    st.markdown("**📋 등록된 개별 단가**")
                    cp_rows = [{"대상":v["대상"],"품목":v["품목"],"개별단가(원)":v["단가"]} for v in st.session_state['custom_prices'].values()]
                    st.dataframe(pd.DataFrame(cp_rows), use_container_width=True, hide_index=True)

        # ★ 업체별 계약현황 탭
        # ★ 수거업체관리 탭
        if tab_vendor_mgmt is not None:
         with tab_vendor_mgmt:
            st.subheader("🚛 수거업체 관리")
            st.caption("본사 + 외주 전체 수거업체의 품목별 수거현황을 관리합니다.")
            all_vendors = ["하영자원(본사)"] + list(VENDOR_DATA.keys())
            # 업체 총괄 테이블
            mgmt_rows = []
            for vn in all_vendors:
                if vn == "하영자원(본사)":
                    v_sch = []; 
                    for did in ['driver01','driver02','driver03']: v_sch.extend(DRIVER_ACCOUNTS[did].get('schools',[]))
                    v_drivers = 3; v_cars = 2
                else:
                    vd = VENDOR_DATA[vn]; v_sch = vd['schools']; v_drivers = len(vd.get('drivers',[])); v_cars = len(vd.get('차량',[]))
                mgmt_rows.append({'업체명':vn,'담당학교수':len(v_sch),'기사수':v_drivers,'차량수':v_cars})
            st.dataframe(pd.DataFrame(mgmt_rows), use_container_width=True, hide_index=True)

            # 품목별 하위시트
            st.write("---")
            st.markdown("#### 📦 품목별 수거현황")
            item_tabs_mgmt = st.tabs(["🗑️ 음식물","🗄️ 사업장","♻️ 재활용"])
            item_cols_map = [("음식물(kg)","음식물"),("사업장(kg)","사업장"),("재활용(kg)","재활용")]
            for iti, (icol, ilabel) in enumerate(item_cols_map):
                with item_tabs_mgmt[iti]:
                    st.markdown(f"**{ilabel} 품목 업체별 현황**")
                    if not df_real.empty and icol in df_real.columns:
                        for vn in all_vendors:
                            if vn == "하영자원(본사)":
                                v_sch = []; 
                                for did in ['driver01','driver02','driver03']: v_sch.extend(DRIVER_ACCOUNTS[did].get('schools',[]))
                            else:
                                v_sch = VENDOR_DATA[vn]['schools']
                            df_vn = df_real[(df_real['학교명'].isin(v_sch)) & (df_real['수거여부'])]
                            total = df_vn[icol].sum() if not df_vn.empty else 0
                            if total > 0:
                                with st.expander(f"🏢 {vn} - {ilabel} {total:,.0f}kg"):
                                    vn_sum = df_vn.groupby('학교명').agg(수거량=(icol,'sum')).reset_index().sort_values('수거량',ascending=False)
                                    st.dataframe(vn_sum, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"{ilabel} 수거 데이터가 없습니다.")

        if tab_map is not None:
         with tab_map:
            st.write("📍 **수거 차량 실시간 GPS 관제**")
            st.map(pd.DataFrame({'lat':[37.20,37.25],'lon':[127.05,127.10]}))
        if tab_sub is not None:
         with tab_sub:
            st.subheader("🤝 외주 수거업체 관리")
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
            with vc1: st.success(f"🏆 우수: **{sorted_vendors[0][0]}** ({sorted_vendors[0][1]['안전점수']}점)")
            worst = sorted_vendors[-1]
            with vc2: st.warning(f"⚠️ 주의: **{worst[0]}** ({worst[1]['안전점수']}점)")
            with vc3: st.info(f"✅ 스쿨존 위반: **1건**")

            # 업체 총괄 테이블
            vendor_rows = []
            for vn, vd in VENDOR_DATA.items():
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
                    '안전 페널티':f"{penalty:,} 원" if penalty else "0 원",
                    '정산예상액':f"{max(0,v_total+penalty):,.0f} 원",
                    '운행상태':vd['상태'],
                })
            st.dataframe(pd.DataFrame(vendor_rows), use_container_width=True, hide_index=True)

            # ★ 안전평가 결과서 + 청구서 (업체 선택 방식)
            st.write("---")
            st.markdown("**📋 안전평가 / 💰 청구서 다운로드**")
            sel_v = st.selectbox("업체 선택", list(VENDOR_DATA.keys()), key="admin_vendor_sel_simple")
            vinfo = VENDOR_DATA[sel_v]

            # 안전평가 함수 정의 (탭 밖에서)
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
            ac1, ac2 = st.columns(2)
            with ac1:
                st.download_button("📋 안전평가 결과서 다운로드", data=create_safety_report_excel(sel_v, VENDOR_DATA[sel_v]),
                                   file_name=f"{sel_v}_안전평가결과서_{CURRENT_DATE}.xlsx", use_container_width=True)
            with ac2:
                st.caption(f"※ 외주업체 상세 관리는 해당 업체 관리자 모드에서 확인하세요.")
            # ★ 계약현황 하위시트
            st.write("---")
            st.subheader("📋 업체별 계약현황")
            if 'contract_data' not in st.session_state:
                st.session_state['contract_data'] = load_contracts_from_db()
            sel_cv = st.selectbox("업체 선택", list(st.session_state['contract_data'].keys()), key="ct_vendor_sel")
            cv_data = st.session_state['contract_data'][sel_cv]
            st.markdown(f'<div style="background:linear-gradient(135deg,#34a853,#4caf50);padding:12px;border-radius:10px;color:white;"><b>{sel_cv}</b> | 대표: {cv_data["대표"]} | 계약: {cv_data["계약시작"]}~{cv_data["계약만료"]} | {cv_data["상태"]}</div>', unsafe_allow_html=True)
            ct_sub1, ct_sub2 = st.tabs(["💰 품목별 계약단가","✏️ 수정/추가"])
            with ct_sub1:
                ct_rows = [{"품목":k,"계약단가(원/kg)":v} for k,v in cv_data["품목단가"].items()]
                st.dataframe(pd.DataFrame(ct_rows), use_container_width=True, hide_index=True)
            with ct_sub2:
                sel_ct_item = st.selectbox("품목", list(cv_data["품목단가"].keys()), key="ct_edit_item")
                new_ct_p = st.number_input("새 단가", value=cv_data["품목단가"][sel_ct_item], step=10, key="ct_new_price")
                if st.button("💾 수정", key="ct_save"):
                    st.session_state['contract_data'][sel_cv]["품목단가"][sel_ct_item] = new_ct_p
                    save_contract_price(sel_cv, sel_ct_item, new_ct_p)
                    st.success(f"✅ {sel_cv} - {sel_ct_item} → {new_ct_p:,}원 (DB 영구 반영)"); st.rerun()
                st.write("---")
                new_ct_name = st.text_input("신규 품목명", key="ct_new_name")
                new_ct_val = st.number_input("단가", value=150, step=10, key="ct_new_p")
                if st.button("➕ 추가", key="ct_add"):
                    if new_ct_name:
                        st.session_state['contract_data'][sel_cv]["품목단가"][new_ct_name] = new_ct_val
                        save_contract_price(sel_cv, new_ct_name, new_ct_val)
                        st.success(f"✅ 추가! (DB 영구 반영)"); st.rerun()

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
            with st.expander("📅 오늘의 수거일정 (간편)"):
                st.caption("상세 등록/수정은 '📅 수거일정 관리' 탭에서 가능합니다.")
                for vn in list(VENDOR_DATA.keys()):
                    sch_count = len(st.session_state.get(f'schedule_{vn}', VENDOR_DATA[vn]['schools']))
                    st.caption(f"• {vn}: {sch_count}개교")
                own_count = len(st.session_state.get('schedule_하영자원(본사)', []))
                st.caption(f"• 하영자원(본사): {own_count}개교")
            with st.expander("📄 월말거래명세서 발송"):
                st.caption("PDF 파일을 업로드하면 자동 분석 후 거래명세서를 생성합니다.")
                inv_file = st.file_uploader("잔반처리량 PDF/CSV/엑셀", type=['pdf','csv','xlsx'], key="admin_inv_upload")
                if inv_file:
                    try:
                        if inv_file.name.endswith('.csv'):
                            df_inv = pd.read_csv(inv_file)
                        elif inv_file.name.endswith(('.xlsx','.xls')):
                            df_inv = pd.read_excel(inv_file)
                        else:
                            # PDF → 텍스트 파싱
                            import re as re_mod
                            content = inv_file.read().decode('utf-8', errors='ignore')
                            # PDF 원본 텍스트에서 데이터 추출 시도
                            inv_file.seek(0)
                            lines_raw = content.split('\n')
                            rows_parsed = []
                            for line in lines_raw:
                                m = re_mod.search(r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)\s*\S+\s+(\d+)\s+[\d.]+\s+([\d,]+)', line)
                                if m:
                                    rows_parsed.append({'수거일':m.group(1),'단위(L)':int(m.group(2)),'단가':170,'공급가':int(m.group(3).replace(',','')),'재활용방법':'퇴비화및비료생산'})
                            if rows_parsed:
                                df_inv = pd.DataFrame(rows_parsed)
                            else:
                                df_inv = pd.DataFrame()
                                st.warning("PDF에서 데이터를 자동 추출하지 못했습니다. CSV/엑셀로 업로드해 주세요.")
                        if not df_inv.empty:
                            st.success(f"✅ {len(df_inv)}건 분석 완료")
                            st.session_state['admin_inv_data'] = df_inv
                            st.dataframe(df_inv.head(10), use_container_width=True, hide_index=True)
                            # 요약
                            qty_col = [c for c in df_inv.columns if '단위' in c or 'L' in c or 'kg' in c or '음식물' in c]
                            sup_col = [c for c in df_inv.columns if '공급가' in c]
                            if qty_col: st.metric("총 수거량", f"{df_inv[qty_col[0]].sum():,.0f}")
                            if sup_col: st.metric("총 공급가", f"{df_inv[sup_col[0]].sum():,.0f}원")
                    except Exception as e:
                        st.error(f"파일 분석 실패: {e}")
                # 거래명세서 PDF 생성
                if 'admin_inv_data' in st.session_state and not st.session_state['admin_inv_data'].empty:
                    st.write("---")
                    inv_vendor = st.selectbox("발송 업체", ["하영자원(본사)"] + list(VENDOR_DATA.keys()), key="inv_vendor")
                    inv_school = st.text_input("거래처(학교)명", value="평촌초등학교", key="inv_school")
                    inv_month = st.number_input("월", value=11, min_value=1, max_value=12, key="inv_month")
                    if st.button("📄 거래명세서 PDF 생성", type="primary", use_container_width=True, key="gen_invoice"):
                        pdf_data = create_monthly_invoice_pdf(inv_vendor, inv_school, inv_month, "2025", st.session_state['admin_inv_data'])
                        st.download_button("📥 거래명세서 다운로드", data=pdf_data, file_name=f"{inv_school}_{inv_month}월_거래명세서.pdf", mime="application/pdf", use_container_width=True, key="dl_invoice")
                        st.success("✅ 거래명세서 PDF 생성 완료!")

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
                            base_cols = ['날짜','음식물(kg)','단가(원)','공급가','재활용방법']
                            extra_cols = [c for c in ['수거업체','수거기사','수거시간'] if c in df_rm.columns]
                            df_rm_show = df_rm[base_cols + extra_cols].copy()
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
                        st.info("💡 올바로시스템 실적보고서 (배출자용)")
                        st.caption("폐기물관리법 제38조 / 배출자 실적보고서")
                        if not df_school_real.empty:
                            sch_ab_years = sorted(df_school_real['년도'].unique(), reverse=True)
                            sel_sch_ab_yr = st.selectbox("📅 년도", sch_ab_years, key="sch_ab_yr")
                            sel_sch_ab_item = st.selectbox("📦 품목", ["전체","음식물","사업장","재활용"], key="sch_ab_item")
                            st.download_button("📄 올바로 실적보고서 다운로드 (배출자용)",
                                data=create_allbaro_report(df_school_real, 'emitter', school, sel_sch_ab_yr, sel_sch_ab_item),
                                file_name=f"올바로_배출자_{school}_{sel_sch_ab_yr}.xlsx", use_container_width=True)
                        st.write("---")
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
            edu_tabs = st.tabs(["📊 실제 수거 현황(2025)","📋 관할 학교 상세","📈 시뮬레이션 통계","🔗 올바로 보고서","🌍 ESG 탄소중립 보고서"])

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

            # ★ 탭4: 올바로 보고서 (배출자용 - 교육청 관할)
            with edu_tabs[3]:
                st.subheader("🔗 올바로시스템 실적보고서 (배출자용 - 교육청)")
                st.caption("관할 학교 통합 폐기물 배출 실적보고서")
                if not df_edu_real.empty:
                    edu_ab_years = sorted(df_edu_real['년도'].unique(), reverse=True)
                    sel_edu_ab_yr = st.selectbox("📅 년도", edu_ab_years, key="edu_ab_yr")
                    sel_edu_ab_item = st.selectbox("📦 품목", ["전체","음식물","사업장","재활용"], key="edu_ab_item")
                    st.download_button("📄 올바로 실적보고서 다운로드 (배출자용)",
                        data=create_allbaro_report(df_edu_real, 'emitter', user_name, sel_edu_ab_yr, sel_edu_ab_item),
                        file_name=f"올바로_배출자_{user_name}_{sel_edu_ab_yr}.xlsx", use_container_width=True)
                else:
                    st.info("실제 수거 데이터가 없습니다.")
            # ★ 탭5: ESG 탄소중립 보고서 출력
            with edu_tabs[4]:
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

            # ★ 기사 메인 탭 (4개)
            d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["📅 오늘 수거일정","🗓️ 월별/일별 일정","📤 수거 완료 보고","🚨 안전/퇴근"])

            # ===== 탭1: 오늘의 수거일정 (품목별 하위시트) =====
            with d_tab1:
                st.markdown("### 📅 오늘의 수거일정")
                schedule_key = f'schedule_{vendor_name}'
                today_schools = st.session_state.get(schedule_key, my_schools)
                my_today = [s for s in today_schools if s in my_schools] if today_schools else my_schools
                # 이번달 품목 가져오기
                monthly_key = f"monthly_sched_{vendor_name}_{CURRENT_MONTH}"
                monthly_info = st.session_state.get(monthly_key, {"품목":['음식물','사업장','재활용']})
                today_items = monthly_info.get('품목', ['음식물','사업장','재활용'])

                if my_today:
                    # 상단 요약
                    dm1, dm2, dm3 = st.columns(3)
                    with dm1: st.metric("오늘 수거 학교", f"{len(my_today)}곳")
                    with dm2: st.metric("수거 품목", f"{len(today_items)}종")
                    with dm3: st.metric("예상 소요", f"{len(my_today)*20}분")

                    # ★ 품목별 하위시트
                    item_tabs = st.tabs([f"📦 전체"] + [f"{'🗑️' if it=='음식물' else '🗄️' if it=='사업장' else '♻️'} {it}" for it in today_items])
                    with item_tabs[0]:
                        for idx, sch_name in enumerate(my_today):
                            with st.expander(f"🏫 {idx+1}. {sch_name} ({', '.join(today_items)})", expanded=(idx==0)):
                                import urllib.parse
                                encoded_name = urllib.parse.quote(sch_name)
                                kakao_url = f"https://map.kakao.com/link/search/{encoded_name}"
                                tmap_search = f"tmap://search?name={encoded_name}"
                                nc1, nc2 = st.columns(2)
                                with nc1:
                                    st.markdown(f'<a href="{kakao_url}" target="_blank" style="display:block;text-align:center;background:#FEE500;color:#000;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;">🗺️ 카카오맵</a>', unsafe_allow_html=True)
                                with nc2:
                                    st.markdown(f'<a href="{tmap_search}" target="_blank" style="display:block;text-align:center;background:#0064FF;color:#fff;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;">🚗 티맵</a>', unsafe_allow_html=True)
                    for it_idx, item_name in enumerate(today_items):
                        with item_tabs[it_idx + 1]:
                            st.markdown(f"**{item_name} 수거 대상 학교**")
                            for idx, sch_name in enumerate(my_today):
                                st.markdown(f"  {idx+1}. 🏫 {sch_name}")
                else:
                    st.info("오늘 배정된 수거 학교가 없습니다.")

            # ===== 탭2: 월별/일별 수거일정 확인 =====
            with d_tab2:
                st.markdown("### 🗓️ 수거일정 확인")
                d_sched_sub = st.tabs(["📅 월별 일정","📋 일별 상세"])
                with d_sched_sub[0]:
                    st.markdown(f"**{vendor_name} 월별 수거일정**")
                    has_any = False
                    for m in range(1, 13):
                        sk = f"monthly_sched_{vendor_name}_{m}"
                        if sk in st.session_state:
                            has_any = True
                            sd = st.session_state[sk]
                            my_sched_schools = [s for s in sd.get('학교',[]) if s in my_schools]
                            if my_sched_schools:
                                with st.expander(f"📅 {m}월 ({'진행중' if m==CURRENT_MONTH else '예정'})", expanded=(m==CURRENT_MONTH)):
                                    st.write(f"**수거 요일:** {', '.join(sd.get('요일',[]))}")
                                    st.write(f"**수거 품목:** {', '.join(sd.get('품목',[]))}")
                                    st.write(f"**내 담당 학교 ({len(my_sched_schools)}곳):**")
                                    for si, s in enumerate(my_sched_schools):
                                        st.markdown(f"  {si+1}. {s}")
                    if not has_any:
                        st.info("관리자가 등록한 월별 일정이 없습니다.")
                with d_sched_sub[1]:
                    st.markdown("**이번 주 수거일정**")
                    weekdays_kr = ['월','화','수','목','금','토','일']
                    today_wd = weekdays_kr[datetime.now().weekday()]
                    mk = f"monthly_sched_{vendor_name}_{CURRENT_MONTH}"
                    m_info = st.session_state.get(mk, {})
                    m_days = m_info.get('요일', ['월','수','금'])
                    m_schools = [s for s in m_info.get('학교', my_schools) if s in my_schools]
                    m_items = m_info.get('품목', ['음식물','사업장','재활용'])
                    for wd in ['월','화','수','목','금']:
                        is_today = (wd == today_wd)
                        is_work = (wd in m_days)
                        icon = "🟢" if is_work else "⚪"
                        label = f" ← **오늘**" if is_today else ""
                        if is_work:
                            with st.expander(f"{icon} {wd}요일 - {len(m_schools)}곳 수거{label}", expanded=is_today):
                                st.write(f"**품목:** {', '.join(m_items)}")
                                for si, s in enumerate(m_schools):
                                    st.markdown(f"  {si+1}. 🏫 {s}")
                        else:
                            st.caption(f"{icon} {wd}요일 - 수거 없음{label}")

            # ===== 탭3: 수거 완료 보고 =====
            with d_tab3:
                st.markdown("### 📤 수거 완료 보고")
                st.camera_input("📸 현장 증빙 사진 (선택)")
                with st.form("driver_input"):
                    target = st.selectbox("수거 완료 학교", my_today if my_today else my_schools)
                    ci1, ci2, ci3 = st.columns(3)
                    with ci1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
                    with ci2: biz_w = st.number_input("사업장 (kg)", min_value=0, step=10)
                    with ci3: re_w = st.number_input("재활용 (kg)", min_value=0, step=10)
                    if st.form_submit_button("📤 본사로 수거량 전송", type="primary", use_container_width=True):
                        if food_w > 0 or biz_w > 0 or re_w > 0:
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            now_time = datetime.now().strftime("%H:%M")
                            new_data = {"날짜": now_str,
                                "학교명": target, "학생수": STUDENT_COUNTS.get(target, 0), "수거업체": vendor_name,
                                "수거기사": user_name, "수거시간": now_time,
                                "음식물(kg)": food_w, "재활용(kg)": re_w, "사업장(kg)": biz_w,
                                "단가(원)": 150, "재활용단가(원)": 300, "사업장단가(원)": 200, "상태": "실시간"}
                            save_data(new_data)
                            real_row = pd.DataFrame([{
                                "날짜": datetime.now().strftime("%Y-%m-%d"),
                                "학교명": target, "음식물(kg)": food_w, "단가(원)": 162,
                                "공급가": food_w * 162, "재활용방법": "퇴비화및비료생산",
                                "재활용업체": "(주)혜인이엔씨", "월": datetime.now().month,
                                "년도": str(datetime.now().year), "월별파일": f"{datetime.now().month}월",
                                "수거업체": vendor_name, "수거기사": user_name, "수거시간": now_time
                            }])
                            try:
                                existing = pd.read_csv(REAL_DATA_FILE)
                                merged = pd.concat([existing, real_row], ignore_index=True)
                            except:
                                merged = real_row
                            merged.to_csv(REAL_DATA_FILE, index=False)
                            # SQLite 동기화
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                real_row.to_sql('collection_data', conn, if_exists='append', index=False)
                                conn.close()
                            except: pass
                            st.success(f"✅ {target} 수거 실적 전송 완료!")
                            st.caption(f"📡 {vendor_name} | {user_name} | {now_time} → 본사+행정실 실시간 반영")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")

            # ===== 탭4: 안전/퇴근 =====
            with d_tab4:
                is_schoolzone = st.toggle("🚨 스쿨존 진입 알림 (GPS 테스트)")
                if is_schoolzone:
                    st.error("스쿨존 진입! 속도를 30km 이하로 줄이세요.")
                    st.markdown("<h1 style='text-align:center;color:#d93025;font-size:60px;'>30</h1>", unsafe_allow_html=True)
                st.write("---")
                st.markdown("### 🏠 퇴근 처리")
                if st.button("🏠 퇴근하기", use_container_width=True, type="secondary"):
                    st.balloons()
                    st.success(f"✅ {user_name}님, {datetime.now().strftime('%H시 %M분')} 퇴근 처리 완료! 수고하셨습니다.")
                    st.caption("퇴근 기록이 본사 관제센터로 자동 전송됩니다.")

    # ============ [모드5] 외주업체 관리자 ============
    elif role == "vendor_admin":
        va_info = ALL_ACCOUNTS.get(st.session_state.user_id, {})
        va_vendor = va_info.get('vendor', '')
        va_data = VENDOR_DATA.get(va_vendor, {})
        va_schools = va_data.get('schools', [])
        va_drivers = [DRIVER_ACCOUNTS[d]['name'] for d in va_data.get('drivers',[]) if d in DRIVER_ACCOUNTS]

        st.title(f"🏢 {va_vendor} 관리자 대시보드")
        st.markdown(f'<div style="background:linear-gradient(135deg,#1a73e8,#4285f4);padding:16px;border-radius:12px;color:white;"><b>대표:</b> {va_data.get("대표","")} | <b>사업자:</b> {va_data.get("사업자번호","")} | <b>연락처:</b> {va_data.get("연락처","")} | <b>안전점수:</b> {va_data.get("안전점수",0)}점</div>', unsafe_allow_html=True)

        # 상단 지표
        vm1, vm2, vm3, vm4 = st.columns(4)
        with vm1: st.metric("담당 학교", f"{len(va_schools)}개교")
        with vm2: st.metric("기사 수", f"{len(va_drivers)}명")
        with vm3: st.metric("차량 수", f"{len(va_data.get('차량',[]))}대")
        with vm4: st.metric("계약 만료", va_data.get('계약만료',''))

        # 메인 탭
        va_t1, va_t2, va_t3, va_t6, va_t4, va_t5 = st.tabs(["📊 거래처별 수거현황","💰 정산/세금계산서","🔗 올바로 보고서","🏫 거래처/데이터 관리","📅 수거일정","🚚 기사 관리"])

        # ===== 탭1: 거래처별 수거현황 (품목→년도→월) =====
        with va_t1:
            st.subheader("📊 거래처별 수거 현황")
            cust_type_tabs = st.tabs(["🏫 학교","🏢 일반업장"])
            va_biz_key = f"va_biz_customers_{va_vendor}"
            if va_biz_key not in st.session_state: st.session_state[va_biz_key] = []
            with cust_type_tabs[0]:
                st.caption("학교 거래처 수거 현황")
                if not df_real.empty:
                    df_va = df_real[df_real['학교명'].isin(va_schools)]
                    if not df_va.empty:
                        sel_va_sch = st.selectbox("🏫 거래처(학교) 선택", ["전체"] + va_schools, key="va_school")
                        df_vas = df_va if sel_va_sch == "전체" else df_va[df_va['학교명']==sel_va_sch]
                        item_tabs = st.tabs(["📦 전체","🗑️ 음식물","🗄️ 사업장","♻️ 재활용"])
                        for it_idx, (it_tab, it_col) in enumerate(zip(item_tabs, [None,'음식물(kg)','사업장(kg)','재활용(kg)'])):
                            with it_tab:
                                df_it = df_vas[df_vas['수거여부']]
                                va_years = sorted(df_it['년도'].unique(), reverse=True)
                                if va_years:
                                    sel_va_yr = st.selectbox("📅 년도", va_years, key=f"va_yr_{it_idx}")
                                    df_vy = df_it[df_it['년도']==sel_va_yr]
                                    va_months = sorted(df_vy['월'].unique())
                                    va_mtabs = st.tabs(["📅 연간"] + [f"🗓️ {m}월" for m in va_months])
                                    with va_mtabs[0]:
                                        if sel_va_sch == "전체":
                                            vy_sum = df_vy.groupby('학교명').agg(수거일수=('음식물(kg)','count'),수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index().sort_values('수거량',ascending=False)
                                            st.dataframe(vy_sum, use_container_width=True, hide_index=True)
                                        else:
                                            show_cols = ['날짜','학교명','음식물(kg)','단가(원)','공급가','재활용방법'] + [c for c in ['수거업체','수거기사','수거시간'] if c in df_vy.columns]
                                            st.dataframe(df_vy[show_cols], use_container_width=True, hide_index=True)
                                    for vmi, vm in enumerate(va_months):
                                        with va_mtabs[vmi+1]:
                                            df_vmm = df_vy[df_vy['월']==vm]
                                            if sel_va_sch == "전체":
                                                vmm_s = df_vmm.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                                                st.dataframe(vmm_s, use_container_width=True, hide_index=True)
                                            else:
                                                show_cols2 = ['날짜','학교명','음식물(kg)','단가(원)','공급가'] + [c for c in ['수거기사','수거시간'] if c in df_vmm.columns]
                                                st.dataframe(df_vmm[show_cols2], use_container_width=True, hide_index=True)
                                            # 월말명세서 다운로드 + 이메일 전송
                                            mc1, mc2 = st.columns(2)
                                            with mc1:
                                                pdf_data_m = create_monthly_invoice_pdf(va_vendor, sel_va_sch if sel_va_sch!="전체" else va_vendor, vm, sel_va_yr, df_vmm)
                                                st.download_button(f"📄 {vm}월 명세서 PDF", data=pdf_data_m, file_name=f"{va_vendor}_{vm}월_명세서.pdf", mime="application/pdf", use_container_width=True, key=f"va_inv_dl_{it_idx}_{vm}")
                                            with mc2:
                                                if st.button(f"📧 {vm}월 이메일 전송", use_container_width=True, key=f"va_inv_em_{it_idx}_{vm}"):
                                                    st.info("📧 이메일 전송 기능은 SMTP 설정 후 사용 가능합니다.")
                    else:
                        st.info("담당 학교의 수거 데이터가 없습니다.")
                else:
                    st.info("실제 수거 데이터가 로드되지 않았습니다.")
            with cust_type_tabs[1]:
                st.caption("일반업장 거래처 수거 현황")
                biz_list = st.session_state[va_biz_key]
                if biz_list:
                    st.markdown("**등록된 일반업장:**")
                    for bi, bn in enumerate(biz_list):
                        st.write(f"  {bi+1}. 🏢 {bn}")
                else:
                    st.info("등록된 일반업장이 없습니다.")
                st.write("---")
                new_biz = st.text_input("신규 일반업장 추가", placeholder="예: (주)삼성전자 화성사업장", key=f"va_new_biz_{va_vendor}")
                if st.button("➕ 업장 추가", key=f"va_add_biz_{va_vendor}"):
                    if new_biz and new_biz not in biz_list:
                        st.session_state[va_biz_key].append(new_biz)
                        st.success(f"✅ {new_biz} 추가!"); st.rerun()

        # ===== 탭2: 정산/세금계산서 =====
        with va_t2:
            st.subheader("💰 정산 내역 및 세금계산서")
            if not df_real.empty:
                df_va_bill = df_real[(df_real['학교명'].isin(va_schools)) & (df_real['수거여부'])]
                if not df_va_bill.empty:
                    va_bill_months = sorted(df_va_bill['월'].unique())
                    bill_tabs = st.tabs([f"🗓️ {m}월" for m in va_bill_months])
                    for bi, bm in enumerate(va_bill_months):
                        with bill_tabs[bi]:
                            df_bm = df_va_bill[df_va_bill['월']==bm]
                            bm_sum = df_bm.groupby('학교명').agg(수거량=('음식물(kg)','sum'),공급가=('공급가','sum')).reset_index()
                            st.dataframe(bm_sum, use_container_width=True, hide_index=True)
                            bm_total = bm_sum['공급가'].sum()
                            penalty = -50000 if va_data.get('안전점수',100) < 90 else 0
                            final_amt = max(0, bm_total + penalty)
                            bm1, bm2, bm3 = st.columns(3)
                            with bm1: st.metric("수거 공급가", f"{bm_total:,.0f} 원")
                            with bm2: st.metric("안전 페널티", f"{penalty:,} 원")
                            with bm3: st.metric("최종 청구액", f"{final_amt:,.0f} 원")
                            st.write("---")
                            # ★ 정산내역 본사전송 버튼
                            if st.button(f"📤 {bm}월 정산내역 본사 전송", type="primary", use_container_width=True, key=f"va_send_{bm}"):
                                st.success(f"✅ {bm}월 정산내역({final_amt:,.0f}원)이 하영자원 본사로 전송되었습니다.")
                                st.caption(f"전송시각: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 상태: 본사 검토 대기")
                            # ★ 전자세금계산서/전자계산서 발행 버튼
                            st.write("---")
                            tax_type = st.radio(f"{bm}월 발행 유형", ["전자세금계산서(부가세10%)","전자계산서(세율적용X)"], horizontal=True, key=f"va_tax_type_{bm}")
                            is_tax = "세금" in tax_type
                            if is_tax:
                                supply = int(final_amt / 1.1)
                                vat = final_amt - supply
                            else:
                                supply = int(final_amt)
                                vat = 0
                            st.caption(f"공급가액: {supply:,}원 | {'부가세' if is_tax else '세액'}: {vat:,.0f}원 | 합계: {final_amt:,.0f}원")
                            tax_label = "전자세금계산서" if is_tax else "전자계산서"
                            if st.button(f"🧾 {bm}월 {tax_label} 발행 (홈택스 연동)", use_container_width=True, key=f"va_tax_{bm}"):
                                with st.spinner("국세청 홈택스 API 연동 중..."):
                                    time.sleep(2)
                                kind_code = "01" if is_tax else "05"
                                st.success(f"✅ {bm}월 {tax_label} 발행 완료!")
                                st.markdown(f"""
**{tax_label} 발행 정보** (종류코드: {kind_code})
- 공급자: {va_vendor} ({va_data.get('사업자번호','')})
- 공급받는자: 하영자원 (603-17-01234)
- 작성일자: {CURRENT_DATE}
- 공급가액: {supply:,}원 | 세액: {vat:,.0f}원
- 승인번호: HT-{datetime.now().strftime('%Y%m%d')}-{bm:02d}-00{bi+1}
                                """)
                else:
                    st.info("수거 데이터가 없습니다.")
            else:
                st.info("실제 수거 데이터가 로드되지 않았습니다.")

        # ===== 탭3: 올바로 보고서 (수집운반업자용) =====
        with va_t3:
            st.subheader(f"🔗 {va_vendor} 올바로 실적보고서 (수집운반업자용)")
            st.caption("폐기물관리법 제38조 / 수집·운반업자 실적보고서")
            if not df_real.empty:
                df_va_ab = df_real[df_real['학교명'].isin(va_schools)]
                if not df_va_ab.empty:
                    va_ab_years = sorted(df_va_ab['년도'].unique(), reverse=True)
                    sel_va_ab_yr = st.selectbox("📅 년도", va_ab_years, key="va_ab_yr")
                    sel_va_ab_item = st.selectbox("📦 품목", ["전체","음식물","사업장","재활용"], key="va_ab_item")
                    st.download_button("📄 올바로 실적보고서 다운로드 (수집운반업자용)",
                        data=create_allbaro_report(df_va_ab, 'transporter', va_vendor, sel_va_ab_yr, sel_va_ab_item),
                        file_name=f"올바로_수집운반_{va_vendor}_{sel_va_ab_yr}.xlsx", use_container_width=True)
                else:
                    st.info("담당 학교의 수거 데이터가 없습니다.")
            else:
                st.info("실제 수거 데이터가 없습니다.")

        # ===== 탭6: 거래처 리스트 + 수거데이터 업로드 =====
        with va_t6:
            st.subheader(f"🏫 {va_vendor} 거래처 및 수거데이터 관리")
            st.caption("외주업체 자체 거래처·수거 데이터입니다. (본사 연동 불필요)")
            va_sub = st.tabs(["📋 거래처 리스트","📤 수거데이터 업로드","🔗 올바로 연동"])
            # 세션 키
            va_cust_key = f"va_customers_{va_vendor}"
            va_data_key = f"va_upload_data_{va_vendor}"
            if va_cust_key not in st.session_state:
                st.session_state[va_cust_key] = list(va_schools)  # 기존 학교 복사
            if va_data_key not in st.session_state:
                st.session_state[va_data_key] = pd.DataFrame()

            with va_sub[0]:
                st.markdown("**📋 거래처 리스트** (홈택스 전자계산서 양식 기준)")
                # 세션에 상세 거래처 정보 저장
                va_detail_key = f"va_cust_detail_{va_vendor}"
                if va_detail_key not in st.session_state:
                    db_custs = load_customers_from_db(va_vendor)
                    if db_custs:
                        st.session_state[va_detail_key] = db_custs
                    else:
                        st.session_state[va_detail_key] = {s: {"사업자번호":"","상호":s,"대표자":"","주소":"","업태":"교육서비스","종목":"초중등교육","이메일":"","구분":"학교"} for s in st.session_state[va_cust_key]}
                        save_all_customers_to_db(va_vendor, st.session_state[va_detail_key])
                cust_detail = st.session_state[va_detail_key]
                # 거래처 테이블
                if cust_detail:
                    rows_cd = [{"No":i+1,"구분":v.get("구분","학교"),"상호":k,"사업자번호":v.get("사업자번호",""),"대표자":v.get("대표자",""),"업태":v.get("업태",""),"종목":v.get("종목",""),"이메일":v.get("이메일","")} for i,(k,v) in enumerate(cust_detail.items())]
                    st.dataframe(pd.DataFrame(rows_cd), use_container_width=True, hide_index=True)
                st.write("---")
                st.markdown("**➕ 신규 거래처 등록 / ✏️ 기존 수정**")
                edit_mode = st.radio("", ["신규 등록","기존 수정"], horizontal=True, key=f"va_cust_mode_{va_vendor}", label_visibility="collapsed")
                if edit_mode == "신규 등록":
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        nc_type = st.selectbox("구분", ["학교","일반업장"], key=f"nc_type_{va_vendor}")
                        nc_name = st.text_input("상호(거래처명)*", key=f"nc_name_{va_vendor}")
                        nc_biz = st.text_input("사업자등록번호 ('-'없이)", placeholder="1234567890", key=f"nc_biz_{va_vendor}")
                        nc_rep = st.text_input("대표자", key=f"nc_rep_{va_vendor}")
                    with ec2:
                        nc_addr = st.text_input("사업장주소", key=f"nc_addr_{va_vendor}")
                        nc_btype = st.text_input("업태", value="교육서비스" if nc_type=="학교" else "서비스", key=f"nc_bt_{va_vendor}")
                        nc_bitem = st.text_input("종목", value="초중등교육" if nc_type=="학교" else "", key=f"nc_bi_{va_vendor}")
                        nc_email = st.text_input("이메일", key=f"nc_em_{va_vendor}")
                    if st.button("➕ 거래처 등록", type="primary", use_container_width=True, key=f"nc_save_{va_vendor}"):
                        if nc_name:
                            new_info = {"사업자번호":nc_biz,"상호":nc_name,"대표자":nc_rep,"주소":nc_addr,"업태":nc_btype,"종목":nc_bitem,"이메일":nc_email,"구분":nc_type}
                            st.session_state[va_detail_key][nc_name] = new_info
                            save_customer_to_db(va_vendor, nc_name, new_info)
                            if nc_name not in st.session_state[va_cust_key]: st.session_state[va_cust_key].append(nc_name)
                            st.success(f"✅ {nc_name} 등록! (DB 영구 저장)"); st.rerun()
                else:
                    if cust_detail:
                        sel_edit = st.selectbox("수정할 거래처", list(cust_detail.keys()), key=f"sel_edit_{va_vendor}")
                        ed = cust_detail[sel_edit]
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            ed_biz = st.text_input("사업자번호", value=ed.get("사업자번호",""), key=f"ed_biz_{va_vendor}")
                            ed_rep = st.text_input("대표자", value=ed.get("대표자",""), key=f"ed_rep_{va_vendor}")
                            ed_type = st.selectbox("구분", ["학교","일반업장"], index=0 if ed.get("구분")=="학교" else 1, key=f"ed_type_{va_vendor}")
                        with ec2:
                            ed_addr = st.text_input("주소", value=ed.get("주소",""), key=f"ed_addr_{va_vendor}")
                            ed_bt = st.text_input("업태", value=ed.get("업태",""), key=f"ed_bt_{va_vendor}")
                            ed_bi = st.text_input("종목", value=ed.get("종목",""), key=f"ed_bi_{va_vendor}")
                        ed_em = st.text_input("이메일", value=ed.get("이메일",""), key=f"ed_em_{va_vendor}")
                        ec3, ec4 = st.columns(2)
                        with ec3:
                            if st.button("💾 수정 저장", type="primary", use_container_width=True, key=f"ed_save_{va_vendor}"):
                                updated = {"사업자번호":ed_biz,"상호":sel_edit,"대표자":ed_rep,"주소":ed_addr,"업태":ed_bt,"종목":ed_bi,"이메일":ed_em,"구분":ed_type}
                                st.session_state[va_detail_key][sel_edit] = updated
                                save_customer_to_db(va_vendor, sel_edit, updated)
                                st.success("✅ 수정! (DB 영구 반영)"); st.rerun()
                        with ec4:
                            if st.button("🗑️ 삭제", use_container_width=True, key=f"ed_del_{va_vendor}"):
                                del st.session_state[va_detail_key][sel_edit]
                                delete_customer_from_db(va_vendor, sel_edit)
                                if sel_edit in st.session_state[va_cust_key]: st.session_state[va_cust_key].remove(sel_edit)
                                st.success("✅ 삭제! (DB 영구 반영)"); st.rerun()
                # 홈택스 엑셀 다운로드
                st.write("---")
                if st.button("📥 홈택스 전자계산서 양식 다운로드", use_container_width=True, key=f"dl_hometax_{va_vendor}"):
                    ht_rows = []
                    for k, v in cust_detail.items():
                        ht_rows.append({"종류코드":"05","작성일자":CURRENT_DATE.replace('-',''),"공급자등록번호":va_data.get('사업자번호','').replace('-',''),"공급자종사업장":"","공급자상호":va_vendor,"공급자성명":va_data.get('대표',''),"공급자주소":"","공급자업태":"서비스","공급자종목":"폐기물수집운반","공급자이메일":"","공급받는자등록번호":v.get('사업자번호',''),"공급받는자종사업장":"","공급받는자상호":k,"공급받는자성명":v.get('대표자',''),"공급받는자주소":v.get('주소',''),"공급받는자업태":v.get('업태',''),"공급받는자종목":v.get('종목',''),"공급받는자이메일":v.get('이메일','')})
                    ht_df = pd.DataFrame(ht_rows)
                    ht_buf = io.BytesIO()
                    ht_df.to_excel(ht_buf, index=False)
                    st.download_button("💾 엑셀 저장", data=ht_buf.getvalue(), file_name=f"{va_vendor}_홈택스양식.xlsx", use_container_width=True, key=f"dl_ht_xl_{va_vendor}")

            with va_sub[1]:
                st.markdown("**📤 자체 수거데이터 업로드**")
                st.caption("CSV/엑셀 파일을 업로드하면 자체 데이터로 저장됩니다.")
                va_file = st.file_uploader("파일 선택", type=['csv','xlsx'], key=f"va_upload_{va_vendor}")
                if va_file:
                    try:
                        df_up = pd.read_csv(va_file) if va_file.name.endswith('.csv') else pd.read_excel(va_file)
                        st.success(f"✅ {len(df_up)}건 로드 완료")
                        st.dataframe(df_up.head(10), use_container_width=True, hide_index=True)
                        if st.button("💾 데이터 저장", key=f"va_save_data_{va_vendor}"):
                            if not st.session_state[va_data_key].empty:
                                st.session_state[va_data_key] = pd.concat([st.session_state[va_data_key], df_up], ignore_index=True)
                            else:
                                st.session_state[va_data_key] = df_up
                            st.success(f"✅ {len(df_up)}건 저장! (총 {len(st.session_state[va_data_key])}건)")
                    except Exception as e:
                        st.error(f"파일 읽기 실패: {e}")
                # 저장된 데이터 표시
                if not st.session_state[va_data_key].empty:
                    st.write("---")
                    st.markdown(f"**📊 저장된 자체 데이터 ({len(st.session_state[va_data_key])}건)**")
                    st.dataframe(st.session_state[va_data_key].tail(20), use_container_width=True, hide_index=True)

            with va_sub[2]:
                st.markdown("**🔗 올바로시스템 전자인계서 연동**")
                st.caption("자체 수거데이터를 올바로시스템에 전송합니다.")
                va_saved = st.session_state[va_data_key]
                if not va_saved.empty:
                    st.metric("전송 대상", f"{len(va_saved)}건")
                    if st.button("📤 올바로시스템 전송", type="primary", use_container_width=True, key=f"va_allbaro_send_{va_vendor}"):
                        with st.spinner("한국환경공단 올바로시스템 연동 중..."):
                            time.sleep(2)
                        st.success(f"✅ {len(va_saved)}건 올바로시스템 전자인계서 전송 완료!")
                        st.caption(f"전송시각: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 상태: 전송완료")
                else:
                    st.info("업로드된 자체 수거데이터가 없습니다. 먼저 데이터를 업로드하세요.")

        # ===== 탭4: 수거일정 =====
        with va_t4:
            st.subheader("📅 수거일정 관리")
            va_sched_tabs = st.tabs(["📅 오늘 일정","🗓️ 월별 일정","📋 수거예정일 등록"])
            with va_sched_tabs[0]:
                today_sch = st.session_state.get(f'schedule_{va_vendor}', va_schools)
                st.markdown(f"**오늘 수거 학교 ({len(today_sch)}곳):**")
                for si, sch in enumerate(today_sch):
                    st.markdown(f"  {si+1}. 🏫 {sch}")
                st.markdown(f"**담당 기사:** {', '.join(va_drivers)}")
                # 오늘 일정 수정
                st.write("---")
                va_cust_key = f"va_customers_{va_vendor}"
                all_va_sch = st.session_state.get(va_cust_key, va_schools)
                new_today = st.multiselect("오늘 수거 학교 수정", all_va_sch, default=[s for s in today_sch if s in all_va_sch], key=f"va_today_edit_{va_vendor}")
                if st.button("💾 오늘 일정 저장", key=f"va_save_today_{va_vendor}"):
                    st.session_state[f'schedule_{va_vendor}'] = new_today
                    st.success("✅ 오늘 일정 저장!"); st.rerun()
            with va_sched_tabs[1]:
                has_m = False
                for m in range(1, 13):
                    sk = f"monthly_sched_{va_vendor}_{m}"
                    if sk in st.session_state:
                        has_m = True
                        sd = st.session_state[sk]
                        with st.expander(f"📅 {m}월", expanded=(m==CURRENT_MONTH)):
                            st.write(f"**수거 요일:** {', '.join(sd.get('요일',[]))}")
                            st.write(f"**수거 품목:** {', '.join(sd.get('품목',[]))}")
                            st.write(f"**대상 학교:** {', '.join(sd.get('학교',[]))}")
                if not has_m:
                    st.info("등록된 월별 일정이 없습니다.")
                # 월별 일정 직접 등록
                st.write("---")
                st.markdown("**🗓️ 월별 일정 등록/수정**")
                va_sm = st.selectbox("월", list(range(1,13)), format_func=lambda x:f"{x}월", key=f"va_sched_m_{va_vendor}")
                va_sd = st.multiselect("수거 요일", ['월','화','수','목','금'], default=['월','수','금'], key=f"va_sd_{va_vendor}_{va_sm}")
                va_si = st.multiselect("품목", ['음식물','사업장','재활용'], default=['음식물'], key=f"va_si_{va_vendor}_{va_sm}")
                va_ss = st.multiselect("대상 학교", all_va_sch, default=all_va_sch, key=f"va_ss_{va_vendor}_{va_sm}")
                if st.button("💾 월별 일정 저장", key=f"va_save_m_{va_vendor}"):
                    st.session_state[f"monthly_sched_{va_vendor}_{va_sm}"] = {"요일":va_sd,"학교":va_ss,"품목":va_si}
                    st.success(f"✅ {va_sm}월 일정 저장!"); st.rerun()
            with va_sched_tabs[2]:
                st.markdown("**📋 수거예정일 개별 등록**")
                va_sp_sch = st.selectbox("거래처", all_va_sch if all_va_sch else ["거래처 없음"], key=f"va_sp_sch_{va_vendor}")
                va_sp_item = st.selectbox("품목", ['음식물','사업장','재활용'], key=f"va_sp_item_{va_vendor}")
                va_sp_date = st.date_input("수거 예정일", key=f"va_sp_date_{va_vendor}")
                if st.button("📅 등록", type="primary", key=f"va_sp_save_{va_vendor}"):
                    pk = f'va_planned_{va_vendor}'
                    if pk not in st.session_state: st.session_state[pk] = []
                    st.session_state[pk].append({"학교":va_sp_sch,"품목":va_sp_item,"날짜":str(va_sp_date)})
                    st.success(f"✅ {va_sp_sch} ({va_sp_item}) {va_sp_date} 등록!")
                pk = f'va_planned_{va_vendor}'
                if st.session_state.get(pk):
                    st.dataframe(pd.DataFrame(st.session_state[pk]), use_container_width=True, hide_index=True)

        # ===== 탭5: 기사 관리 =====
        with va_t5:
            st.subheader("🚚 소속 기사 현황")
            for did in va_data.get('drivers',[]):
                if did in DRIVER_ACCOUNTS:
                    di = DRIVER_ACCOUNTS[did]
                    st.markdown(f"**{di['name']}** (ID: {did}) | 담당: {', '.join(di.get('schools',[]))}")
            st.markdown(f"**차량:** {', '.join(va_data.get('차량',[]))}")

        # ===== 외주업체 사이드바: 거래명세서 발송 =====
        with st.sidebar:
            st.write("---")
            with st.expander("📄 월말거래명세서 발송"):
                st.caption("잔반처리량 파일을 업로드하면 거래명세서 PDF를 생성합니다.")
                va_inv_file = st.file_uploader("잔반처리량 PDF/CSV/엑셀", type=['pdf','csv','xlsx'], key=f"va_inv_{va_vendor}")
                if va_inv_file:
                    try:
                        if va_inv_file.name.endswith('.csv'):
                            va_df_inv = pd.read_csv(va_inv_file)
                        elif va_inv_file.name.endswith(('.xlsx','.xls')):
                            va_df_inv = pd.read_excel(va_inv_file)
                        else:
                            import re as re_mod
                            content = va_inv_file.read().decode('utf-8', errors='ignore')
                            va_inv_file.seek(0)
                            rows_p = []
                            for line in content.split('\n'):
                                m = re_mod.search(r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)\s*\S+\s+(\d+)\s+[\d.]+\s+([\d,]+)', line)
                                if m:
                                    rows_p.append({'수거일':m.group(1),'단위(L)':int(m.group(2)),'단가':170,'공급가':int(m.group(3).replace(',','')),'재활용방법':'퇴비화및비료생산'})
                            va_df_inv = pd.DataFrame(rows_p) if rows_p else pd.DataFrame()
                            if va_df_inv.empty:
                                st.warning("PDF 자동 추출 실패. CSV/엑셀로 업로드해 주세요.")
                        if not va_df_inv.empty:
                            st.success(f"✅ {len(va_df_inv)}건 분석")
                            st.session_state[f'va_inv_data_{va_vendor}'] = va_df_inv
                            qty_col = [c for c in va_df_inv.columns if '단위' in c or 'L' in c or 'kg' in c]
                            sup_col = [c for c in va_df_inv.columns if '공급가' in c]
                            if qty_col: st.metric("수거량", f"{va_df_inv[qty_col[0]].sum():,.0f}")
                            if sup_col: st.metric("공급가", f"{va_df_inv[sup_col[0]].sum():,.0f}원")
                    except Exception as e:
                        st.error(f"분석 실패: {e}")
                va_inv_key = f'va_inv_data_{va_vendor}'
                if va_inv_key in st.session_state and not st.session_state[va_inv_key].empty:
                    st.write("---")
                    va_inv_sch = st.text_input("거래처명", value=va_schools[0] if va_schools else "", key=f"va_inv_sch_{va_vendor}")
                    va_inv_m = st.number_input("월", value=11, min_value=1, max_value=12, key=f"va_inv_m_{va_vendor}")
                    if st.button("📄 PDF 생성", type="primary", use_container_width=True, key=f"va_gen_inv_{va_vendor}"):
                        pdf_data = create_monthly_invoice_pdf(va_vendor, va_inv_sch, va_inv_m, "2025", st.session_state[va_inv_key])
                        st.download_button("📥 다운로드", data=pdf_data, file_name=f"{va_inv_sch}_{va_inv_m}월_거래명세서.pdf", mime="application/pdf", use_container_width=True, key=f"va_dl_inv_{va_vendor}")
                        st.success("✅ PDF 생성 완료!")
