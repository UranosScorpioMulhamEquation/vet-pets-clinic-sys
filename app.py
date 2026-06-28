import streamlit as st
import sqlite3
import uuid
import os
import pandas as pd
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="نظام إدارة عيادة الحيوانات الأليفة البيطري - إعداد د. ملهم احمد")
st.markdown("<style>[data-testid='stAppViewContainer'] { direction: rtl; }</style>", unsafe_allow_html=True)

DB_PATH = "clinic.db"
KEY_FILE = "license.key"
DOC_NAME_FILE = "doctor_name.txt"

# --- دوال الحماية ---
def get_machine_id(): 
    return hex(uuid.getnode())

def generate_password_from_id(mid):
    digits = ''.join(filter(str.isdigit, mid))
    return str(round(abs(int(digits or 0) / 2 * 3.14)))[:6]

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = os.path.exists(KEY_FILE)

if not st.session_state['authenticated']:
    st.title("نظام إدارة عيادة الحيوانات الأليفة البيطري - نظام الحماية")
    st.subheader("راسل المبرمج للحصول على كلمة المرور")
    st.info(f"رقم معرف الجهاز: {get_machine_id()}")
    
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    
    if st.button("دخول"):
        if pwd == generate_password_from_id(get_machine_id()):
            with open(KEY_FILE, "w") as f: 
                f.write(pwd)
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("❌ كلمة المرور غير صحيحة. يرجى التأكد من الرقم والمحاولة مرة أخرى.")
    
    st.markdown("---")
    st.caption("للحصول على كلمة المرور، يرجى مراسلة: mulham81ahmed@gmail.com")
    st.stop()

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visits 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, visit_id TEXT, date TEXT, time TEXT, 
                  Vet_Name TEXT, animal_type TEXT, status TEXT, client_name TEXT, 
                  client_phone TEXT, Services_Prices TEXT, total REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- الوظائف ---
def get_saved_doctor():
    if os.path.exists(DOC_NAME_FILE):
        with open(DOC_NAME_FILE, "r") as f: return f.read()
    return ""

# --- الواجهة ---
st.title("نظام إدارة عيادة الحيوانات الأليفة البيطري - إعداد د. ملهم احمد")
tab1, tab2 = st.tabs(["➕ إدخال بيانات", "🔍 بحث وطباعة"])

with tab1:
    if st.button("معاملة جديدة"):
        st.session_state['visit_id'] = f"V-{uuid.uuid4().hex[:6].upper()}"
        st.session_state['show_prices'] = False
        st.session_state['temp_prices'] = {}

    if 'visit_id' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            doc_name = st.text_input("اسم الطبيب", value=get_saved_doctor())
            animal_type = st.selectbox("نوع الحيوان", ["قط", "كلب", "طائر"])
            status = st.text_area("حالة الحيوان المبدئية")
        with col2:
            client_name = st.text_input("اسم العميل")
            client_phone = st.text_input("رقم هاتف العميل")
            services_list = ["رسوم كشف بيطري", "رسوم إدارية", "رسوم إيواء", "رسوم عناية", "رسوم مستحضرات", "رسوم مستلزمات", "رسوم جراحة", "رسوم أدوية", "رسوم لقاحات", "رسوم أشعة", "رسوم تحاليل"]
            selected_services = st.multiselect("اختر الخدمات", services_list)
            tax_rate = 0.05

        if st.button("إظهار رسوم الخدمات لإدخالها"):
            st.session_state['show_prices'] = True
            with open(DOC_NAME_FILE, "w") as f: f.write(doc_name)
        
        if st.session_state.get('show_prices'):
            subtotal = 0
            temp_prices = {}
            for s in selected_services:
                temp_prices[s] = st.number_input(f"سعر {s}", min_value=0.0)
                subtotal += temp_prices[s]
            
            total_with_tax = subtotal + (subtotal * tax_rate)
            st.metric("الإجمالي مع الضريبة (5%)", f"{total_with_tax:.2f} درهم")
            
            if st.button("حفظ المعاملة"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO visits (visit_id, date, time, Vet_Name, animal_type, status, client_name, client_phone, Services_Prices, total) VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (st.session_state['visit_id'], datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%I:%M %p"), doc_name, animal_type, status, client_name, client_phone, str(temp_prices), total_with_tax))
                conn.commit()
                conn.close()
                st.success("تم الحفظ!")
                del st.session_state['visit_id']
                st.rerun()

with tab2:
    search = st.text_input("ابحث برقم الهاتف")
    if st.button("بحث الآن"):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM visits WHERE client_phone LIKE ?", conn, params=(f"%{search}%",))
        conn.close()
        if not df.empty:
            df.columns = ["رقم السجل", "رقم المعاملة", "التاريخ", "الوقت", "اسم الطبيب", "نوع الحيوان", "التشخيص", "اسم العميل", "رقم العميل", "تفاصيل الرسوم", "المجموع مع الضريبة"]
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("لم يتم العثور على نتائج.")
