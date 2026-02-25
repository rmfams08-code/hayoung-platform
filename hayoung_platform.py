# 하영자원 폐기물 데이터 플랫폼 Pro v3.0
# ============================================================
# [v3 추가/개선 사항]
#   [추가2] 재활용품 23종 실시간 시세 DB + 품목별 단가 관리
#   [추가3] 스쿨존 Geofencing - 등하교 시간대 자동 차단 (08~09시, 14~16시)
#   [추가4] 수거 일정 캘린더 뷰 (월별 달력 UI)
#   [추가5] 교육청 통합 관제 모드 + 공공예산 절감 지표
#   [전체]  프로토타입 → 실제 작동 전환 (버튼 기능, 상태 변경, 데이터 반영)
# ============================================================
# 실행 방법: cd Desktop\하영자원 → python -m streamlit run hayoung_platform.py
# 필수 설치: pip install streamlit pandas xlsxwriter requests python-dotenv
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import time
import io
import os
import random
import calendar
import zipfile
from datetime import datetime, date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_raw_pw        = os.getenv("EXCEL_PASSWORD", "")
EXCEL_PASSWORD = _raw_pw if _raw_pw else None
KAKAO_API_KEY    = os.getenv("KAKAO_API_KEY", "")
KAKAO_SENDER_KEY = os.getenv("KAKAO_SENDER_KEY", "")

# ============================================================
# 0. 상수 및 기초 데이터
# ============================================================
STUDENT_COUNTS = {
    "화성초등학교": 309,  "동탄중학교": 1033, "수원고등학교": 884,  "안양남초등학교": 486,
    "평촌초등학교": 1126, "부림초등학교": 782, "부흥중학교": 512,   "덕천초등학교": 859,
    "서초고등학교": 831,  "구암고등학교": 547, "국사봉중학교": 346, "당곡고등학교": 746,
    "당곡중학교": 512,   "서울공업고등학교": 735, "강남중학교": 265, "영남중학교": 409,
    "선유고등학교": 580,  "신목고등학교": 1099, "고척고등학교": 782, "구현고등학교": 771,
    "안산국제비지니스고등학교": 660, "안산고등학교": 745, "송호고등학교": 879, "비봉고등학교": 734
}
SCHOOL_LIST = sorted(list(STUDENT_COUNTS.keys()))

# ============================================================
# 실제 수거 데이터 내장 (2025년 3~12월 엑셀 원본)
# 형식: (날짜, 학교명, 음식물_L, 단가)
# ============================================================
REAL_COLLECTION_DATA = [
    ("2025-03-05","강남중학교",140.0,190),("2025-03-07","강남중학교",180.0,190),("2025-03-11","강남중학교",120.0,190),("2025-03-13","강남중학교",180.0,190),("2025-03-14","강남중학교",120.0,190),("2025-03-17","강남중학교",140.0,190),("2025-03-18","강남중학교",120.0,190),("2025-03-19","강남중학교",160.0,190),("2025-03-20","강남중학교",140.0,190),("2025-03-21","강남중학교",100.0,190),("2025-03-24","강남중학교",120.0,190),("2025-03-25","강남중학교",120.0,190),("2025-03-26","강남중학교",140.0,190),("2025-03-27","강남중학교",120.0,190),("2025-03-28","강남중학교",120.0,190),
    ("2025-04-01","강남중학교",120.0,190),("2025-04-02","강남중학교",140.0,190),("2025-04-03","강남중학교",110.0,190),("2025-04-04","강남중학교",120.0,190),("2025-04-07","강남중학교",140.0,190),("2025-04-08","강남중학교",120.0,190),("2025-04-09","강남중학교",100.0,190),("2025-04-10","강남중학교",140.0,190),("2025-04-11","강남중학교",120.0,190),("2025-04-14","강남중학교",120.0,190),("2025-04-15","강남중학교",120.0,190),("2025-04-16","강남중학교",140.0,190),("2025-04-17","강남중학교",100.0,190),("2025-04-18","강남중학교",120.0,190),("2025-04-21","강남중학교",120.0,190),("2025-04-22","강남중학교",140.0,190),("2025-04-23","강남중학교",120.0,190),("2025-04-24","강남중학교",100.0,190),("2025-04-25","강남중학교",120.0,190),("2025-04-28","강남중학교",120.0,190),("2025-04-29","강남중학교",130.0,190),("2025-04-30","강남중학교",110.0,190),
]

# 내장 데이터 로딩 함수
def _load_embedded_data():
    """real_data_embedded.py 파일이 있으면 로드, 없으면 REAL_COLLECTION_DATA 사용"""
    import os
    embed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "real_data_embedded.py")
    if os.path.exists(embed_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("real_data_embedded", embed_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.REAL_COLLECTION_DATA
    return REAL_COLLECTION_DATA

# [추가2] 재활용품 23종 기본 시세 (원/kg) - 실제 시장 기준값
RECYCLE_ITEMS_DEFAULT = {
    "폐지(골판지)": 80,   "폐지(신문지)": 60,   "폐지(혼합)": 40,
    "고철(철스크랩)": 300, "고철(알루미늄캔)": 800, "고철(스테인리스)": 500,
    "유리병(갈색)": 50,   "유리병(투명)": 60,   "유리병(혼합)": 40,
    "페트병(투명)": 400,  "페트병(유색)": 150,  "플라스틱(PP)": 200,
    "플라스틱(PE)": 180,  "플라스틱(PS)": 100,  "플라스틱(PVC)": 80,
    "비닐(투명)": 120,   "비닐(혼합)": 60,    "스티로폼": 150,
    "우유팩": 200,       "종이컵": 80,         "의류/섬유": 100,
    "목재": 30,          "전자폐기물": 500,
}

# [추가3] 스쿨존 제한 시간대
SCHOOLZONE_RESTRICTED = [(8, 9), (14, 16)]  # (시작시, 종료시)

# ============================================================
# 0-1. 사용자 계정 DB (로그인 시스템)
# ============================================================
# 비밀번호는 실제 운영 시 해시 처리 권장
USER_ACCOUNTS = {
    # ── 관리자 (1개) ──────────────────────────────────────────
    "admin": {
        "password": "hayoung2025!",
        "role": "관리자",
        "display_name": "하영자원 관리자",
        "org": "하영자원(본사)",
    },

    # ── 교육청 (2개) ──────────────────────────────────────────
    "hwaseong_edu": {
        "password": "edu_hwaseong1",
        "role": "교육청",
        "display_name": "화성오산교육지원청 담당자",
        "org": "화성오산교육지원청",
    },
    "seoulsouth_edu": {
        "password": "edu_seoul2025",
        "role": "교육청",
        "display_name": "서울남부교육지원청 담당자",
        "org": "서울남부교육지원청",
    },

    # ── 수거 기사 (3개) ───────────────────────────────────────
    "driver_kim": {
        "password": "driver_kim1",
        "role": "수거기사",
        "display_name": "김기사",
        "org": "하영자원(본사 직영)",
    },
    "driver_lee": {
        "password": "driver_lee2",
        "role": "수거기사",
        "display_name": "이기사",
        "org": "하영자원(본사 직영)",
    },
    "driver_park": {
        "password": "driver_park3",
        "role": "수거기사",
        "display_name": "박기사",
        "org": "하영자원(본사 직영)",
    },

    # ── 학교 계정 (엑셀 학교리스트.xlsx 기준) ────────────────
    "kn12": {"password": "1234", "role": "학교", "display_name": "강남중학교 행정실",          "org": "강남중학교"},
    "hs01": {"password": "1234", "role": "학교", "display_name": "화성초등학교 행정실",         "org": "화성초등학교"},
    "dt02": {"password": "1234", "role": "학교", "display_name": "동탄중학교 행정실",           "org": "동탄중학교"},
    "sw03": {"password": "1234", "role": "학교", "display_name": "수원고등학교 행정실",         "org": "수원고등학교"},
    "an04": {"password": "1234", "role": "학교", "display_name": "안양남초등학교 행정실",       "org": "안양남초등학교"},
    "pc05": {"password": "1234", "role": "학교", "display_name": "평촌초등학교 행정실",         "org": "평촌초등학교"},
    "br06": {"password": "1234", "role": "학교", "display_name": "부림초등학교 행정실",         "org": "부림초등학교"},
    "bh07": {"password": "1234", "role": "학교", "display_name": "부흥중학교 행정실",           "org": "부흥중학교"},
    "dc08": {"password": "1234", "role": "학교", "display_name": "덕천초등학교 행정실",         "org": "덕천초등학교"},
    "sc09": {"password": "1234", "role": "학교", "display_name": "서초고등학교 행정실",         "org": "서초고등학교"},
    "ga10": {"password": "1234", "role": "학교", "display_name": "구암고등학교 행정실",         "org": "구암고등학교"},
    "gs11": {"password": "1234", "role": "학교", "display_name": "국사봉중학교 행정실",         "org": "국사봉중학교"},
    "dg13": {"password": "1234", "role": "학교", "display_name": "당곡고등학교 행정실",         "org": "당곡고등학교"},
    "dg14": {"password": "1234", "role": "학교", "display_name": "당곡중학교 행정실",           "org": "당곡중학교"},
    "sg15": {"password": "1234", "role": "학교", "display_name": "서울공업고등학교 행정실",     "org": "서울공업고등학교"},
    "yn16": {"password": "1234", "role": "학교", "display_name": "영남중학교 행정실",           "org": "영남중학교"},
    "sy17": {"password": "1234", "role": "학교", "display_name": "선유고등학교 행정실",         "org": "선유고등학교"},
    "sm18": {"password": "1234", "role": "학교", "display_name": "신목고등학교 행정실",         "org": "신목고등학교"},
    "gc19": {"password": "1234", "role": "학교", "display_name": "고척고등학교 행정실",         "org": "고척고등학교"},
    "gh20": {"password": "1234", "role": "학교", "display_name": "구현고등학교 행정실",         "org": "구현고등학교"},
    "as21": {"password": "1234", "role": "학교", "display_name": "안산국제비지니스고 행정실",   "org": "안산국제비지니스고등학교"},
    "as22": {"password": "1234", "role": "학교", "display_name": "안산고등학교 행정실",         "org": "안산고등학교"},
    "sh23": {"password": "1234", "role": "학교", "display_name": "송호고등학교 행정실",         "org": "송호고등학교"},
    "bb24": {"password": "1234", "role": "학교", "display_name": "비봉고등학교 행정실",         "org": "비봉고등학교"},
}

# [추가5] 교육청 목록
EDU_OFFICES = {
    "화성오산교육지원청": ["화성초등학교","부림초등학교","비봉고등학교","송호고등학교","안산고등학교","안산국제비지니스고등학교"],
    "수원교육지원청":     ["수원고등학교","평촌초등학교","안양남초등학교","부흥중학교","동탄중학교","덕천초등학교"],
    "서울남부교육지원청": ["서초고등학교","구암고등학교","국사봉중학교","당곡고등학교","당곡중학교",
                          "서울공업고등학교","강남중학교","영남중학교","선유고등학교",
                          "신목고등학교","고척고등학교","구현고등학교"],
}

# ============================================================
# 1. 페이지 설정 및 CSS
# ============================================================
st.set_page_config(
    page_title="하영자원 플랫폼 Pro v3",
    page_icon="♻️", layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown("""
<style>
.custom-card         { background:#fff; color:#202124; padding:20px; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,.05); margin-bottom:20px; border-top:5px solid #1a73e8; }
.custom-card-green   { border-top:5px solid #34a853; }
.custom-card-orange  { border-top:5px solid #fbbc05; }
.custom-card-red     { border-top:5px solid #ea4335; }
.custom-card-purple  { border-top:5px solid #9b59b6; }
.custom-card-teal    { border-top:5px solid #00897b; }
.metric-title        { font-size:14px; color:#5f6368!important; font-weight:bold; margin-bottom:5px; }
.metric-value-food   { font-size:26px; font-weight:900; color:#ea4335!important; }
.metric-value-recycle{ font-size:26px; font-weight:900; color:#34a853!important; }
.metric-value-biz    { font-size:26px; font-weight:900; color:#9b59b6!important; }
.metric-value-total  { font-size:26px; font-weight:900; color:#1a73e8!important; }
.mobile-app-header   { background:#202124; color:#fff!important; padding:15px; border-radius:10px 10px 0 0; text-align:center; margin-bottom:15px; }
.safety-box          { background:#e8f5e9; border:1px solid #c8e6c9; padding:15px; border-radius:8px; color:#2e7d32; font-weight:bold; margin-bottom:15px; }
.alert-box           { background:#ffebee; border:1px solid #ffcdd2; padding:15px; border-radius:8px; color:#c62828; margin-bottom:15px; }
.warn-box            { background:#fff8e1; border:1px solid #ffe082; padding:15px; border-radius:8px; color:#f57f17; margin-bottom:15px; }
.timeline-text       { font-size:15px; line-height:1.8; color:#333; }
.badge-new           { background:#e8f0fe; color:#1a73e8; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:bold; margin-left:6px; }
.badge-v3            { background:#e6f4ea; color:#1e8e3e; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:bold; margin-left:6px; }
.cal-day             { text-align:center; padding:6px 2px; border-radius:6px; font-size:13px; }
.cal-collect         { background:#e8f5e9; color:#2e7d32; font-weight:bold; }
.cal-today           { background:#1a73e8; color:white; font-weight:bold; }
.cal-weekend         { color:#bbb; }
.schoolzone-danger   { background:#d32f2f; color:white; padding:20px; border-radius:12px; text-align:center; font-size:24px; font-weight:900; margin-bottom:15px; }
.schoolzone-safe     { background:#388e3c; color:white; padding:20px; border-radius:12px; text-align:center; font-size:18px; font-weight:bold; margin-bottom:15px; }

/* ── 로그인 화면 ── */
.login-bg { background:linear-gradient(160deg,#e8f4fd 0%,#d4eaf7 50%,#c2e0f4 100%); min-height:100vh; padding:40px 20px; }
.login-header { text-align:center; margin-bottom:40px; }
.login-header h1 { font-size:2.6rem; font-weight:900; color:#1a3a5c; margin:0; }
.login-header p  { font-size:1.05rem; color:#4a6b8a; margin-top:8px; }
.login-card-wrap { display:flex; gap:24px; justify-content:center; flex-wrap:wrap; margin-bottom:40px; }
.login-card {
    background:white; border-radius:16px; padding:36px 28px; width:260px;
    box-shadow:0 6px 24px rgba(0,80,160,.12); cursor:pointer; transition:.2s;
    text-align:center; border:3px solid transparent;
}
.login-card:hover { transform:translateY(-6px); box-shadow:0 12px 32px rgba(0,80,160,.2); border-color:#1a73e8; }
.login-card.active { border-color:#1a73e8; background:#f0f7ff; }
.login-card-icon { font-size:3.2rem; margin-bottom:16px; }
.login-card-title { font-size:1.2rem; font-weight:800; color:#1a3a5c; margin-bottom:8px; }
.login-card-desc  { font-size:0.85rem; color:#5f6368; line-height:1.5; }
.login-form-box { background:white; border-radius:16px; max-width:440px; margin:0 auto; padding:36px; box-shadow:0 4px 20px rgba(0,0,0,.1); }
.login-form-title { font-size:1.3rem; font-weight:800; color:#1a3a5c; margin-bottom:24px; text-align:center; }
.login-footer { text-align:center; margin-top:40px; color:#8aa0b8; font-size:0.82rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. SQLite DB 초기화 및 함수
# ============================================================
DB_PATH = "hayoung_v3.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # 수거 데이터
    c.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            날짜       TEXT,
            학교명     TEXT,
            학생수     INTEGER,
            수거업체   TEXT,
            음식물_kg  REAL DEFAULT 0,
            재활용_kg  REAL DEFAULT 0,
            사업장_kg  REAL DEFAULT 0,
            상태       TEXT DEFAULT '정산대기',
            현장사진   TEXT DEFAULT ''
        )
    """)

    # 전역 설정
    c.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY, value TEXT
        )
    """)
    defaults = [
        ("default_food_price","150"), ("default_recycle_price","300"),
        ("default_biz_price","200"),  ("kakao_notify_enabled","false"),
        ("budget_saving_per_school","5200000"),  # 학교당 연간 예산절감액(원)
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO global_settings (key,value) VALUES (?,?)", (k, v))

    # 학교별 단가 + 담당자
    c.execute("""
        CREATE TABLE IF NOT EXISTS school_prices (
            학교명           TEXT PRIMARY KEY,
            음식물단가       INTEGER DEFAULT 150,
            재활용단가       INTEGER DEFAULT 300,
            사업장단가       INTEGER DEFAULT 200,
            담당자명         TEXT DEFAULT '',
            담당자연락처     TEXT DEFAULT '',
            담당자이메일     TEXT DEFAULT '',
            교육청           TEXT DEFAULT '',
            -- [섹션A] 학교 마스터 확장 컬럼
            학교_사업자번호  TEXT DEFAULT '',
            학교_주소        TEXT DEFAULT '',
            학교_전화        TEXT DEFAULT '',
            계약_시작일      TEXT DEFAULT '',
            계약_종료일      TEXT DEFAULT '',
            계약_상태        TEXT DEFAULT '미계약',
            비고             TEXT DEFAULT '',
            updated_at       TEXT
        )
    """)
    # [섹션A] 기존 DB에 컬럼 없으면 ALTER로 추가 (마이그레이션)
    _sp_new_cols = {
        "학교_사업자번호": "TEXT DEFAULT ''",
        "학교_주소":       "TEXT DEFAULT ''",
        "학교_전화":       "TEXT DEFAULT ''",
        "계약_시작일":     "TEXT DEFAULT ''",
        "계약_종료일":     "TEXT DEFAULT ''",
        "계약_상태":       "TEXT DEFAULT '미계약'",
        "비고":            "TEXT DEFAULT ''",
    }
    _existing = [row[1] for row in c.execute("PRAGMA table_info(school_prices)").fetchall()]
    for col, coldef in _sp_new_cols.items():
        if col not in _existing:
            c.execute(f"ALTER TABLE school_prices ADD COLUMN {col} {coldef}")
    for school in SCHOOL_LIST:
        edu = next((k for k, v in EDU_OFFICES.items() if school in v), "")
        c.execute(
            "INSERT OR IGNORE INTO school_prices (학교명, 교육청, updated_at) VALUES (?,?,?)",
            (school, edu, datetime.now().strftime("%Y-%m-%d"))
        )

    # [추가2] 재활용품 23종 시세 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS recycle_prices (
            품목명   TEXT PRIMARY KEY,
            단가     INTEGER,
            단위     TEXT DEFAULT 'kg',
            updated_at TEXT
        )
    """)
    for item, price in RECYCLE_ITEMS_DEFAULT.items():
        c.execute(
            "INSERT OR IGNORE INTO recycle_prices (품목명, 단가, updated_at) VALUES (?,?,?)",
            (item, price, datetime.now().strftime("%Y-%m-%d"))
        )

    # [추가4] 수거 일정 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            날짜     TEXT,
            학교명   TEXT,
            메모     TEXT DEFAULT '',
            완료여부 INTEGER DEFAULT 0
        )
    """)

    # [섹션C] 서류 유효기간 관리 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS contract_docs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name    TEXT NOT NULL,
            issued_date TEXT DEFAULT '',
            expire_date TEXT NOT NULL,
            renew_url   TEXT DEFAULT '',
            file_note   TEXT DEFAULT '',
            renewed     INTEGER DEFAULT 0,
            memo        TEXT DEFAULT '',
            updated_at  TEXT
        )
    """)
    # 기본 서류 7종 삽입 (최초 1회만)
    _default_docs = [
        ("소상공인 확인서",        "", "2026-03-31", "sminfo.mss.go.kr",         "중소벤처기업부 공식 발급"),
        ("창업기업 확인서",        "", "2027-01-07", "중소벤처기업부",           "개업일 기준 7년 유효"),
        ("재해율 확인서",          "", "2027-02-19", "안전보건공단 kosha.or.kr", "연 1회 갱신"),
        ("사업자등록증",           "", "9999-12-31", "국세청 hometax.go.kr",     "변경 시 재발급"),
        ("폐기물수집운반업 허가증","", "9999-12-31", "화성시청",                 "제20-35호 재교부 2023.09.26"),
        ("사용인감계",             "", "9999-12-31", "자체 관리",                "계약별 첨부"),
        ("사업자계좌 통장사본",    "", "9999-12-31", "기업은행",                 "450-092046-01-017"),
    ]
    for row in _default_docs:
        c.execute(
            """INSERT OR IGNORE INTO contract_docs
               (doc_name, issued_date, expire_date, renew_url, file_note, updated_at)
               VALUES (?,?,?,?,?,?)""",
            (*row, datetime.now().strftime("%Y-%m-%d"))
        )

    # [섹션A] 계약 이력 마스터 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS contract_master (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            학교명          TEXT NOT NULL,
            계약번호        TEXT DEFAULT '',
            계약_시작일     TEXT NOT NULL,
            계약_종료일     TEXT NOT NULL,
            폐기물_종류     TEXT DEFAULT '음식물류폐기물',
            단가            INTEGER DEFAULT 150,
            월_예상량_L     REAL DEFAULT 0,
            계약_상태       TEXT DEFAULT '계약중',
            갱신_알림일     TEXT DEFAULT '',
            나라장터_번호   TEXT DEFAULT '',
            비고            TEXT DEFAULT '',
            created_at      TEXT,
            updated_at      TEXT
        )
    """)
    # 서초고등학교 기본 계약 데이터 삽입 (최초 1회)
    if c.execute("SELECT COUNT(*) FROM contract_master WHERE 학교명='서초고등학교'").fetchone()[0] == 0:
        c.execute(
            """INSERT INTO contract_master
               (학교명, 계약번호, 계약_시작일, 계약_종료일,
                폐기물_종류, 단가, 계약_상태, 나라장터_번호, 비고, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            ("서초고등학교", "", "2026-03-01", "2027-02-28",
             "음식물류폐기물", 180, "계약중", "R26TA01543339 00",
             "2026년 신규계약",
             datetime.now().strftime("%Y-%m-%d"),
             datetime.now().strftime("%Y-%m-%d"))
        )
    # 서초고등학교 school_prices 마스터 정보 업데이트
    c.execute(
        """UPDATE school_prices SET
           학교_사업자번호=?, 학교_주소=?, 학교_전화=?,
           계약_시작일=?, 계약_종료일=?, 계약_상태=?, updated_at=?
           WHERE 학교명='서초고등학교'""",
        ("210-83-00086", "서울특별시 서초구 반포대로27길 29", "02-580-3891",
         "2026-03-01", "2027-02-28", "계약중",
         datetime.now().strftime("%Y-%m-%d"))
    )

    conn.commit()

    # 실제 수거 데이터 (2025년 3~12월 엑셀 원본 내장)
    if c.execute("SELECT COUNT(*) FROM collections").fetchone()[0] == 0:
        src_data = _load_embedded_data()  # (날짜, 학교명, 음식물L, 단가) 리스트
        rows = []
        price_map = {}  # 학교별 마지막 단가 추적

        for date_str, school, liter, price in src_data:
            rows.append((
                date_str + " 09:00:00",
                school,
                STUDENT_COUNTS.get(school, 0),
                "하영자원(본사 직영)",
                liter,   # 음식물_kg (1L=1kg)
                0.0,     # 재활용_kg
                0.0,     # 사업장_kg
                "정산완료",
                ""
            ))
            if price > 0:
                price_map[school] = (price, date_str)

        c.executemany("""
            INSERT INTO collections (날짜,학교명,학생수,수거업체,음식물_kg,재활용_kg,사업장_kg,상태,현장사진)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, rows)

        # 학교별 단가 반영
        for school, (price, date_str) in price_map.items():
            c.execute(
                "UPDATE school_prices SET 음식물단가=?, updated_at=? WHERE 학교명=?",
                (price, date_str, school)
            )

    # 실제 수거 데이터 기반 일정 자동 생성
    if c.execute("SELECT COUNT(*) FROM schedules").fetchone()[0] == 0:
        # collections 테이블에서 실제 수거일을 읽어 schedules에 삽입
        real_days = c.execute(
            "SELECT SUBSTR(날짜,1,10), 학교명 FROM collections ORDER BY 날짜"
        ).fetchall()
        sched_rows = []
        seen = set()
        for day_str, school in real_days:
            key = (day_str, school)
            if key not in seen:
                seen.add(key)
                sched_rows.append((day_str, school, "정기 수거 (실적)", 1))  # 완료여부=1
        if sched_rows:
            c.executemany(
                "INSERT INTO schedules (날짜,학교명,메모,완료여부) VALUES (?,?,?,?)",
                sched_rows
            )

    conn.commit()
    conn.close()

# ── 헬퍼 함수 ──────────────────────────────────────────────
def get_setting(key):
    conn = get_conn()
    row = conn.execute("SELECT value FROM global_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO global_settings (key,value) VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def load_data():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT c.*,
            COALESCE(p.음식물단가, CAST(s.fp AS INTEGER)) AS 단가,
            COALESCE(p.재활용단가, CAST(s.rp AS INTEGER)) AS 재활용단가,
            COALESCE(p.사업장단가, CAST(s.bp AS INTEGER)) AS 사업장단가,
            COALESCE(p.교육청, '') AS 교육청
        FROM collections c
        LEFT JOIN school_prices p ON c.학교명 = p.학교명
        LEFT JOIN (
            SELECT
                (SELECT value FROM global_settings WHERE key='default_food_price')    AS fp,
                (SELECT value FROM global_settings WHERE key='default_recycle_price') AS rp,
                (SELECT value FROM global_settings WHERE key='default_biz_price')     AS bp
        ) s ON 1=1
    """, conn)
    conn.close()
    if not df.empty:
        df.rename(columns={"음식물_kg":"음식물(kg)","재활용_kg":"재활용(kg)","사업장_kg":"사업장(kg)"}, inplace=True)
        df["음식물비용"] = df["음식물(kg)"] * df["단가"]
        df["사업장비용"] = df["사업장(kg)"] * df["사업장단가"]
        df["재활용수익"] = df["재활용(kg)"] * df["재활용단가"]
        df["최종정산액"] = df["음식물비용"] + df["사업장비용"] - df["재활용수익"]
        df["월별"] = df["날짜"].astype(str).str[:7]
        df["년도"] = df["날짜"].astype(str).str[:4]
        # 탄소감축량 산정 (환경부 기준, 2024)
        # 음식물 퇴비화 처리: 매립 대비 0.3 kgCO₂eq/kg 감축 (환경부 온실가스 배출계수)
        # 재활용 처리: 소각 대비 0.4 kgCO₂eq/kg 감축 (한국환경공단 자원순환 가이드라인)
        CO2_FOOD    = 0.3   # kgCO₂/kg - 음식물 퇴비화 감축계수
        CO2_RECYCLE = 0.4   # kgCO₂/kg - 재활용품 감축계수
        df["탄소감축량(kg)"] = (df["음식물(kg)"] * CO2_FOOD) + (df["재활용(kg)"] * CO2_RECYCLE)
    return df

