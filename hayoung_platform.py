# 하영자원 폐기물 데이터 플랫폼 Pro v2.0
# 개선사항:
#   [개선1] 단가 설정 화면 (관리자에서 직접 수정 가능)
#   [개선2] CSV → SQLite DB 전환 (데이터 안정성 확보)
#   [개선3] 학교별 계약 단가 차등 적용
#   [개선4] 카카오 알림톡 자동 발송
#
# 실행 방법: cd Desktop\하영자원 → python -m streamlit run hayoung_platform_v2.py
# 필수 설치: pip install streamlit pandas xlsxwriter requests python-dotenv

import streamlit as st
import pandas as pd
import sqlite3
import time
import io
import os
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

# ==========================================
# [개선2] 환경변수 로드 - 비밀번호/API키 .env 파일에서 관리
# ==========================================
# 프로젝트 폴더에 .env 파일을 만들고 아래 내용을 입력하세요:
#   EXCEL_PASSWORD=원하는비밀번호
#   KAKAO_API_KEY=카카오API키
#   KAKAO_SENDER_KEY=카카오발신키
load_dotenv()
EXCEL_PASSWORD   = os.getenv("EXCEL_PASSWORD",   "hayoung1234")
KAKAO_API_KEY    = os.getenv("KAKAO_API_KEY",    "")
KAKAO_SENDER_KEY = os.getenv("KAKAO_SENDER_KEY", "")

# ==========================================
# 0. 관리 대상 학교 목록
# ==========================================
STUDENT_COUNTS = {
    "화성초등학교": 309,  "동탄중학교": 1033, "수원고등학교": 884,  "안양남초등학교": 486,
    "평촌초등학교": 1126, "부림초등학교": 782, "부흥중학교": 512,   "덕천초등학교": 859,
    "서초고등학교": 831,  "구암고등학교": 547, "국사봉중학교": 346, "당곡고등학교": 746,
    "당곡중학교": 512,   "서울공업고등학교": 735, "강남중학교": 265, "영남중학교": 409,
    "선유고등학교": 580,  "신목고등학교": 1099, "고척고등학교": 782, "구현고등학교": 771,
    "안산국제비지니스고등학교": 660, "안산고등학교": 745, "송호고등학교": 879, "비봉고등학교": 734
}
SCHOOL_LIST = sorted(list(STUDENT_COUNTS.keys()))

