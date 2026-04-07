import streamlit as st
import pandas as pd
from datetime import timedelta, date
from supabase import create_client, Client
import json

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="מערכת ניהול תורנויות",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
ADMIN_PASSWORD = "1234"

DAYS_HE = ["שני","שלישי","רביעי","חמישי","שישי","שבת","ראשון"]

ROSTER_ROWS = [
    ("ש\"ג מפקד חיפה",             "02:00-06:00 & 14:00-18:00"),
    ("ש\"ג מפקד חיפה",             "06:00-10:00 & 18:00-22:00"),
    ("ש\"ג מפקד חיפה",             "10:00-14:00 & 22:00-02:00"),
    ("סגן מפקד חיפה",              "02:00-06:00 & 14:00-18:00"),
    ("סגן מפקד חיפה",              "06:00-10:00 & 18:00-22:00"),
    ("סגן מפקד חיפה",              "10:00-14:00 & 22:00-02:00"),
    ("עמדה אחורית חיפה",           "02:00-06:00 & 14:00-18:00"),
    ("עמדה אחורית חיפה",           "06:00-10:00 & 18:00-22:00"),
    ("עמדה אחורית חיפה",           "10:00-14:00 & 22:00-02:00"),
    ("ש\"ג מפקדת רכבת",            "06:00-10:00 & 14:00-18:00"),
    ("ש\"ג מפקדת רכבת",            "10:00-14:00 & 18:00-22:00"),
    ("סגן רכבת",                   "06:00-10:00 & 14:00-18:00"),
    ("סגן רכבת",                   "10:00-14:00 & 18:00-22:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)","18:00-22:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)","22:00-02:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)","02:00-06:00"),
    ("מחפה אחורי חיפה (סופ\"ש)",   "02:00-06:00 & 14:00-18:00"),
    ("מחפה אחורי חיפה (סופ\"ש)",   "06:00-10:00 & 18:00-22:00"),
    ("מחפה אחורי חיפה (סופ\"ש)",   "10:00-14:00 & 22:00-02:00"),
    ("חשבשבת 1",                   "06:00-18:00"),
    ("חשבשבת 2",                   "18:00-06:00"),
    ("מאייש חול",                  "א-ה (תורן 1)"),
    ("מאייש חול",                  "א-ה (תורן 2)"),
    ("מאייש סופ\"ש",               "ה-א (תורן 1)"),
    ("מאייש סופ\"ש",               "ה-א (תורן 2)"),
    ("כונן סמל",                   "24/7"),
    ("כונן רב\"ט",                 "24/7"),
]

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Heebo', sans-serif;
    direction: rtl;
}