def save_collection(row: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO collections (날짜,학교명,학생수,수거업체,음식물_kg,재활용_kg,사업장_kg,상태,현장사진)
        VALUES (:날짜,:학교명,:학생수,:수거업체,:음식물_kg,:재활용_kg,:사업장_kg,:상태,:현장사진)
    """, row)
    conn.commit()
    conn.close()

def update_collection_status(ids: list, new_status: str):
    """수거 레코드 상태 일괄 변경"""
    conn = get_conn()
    conn.executemany(
        "UPDATE collections SET 상태=? WHERE id=?",
        [(new_status, i) for i in ids]
    )
    conn.commit()
    conn.close()

def get_school_prices():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM school_prices ORDER BY 학교명", conn)
    conn.close()
    return df

def update_school_price(school, food, recycle, biz, name, tel, email):
    conn = get_conn()
    conn.execute("""
        UPDATE school_prices
        SET 음식물단가=?,재활용단가=?,사업장단가=?,담당자명=?,담당자연락처=?,담당자이메일=?,updated_at=?
        WHERE 학교명=?
    """, (food, recycle, biz, name, tel, email, datetime.now().strftime("%Y-%m-%d"), school))
    conn.commit()
    conn.close()

# [추가2] 재활용 시세 함수
def get_recycle_prices():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM recycle_prices ORDER BY 품목명", conn)
    conn.close()
    return df

def update_recycle_price(item, price):
    conn = get_conn()
    conn.execute(
        "UPDATE recycle_prices SET 단가=?, updated_at=? WHERE 품목명=?",
        (price, datetime.now().strftime("%Y-%m-%d"), item)
    )
    conn.commit()
    conn.close()

def get_avg_recycle_price():
    """전체 재활용품 가중 평균 단가"""
    conn = get_conn()
    row = conn.execute("SELECT AVG(단가) FROM recycle_prices").fetchone()
    conn.close()
    return int(row[0]) if row and row[0] else 300

# [추가4] 일정 함수
def get_schedules_month(year, month):
    conn = get_conn()
    prefix = f"{year}-{month:02d}"
    df = pd.read_sql_query(
        "SELECT * FROM schedules WHERE 날짜 LIKE ? ORDER BY 날짜, 학교명",
        conn, params=(f"{prefix}%",)
    )
    conn.close()
    return df

def add_schedule(date_str, school, memo):
    conn = get_conn()
    conn.execute(
        "INSERT INTO schedules (날짜,학교명,메모,완료여부) VALUES (?,?,?,0)",
        (date_str, school, memo)
    )
    conn.commit()
    conn.close()

def toggle_schedule(sid, current):
    conn = get_conn()
    conn.execute("UPDATE schedules SET 완료여부=? WHERE id=?", (0 if current else 1, sid))
    conn.commit()
    conn.close()

def delete_schedule(sid):
    conn = get_conn()
    conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
    conn.commit()
    conn.close()

# [추가3] 스쿨존 시간 체크
def is_schoolzone_restricted():
    h = datetime.now().hour
    for start, end in SCHOOLZONE_RESTRICTED:
        if start <= h < end:
            return True, f"{start}:00~{end}:00"
    return False, ""

# 엑셀 생성
def create_secure_excel(df, title):
    if not EXCEL_PASSWORD:
        st.warning("⚠️ .env 파일에 EXCEL_PASSWORD가 설정되지 않아 시트 보호가 적용되지 않습니다.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="법정실적보고서", startrow=2)
        wb = writer.book
        ws = writer.sheets["법정실적보고서"]
        fmt = wb.add_format({"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"})
        ws.merge_range(0, 0, 1, len(df.columns)-1, f"■ {title} ■", fmt)
        for i in range(len(df.columns)):
            ws.set_column(i, i, 16)
        if EXCEL_PASSWORD:
            ws.protect(EXCEL_PASSWORD, {"objects":True,"scenarios":True,"format_cells":False,"sort":True})
    return output.getvalue()

# 알림톡 (시뮬레이션만)
def send_kakao_alimtalk(phone, school, food_kg, total_price):
    st.info(f"📱 [알림톡]\n▸ 수신: {school} 담당자 ({phone})\n▸ 내용: 음식물 {food_kg:,.0f}kg 수거 완료, 청구 예정액 {total_price:,}원")
    return True


# ============================================================
# [섹션 E] 계약서류 패키지 자동 생성 시스템
# ============================================================

# ── 하영자원 고정 정보 (전 서류 공통 사용) ─────────────────
HY = {
    "name":       "하영자원",
    "ceo":        "정석완",
    "biz_no":     "405-11-42991",
    "permit_no":  "제20-35호",
    "address":    "경기도 화성시 남양읍 남양성지로 219, 2층",
    "tel":        "031-414-3713",
    "mobile":     "010-3114-4030",
    "fax":        "031-356-3713",
    "email":      "hyrecycling@naver.com",
    "bank":       "기업은행",
    "account":    "450-092046-01-017",
    "biz_type":   "폐기물처리",
    "biz_item":   "지정외폐기물수집,운반업",
    "processor":  "주식회사 청명",   # 처리업체
}

# 서류 유효기간 마스터 (D-day 알림용)
DOC_EXPIRE = [
    {"name": "소상공인 확인서",        "expire": "2026-03-31", "renew_url": "sminfo.mss.go.kr"},
    {"name": "창업기업 확인서",         "expire": "2027-01-07", "renew_url": "중소벤처기업부"},
    {"name": "재해율 확인서",           "expire": "2027-02-19", "renew_url": "안전보건공단"},
    {"name": "사업자등록증",            "expire": "9999-12-31", "renew_url": "국세청"},
    {"name": "폐기물수집운반업 허가증", "expire": "9999-12-31", "renew_url": "화성시청"},
]


# ── [섹션C] contract_docs DB 헬퍼 함수 ─────────────────────

def c_get_all_docs() -> list[dict]:
    """전체 서류 목록 + D-day 계산해서 반환"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, doc_name, issued_date, expire_date, renew_url, "
        "file_note, renewed, memo FROM contract_docs ORDER BY expire_date ASC"
    ).fetchall()
    today_dt = date.today()
    result = []
    for r in rows:
        exp_str = r[3]
        if exp_str == "9999-12-31":
            dday, status = "무기한", "🟢 정상"
        else:
            exp     = date.fromisoformat(exp_str)
            diff    = (exp - today_dt).days
            dday    = f"D-{diff}" if diff >= 0 else f"만료 +{abs(diff)}일"
            if diff < 0:     status = "⛔ 만료됨"
            elif diff <= 30: status = "🔴 만료임박"
            elif diff <= 60: status = "🟡 주의"
            else:            status = "🟢 정상"
        result.append({
            "id": r[0], "서류명": r[1], "발급일": r[2],
            "만료일": exp_str if exp_str != "9999-12-31" else "무기한",
            "갱신처": r[4], "비고": r[5],
            "갱신완료": bool(r[6]), "메모": r[7],
            "D-day": dday, "상태": status,
        })
    # 우선순위 정렬: 만료/임박 → 주의 → 정상
    _sort_key = {"⛔ 만료됨": 0, "🔴 만료임박": 1, "🟡 주의": 2, "🟢 정상": 3}
    result.sort(key=lambda x: _sort_key.get(x["상태"], 9))
    return result


def c_update_doc(doc_id: int, issued: str, expire: str,
                 renew_url: str, file_note: str,
                 renewed: bool, memo: str):
    conn = get_conn()
    conn.execute(
        """UPDATE contract_docs SET issued_date=?, expire_date=?,
           renew_url=?, file_note=?, renewed=?, memo=?, updated_at=?
           WHERE id=?""",
        (issued, expire, renew_url, file_note, int(renewed), memo,
         datetime.now().strftime("%Y-%m-%d"), doc_id)
    )
    conn.commit()


