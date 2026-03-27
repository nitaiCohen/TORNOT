import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- הגדרות בסיסיות ---
st.set_page_config(page_title="ניהול תורנויות - גזרה אזרחית", layout="wide")

DB_DIR = "archive"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

SETTINGS_FILE = "shift_settings.csv"
ADMIN_PASSWORD = "1234"

# --- פונקציות עזר לתאריכים ---
def get_monday_to_monday(date_obj):
    monday = date_obj - timedelta(days=date_obj.weekday())
    next_monday = monday + timedelta(days=7)
    return monday.strftime("%d.%m.%Y"), next_monday.strftime("%d.%m.%Y"), monday.strftime("%Y-%m-%d")

@st.cache_data(ttl=600)
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            df = pd.read_csv(SETTINGS_FILE)
            if not df.empty:
                return {row['עמדה']: [row['שעות'], row['כמות']] for _, row in df.iterrows()}
        except: pass
    
    return {
        "ש\"ג מפקד חיפה": ["02:00-06:00 & 14:00-18:00, 06:00-10:00 & 18:00-22:00, 10:00-14:00 & 22:00-02:00", 1],
        "סגן מפקד חיפה": ["02:00-06:00 & 14:00-18:00, 06:00-10:00 & 18:00-22:00, 10:00-14:00 & 22:00-02:00", 1],
        "עמדה אחורית חיפה": ["02:00-06:00 & 14:00-18:00, 06:00-10:00 & 18:00-22:00, 10:00-14:00 & 22:00-02:00", 1],
        "ש\"ג מפקדת רכבת": ["06:00-10:00 & 14:00-18:00, 10:00-14:00 & 18:00-22:00", 1],
        "סגן רכבת": ["06:00-10:00 & 14:00-18:00, 10:00-14:00 & 18:00-22:00", 1],
        "מחפה קדמי חיפה (ללא סופש)": ["18:00-22:00, 22:00-02:00, 02:00-06:00", 1],
        "מחפה אחורי חיפה (סופ\"ש)": ["02:00-06:00 & 14:00-18:00, 06:00-10:00 & 18:00-22:00, 10:00-14:00 & 22:00-02:00", 1],
        "חשבשבת 1": ["06:00-18:00", 1],
        "חשבשבת 2": ["18:00-06:00", 1],
        "מאייש חול": ["א-ה", 2], 
        "מאייש סופ\"ש": ["ה-א", 2],
        "כונן סמל": ["24/7", 1],
        "כונן רב\"ט": ["24/7", 1]
    }

def save_settings(settings_dict):
    data = [{"עמדה": k, "שעות": v[0], "כמות": v[1]} for k, v in settings_dict.items()]
    pd.DataFrame(data).to_csv(SETTINGS_FILE, index=False)
    st.cache_data.clear()

def load_assignments(file_id):
    path = os.path.join(DB_DIR, f"{file_id}.csv")
    if os.path.exists(path):
        return pd.read_csv(path).set_index('key')['name'].to_dict()
    return {}

def save_assignments(file_id, data):
    path = os.path.join(DB_DIR, f"{file_id}.csv")
    df = pd.DataFrame([{"key": k, "name": v} for k, v in data.items()])
    df.to_csv(path, index=False)

def global_search_soldier(name):
    all_results = []
    current_monday_str = get_monday_to_monday(datetime.now())[2]
    if not os.path.exists(DB_DIR): return pd.DataFrame()
    for filename in os.listdir(DB_DIR):
        if filename.endswith(".csv"):
            date_str = filename.replace(".csv", "")
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            m1, m2, _ = get_monday_to_monday(dt)
            df = pd.read_csv(os.path.join(DB_DIR, filename), usecols=['key', 'name'])
            matches = df[df['name'].str.contains(name, na=False, case=False)]
            for _, row in matches.iterrows():
                parts = row['key'].split(' | ')
                status = "נוכחי" if date_str == current_monday_str else ("בוצע" if date_str < current_monday_str else "מתוכנן")
                all_results.append({
                    "טווח תאריכים": f"{m1} - {m2}",
                    "עמדה": parts[0],
                    "שעות/סבב": parts[1] if len(parts) > 1 else "שיבוץ כללי",
                    "סטטוס": status,
                    "סדר": date_str
                })
    return pd.DataFrame(all_results)