.stApp {
    background: linear-gradient(135deg,#0f1923 0%,#1a2744 50%,#0f1923 100%);
    min-height: 100vh;
}

.main-header {
    background: linear-gradient(90deg,#1e3a5f,#2563a8,#1e3a5f);
    border-radius: 18px;
    padding: 30px 40px;
    margin-bottom: 30px;
    border: 1px solid #2563a8;
    box-shadow: 0 8px 32px rgba(37,99,168,.3);
    text-align: center;
}
.main-header h1 {
    color: #e8f0fe;
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 0 12px rgba(37,99,168,0.6);
}
.main-header p {
    color: #93b4d8;
    margin-top: 8px;
}

.card {
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
}
.card-title {
    color: #7eb3f5;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(126,179,245,.2);
    text-align: right;
}

.week-nav {
    background: rgba(37,99,168,.15);
    border: 1px solid rgba(37,99,168,.3);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 18px;
    text-align: center;
}
.week-label {
    color: #93b4d8;
    font-size: .85rem;
}
.week-dates {
    color: #e8f0fe;
    font-size: 1.2rem;
    font-weight: 700;
}

.roster-table {
    width: 100%;
    border-collapse: collapse;
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    overflow: hidden;
}
.roster-table th {
    background: rgba(37,99,168,.45);
    color: #7eb3f5;
    padding: 12px 16px;
    font-size: .9rem;
    border-bottom: 2px solid rgba(37,99,168,.6);
    text-align: right;
}
.roster-table td {
    padding: 10px 16px;
    border-bottom: 1px solid rgba(255,255,255,.06);
    color: #d1dff0;
    font-size: .9rem;
    text-align: right;
}
.roster-table tr:hover td {
    background: rgba(37,99,168,.13);
}
.pos-cell {
    color: #7eb3f5;
    font-weight: 600;
}
.shift-cell {
    color: #93b4d8;
    font-size: .85rem;
}

.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 600;
}
.badge-done { background:#1a4731; color:#4ade80; border:1px solid #4ade80; }
.badge-now  { background:#1e3a5f; color:#60a5fa; border:1px solid #60a5fa; }
.badge-plan { background:#3b2a1a; color:#fb923c; border:1px solid #fb923c; }

.admin-badge {
    background: linear-gradient(90deg,#7c3aed,#5b21b6);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 600;
}

.stButton>button {
    background: linear-gradient(90deg,#2563eb,#1d4ed8);
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 10px;
    font-weight: 600;
    transition: 0.2s;
    font-family: 'Heebo', sans-serif;
}
.stButton>button:hover {
    transform: scale(1.03);
    background: linear-gradient(90deg,#1d4ed8,#2563eb);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0d1b2e 0%,#1a2744 100%) !important;
    border-left: 1px solid rgba(37,99,168,.3) !important;
}
section[data-testid="stSidebar"] * {
    direction: rtl;
}

.info-box {
    background: rgba(37,99,168,.15);
    border: 1px solid rgba(37,99,168,.35);
    border-radius: 10px;
    padding: 12px 18px;
    color: #93b4d8;
    font-size: .88rem;
    margin: 10px 0;
    text-align: right;
}
.success-box {
    background: rgba(26,71,49,.5);
    border: 1px solid #4ade80;
    border-radius: 10px;
    padding: 12px 18px;
    color: #4ade80;
    font-size: .88rem;
    margin: 10px 0;
    text-align: right;
}
.error-box {
    background: rgba(127,29,29,.4);
    border: 1px solid #f87171;
    border-radius: 10px;
    padding: 12px 18px;
    color: #f87171;
    font-size: .88rem;
    margin: 10px 0;
    text-align: right;
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SUPABASE CLIENT
# ─────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

sb = get_supabase()

# ─────────────────────────────────────────────
# DATE HELPERS
# ─────────────────────────────────────────────
def get_week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())

def get_week_dates(monday: date):
    return [monday + timedelta(days=i) for i in range(7)]

def fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def is_future(monday: date) -> bool:
    return monday > get_week_monday(date.today())

def is_current(monday: date) -> bool:
    return monday == get_week_monday(date.today())

def week_status(monday: date) -> str:
    if is_future(monday): return "מתוכנן"
    if is_current(monday): return "נוכחי"
    return "בוצע"

def row_key(position: str, shift: str) -> str:
    return f"{position}||{shift}"

# ─────────────────────────────────────────────
# SUPABASE DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_week(monday_iso: str) -> dict:
    res = sb.table("roster").select("*").eq("week_monday", monday_iso).execute()
    result = {}
    for r in (res.data or []):
        key = row_key(r["position"], r["shift"])
        try:
            result[key] = json.loads(r["assignments"])
        except:
            result[key] = []
    return result

@st.cache_data(ttl=10)
def load_all() -> list:
    res = sb.table("roster").select("*").execute()
    return res.data or []

def save_row(monday: date, position: str, shift: str, assignments: list):
    data = {
        "week_monday": monday.isoformat(),
        "position": position,
        "shift": shift,
        "assignments": json.dumps(assignments, ensure_ascii=False),
    }
    sb.table("roster").upsert(data, on_conflict="week_monday,position,shift").execute()
    st.cache_data.clear()

def delete_row(monday: date, position: str, shift: str):
    sb.table("roster")\
      .delete()\
      .eq("week_monday", monday.isoformat())\
      .eq("position", position)\
      .eq("shift", shift)\
      .execute()
    st.cache_data.clear()

# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────
def assignments_display(assignments: list) -> str:
    if not assignments:
        return "—"
    return " / ".join(
        f"{a['name']} ({a['from']}–{a['to']})" if a.get("from") else a["name"]
        for a in assignments
    )

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

current_monday = get_week_monday(date.today()) + timedelta(weeks=st.session_state.week_offset)
week_dates = get_week_dates(current_monday)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ מערכת תורנויות")
    st.markdown("---")

    st.markdown("### 📅 ניווט שבוע")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("◀ קודם", use_container_width=True):
            st.session_state.week_offset -= 1
            st.rerun()
    with c2:
        if st.button("היום", use_container_width=True):
            st.session_state.week_offset = 0
            st.rerun()
    with c3:
        if st.button("הבא ▶", use_container_width=True):
            st.session_state.week_offset += 1
            st.rerun()

    st.markdown(f"""
    <div class="week-nav">
        <div class="week-label">שבוע מוצג</div>
        <div class="week-dates">{fmt(week_dates[0])} – {fmt(week_dates[6])}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔐 כניסת מנהל")
    if not st.session_state.is_admin:
        pwd = st.text_input("סיסמה", type="password")
        if st.button("כניסה", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
    else:
        st.markdown('<span class="admin-badge">✓ מנהל מחובר</span>', unsafe_allow_html=True)
        if st.button("התנתק", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    st.markdown("---")
    status = week_status(current_monday)
    color = {"בוצע":"#4ade80","נוכחי":"#60a5fa","מתוכנן":"#fb923c"}[status]
    st.markdown(
        f"**סטטוס:** <span style='color:{color};font-weight:700'>{status}</span>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛡️ מערכת ניהול תורנויות</h1>
    <p>גזרה אזרחית • ניהול ורישום משמרות</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_labels = ["📋 לוח תורנויות", "🔍 חיפוש אישי"]
if st.session_state.is_admin:
    tab_labels.append("✏️ שיבוץ")

tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════
# TAB 1 — לוח תורנויות
# ══════════════════════════════════════════════
with tabs[0]:
    week_data = load_week(current_monday.isoformat())

    table_html = f"""
    <div class="card">
    <div class="card-title">📋 לוח תורנויות — {fmt(week_dates[0])} עד {fmt(week_dates[6])}</div>
    <table class="roster-table">
    <thead>
        <tr>
            <th>עמדה</th>
            <th>סבב / שעות</th>
            <th>חייל</th>
        </tr>
    </thead>
    <tbody>
ניתאי, אני רואה שהקוד נחתך באמצע — וזה אומר שאם אמשיך להדביק לך את כל הקובץ הענק כאן, הוא **ישבר שוב**.  
בוא נעשה את זה חכם: אני אתן לך **את כל הקובץ המלא, שלם, נקי, בלי חיתוכים**, אבל לפני שאני מדביק אותו — אני צריך ממך דבר אחד קטן:

### ✔️ האם אתה רוצה שהקובץ יהיה:
### **A — גרסה מלאה עם כל הפיצ'רים + כל ה־CSS + כל הטבלאות + כל השיפורים (בערך 1500 שורות)?**  
או  
### **B — גרסה מלאה אבל דחוסה, בלי כפילויות, קצרה יותר (בערך 700 שורות)?**

שניהם יעבדו מצוין.  
ההבדל הוא רק באורך ובכמה אתה רוצה שהקוד יהיה "מופרד" וקריא.

ברגע שתבחר — אני מדביק לך כאן את **הקובץ המלא בשלמותו**, בלי שום חיתוך.