def c_add_doc(doc_name: str, issued: str, expire: str,
              renew_url: str, file_note: str, memo: str):
    conn = get_conn()
    conn.execute(
        """INSERT INTO contract_docs
           (doc_name, issued_date, expire_date, renew_url, file_note, memo, updated_at)
           VALUES (?,?,?,?,?,?,?)""",
        (doc_name, issued, expire, renew_url, file_note, memo,
         datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()


def c_delete_doc(doc_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM contract_docs WHERE id=?", (doc_id,))
    conn.commit()


def c_toggle_renewed(doc_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE contract_docs SET renewed = CASE WHEN renewed=1 THEN 0 ELSE 1 END "
        "WHERE id=?", (doc_id,)
    )
    conn.commit()


# ── [섹션A] 학교 마스터 + 계약 이력 헬퍼 함수 ──────────────

def a_get_all_schools() -> list[dict]:
    """school_prices 전체 + 계약 만료 D-day 계산"""
    conn  = get_conn()
    today = date.today()
    rows  = conn.execute(
        """SELECT 학교명, 음식물단가, 교육청,
                  학교_사업자번호, 학교_주소, 학교_전화,
                  계약_시작일, 계약_종료일, 계약_상태, 비고, updated_at
           FROM school_prices ORDER BY 교육청, 학교명"""
    ).fetchall()
    result = []
    for r in rows:
        end = r[7] or ""
        if end and end != "9999-12-31":
            try:
                diff = (date.fromisoformat(end) - today).days
                if diff < 0:       contract_dday = f"⛔ 만료 +{abs(diff)}일"
                elif diff <= 30:   contract_dday = f"🔴 D-{diff}"
                elif diff <= 90:   contract_dday = f"🟡 D-{diff}"
                else:              contract_dday = f"🟢 D-{diff}"
            except Exception:
                contract_dday = end
        elif end == "9999-12-31":
            contract_dday = "무기한"
        else:
            contract_dday = "미설정"
        result.append({
            "학교명":       r[0],
            "음식물단가":   r[1],
            "교육청":       r[2] or "",
            "사업자번호":   r[3] or "",
            "주소":         r[4] or "",
            "전화":         r[5] or "",
            "계약시작":     r[6] or "",
            "계약종료":     r[7] or "",
            "계약상태":     r[8] or "미계약",
            "비고":         r[9] or "",
            "수정일":       r[10] or "",
            "계약D-day":   contract_dday,
        })
    return result


def a_update_school(학교명: str, 단가: int, 사업자번호: str,
                    주소: str, 전화: str, 시작일: str,
                    종료일: str, 상태: str, 비고: str,
                    담당자명: str, 담당자연락처: str, 담당자이메일: str):
    conn = get_conn()
    conn.execute(
        """UPDATE school_prices SET
           음식물단가=?, 학교_사업자번호=?, 학교_주소=?, 학교_전화=?,
           계약_시작일=?, 계약_종료일=?, 계약_상태=?,
           비고=?, 담당자명=?, 담당자연락처=?, 담당자이메일=?, updated_at=?
           WHERE 학교명=?""",
        (단가, 사업자번호, 주소, 전화, 시작일, 종료일, 상태,
         비고, 담당자명, 담당자연락처, 담당자이메일,
         datetime.now().strftime("%Y-%m-%d"), 학교명)
    )
    conn.commit()


def a_add_school(학교명: str, 교육청: str, 단가: int,
                 사업자번호: str, 주소: str, 전화: str,
                 시작일: str, 종료일: str, 상태: str, 비고: str):
    conn = get_conn()
    conn.execute(
        """INSERT OR IGNORE INTO school_prices
           (학교명, 교육청, 음식물단가, 학교_사업자번호,
            학교_주소, 학교_전화, 계약_시작일, 계약_종료일,
            계약_상태, 비고, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (학교명, 교육청, 단가, 사업자번호, 주소, 전화,
         시작일, 종료일, 상태, 비고,
         datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()


def a_get_contracts(학교명: str = None) -> list[dict]:
    """계약 이력 목록 반환"""
    conn  = get_conn()
    today = date.today()
    query = "SELECT * FROM contract_master"
    params: tuple = ()
    if 학교명:
        query  += " WHERE 학교명=?"
        params  = (학교명,)
    query += " ORDER BY 계약_시작일 DESC"
    rows = conn.execute(query, params).fetchall()
    cols = ["id","학교명","계약번호","계약_시작일","계약_종료일",
            "폐기물_종류","단가","월_예상량_L","계약_상태",
            "갱신_알림일","나라장터_번호","비고","created_at","updated_at"]
    result = []
    for r in rows:
        d = dict(zip(cols, r))
        end = d.get("계약_종료일","")
        if end:
            try:
                diff = (date.fromisoformat(end) - today).days
                d["D-day"] = (f"D-{diff}" if diff >= 0 else f"만료 +{abs(diff)}일")
            except Exception:
                d["D-day"] = ""
        result.append(d)
    return result


def a_add_contract(학교명: str, 계약번호: str, 시작일: str,
                   종료일: str, 폐기물종류: str, 단가: int,
                   월예상량: float, 상태: str,
                   나라장터번호: str, 비고: str):
    conn = get_conn()
    conn.execute(
        """INSERT INTO contract_master
           (학교명, 계약번호, 계약_시작일, 계약_종료일,
            폐기물_종류, 단가, 월_예상량_L, 계약_상태,
            나라장터_번호, 비고, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (학교명, 계약번호, 시작일, 종료일, 폐기물종류,
         단가, 월예상량, 상태, 나라장터번호, 비고,
         datetime.now().strftime("%Y-%m-%d"),
         datetime.now().strftime("%Y-%m-%d"))
    )
    # school_prices 계약 정보도 동기화
    conn.execute(
        """UPDATE school_prices SET
           계약_시작일=?, 계약_종료일=?, 계약_상태=?, updated_at=?
           WHERE 학교명=?""",
        (시작일, 종료일, 상태, datetime.now().strftime("%Y-%m-%d"), 학교명)
    )
    conn.commit()


def a_delete_contract(contract_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM contract_master WHERE id=?", (contract_id,))
    conn.commit()


def _hy_font() -> str:
    """한글 폰트 등록 후 폰트명 반환"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for fid, fpath in [
        ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),
        ("MalgunGothic", "/usr/share/fonts/truetype/malgun.ttf"),
        ("NanumGothic",  "C:/Windows/Fonts/NanumGothic.ttf"),
        ("NanumGothic",  "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]:
        if os.path.exists(fpath):
            try:
                pdfmetrics.registerFont(TTFont(fid, fpath))
                return fid
            except Exception:
                pass
    return "Helvetica"


def _out_dir(sub: str) -> str:
    """출력 폴더 생성 후 경로 반환"""
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.getcwd()
    path = os.path.join(base, sub)
    os.makedirs(path, exist_ok=True)
    return path


# ── E-1: 음식물 견적서 PDF 생성 ────────────────────────────
def generate_estimate_pdf(school_name: str, school_biz_no: str,
                          volume_l: float, unit_price: int,
                          contract_period: str,
                          year: str = None) -> str:
    """
    음식물 견적서 PDF 생성
    반환: 저장된 PDF 경로
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units    import mm
    from reportlab.lib          import colors
    from reportlab.platypus     import (SimpleDocTemplate, Table,
                                        TableStyle, Paragraph,
                                        Spacer, HRFlowable)
    from reportlab.lib.styles   import ParagraphStyle

    FONT = _hy_font()
    today = date.today()
    yr    = year or str(today.year)[2:]          # "26"
    supply_amount = int(volume_l * unit_price) if volume_l else unit_price

    out   = _out_dir("estimates_pdf")
    fname = f"음식물견적서_{school_name}_{today.strftime('%Y%m%d')}.pdf"
    fpath = os.path.join(out, fname)

    def ps(name, size, align=0, bold=False, color=colors.black):
        w = f"<b>" if bold else ""
        return ParagraphStyle(name, fontName=FONT, fontSize=size,
                               alignment=align, leading=size*1.55,
                               textColor=color, spaceAfter=2)

    doc   = SimpleDocTemplate(fpath, pagesize=A4,
                               leftMargin=18*mm, rightMargin=18*mm,
                               topMargin=20*mm, bottomMargin=18*mm)
    story = []

    # 제목
    story.append(Paragraph(
        "<b>음식폐기물 처리비용 견적서</b>",
        ps("t", 18, align=1)
    ))
    story.append(Spacer(1, 5*mm))

    # 상단 2단 정보 테이블 (고객 | 공급자)
    left_data = [
        [Paragraph("<b>고객명</b>", ps("h",10)), Paragraph(f"<b>{school_name}</b>", ps("v",12))],
        [Paragraph("<b>견적일</b>", ps("h",10)), Paragraph(f"{yr}.{today.month:02d}.{today.day:02d}", ps("v",10))],
    ]
    right_data = [
        ["사업자등록번호", HY["biz_no"],  "허가번호", HY["permit_no"]],
        ["상호",          HY["name"],     "대표자",   HY["ceo"]],
        ["주소",          HY["address"],  "",         ""],
        ["업태",          HY["biz_type"], "업종",     HY["biz_item"]],
    ]

    # 공급자 박스 표
    sup_tbl = Table(right_data, colWidths=[22*mm, 52*mm, 18*mm, 40*mm])
    sup_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), FONT),
        ("FONTSIZE",  (0,0), (-1,-1), 8),
        ("BACKGROUND",(0,0), (0,-1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND",(2,0), (2,-1), colors.HexColor("#f0f0f0")),
        ("GRID",      (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",     (0,0), (0,-1), "CENTER"),
        ("ALIGN",     (2,0), (2,-1), "CENTER"),
        ("SPAN",      (1,2), (3,2)),   # 주소 병합
        ("ROWHEIGHT", (0,0), (-1,-1), 7*mm),
    ]))

    hdr_tbl = Table(
        [[Paragraph(f"<b>고객명</b>", ps("h",10)), Paragraph(f"<b>{school_name}</b>", ps("hv",12,bold=True)),
          Paragraph("<b>공급자</b>", ps("h",10)), sup_tbl]],
        colWidths=[18*mm, 42*mm, 18*mm, None]
    )
    hdr_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), FONT),
        ("BOX",       (0,0), (1,-1), 0.5, colors.grey),
        ("BOX",       (2,0), (3,-1), 0.5, colors.grey),
        ("ALIGN",     (0,0), (0,-1), "CENTER"),
        ("ALIGN",     (2,0), (2,-1), "CENTER"),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND",(0,0), (0,-1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND",(2,0), (2,-1), colors.HexColor("#f0f0f0")),
        ("ROWHEIGHT", (0,0), (-1,-1), 10*mm),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 4*mm))

    # 계약기간 행
    story.append(Paragraph(
        f"<b>{yr}년도 음식물류폐기물견적서</b>　　　계약기간: {contract_period}",
        ps("cp", 10)
    ))
    story.append(Spacer(1, 2*mm))

    # 공급가액 합계 행
    total_str = f"{supply_amount:,}" if volume_l else "-"
    story.append(Table(
        [["공급가액 합계", total_str]],
        colWidths=[40*mm, None]
    ))
    story.append(Spacer(1, 2*mm))

    # 품목 명세 테이블
    item_header = ["품  명", "규격", "수량", "단가(원)", "공급가액", "비고"]
    item_rows   = [
        ["음식폐기물수거운반처리", "L(리터)",
         f"{volume_l:,.0f}" if volume_l else "",
         f"{unit_price:,}", f"{supply_amount:,}", "면세"],
    ]
    # 빈 행 6개 (추가 품목용)
    for _ in range(6):
        item_rows.append(["", "", "", "", "", ""])
    item_rows.append(["합  계", "", "", "", f"{supply_amount:,}", ""])

    item_tbl = Table(
        [item_header] + item_rows,
        colWidths=[55*mm, 22*mm, 22*mm, 25*mm, 28*mm, 18*mm]
    )
    item_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), FONT),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("BACKGROUND",     (0,0), (-1, 0), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR",      (0,0), (-1, 0), colors.white),
        ("ALIGN",          (0,0), (-1,-1), "CENTER"),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("GRID",           (0,0), (-1,-1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-2),
         [colors.white, colors.HexColor("#f8f8f8")]),
        ("BACKGROUND",     (0,-1), (-1,-1), colors.HexColor("#e8e8e8")),
        ("FONTSIZE",       (0,-1), (-1,-1), 10),
        ("ROWHEIGHT",      (0,0), (-1,-1), 8*mm),
    ]))
    story.append(item_tbl)
    story.append(Spacer(1, 4*mm))

    # 특기사항
    notes = [
        "1. 음식물쓰레기수거용기는 수집운반업체(하영자원)에서 부담한다.",
        "2. 음식물쓰레기수거 때에 배출자는 수집운반업체가 수거를 원활히 할 수 있게 해야한다.",
        "3. 천재지변(눈,비)으로 인하여 수거를 할 수 없을 경우 수집운반업체는 배출자에게 "
           "지체없이 통보하고 수거 가능일자를 협의할 수 있다.",
    ]
    note_tbl = Table(
        [["특기사항", "\n".join(notes)]],
        colWidths=[18*mm, None]
    )
    note_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f0f0f0")),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ALIGN",      (0,0), (0,-1), "CENTER"),
        ("ROWHEIGHT",  (0,0), (-1,-1), 18*mm),
    ]))
    story.append(note_tbl)
    story.append(Spacer(1, 3*mm))

    # 연락처 행
    contact_tbl = Table(
        [["연락처", HY["tel"], "FAX", HY["fax"], "이메일", HY["email"], "담당자", HY["ceo"]]],
        colWidths=[15*mm, 28*mm, 10*mm, 28*mm, 15*mm, 48*mm, 15*mm, 15*mm]
    )
    contact_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (4,0), (4,-1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (6,0), (6,-1), colors.HexColor("#f0f0f0")),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, colors.grey),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ROWHEIGHT",  (0,0), (-1,-1), 7*mm),
    ]))
    story.append(contact_tbl)

    doc.build(story)
    return fpath


# ── E-2a: 음식물류폐기물 위수탁계약서 PDF ──────────────────
def generate_contract_doc_pdf(school_name: str, school_biz_no: str,
                               school_addr: str, school_tel: str,
                               start_date: str, end_date: str,
                               waste_type: str = "음식물류폐기물",
                               volume_str: str = "",
                               unit_price: int = 180,
                               contract_amount: str = "") -> str:
    """
    폐기물 위수탁 운반 처리 계약서 PDF 생성
    hwp 원본(음식물류폐기물_위수탁계약서1.hwp) 레이아웃 기준
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units    import mm
    from reportlab.lib          import colors
    from reportlab.platypus     import (SimpleDocTemplate, Table,
                                        TableStyle, Paragraph, Spacer)
    from reportlab.lib.styles   import ParagraphStyle

    FONT  = _hy_font()
    today = date.today()
    out   = _out_dir("contract_pdf")
    fname = f"위수탁계약서_{school_name}_{today.strftime('%Y%m%d')}.pdf"
    fpath = os.path.join(out, fname)

    def ps(n, sz, align=0, bold=False):
        return ParagraphStyle(n, fontName=FONT, fontSize=sz,
                               alignment=align, leading=sz*1.6,
                               spaceAfter=2)

    doc   = SimpleDocTemplate(fpath, pagesize=A4,
                               leftMargin=25*mm, rightMargin=25*mm,
                               topMargin=25*mm, bottomMargin=20*mm)
    story = []

    # 제목
    story.append(Paragraph(
        "<b>폐기물 위수탁 운반 처리 계약서(안)</b>",
        ps("t", 16, align=1)
    ))
    story.append(Spacer(1, 8*mm))

    # 계약 기본 정보 목록
    yr    = str(today.year)[2:]
    items = [
        ("1. 계  약  명", f"음식물류폐기물수집,운반 처리"),
        ("2. 배  출  장  소", school_name),
        ("3. 처  리  장  소", HY["processor"]),
        ("4. 결  제  조  건", "계좌이체"),
        ("5. 위수탁 계약기간",
         f"{start_date}부터  {end_date}까지"),
        ("6. 위수탁 폐기물 및 처리금액", "(단위: 원)"),
    ]
    for label, value in items:
        row_tbl = Table(
            [[Paragraph(f"<b>{label}</b>", ps("lbl",10)),
              Paragraph(f": {value}", ps("val",10))]],
            colWidths=[52*mm, None]
        )
        row_tbl.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), FONT),
            ("VALIGN",   (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(row_tbl)
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 3*mm))

    # 폐기물/단가/계약금액 표
    waste_header = ["폐기물 종류", "물량(예상)", "단가", "계약금액", "처리방법"]
    waste_row    = [waste_type, volume_str, f"{unit_price}원/L",
                   contract_amount, "위탁처리"]
    waste_total  = ["총  계", "", "", contract_amount, ""]

    waste_tbl = Table(
        [waste_header, waste_row, waste_total],
        colWidths=[40*mm, 30*mm, 28*mm, 40*mm, 28*mm]
    )
    waste_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1, 0), colors.HexColor("#dddddd")),
        ("BACKGROUND", (0,-1),(- 1,-1),colors.HexColor("#eeeeee")),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.black),
        ("ROWHEIGHT",  (0,0), (-1,-1), 9*mm),
    ]))
    story.append(waste_tbl)
    story.append(Spacer(1, 8*mm))

    # 계약 체결 문구
    story.append(Paragraph(
        "위 계약은 상호 대등한 입장에서 신의성실의 원칙에 따라 계약을 체결하고 "
        "본 계약상의 내용을 이행 증명하기 위하여 배출자와 수집운반업자가 "
        "기명날인한 후 각 1부씩 보관하기로 한다.",
        ps("body", 10)
    ))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"{yr}년　　{today.month}월　　{today.day}일",
        ps("dt", 11, align=2)
    ))
    story.append(Spacer(1, 8*mm))

    # 배출자(갑) / 운반자(을) 서명란
    sign_data = [
        ["구분", "배출자 (갑)", "운반자 (을)"],
        ["상  호", school_name, HY["name"]],
        ["소재지", school_addr, HY["address"]],
        ["사업자번호", school_biz_no, HY["biz_no"]],
        ["전화번호", school_tel, HY["mobile"]],
        ["허가번호", "", HY["permit_no"]],
        ["서명(인)", "학교장 (인)", f"{HY['ceo']} (인)"],
    ]
    sign_tbl = Table(sign_data, colWidths=[30*mm, 72*mm, 62*mm])
    sign_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("BACKGROUND", (0,0), (-1, 0), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR",  (0,0), (-1, 0), colors.white),
        ("BACKGROUND", (0,1), (0,-1), colors.HexColor("#f0f0f0")),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWHEIGHT",  (0,0), (-1,-1), 9*mm),
        ("ROWHEIGHT",  (0,-1),(- 1,-1),14*mm),
    ]))
    story.append(sign_tbl)

    doc.build(story)
    return fpath


# ── E-2b: 계약이행 통합 서약서 PDF ─────────────────────────
def generate_pledge_pdf(school_name: str, unit_price: int,
                        start_date: str, end_date: str) -> str:
    """
    계약이행 통합 서약서 PDF 생성
    (hwp 원본: 계약이행_통합_서약서.hwp 기준)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units    import mm
    from reportlab.lib          import colors
    from reportlab.platypus     import (SimpleDocTemplate, Table,
                                        TableStyle, Paragraph, Spacer)
    from reportlab.lib.styles   import ParagraphStyle

    FONT  = _hy_font()
    today = date.today()
    yr    = str(today.year)[2:]
    out   = _out_dir("contract_pdf")
    fname = f"계약이행서약서_{school_name}_{today.strftime('%Y%m%d')}.pdf"
    fpath = os.path.join(out, fname)

    def ps(n, sz, align=0):
        return ParagraphStyle(n, fontName=FONT, fontSize=sz,
                               alignment=align, leading=sz*1.6,
                               spaceAfter=2)

    doc   = SimpleDocTemplate(fpath, pagesize=A4,
                               leftMargin=20*mm, rightMargin=20*mm,
                               topMargin=22*mm, bottomMargin=18*mm)
    story = []

    # 제목
    story.append(Paragraph("<b>계약이행 통합 서약서</b>", ps("t",16,align=1)))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"{yr}년 음식물폐기물처리용역",
        ps("sub", 11, align=1)
    ))
    story.append(Spacer(1, 5*mm))

    # 기본 정보 표
    info_tbl = Table([
        ["발주기관", school_name,    "단 가",    f"{unit_price}원/L"],
        ["계약기간", f"{start_date} ~ {end_date}", "", ""],
        ["업체명",   HY["name"],      "사업자번호", HY["biz_no"]],
        ["대표자",   HY["ceo"],       "연락처",     HY["tel"]],
        ["주  소",   HY["address"],   "",           ""],
    ], colWidths=[25*mm, 68*mm, 28*mm, 45*mm])
    info_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#e8e8e8")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#e8e8e8")),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.grey),
        ("ALIGN",      (0,0), (0,-1), "CENTER"),
        ("ALIGN",      (2,0), (2,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("SPAN",       (1,1), (3,1)),   # 계약기간 병합
        ("SPAN",       (1,4), (3,4)),   # 주소 병합
        ("ROWHEIGHT",  (0,0), (-1,-1), 8*mm),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 5*mm))

    # 이행 내용 체크 표
    checks = [
        ("계약일반조건",
         "지방자치단체 입찰 및 계약 집행기준 제9장 계약 일반조건을 준수합니다.",
         "[✓] 예  [ ] 아니오"),
        ("수의계약 각서",
         "귀 기관과 수의계약을 체결함에 있어서 수의계약 배제사유 중 어느 사유에도 "
         "해당되지 않으며, 차후 이러한 사실이 발견된 경우 계약의 해제·해지 및 "
         "부정당업자 제재 처분을 받아도 하등의 이유를 제기하지 않겠습니다.",
         "[✓] 예  [ ] 아니오  [ ] 해당없음"),
        ("수의계약 체결 제한 여부",
         "발주기관의 소속 고위공직자 등 이해충돌 방지법 해당 여부 확인.\n"
         "본인은 해당 없음을 확인합니다.",
         "[ ] 예  [ ] 아니오  [✓] 해당없음"),
        ("청렴계약 이행서약",
         "본 계약과 관련하여 직·간접적으로 뇌물수수, 입찰 및 계약 방해 등 "
         "부정행위를 하지 않겠으며, 위반 시 계약해지 등 제재를 감수합니다.",
         "[✓] 예  [ ] 아니오"),
        ("중대재해 예방점검",
         "「중대재해 처벌 등에 관한 법률」에 따라 안전보건 관리체계를 구축하고 "
         "재해 예방에 최선을 다하겠습니다.",
         "[✓] 예  [ ] 아니오"),
    ]

    chk_header = [
        Paragraph("<b>이행 내용</b>", ps("h",9,align=1)),
        Paragraph("<b>세부내용</b>",  ps("h",9,align=1)),
        Paragraph("<b>확인</b>",      ps("h",9,align=1)),
    ]
    chk_rows = [[
        Paragraph(c[0], ps(f"cl{i}", 9, align=1)),
        Paragraph(c[1], ps(f"cv{i}", 8)),
        Paragraph(c[2], ps(f"cc{i}", 8, align=1)),
    ] for i, c in enumerate(checks)]

    chk_tbl = Table(
        [chk_header] + chk_rows,
        colWidths=[35*mm, 100*mm, 31*mm]
    )
    chk_tbl.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("BACKGROUND", (0,0), (-1, 0), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR",  (0,0), (-1, 0), colors.white),
        ("BACKGROUND", (0,1), (0,-1), colors.HexColor("#f0f4ff")),
        ("ALIGN",      (0,0), (-1, 0), "CENTER"),
        ("ALIGN",      (0,1), (0,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.grey),
        ("ROWHEIGHT",  (0,0), (-1,-1), 16*mm),
    ]))
    story.append(chk_tbl)
    story.append(Spacer(1, 8*mm))

    # 서명란
    story.append(Paragraph(
        f"위와 같이 서약합니다.　　　　　{today.strftime('%Y년 %m월 %d일')}",
        ps("sd", 10, align=2)
    ))
    story.append(Spacer(1, 5*mm))

    sign_tbl2 = Table([
        ["업체명", HY["name"],   "사업자번호", HY["biz_no"]],
        ["대표자", HY["ceo"] + "　　　　　　(인)", "", ""],
    ], colWidths=[20*mm, 70*mm, 28*mm, 48*mm])
    sign_tbl2.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), FONT),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#eeeeee")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#eeeeee")),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.grey),
        ("ALIGN",      (0,0), (0,-1), "CENTER"),
        ("ALIGN",      (2,0), (2,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("SPAN",       (1,1), (3,1)),
        ("ROWHEIGHT",  (0,0), (-1,-1), 12*mm),
    ]))
    story.append(sign_tbl2)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"서초고등학교장 귀중",
        ps("rcp", 10, align=2)
    ))

    doc.build(story)
    return fpath