# --- ניהול מצב הניווט (Session State) ---
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# --- Sidebar ---
with st.sidebar:
    st.header("🔐 אזור ניהול")
    if not st.session_state.admin_mode:
        pwd = st.text_input("סיסמת מנהל:", type="password")
        if st.button("התחבר"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.rerun()
    else:
        if st.button("יציאה מניהול"):
            st.session_state.admin_mode = False
            st.rerun()
    
    st.divider()
    st.header("📅 ניווט בשבועות")
    
    # כפתור חזרה להיום
    if st.button("🏠 חזרה לשבוע הנוכחי"):
        st.session_state.current_date = datetime.now()
        st.rerun()
        
    # חיצי ניווט
    col_prev, col_next = st.columns(2)
    if col_prev.button("⬅️ שבוע קודם"):
        st.session_state.current_date -= timedelta(days=7)
        st.rerun()
    if col_next.button("שבוע הבא ➡️"):
        st.session_state.current_date += timedelta(days=7)
        st.rerun()
    
    # לוח שנה (לגיבוי)
    st.session_state.current_date = st.date_input("בחר תאריך ספציפי:", st.session_state.current_date)
    
    start_date, end_date, file_id = get_monday_to_monday(st.session_state.current_date)
    
    # בדיקה האם השבוע עתידי
    current_monday_val = datetime.now() - timedelta(days=datetime.now().weekday())
    selected_monday_val = datetime.strptime(file_id, "%Y-%m-%d")
    is_future = selected_monday_val > current_monday_val

# --- תוכן ראשי ---
st.title("📅 מערכת תורנויות")

# חיפוש אישי
search_name = st.text_input("🔍 חיפוש אישי (שם מלא):")
if search_name:
    res = global_search_soldier(search_name)
    if not res.empty:
        st.dataframe(res.sort_values("סדר", ascending=False).drop(columns=["סדר"]), use_container_width=True, hide_index=True)

st.divider()

# טאבים
if st.session_state.admin_mode:
    t_assign, t_manage = st.tabs(["📝 שיבוץ ורישום", "⚙️ ניהול עמדות"])
else:
    t_assign, = st.tabs(["📋 לוח תורנויות שבועי"])

with t_assign:
    status_label = "🔮 תכנון עתידי" if is_future else "📅 רישום ביצוע"
    st.subheader(f"{status_label}: {start_date} עד {end_date}")
    
    cur_assigns = load_assignments(file_id)
    settings = load_settings()
    
    if st.session_state.admin_mode:
        with st.expander("🛠️ כלי שיבוץ"):
            c_in, _ = st.columns([1, 2])
            with c_in:
                names_raw = st.text_area("רשימת שמות (אחד בשורה):")
                names_list = [n.strip() for n in names_raw.split('\n') if n.strip()]
                sel_pos = st.selectbox("עמדה:", list(settings.keys()))
                
                if not is_future:
                    h_str, q = settings[sel_pos]
                    slots = [f"{h.strip()}{' (תורן ' + str(i+1) + ')' if int(q) > 1 else ''}" 
                             for h in h_str.split(',') for i in range(int(q))]
                    sel_slot = st.selectbox("בחר סבב שעות:", slots)
                else:
                    _, q = settings[sel_pos]
                    slots = [f"שיבוץ כללי (חייל {i+1})" for i in range(int(q))]
                    sel_slot = st.selectbox("בחר תקן לשיבוץ:", slots)
                
                sel_soldier = st.selectbox("חייל:", names_list if names_list else ["--"])
                if st.button("שמור"):
                    cur_assigns[f"{sel_pos} | {sel_slot}"] = sel_soldier
                    save_assignments(file_id, cur_assigns)
                    st.rerun()

    # הצגת הטבלה
    full_table = []
    for pos, (h_str, q) in settings.items():
        if not is_future:
            for h in [x.strip() for x in h_str.split(',')]:
                for i in range(int(q)):
                    suffix = f" (תורן {i+1})" if int(q) > 1 else ""
                    key = f"{pos} | {h}{suffix}"
                    full_table.append({"עמדה": pos, "שעות/סבב": f"{h}{suffix}", "חייל": cur_assigns.get(key, "---")})
        else:
            for i in range(int(q)):
                key = f"{pos} | שיבוץ כללי (חייל {i+1})"
                full_table.append({"עמדה": pos, "שעות/סבב": f"תקן {i+1} (כללי)", "חייל": cur_assigns.get(key, "---")})
    
    st.table(pd.DataFrame(full_table))

if st.session_state.admin_mode:
    with t_manage:
        st.subheader("ניהול עמדות קבועות")
        # כלי הוספה
        with st.expander("➕ הוסף עמדה חדשה"):
            c1, c2, c3 = st.columns([2, 3, 1])
            n_name = c1.text_input("שם עמדה:")
            n_hours = c2.text_input("שעות (למשל 02-06, 06-10):")
            n_qty = c3.number_input("כמות תורנים:", min_value=1, value=1)
            if st.button("הוסף"):
                s = load_settings(); s[n_name] = [n_hours, n_qty]; save_settings(s); st.rerun()
        
        # עריכת קיימות
        curr_s = load_settings()
        for s_name in list(curr_s.keys()):
            cols = st.columns([2, 4, 1, 0.5])
            h, q = curr_s[s_name]
            new_h = cols[1].text_input(f"שעות {s_name}", value=h, key=f"h_{s_name}")
            new_q = cols[2].number_input(f"תקן {s_name}", value=int(q), min_value=1, key=f"q_{s_name}")
            if new_h != h or new_q != q:
                curr_s[s_name] = [new_h, new_q]; save_settings(curr_s)
            if cols[3].button("🗑️", key=f"d_{s_name}"):
                del curr_s[s_name]; save_settings(curr_s); st.rerun()