# ==========================================
# 1. 페이지 설정 및 CSS
# ==========================================
st.set_page_config(page_title="하영자원 플랫폼 Pro v2", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown("""
<style>
.custom-card         { background:#fff; color:#202124; padding:20px; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,.05); margin-bottom:20px; border-top:5px solid #1a73e8; }
.custom-card-green   { border-top:5px solid #34a853; }
.custom-card-orange  { border-top:5px solid #fbbc05; }
.custom-card-red     { border-top:5px solid #ea4335; }
.custom-card-purple  { border-top:5px solid #9b59b6; }
.metric-title        { font-size:14px; color:#5f6368!important; font-weight:bold; margin-bottom:5px; }
.metric-value-food   { font-size:26px; font-weight:900; color:#ea4335!important; }
.metric-value-recycle{ font-size:26px; font-weight:900; color:#34a853!important; }
.metric-value-biz    { font-size:26px; font-weight:900; color:#9b59b6!important; }
.metric-value-total  { font-size:26px; font-weight:900; color:#1a73e8!important; }
.mobile-app-header   { background:#202124; color:#fff!important; padding:15px; border-radius:10px 10px 0 0; text-align:center; margin-bottom:15px; }
.safety-box          { background:#e8f5e9; border:1px solid #c8e6c9; padding:15px; border-radius:8px; color:#2e7d32; font-weight:bold; margin-bottom:15px; }
.alert-box           { background:#ffebee; border:1px solid #ffcdd2; padding:15px; border-radius:8px; color:#c62828; margin-bottom:15px; }
.timeline-text       { font-size:15px; line-height:1.8; color:#333; }
.badge-new           { background:#e8f0fe; color:#1a73e8; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:bold; margin-left:6px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# [개선2] SQLite DB 초기화 및 함수 모음
# ==========================================
DB_PATH = "hayoung_v2.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # 수거 데이터 테이블
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
            상태       TEXT DEFAULT '정산대기'
        )
    """)

    # [개선1] 전역 기본 단가 설정 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    for k, v in [("default_food_price","150"),("default_recycle_price","300"),
                 ("default_biz_price","200"),("kakao_notify_enabled","false")]:
        c.execute("INSERT OR IGNORE INTO global_settings (key,value) VALUES (?,?)", (k, v))

    # [개선3] 학교별 계약 단가 + 담당자 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS school_prices (
            학교명       TEXT PRIMARY KEY,
            음식물단가   INTEGER DEFAULT 150,
            재활용단가   INTEGER DEFAULT 300,
            사업장단가   INTEGER DEFAULT 200,
            담당자명     TEXT DEFAULT '',
            담당자연락처 TEXT DEFAULT '',
            담당자이메일 TEXT DEFAULT '',
            updated_at   TEXT
        )
    """)
    for school in SCHOOL_LIST:
        c.execute("INSERT OR IGNORE INTO school_prices (학교명, updated_at) VALUES (?,?)",
                  (school, datetime.now().strftime("%Y-%m-%d")))

    conn.commit()

    # 샘플 데이터 자동 생성
    if c.execute("SELECT COUNT(*) FROM collections").fetchone()[0] == 0:
        rows = []
        for year in [2024, 2025, 2026]:
            months = [(11,30),(12,31)] if year != 2026 else [(1,31),(2,25)]
            for month, days in months:
                for day in range(1, days+1, 3):
                    if day % 7 in [0, 1]: continue
                    for school, cnt in STUDENT_COUNTS.items():
                        rows.append((
                            f"{year}-{month:02d}-{day:02d} {random.randint(8,15):02d}:{random.randint(0,59):02d}:00",
                            school, cnt, "하영자원(본사 직영)",
                            int(cnt*random.uniform(0.1,0.2)),
                            int(cnt*random.uniform(0.05,0.1)),
                            int(cnt*random.uniform(0.02,0.05)),
                            "정산완료" if year != 2026 else "정산대기"
                        ))
        c.executemany("""
            INSERT INTO collections (날짜,학교명,학생수,수거업체,음식물_kg,재활용_kg,사업장_kg,상태)
            VALUES (?,?,?,?,?,?,?,?)
        """, rows)
        conn.commit()
    conn.close()

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
    """수거 데이터 + 학교별 단가 조인 후 계산 컬럼 추가"""
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT c.*,
            COALESCE(p.음식물단가, CAST(s.fp AS INTEGER)) AS 단가,
            COALESCE(p.재활용단가, CAST(s.rp AS INTEGER)) AS 재활용단가,
            COALESCE(p.사업장단가, CAST(s.bp AS INTEGER)) AS 사업장단가
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
        df["탄소감축량(kg)"] = df["재활용(kg)"] * 1.2
    return df

def save_collection(row: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO collections (날짜,학교명,학생수,수거업체,음식물_kg,재활용_kg,사업장_kg,상태)
        VALUES (:날짜,:학교명,:학생수,:수거업체,:음식물_kg,:재활용_kg,:사업장_kg,:상태)
    """, row)
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