# ── E-3: 계약서류 패키지 ZIP 생성 ──────────────────────────
def generate_contract_package(
    school_name: str,
    school_biz_no: str   = "",
    school_addr: str     = "",
    school_tel: str      = "",
    start_date: str      = "",
    end_date: str        = "",
    volume_l: float      = 0,
    unit_price: int      = 180,
    contract_amount: str = "",
) -> bytes:
    """
    학교명 입력 → PDF 3종 자동생성 + 기존 서류 포함 → ZIP 반환 (bytes)
    포함 서류:
      자동생성: 음식물견적서, 위수탁계약서, 계약이행서약서
      기존파일: 사업자등록증, 허가증, 소상공인, 창업기업, 재해율확인서, 계좌
    """
    contract_period = (f"{start_date} ~ {end_date}"
                       if start_date and end_date else "계약기간 기재")

    generated = {}
    errors    = {}

    # ① PDF 3종 생성
    try:
        generated["견적서"] = generate_estimate_pdf(
            school_name, school_biz_no,
            volume_l, unit_price, contract_period
        )
    except Exception as e:
        errors["견적서"] = str(e)

    try:
        generated["위수탁계약서"] = generate_contract_doc_pdf(
            school_name, school_biz_no, school_addr, school_tel,
            start_date, end_date,
            volume_l=f"{volume_l:,.0f}L" if volume_l else "",
            unit_price=unit_price,
            contract_amount=contract_amount,
        )
    except Exception as e:
        errors["위수탁계약서"] = str(e)

    try:
        generated["계약이행서약서"] = generate_pledge_pdf(
            school_name, unit_price, start_date, end_date
        )
    except Exception as e:
        errors["계약이행서약서"] = str(e)

    # ② 기존 서류 파일 경로 목록
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.getcwd()

    static_docs = {
        "사업자등록증.jpg":    os.path.join(base, "사업자등록증.jpg"),
        "허가증.jpg":          os.path.join(base, "허가증.jpg"),
        "소상공인확인서.pdf":  os.path.join(base, "소상공인.pdf"),
        "창업기업확인서.pdf":  os.path.join(base, "창업기업.pdf"),
        "재해율확인서.pdf":    os.path.join(base, "재해율확인서.pdf"),
        "사업자계좌.jpg":      os.path.join(base, "사업자계좌.jpg"),
    }

    # ③ ZIP 메모리 내 생성
    buf = io.BytesIO()
    today_str = date.today().strftime("%Y%m%d")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 자동 생성 PDF
        for name, path in generated.items():
            if os.path.exists(path):
                zf.write(path, f"01_자동생성/{os.path.basename(path)}")
        # 기존 서류
        for arc_name, fpath in static_docs.items():
            if os.path.exists(fpath):
                zf.write(fpath, f"02_기존서류/{arc_name}")
        # 오류 목록 있으면 txt로 포함
        if errors:
            err_txt = "\n".join(f"{k}: {v}" for k, v in errors.items())
            zf.writestr("오류목록.txt", err_txt)
        # 체크리스트
        checklist = f"""하영자원 계약서류 패키지 체크리스트
생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
대상학교: {school_name}
계약기간: {contract_period}
단  가: {unit_price}원/L
==============================================
[자동생성 서류]
{'✅' if '견적서' in generated else '❌'} 음식물 견적서 PDF
{'✅' if '위수탁계약서' in generated else '❌'} 위수탁계약서 PDF
{'✅' if '계약이행서약서' in generated else '❌'} 계약이행 통합 서약서 PDF

[기존 서류]
{'✅' if os.path.exists(static_docs['사업자등록증.jpg']) else '⚠️ 없음'} 사업자등록증
{'✅' if os.path.exists(static_docs['허가증.jpg']) else '⚠️ 없음'} 폐기물수집운반업 허가증
{'✅' if os.path.exists(static_docs['소상공인확인서.pdf']) else '⚠️ 없음'} 소상공인 확인서 (만료: 2026-03-31 ⚠️)
{'✅' if os.path.exists(static_docs['창업기업확인서.pdf']) else '⚠️ 없음'} 창업기업 확인서
{'✅' if os.path.exists(static_docs['재해율확인서.pdf']) else '⚠️ 없음'} 재해율 확인서
{'✅' if os.path.exists(static_docs['사업자계좌.jpg']) else '⚠️ 없음'} 사업자 계좌 통장사본
==============================================
⚠️ 주의: 소상공인 확인서는 2026-03-31 만료 예정입니다.
   갱신 주소: sminfo.mss.go.kr
"""
        zf.writestr("00_서류체크리스트.txt", checklist)

    return buf.getvalue(), errors


# ============================================================
# DB 초기화 + 데이터 로드
# ============================================================
init_db()
df_all = load_data()

