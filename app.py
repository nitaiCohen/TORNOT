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
    ("ש\"ג מפקד חיפה", "02:00-06:00 & 14:00-18:00"),
    ("ש\"ג מפקד חיפה", "06:00-10:00 & 18:00-22:00"),
    ("ש\"ג מפקד חיפה", "10:00-14:00 & 22:00-02:00"),
    ("סגן מפקד חיפה", "02:00-06:00 & 14:00-18:00"),
    ("סגן מפקד חיפה", "06:00-10:00 & 18:00-22:00"),
    ("סגן מפקד חיפה", "10:00-14:00 & 22:00-02:00"),
    ("עמדה אחורית חיפה", "02:00-06:00 & 14:00-18:00"),
    ("עמדה אחורית חיפה", "06:00-10:00 & 18:00-22:00"),
    ("עמדה אחורית חיפה", "10:00-14:00 & 22:00-02:00"),
    ("ש\"ג מפקדת רכבת", "06:00-10:00 & 14:00-18:00"),
    ("ש\"ג מפקדת רכבת", "10:00-14:00 & 18:00-22:00"),
    ("סגן רכבת", "06:00-10:00 & 14:00-18:00"),
    ("סגן רכבת", "10:00-14:00 & 18:00-22:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)", "18:00-22:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)", "22:00-02:00"),
    ("מחפה קדמי חיפה (ללא סופ\"ש)", "02:00-06:00"),
    ("מחפה אחורי חיפה (סופ\"ש)", "02:00-06:00 & 14:00-18:00"),
    ("מחפה אחורי חיפה (סופ\"ש)", "06:00-10:00 & 18:00-22:00"),
    ("מחפה אחורי חיפה (סופ\"ש)", "10:00-14:00 & 22:00-02:00"),
    ("חשבשבת 1", "06:00-18:00"),
    ("חשבשבת 2", "18:00-06:00"),
    ("מאייש חול", "א-ה (תורן 1)"),
    ("מאייש חול", "א-ה (תורן 2)"),
    ("מאייש סופ\"ש", "ה-א (תורן 1)"),
    ("מאייש סופ\"ש", "ה-א (תורן 2)"),
    ("כונן סמל", "24/7"),
    ("כונן רב\"ט", "24/7"),
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

/* ── Roster table ── */
.roster-table {
    width: 100%;
    border-collapse: collapse;
    direction: rtl;
    font-size: 0.92rem;
}
.roster-table thead tr {
    background: rgba(37,99,168,.35);
}
.roster-table th {
    color: #93b4d8;
    font-weight: 700;
    padding: 10px 14px;
    text-align: right;
    border-bottom: 2px solid rgba(37,99,168,.5);
    white-space: nowrap;
}
.roster-table td {
    padding: 9px 14px;
    border-bottom: 1px solid rgba(255,255,255,.06);
    color: #dde8f8;
    vertical-align: middle;
}
.roster-table tbody tr:hover {
    background: rgba(37,99,168,.15);
}
.pos-cell {
    color: #7eb3f5 !important;
    font-weight: 700;
    white-space: nowrap;
    min-width: 160px;
}
.shift-cell {
    color: #a8c4e8 !important;
    white-space: nowrap;
    font-size: 0.85rem;
}

/* ── Week nav ── */
.week-nav {
    background: rgba(37,99,168,.2);
    border: 1px solid rgba(37,99,168,.4);
    border-radius: 10px;
    padding: 10px 14px;
    text-align: center;
    margin-top: 8px;
}
.week-label {
    color: #93b4d8;
    font-size: 0.78rem;
    margin-bottom: 4px;
}
.week-dates {
    color: #e8f0fe;
    font-weight: 700;
    font-size: 1rem;
}

/* ── Admin badge ── */
.admin-badge {
    background: rgba(74,222,128,.15);
    border: 1px solid rgba(74,222,128,.4);
    color: #4ade80;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    display: inline-block;
}