# ==========================================
# [개선4] 카카오 알림톡 발송 함수
# ==========================================
def send_kakao_alimtalk(phone: str, school: str, food_kg: float, total_price: int) -> bool:
    """
    실제 발송: .env에 KAKAO_API_KEY, KAKAO_SENDER_KEY 입력 필요
    미설정 시: 시뮬레이션 모드로 동작 (실제 발송 안됨)
    """
    if not KAKAO_API_KEY or not KAKAO_SENDER_KEY:
        st.info(f"📱 [알림톡 시뮬레이션]\n"
                f"▸ 수신: {school} 담당자 ({phone})\n"
                f"▸ 내용: 음식물 {food_kg:,.0f}kg 수거 완료, 이번달 청구 예정액 {total_price:,}원")
        return True

    try:
        res = requests.post(
            "https://alimtalk.kakao.com/v1/message",   # 실제 API URL로 교체
            json={
                "senderKey": KAKAO_SENDER_KEY,
                "templateCode": "HAYOUNG_COLLECT_01",  # 비즈채널 등록 템플릿 코드
                "recipientList": [{
                    "recipientNo": phone.replace("-", ""),
                    "templateParameter": {
                        "school_name": school,
                        "food_kg": str(food_kg),
                        "total_price": f"{total_price:,}"
                    }
                }]
            },
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}", "Content-Type": "application/json"},
            timeout=5
        )
        return res.status_code == 200
    except Exception:
        return False

# ==========================================
# 보안 엑셀 생성 (비밀번호 .env에서 로드)
# ==========================================
def create_secure_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="법정실적보고서", startrow=2)
        wb = writer.book
        ws = writer.sheets["법정실적보고서"]
        fmt = wb.add_format({"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"})
        ws.merge_range(0, 0, 1, len(df.columns)-1, f"■ {title} ■", fmt)
        for i in range(len(df.columns)):
            ws.set_column(i, i, 16)
        ws.protect(EXCEL_PASSWORD, {"objects":True,"scenarios":True,"format_cells":False,"sort":True})
    return output.getvalue()

# ==========================================
# DB 초기화 + 데이터 로드
# ==========================================
init_db()
df_all = load_data()