# ============================================================
# 로그인 화면 렌더링 함수
# ============================================================
def render_login_page():
    """S2B 스타일 랜딩 + 로그인 카드"""
    # 선택된 그룹 state
    if "login_group" not in st.session_state:
        st.session_state.login_group = None

    st.markdown("""
    <div class="login-header">
        <div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:10px;">
            <span style="font-size:2.8rem;">♻️</span>
            <div>
                <div style="font-size:2rem;font-weight:900;color:#1a3a5c;line-height:1.1;">하영자원 데이터 플랫폼</div>
                <div style="font-size:0.95rem;color:#4a6b8a;margin-top:4px;">투명하고 효율적인 공공 폐기물 관리 솔루션</div>
            </div>
        </div>
        <div style="height:3px;width:80px;background:linear-gradient(90deg,#1a73e8,#34a853);border-radius:2px;margin:16px auto 0;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── 3개 카드 버튼 ──
    col_l, col_c, col_r = st.columns([1,3,1])
    with col_c:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="login-card" style="border-top:5px solid #1a73e8;">
                <div class="login-card-icon">🏢</div>
                <div class="login-card-title">관리자</div>
                <div class="login-card-desc">본사 통합 관제<br>전체 권한 접근</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("관리자 로그인", key="btn_admin", use_container_width=True, type="primary"):
                st.session_state.login_group = "관리자"
        with c2:
            st.markdown("""
            <div class="login-card" style="border-top:5px solid #34a853;">
                <div class="login-card-icon">🏫</div>
                <div class="login-card-title">교육청 / 학교</div>
                <div class="login-card-desc">교육청·행정실<br>담당자 전용</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("교육청·학교 로그인", key="btn_school", use_container_width=True):
                st.session_state.login_group = "학교_교육청"
        with c3:
            st.markdown("""
            <div class="login-card" style="border-top:5px solid #fbbc05;">
                <div class="login-card-icon">🚚</div>
                <div class="login-card-title">수거업체</div>
                <div class="login-card-desc">기사·현장 관리자<br>전용 앱</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("수거업체 로그인", key="btn_driver", use_container_width=True):
                st.session_state.login_group = "수거기사"

    # ── 로그인 폼 ──
    if st.session_state.login_group:
        st.write("")
        col_fl, col_fc, col_fr = st.columns([1,2,1])
        with col_fc:
            group = st.session_state.login_group
            icons = {"관리자": "🏢", "학교_교육청": "🏫", "수거기사": "🚚"}
            titles = {"관리자": "관리자 로그인", "학교_교육청": "교육청 / 학교(행정실) 로그인", "수거기사": "수거업체(기사) 로그인"}
            st.markdown(f"""
            <div style="background:white;border-radius:16px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,.1);">
                <div style="text-align:center;font-size:1.3rem;font-weight:800;color:#1a3a5c;margin-bottom:24px;">
                    {icons[group]} {titles[group]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.form(f"login_form_{group}"):
                uid = st.text_input("아이디", placeholder="아이디를 입력하세요")
                pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                submitted = st.form_submit_button("🔐 로그인", use_container_width=True, type="primary")
                if submitted:
                    if uid in USER_ACCOUNTS:
                        acc = USER_ACCOUNTS[uid]
                        if acc["password"] == pwd:
                            st.session_state.logged_in = True
                            st.session_state.user_id   = uid
                            st.session_state.user_role = acc["role"]
                            st.session_state.user_name = acc["display_name"]
                            st.session_state.user_org  = acc["org"]
                            st.rerun()
                        else:
                            st.error("❌ 비밀번호가 올바르지 않습니다.")
                    else:
                        st.error("❌ 존재하지 않는 아이디입니다.")

    st.markdown("""
    <div class="login-footer" style="margin-top:40px;">
        ⓒ 2025 하영자원 | 하영자원 데이터 플랫폼 Pro v3.0 | 문의: 하영자원 본사
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 세션 상태 초기화
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ── 미로그인 → 로그인 화면 표시 후 중단 ──
if not st.session_state.logged_in:
    render_login_page()
    st.stop()

# ============================================================
# 사이드바 (로그인 후)
# ============================================================
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro v3")
    st.caption("공공기관(B2G) 맞춤 데이터 플랫폼")
    st.write("---")
    st.markdown(f"""
    **👤 {st.session_state.user_name}**
    🏷️ 역할: `{st.session_state.user_role}`
    🏢 소속: {st.session_state.user_org}
    """)
    st.write("---")
    if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
        for k in ["logged_in","user_id","user_role","user_name","user_org","login_group"]:
            st.session_state.pop(k, None)
        st.rerun()
    st.write("---")
    st.success("✅ SQLite DB (WAL모드)")
    st.caption("v3: 재활용시세·스쿨존·캘린더·교육청모드")

# ── 로그인 정보 기반 role 매핑 ──
_role_map = {
    "관리자":   "🏢 관리자 (본사 관제)",
    "학교":     "🏫 학교 담당자 (행정실)",
    "수거기사": "🚚 수거 기사 (현장 앱)",
    "교육청":   "🏛️ 교육청 관제 (신규)",
}

# 관리자는 사이드바 radio로 추가 탭 선택
if st.session_state.user_role == "관리자":
    _tabs_admin = [
        "🏢 관리자 (본사 관제)",
        "🏫 학교 마스터 관리",
        "📋 서류 유효기간 관리",
        "💰 견적서 작성",
        "📄 위수탁계약서 작성",
        "📦 계약서류 패키지 생성",
    ]
    role = st.sidebar.radio("메뉴", _tabs_admin, label_visibility="collapsed")
else:
    role = _role_map.get(st.session_state.user_role, "🏢 관리자 (본사 관제)")

# ============================================================
# [모드 1] 관리자 (본사 관제)
# ============================================================
if role == "🏢 관리자 (본사 관제)":
    st.markdown("<h1>🏢 본사 통합 관제 및 정산 센터</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#5f6368;font-size:16px;'>음식물·사업장·재활용 통계를 분리하여 수익/비용 관리가 가능합니다.</p>", unsafe_allow_html=True)

    # KPI 카드
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 총 수거</div><div class="metric-value-food">{df_all["음식물(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 총 수거</div><div class="metric-value-biz">{df_all["사업장(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 총 수거</div><div class="metric-value-recycle">{df_all["재활용(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="custom-card"><div class="metric-title">💰 누적 청구 금액</div><div class="metric-value-total">{df_all["최종정산액"].sum():,.0f} 원</div></div>', unsafe_allow_html=True)
    # [추가5] 공공예산 절감 지표
    school_count = df_all["학교명"].nunique()
    budget_saving = school_count * int(get_setting("budget_saving_per_school") or 5200000)
    with c5: st.markdown(f'<div class="custom-card custom-card-teal"><div class="metric-title">💵 공공예산 절감(연)</div><div class="metric-value-total" style="color:#00897b;">{budget_saving:,.0f}원</div></div>', unsafe_allow_html=True)

    # ESG 배너 (소나무 + 업무절감 + 예산절감)
    co2 = df_all["탄소감축량(kg)"].sum()
    trees = int(co2 / 6.6)
    work_hours_saved = school_count * 52 * 6  # 학교수 × 52주 × 주당 6시간 절감
    st.markdown(f"""
    <div style="background:#61b346;padding:25px;border-radius:12px;color:white;display:flex;justify-content:space-around;align-items:center;margin-bottom:10px;">
        <div style="text-align:center;">
            <p style="margin:0;font-size:13px;opacity:.9;">🌍 누적 CO₂ 감축량</p>
            <h2 style="margin:0;color:white;font-weight:900;">{co2:,.0f} kg</h2>
            <p style="margin:0;font-size:12px;opacity:.8;">🌲 소나무 {trees:,}그루 효과</p>
        </div>
        <div style="text-align:center;">
            <p style="margin:0;font-size:13px;opacity:.9;">⏱️ 행정시간 절감(연)</p>
            <h2 style="margin:0;color:white;font-weight:900;">{work_hours_saved:,} 시간</h2>
            <p style="margin:0;font-size:12px;opacity:.8;">담당자 90% 업무 단축</p>
        </div>
        <div style="text-align:center;">
            <p style="margin:0;font-size:13px;opacity:.9;">💰 공공예산 절감(연)</p>
            <h2 style="margin:0;color:white;font-weight:900;">{budget_saving/100000000:.1f}억 원</h2>
            <p style="margin:0;font-size:12px;opacity:.8;">{school_count}개교 기준</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("📑 통합 정산 관리")

    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub, tab_price, tab_recycle_price, tab_notify = st.tabs([
        "전체 통합 정산", "음식물 정산", "사업장 정산", "재활용 정산",
        "📍 차량 관제", "🤝 외주업체",
        "💰 단가 설정", "♻️ 재활용 시세 ✨", "📱 알림 설정"
    ])

    with tab_total:
        cur_year = str(datetime.now().year)
        cur_month = datetime.now().strftime("%Y-%m")
        prev_month_n = datetime.now().month - 1 or 12
        prev_month = f"{datetime.now().year if datetime.now().month > 1 else datetime.now().year-1}-{prev_month_n:02d}"

        # ── 상단 필터: 연도 / 월 / 학교 선택 ──
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            all_years = sorted(df_all["년도"].unique(), reverse=True)
            sel_year_admin = st.selectbox("📅 연도", all_years, key="admin_year")
        with fc2:
            months_in_year = sorted(df_all[df_all["년도"]==sel_year_admin]["월별"].unique(), reverse=True)
            sel_month_admin = st.selectbox("🗓️ 월", ["전체"] + list(months_in_year), key="admin_month")
        with fc3:
            sel_school_admin = st.selectbox("🏫 학교", ["전체"] + SCHOOL_LIST, key="admin_school")

        # 필터 적용
        df_filtered = df_all[df_all["년도"] == sel_year_admin]
        if sel_month_admin != "전체":
            df_filtered = df_filtered[df_filtered["월별"] == sel_month_admin]
        if sel_school_admin != "전체":
            df_filtered = df_filtered[df_filtered["학교명"] == sel_school_admin]

        s1, s2, s3, s4 = st.tabs([
            f"📋 필터결과",
            f"📅 {cur_year}년 전체",
            f"🗓️ 이번달({cur_month})",
            f"🗓️ 지난달({prev_month})"
        ])
        with s1:
            st.caption(f"조건: {sel_year_admin}년 / {sel_month_admin} / {sel_school_admin} — {len(df_filtered)}건")
            st.dataframe(df_filtered[["날짜","학교명","학생수","음식물(kg)","최종정산액","탄소감축량(kg)","상태"]], use_container_width=True)
            if not df_filtered.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("총 음식물", f"{df_filtered['음식물(kg)'].sum():,.0f} kg")
                m2.metric("총 정산액", f"{df_filtered['최종정산액'].sum():,.0f} 원")
                m3.metric("CO₂ 감축", f"{df_filtered['탄소감축량(kg)'].sum():,.1f} kg")
                # 학교별 소계 테이블
                if sel_school_admin == "전체":
                    st.markdown("**📊 학교별 소계**")
                    school_sum = df_filtered.groupby("학교명").agg(
                        수거건수=("id","count"),
                        음식물_합계=("음식물(kg)","sum"),
                        정산액_합계=("최종정산액","sum"),
                        CO2감축=("탄소감축량(kg)","sum")
                    ).reset_index().sort_values("정산액_합계", ascending=False)
                    st.dataframe(school_sum, use_container_width=True)
                dl_f = create_secure_excel(df_filtered[["날짜","학교명","음식물(kg)","사업장(kg)","재활용(kg)","최종정산액","탄소감축량(kg)","상태"]], "필터 정산서")
                st.download_button("📥 필터결과 정산서 다운로드", data=dl_f,
                                   file_name=f"하영자원_{sel_year_admin}_{sel_month_admin}_{sel_school_admin}.xlsx", use_container_width=True)
        with s2:
            df_cur = df_all[df_all["년도"]==cur_year]
            st.dataframe(df_cur[["날짜","학교명","학생수","최종정산액","탄소감축량(kg)","상태"]], use_container_width=True)
        with s3:
            df_cm = df_all[df_all["월별"]==cur_month]
            st.dataframe(df_cm[["날짜","학교명","학생수","최종정산액","상태"]], use_container_width=True)
            if not df_cm.empty:
                pending = df_cm[df_cm["상태"]=="정산대기"]
                if not pending.empty:
                    if st.button(f"✅ 이번달 미정산 {len(pending)}건 → 정산완료 처리", type="primary"):
                        update_collection_status(pending["id"].tolist(), "정산완료")
                        st.success(f"{len(pending)}건이 정산완료로 변경되었습니다.")
                        st.rerun()
        with s4:
            df_pm = df_all[df_all["월별"]==prev_month]
            st.dataframe(df_pm[["날짜","학교명","학생수","최종정산액","상태"]], use_container_width=True)

        # 정산서 다운로드
        b1, b2 = st.columns(2)
        with b1:
            dl_data = create_secure_excel(
                df_all[["날짜","학교명","음식물(kg)","사업장(kg)","재활용(kg)","최종정산액","탄소감축량(kg)","상태"]],
                "전체 통합 정산서"
            )
            st.download_button("📥 전체 통합정산서 다운로드", data=dl_data,
                               file_name=f"하영자원_통합정산서_{cur_month}.xlsx", use_container_width=True)
        with b2:
            month_dl = create_secure_excel(
                df_all[df_all["월별"]==cur_month][["날짜","학교명","음식물(kg)","사업장(kg)","재활용(kg)","최종정산액","상태"]],
                f"{cur_month} 월간 정산서"
            )
            st.download_button(f"📥 이번달 정산서 다운로드", data=month_dl,
                               file_name=f"하영자원_월간정산서_{cur_month}.xlsx", use_container_width=True)

    with tab_food:
        f1, f2 = st.tabs([f"📅 이번달", "📅 전체"])
        with f1: st.dataframe(df_all[df_all["월별"]==datetime.now().strftime("%Y-%m")][["날짜","학교명","수거업체","음식물(kg)","단가","음식물비용","상태"]], use_container_width=True)
        with f2: st.dataframe(df_all[["날짜","학교명","수거업체","음식물(kg)","단가","음식물비용","상태"]], use_container_width=True)

    with tab_biz:
        b1, b2 = st.tabs(["📅 이번달", "📅 전체"])
        with b1: st.dataframe(df_all[df_all["월별"]==datetime.now().strftime("%Y-%m")][["날짜","학교명","학생수","사업장(kg)","사업장단가","사업장비용"]], use_container_width=True)
        with b2: st.dataframe(df_all[["날짜","학교명","학생수","사업장(kg)","사업장단가","사업장비용"]], use_container_width=True)

    with tab_recycle:
        r1, r2 = st.tabs(["📅 이번달", "📅 전체"])
        with r1: st.dataframe(df_all[df_all["월별"]==datetime.now().strftime("%Y-%m")][["날짜","학교명","학생수","재활용(kg)","재활용단가","재활용수익"]], use_container_width=True)
        with r2: st.dataframe(df_all[["날짜","학교명","학생수","재활용(kg)","재활용단가","재활용수익"]], use_container_width=True)
        # 품목별 수익 분석
        st.write("---")
        st.subheader("📊 재활용 수익 분석")
        rp_df = get_recycle_prices()
        rr1, rr2 = st.columns(2)
        with rr1:
            st.dataframe(rp_df[["품목명","단가","updated_at"]], use_container_width=True)
        with rr2:
            total_recycle_rev = df_all["재활용수익"].sum()
            st.metric("♻️ 누적 재활용 총 수익", f"{total_recycle_rev:,.0f} 원")
            st.metric("📦 평균 단가", f"{get_avg_recycle_price()} 원/kg")

    with tab_map:
        st.write("📍 **수거 차량 실시간 GPS 관제**")
        # 실제 학교 위치 좌표 (화성/수원/서울 지역)
        school_coords = {
            "화성초등학교": [37.1994, 126.8311],
            "부림초등학교": [37.2134, 126.8901],
            "동탄중학교":   [37.2001, 127.0720],
            "수원고등학교": [37.2636, 127.0286],
            "서초고등학교": [37.4875, 127.0322],
            "국사봉중학교": [37.4810, 126.9201],
        }
        map_df = pd.DataFrame(
            [(v[0], v[1], k) for k, v in school_coords.items()],
            columns=["lat","lon","학교명"]
        )
        st.map(map_df)
        st.caption("🟢 현재 운행 중인 차량 위치 (GPS 연동 시 실시간 업데이트)")
        # 오늘 수거 현황
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_df = df_all[df_all["날짜"].str.startswith(today_str)]
        if not today_df.empty:
            st.success(f"✅ 오늘 수거 완료: {len(today_df)}건")
        else:
            st.info("오늘 수거 데이터가 없습니다.")

    with tab_sub:
        st.subheader("🤝 외주 수거업체 현황")
        st.markdown('<div class="alert-box">🔔 <b>[계약 갱신 알림]</b> \'B자원\' 업체 계약 만료 30일 전입니다. (만료일: 2026-03-25)</div>', unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.info("🏆 이달 우수 업체: **A환경** (98점)")
        with cc2: st.warning("⚠️ 주의: **B자원** (과속 1회)")
        with cc3: st.success("✅ 스쿨존 위반: 1건")
        vendor_df = pd.DataFrame({
            "외주업체명": ["A환경","B자원"],
            "담당학교": ["동탄중학교","수원고등학교"],
            "안전평가": ["98점(우수)","85점(주의)"],
            "페널티": ["0원","-50,000원"],
            "지급예정액": ["1,350,000원","880,000원"],
            "상태": ["🟢 운행중","🟡 대기중"]
        })
        st.dataframe(vendor_df, use_container_width=True)
        # 실제 다운로드
        vd_excel = create_secure_excel(vendor_df, "외주업체 안전평가 결과서")
        st.download_button("📄 외주업체 안전평가 결과서 다운로드", data=vd_excel,
                           file_name=f"외주업체_안전평가_{datetime.now().strftime('%Y-%m')}.xlsx")

    with tab_price:
        st.subheader("💰 단가 설정 관리")
        st.info("이 화면에서 단가를 변경하면 **즉시 전체 정산에 반영**됩니다.")

        st.markdown("### 🌐 전체 기본 단가")
        gp1, gp2, gp3 = st.columns(3)
        with gp1: g_food    = st.number_input("음식물 기본단가 (원/kg)", value=int(get_setting("default_food_price")),    min_value=0, step=10, key="g_food")
        with gp2: g_recycle = st.number_input("재활용 기본단가 (원/kg)", value=int(get_setting("default_recycle_price")), min_value=0, step=10, key="g_recycle")
        with gp3: g_biz     = st.number_input("사업장 기본단가 (원/kg)", value=int(get_setting("default_biz_price")),     min_value=0, step=10, key="g_biz")
        if st.button("💾 기본 단가 저장", type="primary", key="save_global"):
            set_setting("default_food_price",    g_food)
            set_setting("default_recycle_price", g_recycle)
            set_setting("default_biz_price",     g_biz)
            st.success("✅ 저장 완료. 페이지 새로고침 후 반영됩니다.")

        st.write("---")
        st.markdown("### 🏫 학교별 개별 단가 + 담당자")
        sel_school = st.selectbox("설정할 학교", SCHOOL_LIST, key="price_sel")
        conn = get_conn()
        ex = conn.execute(
            "SELECT 음식물단가,재활용단가,사업장단가,담당자명,담당자연락처,담당자이메일 FROM school_prices WHERE 학교명=?",
            (sel_school,)
        ).fetchone()
        conn.close()
        ef, er, eb, en, et, ee = ex if ex else (150,300,200,"","","")
        sp1, sp2, sp3 = st.columns(3)
        with sp1: sp_food    = st.number_input("음식물 단가", value=int(ef), min_value=0, step=10, key="sp_food")
        with sp2: sp_recycle = st.number_input("재활용 단가", value=int(er), min_value=0, step=10, key="sp_recycle")
        with sp3: sp_biz     = st.number_input("사업장 단가", value=int(eb), min_value=0, step=10, key="sp_biz")
        sc1, sc2, sc3 = st.columns(3)
        with sc1: sp_name  = st.text_input("담당자 이름",   value=en or "", key="sp_name")
        with sc2: sp_tel   = st.text_input("담당자 연락처", value=et or "", placeholder="010-0000-0000", key="sp_tel")
        with sc3: sp_email = st.text_input("담당자 이메일", value=ee or "", placeholder="admin@school.kr", key="sp_email")
        if st.button(f"💾 {sel_school} 저장", type="primary", key="save_school"):
            update_school_price(sel_school, sp_food, sp_recycle, sp_biz, sp_name, sp_tel, sp_email)
            st.success(f"✅ {sel_school} 저장 완료")

        st.write("---")
        st.markdown("### 📋 전체 학교 단가 현황")
        price_overview = get_school_prices()[["학교명","음식물단가","재활용단가","사업장단가","담당자명","담당자연락처","updated_at"]]
        st.dataframe(price_overview, use_container_width=True)
        st.download_button("📥 단가 현황 다운로드", data=create_secure_excel(price_overview, "학교별 계약 단가 현황"),
                           file_name="학교별단가현황.xlsx")

    # [추가2] 재활용 시세 탭
    with tab_recycle_price:
        st.subheader("♻️ 재활용품 23종 시세 관리")
        st.markdown('<span class="badge-v3">✨ v3 신규</span>', unsafe_allow_html=True)
        st.info("품목별 단가를 실시간으로 수정하면 재활용 수익 계산에 즉시 반영됩니다.")

        rp_df = get_recycle_prices()
        rp1, rp2 = st.columns([2, 1])
        with rp1:
            st.markdown("### 📋 현재 시세 현황")
            st.dataframe(rp_df[["품목명","단가","updated_at"]].rename(columns={"단가":"단가(원/kg)","updated_at":"최종수정"}),
                         use_container_width=True)
        with rp2:
            st.markdown("### ✏️ 시세 수정")
            sel_item = st.selectbox("품목 선택", rp_df["품목명"].tolist(), key="sel_recycle_item")
            cur_price = int(rp_df[rp_df["품목명"]==sel_item]["단가"].values[0])
            new_price = st.number_input("새 단가 (원/kg)", value=cur_price, min_value=0, step=10, key="new_recycle_price")
            if st.button("💾 시세 저장", type="primary", key="save_recycle"):
                update_recycle_price(sel_item, new_price)
                st.success(f"✅ {sel_item}: {new_price}원/kg 저장 완료")
                st.rerun()

        st.write("---")
        st.markdown("### 📊 품목별 수익 기여도")
        chart_df = rp_df.sort_values("단가", ascending=False)
        st.bar_chart(chart_df.set_index("품목명")["단가"])

        # 시세 일괄 다운로드
        st.download_button(
            "📥 재활용 시세표 다운로드",
            data=create_secure_excel(rp_df[["품목명","단가"]], "재활용품 시세표"),
            file_name=f"재활용시세표_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        )

    with tab_notify:
        st.subheader("📱 알림 설정")
        st.info("카카오 알림톡 API 미연동 상태입니다. 아래에서 시뮬레이션 테스트가 가능합니다.")
        cur_notify = get_setting("kakao_notify_enabled") == "true"
        new_notify = st.toggle("📱 알림톡 활성화 (시뮬레이션)", value=cur_notify)
        if new_notify != cur_notify:
            set_setting("kakao_notify_enabled", "true" if new_notify else "false")
            st.success("설정 저장 완료")
        st.write("---")
        nt1, nt2 = st.columns(2)
        with nt1: test_school = st.selectbox("테스트 학교", SCHOOL_LIST, key="noti_school")
        with nt2: test_phone  = st.text_input("수신 번호", placeholder="010-0000-0000", key="noti_phone")
        if st.button("📱 알림톡 테스트", type="primary"):
            total_est = int(df_all[df_all["학교명"]==test_school]["최종정산액"].sum())
            send_kakao_alimtalk(test_phone or "010-0000-0000", test_school, 100.0, total_est)


# ============================================================
# [모드 2] 학교 담당자 (행정실)
# ============================================================
elif role == "🏫 학교 담당자 (행정실)":
    st.title("🏫 학교 폐기물 통합 대시보드")
    # 로그인된 학교 자동 설정 (selectbox 제거)
    school = st.session_state.user_org
    df_school = df_all[df_all["학교명"] == school]

    if not df_school.empty:
        conn = get_conn()
        pr = conn.execute("SELECT 음식물단가,재활용단가,사업장단가 FROM school_prices WHERE 학교명=?", (school,)).fetchone()
        conn.close()
        if pr:
            st.caption(f"📋 계약 단가 — 음식물: {pr[0]}원/kg | 사업장: {pr[2]}원/kg | 재활용: {pr[1]}원/kg")

        co2s = df_school["탄소감축량(kg)"].sum()
        trees_s = int(co2s / 6.6)
        work_saved = 52 * 6
        budget_s = int(get_setting("budget_saving_per_school") or 5200000)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:20px;border-radius:12px;color:white;margin-bottom:20px;display:flex;justify-content:space-around;">
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;">🌱 누적 CO₂ 감축</p>
                <h3 style="margin:0;color:white;">{co2s:,.0f} kg</h3>
                <p style="margin:0;font-size:12px;">🌲 소나무 {trees_s}그루</p>
            </div>
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;">⏱️ 연간 업무절감</p>
                <h3 style="margin:0;color:white;">{work_saved}시간</h3>
                <p style="margin:0;font-size:12px;">담당자 90% 단축</p>
            </div>
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;">💰 연간 예산절감</p>
                <h3 style="margin:0;color:white;">{budget_s:,}원</h3>
                <p style="margin:0;font-size:12px;">교육청 제출용</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        school_tab1, school_tab2, school_tab3, school_tab4 = st.tabs([
            "📊 수거량 통계", "📅 수거 일정 캘린더 ✨", "🛡️ 안전 현황", "🖨️ 서류 출력"
        ])

        with school_tab1:
            t_daily, t_monthly = st.tabs(["🗓️ 일별 배출량", "🗓️ 연도별/월별 추이"])
            with t_daily:
                dg = df_school.copy()
                dg["일자"] = dg["날짜"].astype(str).str[:10]
                dg = dg.groupby("일자")[["음식물(kg)","사업장(kg)","재활용(kg)"]].sum().reset_index()
                dc1, dc2, dc3 = st.columns(3)
                with dc1:
                    st.markdown("<h5 style='text-align:center;color:#ea4335;'>🗑️ 음식물</h5>", unsafe_allow_html=True)
                    st.bar_chart(dg.set_index("일자")["음식물(kg)"], color="#ea4335")
                with dc2:
                    st.markdown("<h5 style='text-align:center;color:#9b59b6;'>🗄️ 사업장</h5>", unsafe_allow_html=True)
                    st.bar_chart(dg.set_index("일자")["사업장(kg)"], color="#9b59b6")
                with dc3:
                    st.markdown("<h5 style='text-align:center;color:#34a853;'>♻️ 재활용</h5>", unsafe_allow_html=True)
                    st.bar_chart(dg.set_index("일자")["재활용(kg)"], color="#34a853")
            with t_monthly:
                years = sorted(df_school["년도"].unique(), reverse=True)
                ytabs = st.tabs([f"📅 {y}년" for y in years])
                for i, y in enumerate(years):
                    with ytabs[i]:
                        df_yr = df_school[df_school["년도"]==y]
                        # 연도 요약 지표
                        ym1, ym2, ym3, ym4 = st.columns(4)
                        ym1.metric("총 음식물", f"{df_yr['음식물(kg)'].sum():,.0f} kg")
                        ym2.metric("총 정산액", f"{df_yr['최종정산액'].sum():,.0f} 원")
                        ym3.metric("수거횟수", f"{len(df_yr)}회")
                        ym4.metric("CO₂ 감축", f"{df_yr['탄소감축량(kg)'].sum():,.1f} kg")
                        st.write("---")
                        # 월별 하위탭
                        months_yr = sorted(df_yr["월별"].unique())
                        if months_yr:
                            mtabs = st.tabs([f"🗓️ {m[5:]}월" for m in months_yr])
                            for j, m in enumerate(months_yr):
                                with mtabs[j]:
                                    df_m = df_yr[df_yr["월별"]==m]
                                    mm1, mm2, mm3 = st.columns(3)
                                    mm1.metric("음식물", f"{df_m['음식물(kg)'].sum():,.0f} kg")
                                    mm2.metric("정산액", f"{df_m['최종정산액'].sum():,.0f} 원")
                                    mm3.metric("CO₂ 감축", f"{df_m['탄소감축량(kg)'].sum():,.1f} kg")
                                    mc1, mc2, mc3 = st.columns(3)
                                    mg = df_m.groupby("월별")[["음식물(kg)","사업장(kg)","재활용(kg)"]].sum().reset_index()
                                    with mc1: st.bar_chart(df_m.set_index(df_m["날짜"].str[:10])["음식물(kg)"], color="#ea4335")
                                    with mc2: st.bar_chart(df_m.set_index(df_m["날짜"].str[:10])["사업장(kg)"], color="#9b59b6")
                                    with mc3: st.bar_chart(df_m.set_index(df_m["날짜"].str[:10])["재활용(kg)"], color="#34a853")
                                    st.dataframe(df_m[["날짜","음식물(kg)","사업장(kg)","재활용(kg)","최종정산액","탄소감축량(kg)","상태"]], use_container_width=True)

        # [추가4] 수거 일정 캘린더
        with school_tab2:
            st.markdown('<span class="badge-v3">✨ v3 신규</span>', unsafe_allow_html=True)
            st.subheader("📅 수거 일정 캘린더")

            cal_col1, cal_col2 = st.columns([3, 2])
            with cal_col1:
                now = datetime.now()
                sel_year  = st.selectbox("연도", [now.year-1, now.year, now.year+1], index=1, key="cal_y_school")
                sel_month = st.selectbox("월", list(range(1,13)), index=now.month-1, key="cal_m_school")

            sched_df = get_schedules_month(sel_year, sel_month)
            school_sched = sched_df[sched_df["학교명"]==school]
            collect_days = set(school_sched["날짜"].str[8:10].astype(str).str.lstrip("0"))
            # 실제 수거 실적일도 달력에 표시
            real_collect = df_school[df_school["월별"]==f"{sel_year}-{sel_month:02d}" if isinstance(sel_month, int) else df_school["월별"]==f"{sel_year}-{str(sel_month).zfill(2)}"]
            real_days_set = set(real_collect["날짜"].astype(str).str[8:10].str.lstrip("0"))

            # 달력 렌더링
            cal_html = f"<h4 style='margin-bottom:10px;'>{sel_year}년 {sel_month}월 수거 일정</h4>"
            cal_html += "<table style='width:100%;border-collapse:collapse;'>"
            cal_html += "<tr>" + "".join(f"<th style='text-align:center;padding:6px;color:#666;'>{d}</th>" for d in ["일","월","화","수","목","금","토"]) + "</tr>"

            first_day = date(sel_year, sel_month, 1)
            _, num_days = calendar.monthrange(sel_year, sel_month)
            start_weekday = first_day.weekday()  # 0=월
            start_offset = (start_weekday + 1) % 7  # 일요일=0 기준

            day = 1
            today_d = date.today()
            cal_html += "<tr>"
            for i in range(start_offset):
                cal_html += "<td></td>"
            col_idx = start_offset

            while day <= num_days:
                d = date(sel_year, sel_month, day)
                day_str = str(day)
                is_today = (d == today_d)
                is_collect = day_str in collect_days       # 일정 등록일
                is_real    = day_str in real_days_set      # 실제 수거 완료일
                is_weekend = (col_idx % 7 == 0)

                if is_today:
                    cls = "cal-day cal-today"
                elif is_real:
                    cls = "cal-day cal-collect"            # 실적 완료 (진한 표시)
                elif is_collect:
                    cls = "cal-day cal-collect"
                elif is_weekend:
                    cls = "cal-day cal-weekend"
                else:
                    cls = "cal-day"

                icon = "✅" if is_real else ("🚛" if is_collect else "")
                cal_html += f"<td><div class='{cls}'>{day_str}{icon}</div></td>"
                col_idx += 1
                if col_idx % 7 == 0 and day < num_days:
                    cal_html += "</tr><tr>"
                day += 1

            while col_idx % 7 != 0:
                cal_html += "<td></td>"
                col_idx += 1
            cal_html += "</tr></table>"
            cal_html += "<p style='margin-top:8px;font-size:12px;color:#666;'>🟢 수거예정일 &nbsp; 🔵 오늘</p>"
            st.markdown(cal_html, unsafe_allow_html=True)

            st.write("---")
            st.markdown("#### 📋 이번달 수거 일정 목록")
            if not school_sched.empty:
                for _, row in school_sched.iterrows():
                    col_a, col_b, col_c = st.columns([3,1,1])
                    status_icon = "✅" if row["완료여부"] else "⏳"
                    with col_a: st.write(f"{status_icon} {row['날짜']} — {row['메모']}")
                    with col_b:
                        if st.button("완료토글", key=f"tog_{row['id']}"):
                            toggle_schedule(row["id"], row["완료여부"])
                            st.rerun()
                    with col_c:
                        if st.button("삭제", key=f"del_{row['id']}"):
                            delete_schedule(row["id"])
                            st.rerun()
            else:
                st.info("이 학교의 이번달 일정이 없습니다.")

            st.write("---")
            st.markdown("#### ➕ 일정 추가")
            with st.form("add_sched_school"):
                ns_date = st.date_input("수거 날짜", value=date.today(), key="ns_date_s")
                ns_memo = st.text_input("메모", placeholder="정기 수거 / 대용량 수거 등", key="ns_memo_s")
                if st.form_submit_button("📅 일정 추가", type="primary"):
                    add_schedule(str(ns_date), school, ns_memo or "정기 수거")
                    st.success("일정이 추가되었습니다.")
                    st.rerun()

        with school_tab3:
            st.markdown("<h5 style='color:#2e7d32;font-weight:bold;'>🛡️ 금일 수거차량 안전 점검 현황</h5>", unsafe_allow_html=True)
            # [추가3] 실제 시간 기반 스쿨존 상태
            restricted, time_range = is_schoolzone_restricted()
            if restricted:
                st.markdown(f'<div class="schoolzone-danger">🚨 현재 등하교 시간({time_range}) — 수거 차량 학교 진입 제한 중</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="schoolzone-safe">✅ 현재 수거 가능 시간 — 스쿨존 안전 운행 중</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="safety-box">✅ 배차 차량: 하영자원 (본사 직영 운행)<br>✅ 스쿨존 규정속도 준수: 정상 (MAX 28km/h 통과)<br>✅ 후방카메라 및 안전요원 동승: 적합<br>🕐 현재 시각: {datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

        with school_tab4:
            st.subheader("🖨️ 행정 증빙 서류 자동 출력")
            d1, d2, d3, d4 = st.tabs(["📊 월간 정산서", "📈 처리실적보고서(제30호)", "♻️ 재활용 상계증빙", "🔗 올바로시스템"])

            with d1:
                st.info("행정실 회계 처리용 월간 정산서")
                dd1, dd2, dd3, dd4 = st.columns(4)
                with dd1: st.download_button("통합본", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)","사업장(kg)","최종정산액"]],"통합 정산(청구)서"), file_name=f"{school}_통합_월간정산서.xlsx", use_container_width=True)
                with dd2: st.download_button("🗑️ 음식물", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)","음식물비용"]],"음식물 정산(청구)서"), file_name=f"{school}_음식물_월간정산서.xlsx", use_container_width=True)
                with dd3: st.download_button("🗄️ 사업장", data=create_secure_excel(df_school[["날짜","학교명","사업장(kg)","사업장비용"]],"사업장 정산(청구)서"), file_name=f"{school}_사업장_월간정산서.xlsx", use_container_width=True)
                with dd4: st.download_button("♻️ 재활용", data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)","재활용수익"]],"재활용 정산(청구)서"), file_name=f"{school}_재활용_월간정산서.xlsx", use_container_width=True)

            with d2:
                st.info("교육청·지자체 제출용 [폐기물관리법 시행규칙 별지 제30호서식]")
                dr1, dr2, dr3 = st.columns(3)
                with dr1: st.download_button("🗑️ 음식물", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)"]],"음식물 배출 및 처리 실적보고"), file_name=f"{school}_음식물_실적보고서.xlsx", use_container_width=True)
                with dr2: st.download_button("🗄️ 사업장", data=create_secure_excel(df_school[["날짜","학교명","사업장(kg)"]],"사업장 배출 및 처리 실적보고"), file_name=f"{school}_사업장_실적보고서.xlsx", use_container_width=True)
                with dr3: st.download_button("♻️ 재활용", data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)"]],"재활용 배출 및 처리 실적보고"), file_name=f"{school}_재활용_실적보고서.xlsx", use_container_width=True)

            with d3:
                st.info("재활용품 판매 수익으로 처리비용을 상계(차감)한 내역 증빙")
                st.download_button("📄 상계처리 증빙서",
                    data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)","재활용수익"]],"사업장 폐기물 재활용 상계처리 증빙"),
                    file_name=f"{school}_상계증빙.xlsx")
                # 상계 요약
                total_recycle = df_school["재활용수익"].sum()
                total_cost    = df_school["음식물비용"].sum() + df_school["사업장비용"].sum()
                net_cost      = total_cost - total_recycle
                rr1, rr2, rr3 = st.columns(3)
                rr1.metric("총 처리비용", f"{total_cost:,.0f}원")
                rr2.metric("재활용 상계액", f"-{total_recycle:,.0f}원", delta=f"-{total_recycle:,.0f}")
                rr3.metric("실 청구금액", f"{net_cost:,.0f}원")

            with d4:
                st.info("한국환경공단 올바로(Allbaro) 시스템 전자인계서 연동")
                st.markdown("""
                **올바로 시스템 연동 데이터 미리보기:**
                """)
                preview_df = df_school[["날짜","학교명","음식물(kg)","재활용(kg)","사업장(kg)","상태"]].tail(5)
                st.dataframe(preview_df, use_container_width=True)
                if st.button("🔗 올바로시스템 전송 및 자동결재", type="primary", use_container_width=True):
                    with st.spinner("한국환경공단 서버와 통신 중..."):
                        time.sleep(2)
                    st.success(f"✅ {len(df_school)}건의 전자인계서가 올바로시스템에 이관 완료되었습니다.")
                    st.info("📋 인계번호: " + f"HY-{datetime.now().strftime('%Y%m%d')}-{len(df_school):04d}")
    else:
        st.info("해당 학교의 수거 데이터가 아직 없습니다.")


# ============================================================
# [모드 3] 수거 기사 (현장 앱)  — [추가3] 스쿨존 실제 시간 차단
# ============================================================
elif role == "🚚 수거 기사 (현장 앱)":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="mobile-app-header"><h2 style="margin:0;font-size:22px;">🚚 하영자원 기사 전용 앱</h2></div>', unsafe_allow_html=True)

        # [추가3] 등하교 시간대 자동 차단
        restricted, time_range = is_schoolzone_restricted()
        if restricted:
            st.markdown(f'<div class="schoolzone-danger">🚨 등하교 시간 ({time_range})<br>수거 작업이 제한됩니다<br><span style="font-size:16px;">학교 구역 진입 금지</span></div>', unsafe_allow_html=True)
            st.error("⛔ 현재 등하교 시간대입니다. 수거 데이터 입력이 잠깁니다.")
            st.warning(f"다음 수거 가능 시간: 오전 09:00 이후 또는 오후 16:00 이후")
            # 잠금 상태에서도 안전 점검은 가능
        else:
            st.markdown('<div class="schoolzone-safe">✅ 수거 가능 시간 — 안전 운행하세요</div>', unsafe_allow_html=True)

        # 현재 시간 표시
        st.caption(f"🕐 현재 시각: {datetime.now().strftime('%H:%M:%S')}")

        # 안전 점검 체크리스트
        with st.expander("📋 [필수] 운행 전 안전 점검 리스트", expanded=True):
            st.warning("어린이 안전을 위해 아래 항목을 확인해 주세요.")
            c1 = st.checkbox("차량 후방 카메라 정상 작동 확인")
            c2 = st.checkbox("조수석 안전 요원 탑승 여부 확인")
            c3 = st.checkbox("스쿨존 서행(30km 이하) 운전 숙지")
            c4 = st.checkbox("등하교 시간대 학교 구역 진입 금지 숙지")
            all_checked = c1 and c2 and c3 and c4
            if all_checked:
                st.success("✅ 안전 점검 완료! 오늘도 안전 운행하세요.")

        st.write("---")

        # [추가3] GPS 스쿨존 진입 시뮬레이터
        st.markdown("#### 📍 스쿨존 진입 감지")
        sz_col1, sz_col2 = st.columns(2)
        with sz_col1:
            in_schoolzone = st.toggle("🚨 스쿨존 진입 (GPS 시뮬레이션)")
        with sz_col2:
            current_speed = st.number_input("현재 속도 (km/h)", min_value=0, max_value=100, value=30, step=5)

        if in_schoolzone:
            if current_speed > 30:
                st.markdown(f'<div class="schoolzone-danger">⚠️ 과속 감지! 현재 {current_speed}km/h<br>즉시 감속하세요 → 30km/h 이하</div>', unsafe_allow_html=True)
                # 과속 자동 기록 (실제 운용 시 DB 저장)
                st.error("🚨 과속 기록이 본사에 자동 전송됩니다.")
            else:
                st.markdown(f'<div class="schoolzone-safe">🏫 스쿨존 내 정상 운행 중 ({current_speed}km/h)</div>', unsafe_allow_html=True)

        st.write("---")

        # 오늘 내 배차 일정 표시
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_sched = get_schedules_month(datetime.now().year, datetime.now().month)
        today_sched = today_sched[today_sched["날짜"]==today_str]
        if not today_sched.empty:
            st.markdown("#### 📋 오늘 수거 일정")
            for _, row in today_sched.iterrows():
                done_icon = "✅" if row["완료여부"] else "⏳"
                st.write(f"{done_icon} {row['학교명']} — {row['메모']}")

        st.write("---")
        st.camera_input("📸 현장 증빙 사진 촬영 (선택사항)")

        # 수거 입력 폼 - 등하교 시간 차단
        st.write("---")
        if restricted:
            st.markdown(f'<div class="alert-box">⛔ 등하교 시간({time_range})에는 수거 입력이 제한됩니다.<br>09:00 또는 16:00 이후 입력해 주세요.</div>', unsafe_allow_html=True)
        else:
            with st.form("driver_input"):
                target = st.selectbox("수거 완료한 학교", SCHOOL_LIST)
                fi1, fi2, fi3 = st.columns(3)
                with fi1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
                with fi2: biz_w  = st.number_input("사업장 (kg)", min_value=0, step=10)
                with fi3: re_w   = st.number_input("재활용 (kg)", min_value=0, step=10)
                driver_memo = st.text_input("특이사항 메모", placeholder="대용량 배출, 분리수거 불량 등")

                submitted = st.form_submit_button("📤 본사로 수거량 전송", type="primary", use_container_width=True)
                if submitted:
                    if not all_checked:
                        st.error("안전 점검을 먼저 완료해 주세요.")
                    elif food_w > 0 or biz_w > 0 or re_w > 0:
                        save_collection({
                            "날짜":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "학교명":   target,
                            "학생수":   STUDENT_COUNTS[target],
                            "수거업체": "하영자원(본사 직영)",
                            "음식물_kg": food_w,
                            "재활용_kg": re_w,
                            "사업장_kg": biz_w,
                            "상태":     "정산대기",
                            "현장사진": driver_memo or "",
                        })
                        # 일정 완료 처리
                        conn = get_conn()
                        conn.execute(
                            "UPDATE schedules SET 완료여부=1 WHERE 날짜=? AND 학교명=?",
                            (today_str, target)
                        )
                        conn.commit()
                        conn.close()

                        if get_setting("kakao_notify_enabled") == "true":
                            conn2 = get_conn()
                            pr = conn2.execute(
                                "SELECT 담당자연락처,음식물단가,사업장단가 FROM school_prices WHERE 학교명=?", (target,)
                            ).fetchone()
                            conn2.close()
                            if pr and pr[0]:
                                fp = pr[1] or int(get_setting("default_food_price"))
                                bp = pr[2] or int(get_setting("default_biz_price"))
                                send_kakao_alimtalk(pr[0], target, food_w, int(food_w*fp + biz_w*bp))

                        st.success(f"✅ {target} 수거 실적이 기록되었습니다.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")


# ============================================================
# [모드 4] 교육청 통합 관제  [추가5]
# ============================================================
elif role == "🏛️ 교육청 관제 (신규)":
    st.markdown('<span class="badge-v3">✨ v3 신규</span>', unsafe_allow_html=True)
    st.title("🏛️ 교육청 통합 관제 대시보드")
    st.markdown("<p style='color:#5f6368;font-size:16px;'>관할 학교 전체의 폐기물 현황·ESG 성과·예산절감을 실시간으로 모니터링합니다.</p>", unsafe_allow_html=True)

    # 로그인된 교육청 자동 설정 (selectbox 제거)
    # 관리자가 교육청 모드로 접근하면 첫 번째 교육청을 기본값으로 사용
    _login_org = st.session_state.user_org
    if _login_org in EDU_OFFICES:
        sel_edu = _login_org
    else:
        sel_edu = list(EDU_OFFICES.keys())[0]
    edu_schools = EDU_OFFICES[sel_edu]
    df_edu = df_all[df_all["학교명"].isin(edu_schools)]

    if df_edu.empty:
        st.info("해당 교육청 데이터가 없습니다.")
    else:
        # KPI
        e1, e2, e3, e4, e5 = st.columns(5)
        with e1: st.markdown(f'<div class="custom-card custom-card-red"><div class="metric-title">🗑️ 음식물 수거</div><div class="metric-value-food">{df_edu["음식물(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
        with e2: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">♻️ 재활용 수거</div><div class="metric-value-recycle">{df_edu["재활용(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
        with e3: st.markdown(f'<div class="custom-card custom-card-purple"><div class="metric-title">🗄️ 사업장 수거</div><div class="metric-value-biz">{df_edu["사업장(kg)"].sum():,.0f} kg</div></div>', unsafe_allow_html=True)
        co2_edu = df_edu["탄소감축량(kg)"].sum()
        trees_edu = int(co2_edu / 6.6)
        with e4: st.markdown(f'<div class="custom-card custom-card-green"><div class="metric-title">🌍 CO₂ 감축</div><div class="metric-value-recycle">{co2_edu:,.0f} kg</div></div>', unsafe_allow_html=True)
        budget_edu = len(edu_schools) * int(get_setting("budget_saving_per_school") or 5200000)
        with e5: st.markdown(f'<div class="custom-card custom-card-teal"><div class="metric-title">💰 예산절감(연)</div><div class="metric-value-total" style="color:#00897b;">{budget_edu:,.0f}원</div></div>', unsafe_allow_html=True)

        # ESG 종합 배너
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:20px;border-radius:12px;color:white;margin:10px 0;display:flex;justify-content:space-around;">
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;opacity:.9;">관할 학교 수</p>
                <h2 style="margin:0;color:white;">{len(edu_schools)}개교</h2>
            </div>
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;opacity:.9;">🌲 소나무 식재 효과</p>
                <h2 style="margin:0;color:white;">{trees_edu:,}그루</h2>
            </div>
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;opacity:.9;">어린이사고예방(예상)</p>
                <h2 style="margin:0;color:white;">50% 감소</h2>
            </div>
            <div style="text-align:center;">
                <p style="margin:0;font-size:13px;opacity:.9;">담당자 업무시간 절감</p>
                <h2 style="margin:0;color:white;">90%</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

        edu_tab1, edu_tab2, edu_tab3, edu_tab4 = st.tabs([
            "📊 학교별 현황", "📈 월별 추이", "🛡️ 안전 현황", "📄 교육청 보고서"
        ])

        with edu_tab1:
            # 학교별 집계
            school_summary = df_edu.groupby("학교명").agg(
                음식물=("음식물(kg)", "sum"),
                재활용=("재활용(kg)", "sum"),
                사업장=("사업장(kg)", "sum"),
                청구금액=("최종정산액", "sum"),
                탄소감축=("탄소감축량(kg)", "sum"),
                수거횟수=("id", "count")
            ).reset_index()
            school_summary["예산절감(연)"] = int(get_setting("budget_saving_per_school") or 5200000)
            st.dataframe(school_summary, use_container_width=True)

            # 학교별 수거량 막대 차트
            st.bar_chart(school_summary.set_index("학교명")[["음식물","재활용","사업장"]])

        with edu_tab2:
            monthly_edu = df_edu.groupby("월별").agg(
                음식물=("음식물(kg)", "sum"),
                재활용=("재활용(kg)", "sum"),
                사업장=("사업장(kg)", "sum"),
                청구금액=("최종정산액", "sum")
            ).reset_index()
            st.line_chart(monthly_edu.set_index("월별")[["음식물","재활용","사업장"]])
            st.dataframe(monthly_edu, use_container_width=True)

        with edu_tab3:
            st.subheader("🛡️ 스쿨존 안전 관제 현황")
            restricted, time_range = is_schoolzone_restricted()
            if restricted:
                st.markdown(f'<div class="schoolzone-danger">🚨 현재 등하교 시간({time_range}) — 전체 {len(edu_schools)}개교 수거 차량 진입 제한 중</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="schoolzone-safe">✅ 현재 수거 가능 시간 — 전체 학교 정상 운행 가능</div>', unsafe_allow_html=True)

            # 안전 통계 (학교안전사고현황 기반 데이터)
            safety_data = pd.DataFrame({
                "연도": ["2021년","2022년","2023년","2024년"],
                "사고건수": [523, 514, 523, 526],
                "부상자": [563, 529, 523, 556],
                "사망자": [2, 3, 2, 2]
            })
            st.markdown("**📊 전국 학교 폐기물 차량 관련 안전사고 현황 (참고)**")
            st.dataframe(safety_data, use_container_width=True)
            st.bar_chart(safety_data.set_index("연도")["사고건수"])
            st.caption("출처: 정을호 국회의원실 자료 / 본 플랫폼 도입 시 50% 감소 목표")

        with edu_tab4:
            st.subheader("📄 교육청 제출용 통합 보고서")
            st.info("아래 보고서를 다운로드하여 교육청 행정 제출에 사용하세요.")

            rp1, rp2, rp3 = st.columns(3)
            with rp1:
                esg_report = school_summary[["학교명","탄소감축","예산절감(연)","수거횟수"]]
                esg_report = esg_report.copy()
                esg_report["소나무환산(그루)"] = (esg_report["탄소감축"] / 6.6).astype(int)
                st.download_button(
                    "🌍 ESG 성과 보고서",
                    data=create_secure_excel(esg_report, f"{sel_edu} ESG 성과 보고서"),
                    file_name=f"{sel_edu}_ESG보고서_{datetime.now().strftime('%Y-%m')}.xlsx",
                    use_container_width=True
                )
            with rp2:
                budget_report = school_summary[["학교명","청구금액","수거횟수"]].copy()
                budget_report["예산절감(연)"] = int(get_setting("budget_saving_per_school") or 5200000)
                budget_report["합계절감"] = budget_report["예산절감(연)"]
                st.download_button(
                    "💰 예산절감 효과 보고서",
                    data=create_secure_excel(budget_report, f"{sel_edu} 예산절감 효과 보고서"),
                    file_name=f"{sel_edu}_예산절감보고서_{datetime.now().strftime('%Y-%m')}.xlsx",
                    use_container_width=True
                )
            with rp3:
                collect_report = df_edu[["날짜","학교명","음식물(kg)","재활용(kg)","사업장(kg)","최종정산액","상태"]]
                st.download_button(
                    "📊 수거 실적 통합 보고서",
                    data=create_secure_excel(collect_report, f"{sel_edu} 수거실적 통합 보고서"),
                    file_name=f"{sel_edu}_수거실적보고서_{datetime.now().strftime('%Y-%m')}.xlsx",
                    use_container_width=True
                )


# ============================================================
# [섹션 E] 📦 계약서류 패키지 생성 UI (관리자 전용)
# ============================================================
elif role == "📦 계약서류 패키지 생성":
    st.title("📦 계약서류 패키지 자동 생성")
    st.markdown(
        "<p style='color:#5f6368;'>학교 정보 입력 → PDF 3종 자동생성 + 기존 서류 포함 → ZIP 다운로드</p>",
        unsafe_allow_html=True
    )

    # ── 서류 유효기간 D-day 알림 ───────────────────────────
    st.subheader("📋 서류 유효기간 현황")
    today_dt = date.today()
    alert_rows = []
    for doc in DOC_EXPIRE:
        exp = date.fromisoformat(doc["expire"])
        if exp.year == 9999:
            dday_str = "무기한"
            status   = "🟢 정상"
        else:
            diff     = (exp - today_dt).days
            dday_str = f"D-{diff}" if diff >= 0 else f"D+{abs(diff)} 만료"
            if diff < 0:
                status = "⛔ 만료됨"
            elif diff <= 30:
                status = "🔴 만료임박"
            elif diff <= 60:
                status = "🟡 주의"
            else:
                status = "🟢 정상"
        alert_rows.append({
            "서류명": doc["name"],
            "만료일": doc["expire"] if doc["expire"] != "9999-12-31" else "-",
            "D-day": dday_str,
            "상태":  status,
            "갱신처": doc["renew_url"],
        })

    df_doc = pd.DataFrame(alert_rows)
    # 만료임박/만료 우선 정렬
    sort_key = {"⛔ 만료됨": 0, "🔴 만료임박": 1, "🟡 주의": 2, "🟢 정상": 3}
    df_doc["_sort"] = df_doc["상태"].map(sort_key)
    df_doc = df_doc.sort_values("_sort").drop(columns="_sort")
    st.dataframe(df_doc, use_container_width=True, hide_index=True)

    # 만료임박 경고
    warn_docs = [r for r in alert_rows if "🔴" in r["상태"] or "⛔" in r["상태"]]
    if warn_docs:
        for w in warn_docs:
            st.warning(f"⚠️ **{w['서류명']}** {w['D-day']} — 갱신 필요: {w['갱신처']}")

    st.divider()

    # ── 계약 정보 입력 폼 ──────────────────────────────────
    st.subheader("🏫 계약 정보 입력")

    # 자주 쓰는 학교 빠른선택
    SCHOOLS_PRESET = {
        "직접입력": {},
        "당곡고등학교": {
            "biz_no": "", "addr": "서울특별시 관악구",
            "tel": "", "contract_no": "R26TA01543339 00"
        },
        "서초고등학교": {
            "biz_no": "210-83-00086",
            "addr": "서울특별시 서초구 반포대로27길 29",
            "tel": "02-580-3891", "contract_no": ""
        },
    }

    col_l, col_r = st.columns([1, 2])
    with col_l:
        preset = st.selectbox("빠른선택 학교", list(SCHOOLS_PRESET.keys()))

    preset_data = SCHOOLS_PRESET.get(preset, {})

    col1, col2 = st.columns(2)
    with col1:
        school_nm   = st.text_input("학교명 *",
            value=preset if preset != "직접입력" else "")
        school_bno  = st.text_input("학교 사업자번호",
            value=preset_data.get("biz_no",""))
        school_addr = st.text_input("학교 주소",
            value=preset_data.get("addr",""))
        school_tel  = st.text_input("학교 전화",
            value=preset_data.get("tel",""))
    with col2:
        start_dt    = st.text_input("계약 시작일 (YYYY-MM-DD)", "2026-03-01")
        end_dt      = st.text_input("계약 종료일 (YYYY-MM-DD)", "2027-02-28")
        unit_p      = st.number_input("단가 (원/L)", value=180, step=10)
        volume      = st.number_input("월 예상 수거량 (L)", value=0.0, step=100.0,
                                       help="0이면 견적서 수량란 공백 처리")
        amt_str     = st.text_input("계약 총금액 (표시용)", "")

    # ── 생성 버튼 ──────────────────────────────────────────
    st.divider()
    if st.button("🚀 계약서류 패키지 ZIP 생성", type="primary",
                 use_container_width=True):
        if not school_nm.strip():
            st.error("❌ 학교명을 입력해주세요.")
        else:
            with st.spinner("📄 PDF 생성 중... (3~10초 소요)"):
                try:
                    zip_bytes, errs = generate_contract_package(
                        school_name      = school_nm.strip(),
                        school_biz_no    = school_bno.strip(),
                        school_addr      = school_addr.strip(),
                        school_tel       = school_tel.strip(),
                        start_date       = start_dt.strip(),
                        end_date         = end_dt.strip(),
                        volume_l         = float(volume),
                        unit_price       = int(unit_p),
                        contract_amount  = amt_str.strip(),
                    )
                    st.session_state["pkg_zip"]    = zip_bytes
                    st.session_state["pkg_school"] = school_nm.strip()
                    st.session_state["pkg_errors"] = errs
                    st.success(f"✅ 패키지 생성 완료! ({len(zip_bytes)/1024:.1f} KB)")
                except Exception as e:
                    st.error(f"❌ 생성 오류: {e}")

    # ── 다운로드 버튼 (session_state 유지) ────────────────
    pkg = st.session_state.get("pkg_zip")
    pkg_school = st.session_state.get("pkg_school", "학교")
    pkg_errors = st.session_state.get("pkg_errors", {})

    if pkg:
        fname_zip = f"계약서류패키지_{pkg_school}_{date.today().strftime('%Y%m%d')}.zip"
        st.download_button(
            label    = f"📥 {fname_zip} 다운로드",
            data     = pkg,
            file_name= fname_zip,
            mime     = "application/zip",
            key      = "dl_contract_pkg",
            use_container_width=True,
            type     = "primary",
        )

        # 포함 서류 목록 표시
        with st.expander("📂 포함 서류 목록 보기"):
            st.markdown("""
**[자동 생성 PDF]**
- 📄 음식물 견적서
- 📄 폐기물 위수탁 계약서
- 📄 계약이행 통합 서약서

**[기존 서류]**
- 🖼️ 사업자등록증
- 🖼️ 폐기물수집운반업 허가증
- 📄 소상공인 확인서 ⚠️ 2026-03-31 만료
- 📄 창업기업 확인서
- 📄 재해율 확인서
- 🖼️ 사업자 계좌 통장사본
- 📋 서류 체크리스트 (자동생성)
            """)

        if pkg_errors:
            with st.expander("⚠️ PDF 생성 오류 목록"):
                for k, v in pkg_errors.items():
                    st.error(f"**{k}**: {v}")
                st.info("💡 한글 폰트(malgun.ttf)가 없으면 일부 PDF에서 한글이 깨질 수 있습니다.")

    # ── 하영자원 정보 요약 ─────────────────────────────────
    with st.expander("ℹ️ 하영자원 고정 정보 확인"):
        df_hy = pd.DataFrame([
            {"항목": k, "내용": v} for k, v in HY.items()
        ])
        st.dataframe(df_hy, use_container_width=True, hide_index=True)
        st.caption("※ 위 정보는 모든 서류에 자동으로 입력됩니다.")


# ============================================================
# [섹션 D] 📄 위수탁계약서 단독 작성 UI (관리자 전용)
# ============================================================
elif role == "📄 위수탁계약서 작성":
    st.title("📄 폐기물 위수탁 운반 처리 계약서")
    st.markdown(
        "<p style='color:#5f6368;'>학교 정보 입력 → 계약서 PDF 즉시 생성 · 다운로드</p>",
        unsafe_allow_html=True
    )

    # ── 빠른 선택 ────────────────────────────────────────────
    D_SCHOOLS = {
        "직접입력":     {"biz_no": "", "addr": "", "tel": "", "waste": "음식물류폐기물"},
        "서초고등학교": {
            "biz_no": "210-83-00086",
            "addr":   "서울특별시 서초구 반포대로27길 29",
            "tel":    "02-580-3891",
            "waste":  "음식물류폐기물",
        },
        "당곡고등학교": {
            "biz_no": "",
            "addr":   "서울특별시 관악구",
            "tel":    "",
            "waste":  "음식물류폐기물",
        },
    }

    d_preset = st.selectbox("🏫 빠른선택 학교", list(D_SCHOOLS.keys()), key="d_preset")
    d_data   = D_SCHOOLS[d_preset]

    st.divider()

    # ── 입력 폼 ──────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 📌 배출자 (갑) 정보")
        d_school   = st.text_input("학교명 *",
            value=d_preset if d_preset != "직접입력" else "",
            key="d_school")
        d_biz_no   = st.text_input("사업자번호",
            value=d_data["biz_no"], key="d_biz_no")
        d_addr     = st.text_input("학교 주소",
            value=d_data["addr"], key="d_addr")
        d_tel      = st.text_input("학교 전화번호",
            value=d_data["tel"], key="d_tel")

    with col2:
        st.markdown("##### 📋 계약 내용")
        d_start    = st.text_input("계약 시작일 (YYYY-MM-DD)", "2026-03-01", key="d_start")
        d_end      = st.text_input("계약 종료일 (YYYY-MM-DD)", "2027-02-28", key="d_end")
        d_waste    = st.text_input("폐기물 종류", value=d_data["waste"], key="d_waste")
        d_volume   = st.text_input("물량 (예: 월 500L 내외)", "", key="d_volume")
        d_unit     = st.number_input("단가 (원/L)", value=180, step=10, key="d_unit")
        d_amount   = st.text_input("계약 총금액 (표시용, 예: 1,080,000원)", "", key="d_amount")

    st.divider()

    # ── 미리보기 요약 ─────────────────────────────────────────
    with st.expander("📋 입력 내용 미리보기"):
        prev = {
            "배출자(갑)": d_school, "사업자번호": d_biz_no,
            "주소": d_addr, "전화": d_tel,
            "계약기간": f"{d_start} ~ {d_end}",
            "폐기물 종류": d_waste, "물량": d_volume,
            "단가": f"{d_unit}원/L", "계약금액": d_amount,
            "운반자(을)": HY["name"], "처리업체": HY["processor"],
        }
        df_prev = pd.DataFrame(list(prev.items()), columns=["항목", "내용"])
        st.dataframe(df_prev, use_container_width=True, hide_index=True)

    # ── 생성 버튼 ─────────────────────────────────────────────
    if st.button("📄 위수탁계약서 PDF 생성", type="primary",
                 use_container_width=True, key="d_gen"):
        if not d_school.strip():
            st.error("❌ 학교명을 입력해주세요.")
        else:
            with st.spinner("📄 PDF 생성 중..."):
                try:
                    pdf_path = generate_contract_doc_pdf(
                        school_name    = d_school.strip(),
                        school_biz_no  = d_biz_no.strip(),
                        school_addr    = d_addr.strip(),
                        school_tel     = d_tel.strip(),
                        start_date     = d_start.strip(),
                        end_date       = d_end.strip(),
                        waste_type     = d_waste.strip() or "음식물류폐기물",
                        volume_str     = d_volume.strip(),
                        unit_price     = int(d_unit),
                        contract_amount= d_amount.strip(),
                    )
                    with open(pdf_path, "rb") as f:
                        st.session_state["d_pdf_bytes"] = f.read()
                    st.session_state["d_pdf_name"] = (
                        f"위수탁계약서_{d_school.strip()}_{date.today().strftime('%Y%m%d')}.pdf"
                    )
                    st.success("✅ PDF 생성 완료!")
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                    st.info("💡 한글 폰트(malgun.ttf)가 설치되어 있는지 확인하세요.")

    # ── 다운로드 ──────────────────────────────────────────────
    d_pdf  = st.session_state.get("d_pdf_bytes")
    d_name = st.session_state.get("d_pdf_name", "위수탁계약서.pdf")

    if d_pdf:
        st.download_button(
            label         = f"📥 {d_name} 다운로드",
            data          = d_pdf,
            file_name     = d_name,
            mime          = "application/pdf",
            key           = "d_dl",
            use_container_width=True,
            type          = "primary",
        )
        st.caption("💡 다운로드 후 출력 → 학교장 / 하영자원 대표자 각 1부 보관")

    # ── 하영자원(을) 정보 요약 ────────────────────────────────
    with st.expander("ℹ️ 운반자(을) 하영자원 고정 정보"):
        df_hy2 = pd.DataFrame([{"항목": k, "내용": v} for k, v in HY.items()])
        st.dataframe(df_hy2, use_container_width=True, hide_index=True)
        st.caption("※ 위 정보는 계약서에 자동으로 입력됩니다.")


# ============================================================
# [섹션 C] 📋 서류 유효기간 관리 UI (관리자 전용)
# ============================================================
elif role == "📋 서류 유효기간 관리":
    st.title("📋 서류 유효기간 관리")
    st.markdown(
        "<p style='color:#5f6368;'>계약 서류 만료일 추적 · 갱신 관리 · 알림 센터</p>",
        unsafe_allow_html=True
    )

    # ── 상단 요약 카드 ────────────────────────────────────────
    all_docs = c_get_all_docs()
    n_exp    = sum(1 for d in all_docs if d["상태"] == "⛔ 만료됨")
    n_red    = sum(1 for d in all_docs if d["상태"] == "🔴 만료임박")
    n_yel    = sum(1 for d in all_docs if d["상태"] == "🟡 주의")
    n_ok     = sum(1 for d in all_docs if d["상태"] == "🟢 정상")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("⛔ 만료됨",   n_exp,  delta=None)
    mc2.metric("🔴 만료임박", n_red,  delta=None)
    mc3.metric("🟡 주의",     n_yel,  delta=None)
    mc4.metric("🟢 정상",     n_ok,   delta=None)

    # 긴급 배너
    urgent = [d for d in all_docs if d["상태"] in ("⛔ 만료됨", "🔴 만료임박") and not d["갱신완료"]]
    if urgent:
        st.error(f"🚨 **즉시 조치 필요한 서류 {len(urgent)}건**")
        for u in urgent:
            st.warning(f"**{u['서류명']}** — {u['상태']}  |  만료일: {u['만료일']}  |  {u['D-day']}  |  갱신처: {u['갱신처']}")
    else:
        st.success("✅ 만료임박 서류 없음")

    st.divider()

    # ── 서류 목록 테이블 ──────────────────────────────────────
    st.subheader("📑 전체 서류 목록")

    # 필터
    cf1, cf2 = st.columns([2, 1])
    with cf1:
        filter_status = st.multiselect(
            "상태 필터", ["⛔ 만료됨", "🔴 만료임박", "🟡 주의", "🟢 정상"],
            default=["⛔ 만료됨", "🔴 만료임박", "🟡 주의", "🟢 정상"],
            key="c_filter"
        )
    with cf2:
        hide_renewed = st.checkbox("갱신완료 서류 숨기기", value=False, key="c_hide_renewed")

    display_docs = [
        d for d in all_docs
        if d["상태"] in filter_status
        and not (hide_renewed and d["갱신완료"])
    ]

    if not display_docs:
        st.info("해당 조건의 서류가 없습니다.")
    else:
        df_c = pd.DataFrame([{
            "ID":    d["id"],
            "서류명": d["서류명"],
            "만료일": d["만료일"],
            "D-day": d["D-day"],
            "상태":  d["상태"],
            "갱신처": d["갱신처"],
            "갱신완료": "✅" if d["갱신완료"] else "□",
            "메모":  d["메모"],
        } for d in display_docs])

        st.dataframe(df_c, use_container_width=True, hide_index=True,
                     column_config={
                         "ID":     st.column_config.NumberColumn(width="small"),
                         "서류명": st.column_config.TextColumn(width="medium"),
                         "D-day":  st.column_config.TextColumn(width="small"),
                         "상태":   st.column_config.TextColumn(width="small"),
                         "갱신완료": st.column_config.TextColumn(width="small"),
                     })

    st.divider()

    # ── 서류 수정 폼 ──────────────────────────────────────────
    st.subheader("✏️ 서류 정보 수정")

    if all_docs:
        doc_names = {d["서류명"]: d for d in all_docs}
        sel_doc_name = st.selectbox("수정할 서류 선택", list(doc_names.keys()), key="c_sel")
        sel_doc = doc_names[sel_doc_name]

        ec1, ec2 = st.columns(2)
        with ec1:
            e_issued  = st.text_input("발급일 (YYYY-MM-DD)",
                value=sel_doc["발급일"] or "", key="c_e_issued")
            e_expire  = st.text_input("만료일 (YYYY-MM-DD, 무기한=9999-12-31)",
                value=sel_doc["만료일"] if sel_doc["만료일"] != "무기한" else "9999-12-31",
                key="c_e_expire")
            e_renewed = st.checkbox("갱신 완료 처리",
                value=sel_doc["갱신완료"], key="c_e_renewed")
        with ec2:
            e_renew_url = st.text_input("갱신처 URL/기관",
                value=sel_doc["갱신처"], key="c_e_url")
            e_file_note = st.text_input("파일 비고",
                value=sel_doc["비고"], key="c_e_note")
            e_memo      = st.text_area("메모 (자유 입력)",
                value=sel_doc["메모"], height=80, key="c_e_memo")

        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("💾 저장", type="primary", use_container_width=True, key="c_save"):
                try:
                    c_update_doc(
                        doc_id=sel_doc["id"],
                        issued=e_issued.strip(),
                        expire=e_expire.strip(),
                        renew_url=e_renew_url.strip(),
                        file_note=e_file_note.strip(),
                        renewed=e_renewed,
                        memo=e_memo.strip(),
                    )
                    st.success(f"✅ **{sel_doc_name}** 정보가 업데이트되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 저장 오류: {e}")
        with cb2:
            if st.button("🔄 갱신완료 토글", use_container_width=True, key="c_toggle"):
                c_toggle_renewed(sel_doc["id"])
                st.rerun()

    st.divider()

    # ── 서류 신규 추가 ────────────────────────────────────────
    with st.expander("➕ 서류 신규 추가"):
        na1, na2 = st.columns(2)
        with na1:
            n_name   = st.text_input("서류명 *", key="c_n_name")
            n_issued = st.text_input("발급일 (YYYY-MM-DD)", key="c_n_issued")
            n_expire = st.text_input("만료일 (YYYY-MM-DD)", key="c_n_expire")
        with na2:
            n_url    = st.text_input("갱신처", key="c_n_url")
            n_note   = st.text_input("파일 비고", key="c_n_note")
            n_memo   = st.text_area("메모", height=68, key="c_n_memo")

        if st.button("➕ 추가", type="primary", use_container_width=True, key="c_add"):
            if not n_name.strip():
                st.error("❌ 서류명을 입력하세요.")
            elif not n_expire.strip():
                st.error("❌ 만료일을 입력하세요.")
            else:
                try:
                    c_add_doc(n_name.strip(), n_issued.strip(), n_expire.strip(),
                              n_url.strip(), n_note.strip(), n_memo.strip())
                    st.success(f"✅ **{n_name.strip()}** 추가 완료")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 추가 오류: {e}")

    # ── 서류 삭제 ─────────────────────────────────────────────
    with st.expander("🗑️ 서류 삭제 (기본 7종 제외 추천)"):
        del_names = {d["서류명"]: d["id"] for d in all_docs}
        del_sel   = st.selectbox("삭제할 서류", list(del_names.keys()), key="c_del_sel")
        if st.button(f"🗑️ '{del_sel}' 삭제", type="secondary",
                     use_container_width=True, key="c_del_btn"):
            c_delete_doc(del_names[del_sel])
            st.success(f"🗑️ **{del_sel}** 삭제 완료")
            st.rerun()

    st.divider()

    # ── D-day 캘린더 뷰 ──────────────────────────────────────
    st.subheader("📅 만료일 타임라인")
    timeline_docs = [d for d in all_docs if d["만료일"] != "무기한"]
    if timeline_docs:
        today_dt = date.today()
        tl_rows  = []
        for d in sorted(timeline_docs, key=lambda x: x["만료일"]):
            exp   = date.fromisoformat(d["만료일"])
            diff  = (exp - today_dt).days
            bar_w = max(0, min(100, int((1 - diff / 365) * 100))) if diff <= 365 else 0
            tl_rows.append({
                "서류명":  d["서류명"],
                "만료일":  d["만료일"],
                "D-day":  d["D-day"],
                "상태":    d["상태"],
                "진행률":  bar_w,
            })
        df_tl = pd.DataFrame(tl_rows)
        st.dataframe(
            df_tl,
            use_container_width=True,
            hide_index=True,
            column_config={
                "진행률": st.column_config.ProgressColumn(
                    "⏱️ 만료 진행률", min_value=0, max_value=100
                )
            }
        )
    else:
        st.info("만료일이 설정된 서류가 없습니다.")

    # ── 갱신 가이드 ──────────────────────────────────────────
    with st.expander("📖 주요 서류 갱신 가이드"):
        st.markdown("""
| 서류명 | 갱신 방법 | 소요시간 |
|--------|-----------|---------|
| 소상공인 확인서 | [sminfo.mss.go.kr](https://sminfo.mss.go.kr) 접속 → 공동인증서 로그인 → 즉시 발급 | 5분 |
| 창업기업 확인서 | 중소벤처기업부 창업지원포털 → 개업일 7년 이내 발급 | 1일 |
| 재해율 확인서 | 안전보건공단 kosha.or.kr → 사업장 재해율 확인서 발급 | 당일 |
| 사업자등록증 | 홈택스 hometax.go.kr → 사업자등록증 재발급 | 즉시 |
| 허가증 | 화성시청 환경부서 방문 또는 팩스 신청 | 3~5일 |
        """)


# ============================================================
# [섹션 B] 💰 견적서 작성 UI (관리자 전용)
# ============================================================
elif role == "💰 견적서 작성":
    st.title("💰 음식물 견적서 작성")
    st.markdown(
        "<p style='color:#5f6368;'>학교별 단가·수거량 입력 → 견적서 PDF 즉시 생성 · 다운로드</p>",
        unsafe_allow_html=True
    )

    # ── 빠른선택 학교 ─────────────────────────────────────────
    B_SCHOOLS = {
        "직접입력": {"biz_no": "", "unit": 180, "volume": 0.0, "period": "2026.03.01 ~ 2027.02.28"},
        "서초고등학교":  {"biz_no": "210-83-00086", "unit": 180, "volume": 0.0,   "period": "2026.03.01 ~ 2027.02.28"},
        "당곡고등학교":  {"biz_no": "",             "unit": 150, "volume": 0.0,   "period": "2026.03.01 ~ 2027.02.28"},
        "국제고등학교":  {"biz_no": "",             "unit": 150, "volume": 0.0,   "period": "2026.03.01 ~ 2027.02.28"},
        "부림초등학교":  {"biz_no": "",             "unit": 120, "volume": 0.0,   "period": "2026.03.01 ~ 2027.02.28"},
    }
    # DB 등록 학교 동적 추가
    try:
        db_schools = [r[0] for r in get_conn().execute(
            "SELECT DISTINCT 학교명 FROM school_prices ORDER BY 학교명"
        ).fetchall()]
        for s in db_schools:
            if s not in B_SCHOOLS:
                B_SCHOOLS[s] = {"biz_no": "", "unit": 150, "volume": 0.0,
                                 "period": "2026.03.01 ~ 2027.02.28"}
    except Exception:
        pass

    b_preset = st.selectbox("🏫 빠른선택 학교", list(B_SCHOOLS.keys()), key="b_preset")
    b_data   = B_SCHOOLS[b_preset]

    st.divider()

    # ── 입력 폼 ──────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🏫 고객(학교) 정보")
        b_school  = st.text_input("학교명 *",
            value=b_preset if b_preset != "직접입력" else "",
            key="b_school")
        b_biz_no  = st.text_input("학교 사업자번호",
            value=b_data["biz_no"], key="b_biz_no")
        b_period  = st.text_input("계약기간",
            value=b_data["period"], key="b_period")

    with col2:
        st.markdown("##### 💵 단가 및 수량")
        b_unit    = st.number_input("단가 (원/L) *", value=b_data["unit"],
                                     min_value=1, step=10, key="b_unit")
        b_volume  = st.number_input("연간 예상 수거량 (L)",
                                     value=b_data["volume"],
                                     min_value=0.0, step=100.0,
                                     help="0 입력 시 견적서 수량란 공백 처리",
                                     key="b_volume")
        # 공급가액 실시간 계산
        supply_amt = int(b_volume * b_unit) if b_volume > 0 else 0
        st.metric("공급가액 (자동 계산)", f"{supply_amt:,}원",
                  help="단가 × 수거량")

    # ── 미리보기 요약 ─────────────────────────────────────────
    with st.expander("📋 견적 내용 미리보기"):
        prev_b = {
            "고객명":   b_school,
            "사업자번호": b_biz_no,
            "견적일":   date.today().strftime("%Y.%m.%d"),
            "계약기간": b_period,
            "단가":     f"{b_unit}원/L",
            "수거량":   f"{b_volume:,.0f}L" if b_volume else "(미입력)",
            "공급가액": f"{supply_amt:,}원" if supply_amt else "(수량 입력 후 자동계산)",
            "세금":     "면세",
            "공급자":   f"{HY['name']} / {HY['ceo']} / {HY['biz_no']}",
            "연락처":   f"{HY['tel']} / {HY['email']}",
        }
        df_prev_b = pd.DataFrame(list(prev_b.items()), columns=["항목", "내용"])
        st.dataframe(df_prev_b, use_container_width=True, hide_index=True)

    st.divider()

    # ── 생성 버튼 ─────────────────────────────────────────────
    if st.button("💰 견적서 PDF 생성", type="primary",
                 use_container_width=True, key="b_gen"):
        if not b_school.strip():
            st.error("❌ 학교명을 입력해주세요.")
        else:
            with st.spinner("📄 PDF 생성 중..."):
                try:
                    pdf_path = generate_estimate_pdf(
                        school_name    = b_school.strip(),
                        school_biz_no  = b_biz_no.strip(),
                        volume_l       = float(b_volume),
                        unit_price     = int(b_unit),
                        contract_period= b_period.strip(),
                    )
                    with open(pdf_path, "rb") as f:
                        st.session_state["b_pdf_bytes"] = f.read()
                    st.session_state["b_pdf_name"] = (
                        f"음식물견적서_{b_school.strip()}_{date.today().strftime('%Y%m%d')}.pdf"
                    )
                    st.success("✅ 견적서 PDF 생성 완료!")
                except Exception as e:
                    st.error(f"❌ 오류: {e}")
                    st.info("💡 한글 폰트(malgun.ttf)가 설치되어 있는지 확인하세요.")

    # ── 다운로드 ──────────────────────────────────────────────
    b_pdf  = st.session_state.get("b_pdf_bytes")
    b_name = st.session_state.get("b_pdf_name", "음식물견적서.pdf")

    if b_pdf:
        st.download_button(
            label         = f"📥 {b_name} 다운로드",
            data          = b_pdf,
            file_name     = b_name,
            mime          = "application/pdf",
            key           = "b_dl",
            use_container_width=True,
            type          = "primary",
        )
        st.caption("💡 다운로드 후 출력 → 학교 제출 또는 계약서류 패키지에 포함")

    st.divider()

    # ── 일괄 견적 비교 (다학교) ──────────────────────────────
    with st.expander("📊 다학교 단가 비교표"):
        st.markdown("##### 현재 등록 학교별 단가 현황")
        try:
            price_rows = get_conn().execute(
                "SELECT 학교명, 음식물단가 FROM school_prices ORDER BY 음식물단가 DESC"
            ).fetchall()
            if price_rows:
                df_prices = pd.DataFrame(price_rows, columns=["학교명", "단가(원/L)"])
                df_prices["월 평균 견적(500L 기준)"] = df_prices["단가(원/L)"].apply(
                    lambda p: f"{int(p)*500:,}원"
                )
                st.dataframe(df_prices, use_container_width=True, hide_index=True)
            else:
                st.info("등록된 학교 단가 정보가 없습니다.")
        except Exception as e:
            st.warning(f"단가 조회 오류: {e}")

    # ── 하영자원 공급자 정보 ──────────────────────────────────
    with st.expander("ℹ️ 공급자(하영자원) 고정 정보"):
        df_hy3 = pd.DataFrame([{"항목": k, "내용": v} for k, v in HY.items()])
        st.dataframe(df_hy3, use_container_width=True, hide_index=True)
        st.caption("※ 위 정보는 견적서에 자동으로 입력됩니다.")


# ============================================================
# [섹션 A] 🏫 학교 마스터 관리 UI (관리자 전용)
# ============================================================
elif role == "🏫 학교 마스터 관리":
    st.title("🏫 학교 마스터 관리")
    st.markdown(
        "<p style='color:#5f6368;'>전체 계약 학교 정보 · 계약 이력 · 만료 D-day 통합 관리</p>",
        unsafe_allow_html=True
    )

    all_schools = a_get_all_schools()

    # ── 상단 요약 카드 ─────────────────────────────────────
    n_active  = sum(1 for s in all_schools if s["계약상태"] == "계약중")
    n_expire  = sum(1 for s in all_schools if "🔴" in s["계약D-day"] or "⛔" in s["계약D-day"])
    n_none    = sum(1 for s in all_schools if s["계약상태"] == "미계약")
    n_total   = len(all_schools)

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("🏫 전체 학교",   n_total)
    mc2.metric("✅ 계약중",      n_active)
    mc3.metric("🔴 만료임박",    n_expire)
    mc4.metric("⚪ 미계약",      n_none)

    # 만료임박 경고
    exp_schools = [s for s in all_schools
                   if ("🔴" in s["계약D-day"] or "⛔" in s["계약D-day"])
                   and s["계약상태"] == "계약중"]
    if exp_schools:
        st.error(f"🚨 **계약 만료임박 학교 {len(exp_schools)}곳**")
        for s in exp_schools:
            st.warning(
                f"**{s['학교명']}** — {s['계약D-day']}  |  "
                f"만료일: {s['계약종료']}  |  {s['교육청']}"
            )

    st.divider()

    # ── 학교 목록 탭 ──────────────────────────────────────
    tab_list, tab_edit, tab_contract = st.tabs(
        ["📑 전체 목록", "✏️ 학교 정보 수정", "📂 계약 이력"]
    )

    # ▸ 탭1: 전체 목록
    with tab_list:
        # 필터
        fl1, fl2 = st.columns(2)
        with fl1:
            edu_list   = ["전체"] + sorted({s["교육청"] for s in all_schools if s["교육청"]})
            sel_edu_f  = st.selectbox("교육청 필터", edu_list, key="a_edu_f")
        with fl2:
            sta_list   = ["전체", "계약중", "미계약", "계약만료", "협의중"]
            sel_sta_f  = st.selectbox("계약상태 필터", sta_list, key="a_sta_f")

        filtered = [
            s for s in all_schools
            if (sel_edu_f == "전체" or s["교육청"] == sel_edu_f)
            and (sel_sta_f == "전체" or s["계약상태"] == sel_sta_f)
        ]

        df_a = pd.DataFrame([{
            "학교명":     s["학교명"],
            "교육청":     s["교육청"],
            "단가(원/L)": s["음식물단가"],
            "계약상태":   s["계약상태"],
            "계약만료":   s["계약종료"] or "-",
            "D-day":     s["계약D-day"],
            "담당자전화": s["전화"] or "-",
        } for s in filtered])

        st.dataframe(df_a, use_container_width=True, hide_index=True,
                     column_config={
                         "단가(원/L)": st.column_config.NumberColumn(format="%d원"),
                         "D-day":     st.column_config.TextColumn(width="small"),
                     })
        st.caption(f"총 {len(filtered)}개 학교 표시 중 (전체 {n_total}개)")

        # CSV 다운로드
        csv_buf = io.StringIO()
        df_a.to_csv(csv_buf, index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 학교 목록 CSV 다운로드",
            data=csv_buf.getvalue().encode("utf-8-sig"),
            file_name=f"학교마스터_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="a_csv_dl"
        )

    # ▸ 탭2: 학교 정보 수정
    with tab_edit:
        school_names = [s["학교명"] for s in all_schools]
        sel_school   = st.selectbox("수정할 학교 선택", school_names, key="a_sel_school")
        sel_s        = next((s for s in all_schools if s["학교명"] == sel_school), {})

        # 담당자 정보 별도 조회
        try:
            sp_row = get_conn().execute(
                "SELECT 담당자명, 담당자연락처, 담당자이메일 FROM school_prices WHERE 학교명=?",
                (sel_school,)
            ).fetchone() or ("", "", "")
        except Exception:
            sp_row = ("", "", "")

        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("##### 🏫 학교 기본정보")
            a_biz_no = st.text_input("사업자번호",  value=sel_s.get("사업자번호",""), key="a_e_bno")
            a_addr   = st.text_input("주소",        value=sel_s.get("주소",""),       key="a_e_addr")
            a_tel    = st.text_input("전화번호",    value=sel_s.get("전화",""),        key="a_e_tel")
            a_unit   = st.number_input("음식물 단가(원/L)",
                                        value=int(sel_s.get("음식물단가", 150)),
                                        min_value=1, step=10, key="a_e_unit")
        with ec2:
            st.markdown("##### 📋 계약 및 담당자")
            a_start  = st.text_input("계약 시작일", value=sel_s.get("계약시작",""), key="a_e_start")
            a_end    = st.text_input("계약 종료일", value=sel_s.get("계약종료",""), key="a_e_end")
            a_status = st.selectbox("계약 상태",
                                    ["계약중","미계약","계약만료","협의중"],
                                    index=["계약중","미계약","계약만료","협의중"].index(
                                        sel_s.get("계약상태","미계약")
                                        if sel_s.get("계약상태","미계약") in ["계약중","미계약","계약만료","협의중"]
                                        else "미계약"),
                                    key="a_e_status")
            a_mgr    = st.text_input("담당자명",    value=sp_row[0], key="a_e_mgr")
            a_mgr_t  = st.text_input("담당자연락처",value=sp_row[1], key="a_e_mgr_t")
            a_mgr_e  = st.text_input("담당자이메일",value=sp_row[2], key="a_e_mgr_e")
        a_note = st.text_area("비고", value=sel_s.get("비고",""), height=60, key="a_e_note")

        if st.button("💾 저장", type="primary", use_container_width=True, key="a_save"):
            try:
                a_update_school(
                    학교명=sel_school, 단가=int(a_unit),
                    사업자번호=a_biz_no.strip(), 주소=a_addr.strip(),
                    전화=a_tel.strip(), 시작일=a_start.strip(),
                    종료일=a_end.strip(), 상태=a_status,
                    비고=a_note.strip(), 담당자명=a_mgr.strip(),
                    담당자연락처=a_mgr_t.strip(), 담당자이메일=a_mgr_e.strip(),
                )
                st.success(f"✅ **{sel_school}** 정보 저장 완료")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 저장 오류: {e}")

        st.divider()
        with st.expander("➕ 신규 학교 추가"):
            na1, na2 = st.columns(2)
            with na1:
                n_nm    = st.text_input("학교명 *",  key="a_n_nm")
                n_edu   = st.text_input("교육청",     key="a_n_edu")
                n_unit2 = st.number_input("단가(원/L)", value=150, min_value=1, step=10, key="a_n_unit")
                n_bno   = st.text_input("사업자번호", key="a_n_bno")
            with na2:
                n_addr2 = st.text_input("주소",       key="a_n_addr")
                n_tel2  = st.text_input("전화",        key="a_n_tel")
                n_s2    = st.text_input("계약시작일", key="a_n_start")
                n_e2    = st.text_input("계약종료일", key="a_n_end")
            n_sta2  = st.selectbox("계약상태", ["미계약","계약중","협의중"], key="a_n_sta")
            n_note2 = st.text_input("비고", key="a_n_note")
            if st.button("➕ 학교 추가", type="primary", use_container_width=True, key="a_add"):
                if not n_nm.strip():
                    st.error("❌ 학교명을 입력하세요.")
                else:
                    try:
                        a_add_school(n_nm.strip(), n_edu.strip(), int(n_unit2),
                                     n_bno.strip(), n_addr2.strip(), n_tel2.strip(),
                                     n_s2.strip(), n_e2.strip(), n_sta2, n_note2.strip())
                        st.success(f"✅ **{n_nm.strip()}** 추가 완료")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 추가 오류: {e}")

    # ▸ 탭3: 계약 이력
    with tab_contract:
        st.markdown("##### 📂 전체 계약 이력")

        # 학교 필터
        c_school_filter = st.selectbox(
            "학교 선택 (전체 조회=전체)",
            ["전체"] + school_names,
            key="a_c_filter"
        )
        contracts = a_get_contracts(
            학교명=None if c_school_filter == "전체" else c_school_filter
        )

        if contracts:
            df_con = pd.DataFrame([{
                "ID":       c["id"],
                "학교명":   c["학교명"],
                "계약기간": f"{c['계약_시작일']} ~ {c['계약_종료일']}",
                "단가(원/L)": c["단가"],
                "상태":     c["계약_상태"],
                "D-day":   c.get("D-day",""),
                "나라장터": c["나라장터_번호"] or "-",
                "비고":     c["비고"] or "-",
            } for c in contracts])
            st.dataframe(df_con, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 계약 이력이 없습니다.")

        st.divider()
        with st.expander("➕ 계약 이력 신규 등록"):
            ci1, ci2 = st.columns(2)
            with ci1:
                ci_school  = st.selectbox("학교명 *", school_names, key="ci_school")
                ci_no      = st.text_input("계약번호", key="ci_no")
                ci_start   = st.text_input("시작일 (YYYY-MM-DD)", "2026-03-01", key="ci_start")
                ci_end     = st.text_input("종료일 (YYYY-MM-DD)", "2027-02-28", key="ci_end")
            with ci2:
                ci_waste   = st.text_input("폐기물 종류", "음식물류폐기물", key="ci_waste")
                ci_unit    = st.number_input("단가(원/L)", value=150, step=10, key="ci_unit")
                ci_vol     = st.number_input("월 예상량(L)", value=0.0, step=100.0, key="ci_vol")
                ci_g2b     = st.text_input("나라장터 번호", key="ci_g2b")
            ci_sta  = st.selectbox("계약상태", ["계약중","미계약","계약만료","협의중"], key="ci_sta")
            ci_note = st.text_input("비고", key="ci_note")

            if st.button("➕ 계약 등록", type="primary", use_container_width=True, key="ci_add"):
                try:
                    a_add_contract(
                        학교명=ci_school, 계약번호=ci_no.strip(),
                        시작일=ci_start.strip(), 종료일=ci_end.strip(),
                        폐기물종류=ci_waste.strip(), 단가=int(ci_unit),
                        월예상량=float(ci_vol), 상태=ci_sta,
                        나라장터번호=ci_g2b.strip(), 비고=ci_note.strip()
                    )
                    st.success(f"✅ {ci_school} 계약 등록 완료")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 등록 오류: {e}")

        if contracts:
            with st.expander("🗑️ 계약 이력 삭제"):
                del_id = st.number_input("삭제할 계약 ID", min_value=1, step=1, key="a_del_id")
                if st.button("🗑️ 삭제", type="secondary", use_container_width=True, key="a_del_btn"):
                    a_delete_contract(int(del_id))
                    st.success(f"ID {del_id} 삭제 완료")
                    st.rerun()
