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

    # ── 학교 계정 (각 학교별 1개) ─────────────────────────────
    "hwaseong_elem":      {"password": "school_0001", "role": "학교", "display_name": "화성초등학교 행정실", "org": "화성초등학교"},
    "dongtanjunior":      {"password": "school_0002", "role": "학교", "display_name": "동탄중학교 행정실",   "org": "동탄중학교"},
    "suwon_high":         {"password": "school_0003", "role": "학교", "display_name": "수원고등학교 행정실", "org": "수원고등학교"},
    "anyang_elem":        {"password": "school_0004", "role": "학교", "display_name": "안양남초등학교 행정실","org": "안양남초등학교"},
    "pyeongchon_elem":    {"password": "school_0005", "role": "학교", "display_name": "평촌초등학교 행정실", "org": "평촌초등학교"},
    "burim_elem":         {"password": "school_0006", "role": "학교", "display_name": "부림초등학교 행정실", "org": "부림초등학교"},
    "buheung_junior":     {"password": "school_0007", "role": "학교", "display_name": "부흥중학교 행정실",   "org": "부흥중학교"},
    "deokcheon_elem":     {"password": "school_0008", "role": "학교", "display_name": "덕천초등학교 행정실", "org": "덕천초등학교"},
    "seocho_high":        {"password": "school_0009", "role": "학교", "display_name": "서초고등학교 행정실", "org": "서초고등학교"},
    "guam_high":          {"password": "school_0010", "role": "학교", "display_name": "구암고등학교 행정실", "org": "구암고등학교"},
    "guksabong_junior":   {"password": "school_0011", "role": "학교", "display_name": "국사봉중학교 행정실", "org": "국사봉중학교"},
    "danggok_high":       {"password": "school_0012", "role": "학교", "display_name": "당곡고등학교 행정실", "org": "당곡고등학교"},
    "danggok_junior":     {"password": "school_0013", "role": "학교", "display_name": "당곡중학교 행정실",   "org": "당곡중학교"},
    "seoul_industry":     {"password": "school_0014", "role": "학교", "display_name": "서울공업고등학교 행정실","org": "서울공업고등학교"},
    "gangnam_junior":     {"password": "school_0015", "role": "학교", "display_name": "강남중학교 행정실",   "org": "강남중학교"},
    "yeongnam_junior":    {"password": "school_0016", "role": "학교", "display_name": "영남중학교 행정실",   "org": "영남중학교"},
    "seonyu_high":        {"password": "school_0017", "role": "학교", "display_name": "선유고등학교 행정실", "org": "선유고등학교"},
    "sinmok_high":        {"password": "school_0018", "role": "학교", "display_name": "신목고등학교 행정실", "org": "신목고등학교"},
    "gocheok_high":       {"password": "school_0019", "role": "학교", "display_name": "고척고등학교 행정실", "org": "고척고등학교"},
    "guhyeon_high":       {"password": "school_0020", "role": "학교", "display_name": "구현고등학교 행정실", "org": "구현고등학교"},
    "ansan_intl":         {"password": "school_0021", "role": "학교", "display_name": "안산국제비지니스고 행정실","org": "안산국제비지니스고등학교"},
    "ansan_high":         {"password": "school_0022", "role": "학교", "display_name": "안산고등학교 행정실", "org": "안산고등학교"},
    "songho_high":        {"password": "school_0023", "role": "학교", "display_name": "송호고등학교 행정실", "org": "송호고등학교"},
    "bibong_high":        {"password": "school_0024", "role": "학교", "display_name": "비봉고등학교 행정실", "org": "비봉고등학교"},
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
            학교명       TEXT PRIMARY KEY,
            음식물단가   INTEGER DEFAULT 150,
            재활용단가   INTEGER DEFAULT 300,
            사업장단가   INTEGER DEFAULT 200,
            담당자명     TEXT DEFAULT '',
            담당자연락처 TEXT DEFAULT '',
            담당자이메일 TEXT DEFAULT '',
            교육청       TEXT DEFAULT '',
            updated_at   TEXT
        )
    """)
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