/* ── Info / success / error boxes ── */
.info-box {
    background: rgba(96,165,250,.1);
    border: 1px solid rgba(96,165,250,.35);
    color: #93c5fd;
    border-radius: 10px;
    padding: 10px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
.success-box {
    background: rgba(74,222,128,.1);
    border: 1px solid rgba(74,222,128,.35);
    color: #86efac;
    border-radius: 10px;
    padding: 10px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}
.error-box {
    background: rgba(248,113,113,.1);
    border: 1px solid rgba(248,113,113,.35);
    color: #fca5a5;
    border-radius: 10px;
    padding: 10px 16px;
    margin: 8px 0;
    font-size: 0.9rem;
}

/* ── Status badges ── */
.badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}
.badge-done  { background: rgba(74,222,128,.15); color: #4ade80; border: 1px solid rgba(74,222,128,.4); }
.badge-now   { background: rgba(96,165,250,.15); color: #60a5fa; border: 1px solid rgba(96,165,250,.4); }
.badge-plan  { background: rgba(251,146,60,.15);  color: #fb923c; border: 1px solid rgba(251,146,60,.4); }
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
    """

    prev_pos = None
    for position, shift in ROSTER_ROWS:
        key = row_key(position, shift)
        asgns = week_data.get(key, [])
        disp = assignments_display(asgns)
        pos_display = position if position != prev_pos else ""
        prev_pos = position

        table_html += f"""
        <tr>
            <td class="pos-cell">{pos_display}</td>
            <td class="shift-cell">{shift}</td>
            <td>{disp}</td>
        </tr>
        """

    table_html += """
    </tbody>
    </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)
    # ══════════════════════════════════════════════
# TAB 2 — חיפוש אישי
# ══════════════════════════════════════════════
with tabs[1]:
    st.markdown(
        '<div class="card"><div class="card-title">🔍 חיפוש תורנויות לפי שם</div>',
        unsafe_allow_html=True,
    )
    search_name = st.text_input("הזן שם מלא או חלקי", placeholder="לדוגמה: כהן")
    st.markdown("</div>", unsafe_allow_html=True)

    if search_name.strip():
        all_rows = load_all()
        found = []
        q = search_name.strip().lower()

        for r in all_rows:
            try:
                asgns = json.loads(r["assignments"])
            except:
                continue

            monday = date.fromisoformat(r["week_monday"])

            for a in asgns:
                if q in a.get("name", "").lower():
                    frm = a.get("from", "")
                    to = a.get("to", "")
                    period = f"{frm}–{to}" if frm and to else "כל השבוע"

                    found.append({
                        "שבוע": f"{fmt(monday)} – {fmt(monday + timedelta(days=6))}",
                        "עמדה": r["position"],
                        "סבב": r["shift"],
                        "תקופה": period,
                        "סטטוס": week_status(monday),
                        "_monday": monday,
                    })

        if not found:
            st.markdown(
                f'<div class="error-box">לא נמצאו תורנויות עבור "{search_name}".</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="success-box">נמצאו {len(found)} תורנויות עבור "{search_name}"</div>',
                unsafe_allow_html=True,
            )

            table_html = """
            <div class="card">
            <table class="roster-table">
            <thead>
                <tr>
                    <th>שבוע</th>
                    <th>עמדה</th>
                    <th>סבב</th>
                    <th>תקופה</th>
                    <th>סטטוס</th>
                </tr>
            </thead>
            <tbody>
            """

            for f in sorted(found, key=lambda x: x["_monday"], reverse=True):
                bc = {
                    "בוצע": "badge-done",
                    "נוכחי": "badge-now",
                    "מתוכנן": "badge-plan",
                }[f["סטטוס"]]

                table_html += f"""
                <tr>
                    <td>{f['שבוע']}</td>
                    <td>{f['עמדה']}</td>
                    <td>{f['סבב']}</td>
                    <td>{f['תקופה']}</td>
                    <td><span class='badge {bc}'>{f['סטטוס']}</span></td>
                </tr>
                """

            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — שיבוץ (מנהל)
# ══════════════════════════════════════════════
if st.session_state.is_admin:
    with tabs[2]:
        week_data = load_week(current_monday.isoformat())
        future = is_future(current_monday)

        st.markdown(f"""
        <div class="card">
            <div class="card-title">✏️ שיבוץ שבועי — {fmt(week_dates[0])} עד {fmt(week_dates[6])}</div>
        </div>
        """, unsafe_allow_html=True)

        if future:
            st.markdown(
                '<div class="info-box">📅 שבוע עתידי — שיבוץ לתכנון</div>',
                unsafe_allow_html=True,
            )

        st.markdown("#### בחר עמדה וסבב לשיבוץ")
        row_options = [f"{pos} | {shft}" for pos, shft in ROSTER_ROWS]
        selected_row_str = st.selectbox("עמדה | סבב", row_options)
        sel_idx = row_options.index(selected_row_str)
        sel_pos, sel_shift = ROSTER_ROWS[sel_idx]
        sel_key = row_key(sel_pos, sel_shift)
        current_assignments = week_data.get(sel_key, [])

        if current_assignments:
            st.markdown(
                f'<div class="info-box">שיבוץ נוכחי: <strong>{assignments_display(current_assignments)}</strong></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="info-box">אין שיבוץ לסבב זה עדיין</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        use_split = st.toggle("פיצול שמירה (יותר מחייל אחד בסבב זה)", value=False)
        new_assignments = []
        split_valid = True
        st.markdown("---")

        btn1, btn2 = st.columns(2)

        with btn1:
            if st.button("💾 שמור שיבוץ", use_container_width=True):
                if not new_assignments:
                    st.error("יש למלא לפחות חייל אחד")
                elif use_split and not split_valid:
                    st.error("יש לתקן את שדות הפיצול לפני השמירה")
                else:
                    save_row(current_monday, sel_pos, sel_shift, new_assignments)
                    st.success("השיבוץ נשמר בהצלחה")
                    st.rerun()

        with btn2:
            if st.button("🗑️ נקה שיבוץ", use_container_width=True):
                delete_row(current_monday, sel_pos, sel_shift)
                st.success("השיבוץ נמחק")
                st.rerun()

        st.markdown("---")
        st.markdown("#### סיכום שיבוצים לשבוע זה")

        week_data = load_week(current_monday.isoformat())

        summary_html = """
        <div class="card">
        <table class="roster-table">
        <thead>
            <tr>
                <th>עמדה</th>
                <th>סבב</th>
                <th>חייל</th>
            </tr>
        </thead>
        <tbody>
        """

        prev_p = None
        for position, shift in ROSTER_ROWS:
            key = row_key(position, shift)
            asgns = week_data.get(key, [])
            disp = assignments_display(asgns)

            if disp == "—":
                continue

            pos_d = position if position != prev_p else ""
            prev_p = position

            summary_html += f"""
            <tr>
                <td class='pos-cell'>{pos_d}</td>
                <td class='shift-cell'>{shift}</td>
                <td>{disp}</td>
            </tr>
            """

        summary_html += "</tbody></table></div>"
        st.markdown(summary_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:rgba(255,255,255,.25);font-size:.78rem;padding:10px 0">'
    'מערכת ניהול תורנויות • גזרה אזרחית'
    '</div>',
    unsafe_allow_html=True,
)