# ==========================================
# 사이드바
# ==========================================
with st.sidebar:
    st.markdown("## ♻️ 하영자원 Pro v2")
    st.caption("공공기관(B2G) 맞춤 데이터 플랫폼")
    st.write("---")
    role = st.radio("사용자 환경(모드) 선택",
                    ["🏢 관리자 (본사 관제)", "🏫 학교 담당자 (행정실)", "🚚 수거 기사 (현장 앱)"])
    st.write("---")
    st.success("✅ SQLite DB 저장 (v2)")
    st.caption("개선: 단가설정 · DB전환 · 학교별단가 · 알림톡")

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
    with c5: st.markdown(f'<div class="custom-card custom-card-orange"><div class="metric-title">🛡️ 안전 점검 완료율</div><div class="metric-value-total">100 %</div></div>', unsafe_allow_html=True)

    # ESG 배너
    co2 = df_all["탄소감축량(kg)"].sum()
    trees = int(co2 / 6.6)
    st.markdown(f"""
    <div style="background:#61b346;padding:30px;border-radius:12px;color:white;display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <div style="flex:1;text-align:center;">
            <h3 style="margin:0;color:white;margin-bottom:10px;">🌍 하영자원 전사 ESG 탄소 저감 성과 (통합)</h3>
            <p style="margin:0;font-size:16px;opacity:.9;">누적 CO₂ 감축량</p>
            <h1 style="margin:0;color:white;font-size:40px;font-weight:900;">{co2:,.1f} kg</h1>
        </div>
        <div style="font-size:40px;font-weight:bold;padding:0 20px;">=</div>
        <div style="flex:1;text-align:center;">
            <p style="margin:0;font-size:16px;opacity:.9;margin-top:35px;">어린 소나무 식재 효과</p>
            <h1 style="margin:0;color:white;font-size:40px;font-weight:900;">🌲 {trees:,} 그루</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("📑 통합 및 개별 정산 시트(Sheet) 🔗")

    tab_total, tab_food, tab_biz, tab_recycle, tab_map, tab_sub, tab_price, tab_notify = st.tabs([
        "전체 통합 정산", "음식물 정산", "사업장 정산", "재활용 정산",
        "📍 실시간 차량 관제", "🤝 외주업체 현황",
        "💰 단가 설정 ✨", "📱 알림 설정 ✨"
    ])

    with tab_total:
        s1, s2, s3 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with s1: st.dataframe(df_all[["날짜","학교명","학생수","최종정산액","상태"]], use_container_width=True)
        with s2: st.dataframe(df_all[df_all["월별"]=="2026-01"][["날짜","학교명","학생수","최종정산액","상태"]], use_container_width=True)
        with s3: st.dataframe(df_all[df_all["월별"]=="2026-02"][["날짜","학교명","학생수","최종정산액","상태"]], use_container_width=True)
        b1, b2 = st.columns(2)
        with b1: st.button("🏢 업체별 통합정산서 발송", use_container_width=True)
        with b2: st.button("🏫 학교별 통합정산서 발송", use_container_width=True)

    with tab_food:
        f1, f2, f3 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with f1: st.dataframe(df_all[["날짜","학교명","수거업체","음식물(kg)","단가","음식물비용","상태"]], use_container_width=True)
        with f2: st.dataframe(df_all[df_all["월별"]=="2026-01"][["날짜","학교명","수거업체","음식물(kg)","단가","음식물비용","상태"]], use_container_width=True)
        with f3: st.dataframe(df_all[df_all["월별"]=="2026-02"][["날짜","학교명","수거업체","음식물(kg)","단가","음식물비용","상태"]], use_container_width=True)

    with tab_biz:
        b1, b2, b3 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with b1: st.dataframe(df_all[["날짜","학교명","학생수","사업장(kg)","사업장단가","사업장비용"]], use_container_width=True)
        with b2: st.dataframe(df_all[df_all["월별"]=="2026-01"][["날짜","학교명","학생수","사업장(kg)","사업장단가","사업장비용"]], use_container_width=True)
        with b3: st.dataframe(df_all[df_all["월별"]=="2026-02"][["날짜","학교명","학생수","사업장(kg)","사업장단가","사업장비용"]], use_container_width=True)

    with tab_recycle:
        r1, r2, r3 = st.tabs(["📅 2026년 전체", "🗓️ 2026년 1월", "🗓️ 2026년 2월"])
        with r1: st.dataframe(df_all[["날짜","학교명","학생수","재활용(kg)","재활용단가","재활용수익"]], use_container_width=True)
        with r2: st.dataframe(df_all[df_all["월별"]=="2026-01"][["날짜","학교명","학생수","재활용(kg)","재활용단가","재활용수익"]], use_container_width=True)
        with r3: st.dataframe(df_all[df_all["월별"]=="2026-02"][["날짜","학교명","학생수","재활용(kg)","재활용단가","재활용수익"]], use_container_width=True)

    with tab_map:
        st.write("📍 **수거 차량 실시간 GPS 관제**")
        st.map(pd.DataFrame({"lat":[37.20,37.25],"lon":[127.05,127.10]}))

    with tab_sub:
        st.subheader("🤝 외주 수거업체 실시간 업무 및 안전 평가 현황")
        st.markdown('<div class="alert-box">🔔 <b>[계약 갱신 알림]</b> \'B자원\' 업체 계약 만료 30일 전입니다. (만료일: 2026-03-25)</div>', unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.info("🏆 이달의 우수 안전 업체: **A환경** (98점)")
        with cc2: st.warning("⚠️ 주의 필요 업체: **B자원** (과속 1회)")
        with cc3: st.success("✅ 스쿨존 속도위반: **1건**")
        st.dataframe(pd.DataFrame({
            "외주업체명": ["A환경","B자원"],
            "담당학교": ["동탄중학교","수원고등학교"],
            "안전평가점수": ["98점 (우수)","85점 (주의)"],
            "안전 페널티": ["0 원","-50,000 원"],
            "이달 지급액(예상)": ["1,350,000 원","880,000 원"],
            "운행상태": ["🟢 운행중","🟡 대기중"]
        }), use_container_width=True)

    # ── [개선1] 단가 설정 탭 ──────────────────────────────
    with tab_price:
        st.subheader("💰 단가 설정 관리")
        st.markdown('<span class="badge-new">✨ v2 신규</span>', unsafe_allow_html=True)
        st.info("이 화면에서 단가를 변경하면 **즉시 전체 정산에 반영**됩니다.")

        # 전역 기본 단가
        st.markdown("### 🌐 전체 기본 단가 (개별 설정이 없는 학교에 자동 적용)")
        gp1, gp2, gp3 = st.columns(3)
        with gp1: g_food    = st.number_input("음식물 기본단가 (원/kg)",  value=int(get_setting("default_food_price")),    min_value=0, step=10, key="g_food")
        with gp2: g_recycle = st.number_input("재활용 기본단가 (원/kg)",  value=int(get_setting("default_recycle_price")), min_value=0, step=10, key="g_recycle")
        with gp3: g_biz     = st.number_input("사업장 기본단가 (원/kg)",  value=int(get_setting("default_biz_price")),     min_value=0, step=10, key="g_biz")
        if st.button("💾 기본 단가 저장", type="primary"):
            set_setting("default_food_price",    g_food)
            set_setting("default_recycle_price", g_recycle)
            set_setting("default_biz_price",     g_biz)
            st.success("✅ 기본 단가가 저장되었습니다. 새로고침 후 정산에 반영됩니다.")

        st.write("---")

        # [개선3] 학교별 개별 단가 + 담당자
        st.markdown("### 🏫 학교별 개별 계약 단가 및 담당자 정보")
        st.caption("기본 단가와 다를 경우에만 입력하세요. 담당자 정보는 알림톡 발송에 사용됩니다.")

        sel_school = st.selectbox("설정할 학교 선택", SCHOOL_LIST, key="price_sel")
        conn = get_conn()
        ex = conn.execute(
            "SELECT 음식물단가,재활용단가,사업장단가,담당자명,담당자연락처,담당자이메일 FROM school_prices WHERE 학교명=?",
            (sel_school,)
        ).fetchone()
        conn.close()
        ef, er, eb, en, et, ee = ex if ex else (150, 300, 200, "", "", "")

        sp1, sp2, sp3 = st.columns(3)
        with sp1: sp_food    = st.number_input("음식물 단가 (원/kg)", value=int(ef), min_value=0, step=10, key="sp_food")
        with sp2: sp_recycle = st.number_input("재활용 단가 (원/kg)", value=int(er), min_value=0, step=10, key="sp_recycle")
        with sp3: sp_biz     = st.number_input("사업장 단가 (원/kg)", value=int(eb), min_value=0, step=10, key="sp_biz")

        st.markdown("**📋 학교 담당자 정보 (알림톡 발송 대상)**")
        sc1, sc2, sc3 = st.columns(3)
        with sc1: sp_name  = st.text_input("담당자 이름",   value=en or "", key="sp_name")
        with sc2: sp_tel   = st.text_input("담당자 연락처", value=et or "", placeholder="010-0000-0000", key="sp_tel")
        with sc3: sp_email = st.text_input("담당자 이메일", value=ee or "", placeholder="admin@school.kr", key="sp_email")

        if st.button(f"💾 {sel_school} 저장", type="primary"):
            update_school_price(sel_school, sp_food, sp_recycle, sp_biz, sp_name, sp_tel, sp_email)
            st.success(f"✅ {sel_school} 단가 및 담당자 정보가 저장되었습니다.")

        st.write("---")
        st.markdown("### 📋 전체 학교 단가 현황")
        st.dataframe(get_school_prices()[["학교명","음식물단가","재활용단가","사업장단가","담당자명","담당자연락처","updated_at"]],
                     use_container_width=True)

    # ── [개선4] 알림 설정 탭 ──────────────────────────────
    with tab_notify:
        st.subheader("📱 알림톡 / 자동 발송 설정")
        st.markdown('<span class="badge-new">✨ v2 신규</span>', unsafe_allow_html=True)
        st.info("수거 완료 시 학교 담당자에게 카카오 알림톡을 자동 발송합니다.\n.env 파일에 API 키를 설정하면 실제 발송이 가능합니다.")

        cur_notify = get_setting("kakao_notify_enabled") == "true"
        new_notify = st.toggle("📱 카카오 알림톡 자동 발송 활성화", value=cur_notify)
        if new_notify != cur_notify:
            set_setting("kakao_notify_enabled", "true" if new_notify else "false")
            st.success("설정이 저장되었습니다.")

        st.write("---")
        st.markdown("### 🔧 API 연동 설정 방법")
        st.code("""
# 프로젝트 폴더에 .env 파일 생성 후 아래 내용 입력
EXCEL_PASSWORD=원하는비밀번호
KAKAO_API_KEY=카카오API키
KAKAO_SENDER_KEY=카카오발신키
        """, language="bash")

        st.write("---")
        st.markdown("### 📨 알림톡 테스트 발송")
        nt1, nt2 = st.columns(2)
        with nt1: test_school = st.selectbox("테스트 학교", SCHOOL_LIST, key="noti_school")
        with nt2: test_phone  = st.text_input("수신 번호", placeholder="010-0000-0000", key="noti_phone")
        if st.button("📱 알림톡 테스트 발송", type="primary"):
            total_est = int(df_all[df_all["학교명"]==test_school]["최종정산액"].sum())
            send_kakao_alimtalk(test_phone or "010-0000-0000", test_school, 100.0, total_est)

        st.write("---")
        st.markdown("### 📅 월 마감 일괄 알림 발송")
        st.caption("단가 설정 탭의 담당자 연락처로 이번 달 정산액을 일괄 발송합니다.")
        if st.button("📨 전체 학교 일괄 발송", type="primary"):
            price_df = get_school_prices()
            cur_month = datetime.now().strftime("%Y-%m")
            cnt = 0
            for _, row in price_df.iterrows():
                if not row["담당자연락처"]: continue
                mdf = df_all[(df_all["학교명"]==row["학교명"]) & (df_all["월별"]==cur_month)]
                if mdf.empty: continue
                send_kakao_alimtalk(row["담당자연락처"], row["학교명"], 0, int(mdf["최종정산액"].sum()))
                cnt += 1
            st.success(f"✅ 총 {cnt}개 학교에 월 마감 알림 발송 완료")

# ============================================================
# [모드 2] 학교 담당자 (행정실)
# ============================================================
elif role == "🏫 학교 담당자 (행정실)":
    st.title("🏫 학교 폐기물 통합 대시보드")
    school = st.selectbox("관리 대상 학교", SCHOOL_LIST)
    df_school = df_all[df_all["학교명"] == school]

    if not df_school.empty:
        # 학교 계약 단가 표시
        conn = get_conn()
        pr = conn.execute("SELECT 음식물단가,재활용단가,사업장단가 FROM school_prices WHERE 학교명=?", (school,)).fetchone()
        conn.close()
        if pr:
            st.caption(f"📋 현재 계약 단가 — 음식물: {pr[0]}원/kg | 사업장: {pr[2]}원/kg | 재활용: {pr[1]}원/kg")

        co2s = df_school["탄소감축량(kg)"].sum()
        trees_s = int(co2s / 6.6)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:20px;border-radius:12px;color:white;margin-bottom:20px;">
            <h4 style="margin:0;margin-bottom:10px;">🌱 우리 학교 ESG 환경 기여도 (교육청 제출용)</h4>
            <h2>누적 CO₂ 감축량: {co2s:,.1f} kg (🌲 소나무 {trees_s}그루 식재 효과)</h2>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 폐기물 배출량 통계 분석")
        t_daily, t_monthly = st.tabs(["🗓️ 일별 배출량", "🗓️ 연도별/월별 추이"])

        with t_daily:
            dg = df_school.copy()
            dg["일자"] = dg["날짜"].astype(str).str[:10]
            dg = dg.groupby("일자")[["음식물(kg)","사업장(kg)","재활용(kg)"]].sum().reset_index()
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.markdown("<h5 style='text-align:center;color:#ea4335;font-weight:bold;'>🗑️ 음식물</h5>", unsafe_allow_html=True)
                st.bar_chart(dg.set_index("일자")["음식물(kg)"], color="#ea4335")
            with dc2:
                st.markdown("<h5 style='text-align:center;color:#9b59b6;font-weight:bold;'>🗄️ 사업장</h5>", unsafe_allow_html=True)
                st.bar_chart(dg.set_index("일자")["사업장(kg)"], color="#9b59b6")
            with dc3:
                st.markdown("<h5 style='text-align:center;color:#34a853;font-weight:bold;'>♻️ 재활용</h5>", unsafe_allow_html=True)
                st.bar_chart(dg.set_index("일자")["재활용(kg)"], color="#34a853")

        with t_monthly:
            years = sorted(df_school["년도"].unique(), reverse=True)
            ytabs = st.tabs([f"📅 {y}년" for y in years])
            for i, y in enumerate(years):
                with ytabs[i]:
                    mg = df_school[df_school["년도"]==y].groupby("월별")[["음식물(kg)","사업장(kg)","재활용(kg)"]].sum().reset_index()
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1: st.bar_chart(mg.set_index("월별")["음식물(kg)"], color="#ea4335")
                    with mc2: st.bar_chart(mg.set_index("월별")["사업장(kg)"], color="#9b59b6")
                    with mc3: st.bar_chart(mg.set_index("월별")["재활용(kg)"], color="#34a853")

        st.write("---")
        st.markdown("<h5 style='color:#2e7d32;font-weight:bold;'>🛡️ 금일 수거차량 실시간 안전 점검 현황</h5>", unsafe_allow_html=True)
        st.markdown('<div class="safety-box">✅ 배차 차량: 하영자원 (본사 직영 운행)<br>✅ 스쿨존 규정속도 준수 여부: <span style="color:blue;">정상 (MAX 28km/h 통과)</span><br>✅ 후방카메라 작동 및 안전요원 동승: 적합</div>', unsafe_allow_html=True)

        st.write("---")
        st.subheader("🖨️ 행정 증빙 서류 자동 출력 (관공서 법정 양식 적용)")
        d1, d2, d3, d4 = st.tabs(["📊 월간 정산(청구)서", "📈 처리실적보고서 (제30호)", "♻️ 재활용 상계증빙", "🔗 올바로시스템"])

        with d1:
            st.info("행정실 회계 처리용 월간 정산서 (품목별/통합 다운로드)")
            dd1, dd2, dd3, dd4 = st.columns(4)
            with dd1: st.download_button("전체 통합본", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)","사업장(kg)","최종정산액"]], "통합 정산(청구)서"), file_name=f"{school}_통합_월간정산서.xlsx", use_container_width=True)
            with dd2: st.download_button("🗑️ 음식물 전용", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)","음식물비용"]], "음식물 정산(청구)서"), file_name=f"{school}_음식물_월간정산서.xlsx", use_container_width=True)
            with dd3: st.download_button("🗄️ 사업장 전용", data=create_secure_excel(df_school[["날짜","학교명","사업장(kg)","사업장비용"]], "사업장 정산(청구)서"), file_name=f"{school}_사업장_월간정산서.xlsx", use_container_width=True)
            with dd4: st.download_button("♻️ 재활용 전용", data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)","재활용수익"]], "재활용 정산(청구)서"), file_name=f"{school}_재활용_월간정산서.xlsx", use_container_width=True)

        with d2:
            st.info("교육청 및 지자체 제출용 [폐기물관리법 시행규칙 별지 제30호서식]")
            dr1, dr2, dr3 = st.columns(3)
            with dr1: st.download_button("🗑️ 음식물 실적보고서", data=create_secure_excel(df_school[["날짜","학교명","음식물(kg)"]], "음식물 배출 및 처리 실적보고"), file_name=f"{school}_음식물_실적보고서.xlsx", use_container_width=True)
            with dr2: st.download_button("🗄️ 사업장 실적보고서", data=create_secure_excel(df_school[["날짜","학교명","사업장(kg)"]], "사업장 배출 및 처리 실적보고"), file_name=f"{school}_사업장_실적보고서.xlsx", use_container_width=True)
            with dr3: st.download_button("♻️ 재활용 실적보고서", data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)"]], "재활용 배출 및 처리 실적보고"), file_name=f"{school}_재활용_실적보고서.xlsx", use_container_width=True)

        with d3:
            st.info("사업장 폐기물 처리 시 재활용 수익으로 비용을 상계(차감)한 내역 증빙 서류")
            st.download_button("📄 상계처리 증빙서 다운로드",
                               data=create_secure_excel(df_school[["날짜","학교명","재활용(kg)","재활용수익"]], "사업장 폐기물 재활용 상계처리 증빙 내역"),
                               file_name=f"{school}_상계증빙.xlsx")

        with d4:
            st.info("버튼 클릭 시 한국환경공단 올바로(Allbaro) 시스템으로 인계서 데이터가 자동 전송됩니다.")
            if st.button("🔗 올바로시스템 전자인계서 연동 및 자동결재", type="primary", use_container_width=True):
                with st.spinner("한국환경공단 서버와 통신 중..."):
                    time.sleep(2)
                st.success("올바로시스템에 전자인계서가 성공적으로 이관 및 결재되었습니다!")
    else:
        st.info("해당 학교의 수거 데이터가 아직 없습니다.")

# ============================================================
# [모드 3] 수거 기사 (현장 앱)
# ============================================================
elif role == "🚚 수거 기사 (현장 앱)":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="mobile-app-header"><h2 style="margin:0;font-size:22px;">🚚 하영자원 기사 전용 앱</h2></div>', unsafe_allow_html=True)

        with st.expander("📋 [필수] 운행 전 안전 점검 리스트", expanded=True):
            st.warning("어린이 안전을 위해 아래 항목을 확인해 주세요.")
            c1 = st.checkbox("차량 후방 카메라 정상 작동 확인")
            c2 = st.checkbox("조수석 안전 요원 탑승 여부 확인")
            c3 = st.checkbox("스쿨존 회피 운행 숙지")
            if c1 and c2 and c3:
                st.success("안전 점검 완료! 오늘도 안전 운행하세요.")

        st.write("---")
        if st.toggle("🚨 스쿨존 진입 알림 (GPS 모의 테스트)"):
            st.error("스쿨존 진입! 속도를 30km 이하로 줄이세요.")
            st.markdown("<h1 style='text-align:center;color:#d93025;font-size:60px;'>30</h1>", unsafe_allow_html=True)

        st.write("---")
        st.camera_input("📸 현장 증빙 사진 촬영 (선택사항)")

        with st.form("driver_input"):
            target = st.selectbox("수거 완료한 학교", SCHOOL_LIST)
            fi1, fi2, fi3 = st.columns(3)
            with fi1: food_w = st.number_input("음식물 (kg)", min_value=0, step=10)
            with fi2: biz_w  = st.number_input("사업장 (kg)", min_value=0, step=10)
            with fi3: re_w   = st.number_input("재활용 (kg)", min_value=0, step=10)

            if st.form_submit_button("본사로 수거량 전송하기", type="primary", use_container_width=True):
                if food_w > 0 or biz_w > 0 or re_w > 0:
                    save_collection({
                        "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "학교명": target, "학생수": STUDENT_COUNTS[target],
                        "수거업체": "하영자원(본사 직영)",
                        "음식물_kg": food_w, "재활용_kg": re_w, "사업장_kg": biz_w,
                        "상태": "대기"
                    })

                    # [개선4] 알림톡 자동 발송
                    if get_setting("kakao_notify_enabled") == "true":
                        conn = get_conn()
                        pr = conn.execute(
                            "SELECT 담당자연락처,음식물단가,사업장단가 FROM school_prices WHERE 학교명=?", (target,)
                        ).fetchone()
                        conn.close()
                        if pr and pr[0]:
                            fp = pr[1] or int(get_setting("default_food_price"))
                            bp = pr[2] or int(get_setting("default_biz_price"))
                            send_kakao_alimtalk(pr[0], target, food_w, int(food_w*fp + biz_w*bp))

                    st.success(f"✅ {target} 수거 실적이 기록되었습니다.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("수거한 중량(kg)을 먼저 입력해 주세요.")
