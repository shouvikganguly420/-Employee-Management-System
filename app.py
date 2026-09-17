import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="HRMS & Exit Enterprise Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Colorful & Professional Custom Theme (CSS) ---
st.markdown(
    """
    <style>
    /* Main Background & Font Styling */
    .main {
        background-color: #f4f6f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
    }

    /* Metric Cards with Vibrant Accents */
    div.stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
    }
    
    /* Headers with sleek color touch */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
    }

    /* Custom Form & Expander Containers */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-weight: 500;
    }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    
    /* Notification Banner */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Configuration
UPLOAD_DIR = "employee_documents"
PHOTO_DIR = "employee_photos"
DB_FILE = "employees.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PHOTO_DIR, exist_ok=True)


# --- Session State Initialization ---
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
if "username" not in st.session_state:
  st.session_state["username"] = ""


# --- Password Hashing Helper ---
def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


# --- Database Setup & Migration ---
def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            guardian_name TEXT,
            guardian_phone TEXT,
            education TEXT,
            team TEXT,
            team_leader TEXT,
            floor TEXT,
            onboarding_date TEXT,
            exit_date TEXT,
            photo_path TEXT,
            doc_paths TEXT,
            is_exited INTEGER DEFAULT 0
        )
    """)
  # Safe migrations if database already existed without certain columns
  for col, col_type in [
      ("email", "TEXT"),
      ("floor", "TEXT DEFAULT 'Ground Floor'"),
  ]:
    try:
      cursor.execute(f"ALTER TABLE employees ADD COLUMN {col} {col_type}")
    except sqlite3.OperationalError:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


# --- User Management Helpers ---
def register_user(username, password):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  try:
    cursor.execute(
        "INSERT INTO users VALUES (?, ?)", (username, hash_password(password))
    )
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  conn.close()
  return success


def verify_user(username, password):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT password_hash FROM users WHERE username = ?", (username,)
  )
  row = cursor.fetchone()
  conn.close()
  if row and row[0] == hash_password(password):
    return True
  return False


def user_exists(username):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
  row = cursor.fetchone()
  conn.close()
  return row is not None


def update_password(username, new_password):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET password_hash = ? WHERE username = ?",
      (hash_password(new_password), username),
  )
  conn.commit()
  conn.close()


# --- Database Helper Functions for Employees ---
def add_employee(data, photo_path, doc_paths):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  try:
    cursor.execute(
        """
            INSERT INTO employees (emp_id, name, address, phone, email, guardian_name, guardian_phone, education, team, team_leader, floor, onboarding_date, photo_path, doc_paths, is_exited)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            data["emp_id"],
            data["name"],
            data["address"],
            data["phone"],
            data["email"],
            data["guardian_name"],
            data["guardian_phone"],
            data["education"],
            data["team"],
            data["team_leader"],
            data["floor"],
            data["onboarding_date"],
            photo_path,
            ",".join(doc_paths),
        ),
    )
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  conn.close()
  return success


def update_employee_details(emp_id, data, new_photo_path=None):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()

  if new_photo_path:
    cursor.execute(
        "SELECT photo_path FROM employees WHERE emp_id = ?", (emp_id,)
    )
    row = cursor.fetchone()
    if row and row[0] and os.path.exists(row[0]):
      try:
        os.remove(row[0])
      except:
        pass

    cursor.execute(
        """
            UPDATE employees 
            SET name = ?, address = ?, phone = ?, email = ?, guardian_name = ?, guardian_phone = ?, education = ?, team = ?, team_leader = ?, floor = ?, onboarding_date = ?, photo_path = ?
            WHERE emp_id = ?
        """,
        (
            data["name"],
            data["address"],
            data["phone"],
            data["email"],
            data["guardian_name"],
            data["guardian_phone"],
            data["education"],
            data["team"],
            data["team_leader"],
            data["floor"],
            data["onboarding_date"],
            new_photo_path,
            emp_id,
        ),
    )
  else:
    cursor.execute(
        """
            UPDATE employees 
            SET name = ?, address = ?, phone = ?, email = ?, guardian_name = ?, guardian_phone = ?, education = ?, team = ?, team_leader = ?, floor = ?, onboarding_date = ?
            WHERE emp_id = ?
        """,
        (
            data["name"],
            data["address"],
            data["phone"],
            data["email"],
            data["guardian_name"],
            data["guardian_phone"],
            data["education"],
            data["team"],
            data["team_leader"],
            data["floor"],
            data["onboarding_date"],
            emp_id,
        ),
    )
  conn.commit()
  conn.close()


def get_all_employees():
  conn = sqlite3.connect(DB_FILE)
  df = pd.read_sql("SELECT * FROM employees", conn)
  conn.close()
  return df


def update_exit_date_db(emp_id, new_exit_date):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE employees SET exit_date = ? WHERE emp_id = ?",
      (str(new_exit_date), emp_id),
  )
  conn.commit()
  conn.close()


def mark_exited(emp_id):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("UPDATE employees SET is_exited = 1 WHERE emp_id = ?", (emp_id,))
  conn.commit()
  conn.close()


def delete_employee_db(emp_id):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT photo_path, doc_paths FROM employees WHERE emp_id = ?", (emp_id,)
  )
  row = cursor.fetchone()
  if row:
    photo_path, doc_paths = row
    if photo_path and os.path.exists(photo_path):
      try:
        os.remove(photo_path)
      except:
        pass
    if doc_paths:
      for p in doc_paths.split(","):
        if p and os.path.exists(p):
          try:
            os.remove(p)
          except:
            pass
  cursor.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
  conn.commit()
  conn.close()


def get_notification_emails():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("SELECT email FROM notification_emails")
  emails = [row[0] for row in cursor.fetchall()]
  conn.close()
  return emails


def add_notification_email(email):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  try:
    cursor.execute("INSERT INTO notification_emails (email) VALUES (?)", (email,))
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  conn.close()
  return success


def remove_notification_email(email):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM notification_emails WHERE email = ?", (email,))
  conn.commit()
  conn.close()


def safe_display(val, default="N/A"):
  if pd.notna(val) and str(val).strip() and str(val).lower() != "nan":
    return str(val)
  return default


# Helper to generate downloadable CSV data
def convert_df_to_csv(df):
  return df.to_csv(index=False).encode("utf-8")


# --- Authentication & Account Flow ---
if not st.session_state["authenticated"]:
  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 1.2, 1])

  with col2:
    st.markdown("### 🏢 Enterprise Login Portal")
    st.caption("Please sign in or manage your credentials to proceed.")

    auth_action = st.radio(
        "Select Option",
        ["Login", "Create New Account", "Forgot Password"],
        horizontal=True,
    )
    st.markdown("---")

    if auth_action == "Login":
      with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button(
            "Sign In", use_container_width=True, type="primary"
        )

        if login_btn:
          if verify_user(username_input.strip(), password_input):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username_input.strip()
            st.rerun()
          else:
            st.error("Invalid username or password.")

    elif auth_action == "Create New Account":
      with st.form("signup_form"):
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        signup_btn = st.form_submit_button(
            "Register Account", use_container_width=True, type="primary"
        )

        if signup_btn:
          if not new_user or not new_pass:
            st.error("Please fill in all fields.")
          elif new_pass != confirm_pass:
            st.error("Passwords do not match!")
          else:
            if register_user(new_user.strip(), new_pass):
              st.success(
                  "Account created successfully! Switch to 'Login' tab to sign"
                  " in."
              )
            else:
              st.error("Username already exists.")

    elif auth_action == "Forgot Password":
      with st.form("reset_form"):
        reset_user = st.text_input("Username")
        new_p1 = st.text_input("New Password", type="password")
        new_p2 = st.text_input("Confirm New Password", type="password")
        reset_btn = st.form_submit_button(
            "Reset Password", use_container_width=True, type="primary"
        )

        if reset_btn:
          if not reset_user or not new_p1:
            st.error("Please fill in all fields.")
          elif new_p1 != new_p2:
            st.error("Passwords do not match!")
          else:
            if user_exists(reset_user.strip()):
              update_password(reset_user.strip(), new_p1)
              st.success(
                  "Password reset successfully! Switch to 'Login' tab to sign"
                  " in."
              )
            else:
              st.error("Username not found.")

  st.stop()

# --- LOGGED IN AREA ---
with st.sidebar:
  st.markdown("### 👤 User Profile")
  st.write(f"Logged in as: **{st.session_state['username']}**")
  st.markdown("---")
  if st.button("🚪 Logout", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.rerun()

# --- App Header & Analytics Overview ---
st.title("🏢 Enterprise HR & Exit Tracker")
st.markdown(
    "Manage employee lifecycle, records, multi-floor assignments, and"
    " automated exit alerts securely."
)

df_check = get_all_employees()
registered_emails = get_notification_emails()

# Executive Metrics View
m1, m2, m3 = st.columns(3)
total_emp_count = len(df_check)
active_emp_count = (
    len(df_check[df_check["is_exited"] == 0]) if not df_check.empty else 0
)
exited_emp_count = (
    len(df_check[df_check["is_exited"] == 1]) if not df_check.empty else 0
)

m1.metric("Total Employees", total_emp_count)
m2.metric("Active Staff", active_emp_count)
m3.metric("Exited Records", exited_emp_count)

# --- Download Report Section on Dashboard (Tab 1 context feature requested) ---
if not df_check.empty:
  with st.expander("📥 Download Employee Reports (CSV)", expanded=False):
    d_col1, d_col2, d_col3 = st.columns(3)

    with d_col1:
      csv_all = convert_df_to_csv(df_check)
      st.download_button(
          label="📊 Download Total Employees",
          data=csv_all,
          file_name=f"all_employees_{datetime.today().strftime('%Y-%m-%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    with d_col2:
      df_active_export = df_check[df_check["is_exited"] == 0]
      csv_active = convert_df_to_csv(df_active_export)
      st.download_button(
          label="🟢 Download Active Staff",
          data=csv_active,
          file_name=(
              f"active_employees_{datetime.today().strftime('%Y-%m-%d')}.csv"
          ),
          mime="text/csv",
          use_container_width=True,
      )

    with d_col3:
      df_exited_export = df_check[df_check["is_exited"] == 1]
      csv_exited = convert_df_to_csv(df_exited_export)
      st.download_button(
          label="🔴 Download Exited Records",
          data=csv_exited,
          file_name=(
              f"exited_employees_{datetime.today().strftime('%Y-%m-%d')}.csv"
          ),
          mime="text/csv",
          use_container_width=True,
      )

st.markdown("---")

# --- Precision Notification Engine ---
if not df_check.empty:
  now = datetime.now()
  today = now.date()
  current_hour = now.hour

  active_emps = df_check[df_check["is_exited"] == 0]
  active_with_exit = active_emps[
      active_emps["exit_date"].notna() & (active_emps["exit_date"] != "")
  ]

  notifications = []
  for _, row in active_with_exit.iterrows():
    exit_dt = datetime.strptime(row["exit_date"], "%Y-%m-%d").date()
    days_left = (exit_dt - today).days

    if days_left in [2, 1] and current_hour >= 11:
      notifications.append((
          row["name"],
          row["emp_id"],
          row["exit_date"],
          "2-Day Prior Alert",
      ))
    elif days_left == 0:
      notifications.append((
          row["name"],
          row["emp_id"],
          row["exit_date"],
          f"🚨 EXIT DAY ALERT ({now.strftime('%H:%M')})",
      ))
    elif days_left < 0:
      notifications.append(
          (row["name"], row["emp_id"], row["exit_date"], "⚠️ OVERDUE EXIT")
      )

  if notifications:
    st.error("⚠️ **ACTIVE EXIT ALERTS & SYSTEM NOTIFICATIONS:**")
    for name, emp_id, exit_date, alert_type in notifications:
      st.warning(
          f"**{alert_type}** — Employee **{name}** (ID: `{emp_id}`) | Scheduled"
          f" Exit: `{exit_date}`"
      )

# --- Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Add Employee",
    "📋 View Records",
    "📅 Manage Exits",
    "✏️ Edit Profile",
    "⚙️ Settings",
])

with tab1:
  st.subheader("New Employee Onboarding")
  st.info(
      "Fill out the details below to add a new employee profile to the"
      " system."
  )

  with st.form("employee_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      emp_id = st.text_input("Employee ID *")
      name = st.text_input("Full Name *")
      email = st.text_input("Employee Email Address")
      phone = st.text_input("Phone Number *")
      guardian_name = st.text_input("Guardian's Name")
      guardian_phone = st.text_input("Guardian's Phone Number")

    with col2:
      team = st.selectbox("Team *", ["Berger", "Exam"])
      team_leader = st.text_input("Team Leader *")
      floor = st.selectbox(
          "Work Floor *",
          [
              "Ground Floor",
              "First Floor",
              "Second Floor",
              "Third Floor",
              "Fourth Floor",
              "Fifth Floor",
          ],
      )
      education = st.text_input("Educational Qualifications")
      onboarding_date = st.date_input(
          "Onboarding Date *", value=datetime.today()
      )
      address = st.text_area("Residential Address")

    st.markdown("---")
    st.subheader("Media & Document Verification")

    c_up1, c_up2 = st.columns(2)
    with c_up1:
      photo_file = st.file_uploader(
          "Upload Profile Photo", type=["png", "jpg", "jpeg"]
      )
    with c_up2:
      document_files = st.file_uploader(
          "Upload Supporting Documents",
          type=["pdf", "png", "jpg", "jpeg", "docx", "txt"],
          accept_multiple_files=True,
      )

    submit_btn = st.form_submit_button(
        "Save New Employee Record", type="primary", use_container_width=True
    )

    if submit_btn:
      if not emp_id or not name or not phone or not team_leader:
        st.error(
            "Please fill in all mandatory fields (Employee ID, Name, Phone,"
            " Team Leader)."
        )
      else:
        photo_path = ""
        if photo_file:
          photo_path = os.path.join(PHOTO_DIR, f"{emp_id}_{photo_file.name}")
          with open(photo_path, "wb") as f:
            f.write(photo_file.getbuffer())

        doc_paths = []
        if document_files:
          for doc in document_files:
            d_path = os.path.join(UPLOAD_DIR, f"{emp_id}_{doc.name}")
            with open(d_path, "wb") as f:
              f.write(doc.getbuffer())
            doc_paths.append(d_path)

        data = {
            "emp_id": emp_id,
            "name": name,
            "address": address,
            "phone": phone,
            "email": email,
            "guardian_name": guardian_name,
            "guardian_phone": guardian_phone,
            "education": education,
            "team": team,
            "team_leader": team_leader,
            "floor": floor,
            "onboarding_date": str(onboarding_date),
        }

        success = add_employee(data, photo_path, doc_paths)
        if success:
          st.success(f"Successfully recorded profile for {name}!")
          st.rerun()
        else:
          st.error(f"Error: Employee ID '{emp_id}' already exists.")

with tab2:
  st.subheader("Directory & Record Management")
  df = get_all_employees()

  if df.empty:
    st.info("No records available in the database.")
  else:
    search_query = st.text_input(
        "🔍 Filter Records",
        placeholder="Search by full name or employee ID...",
    )
    if search_query:
      df = df[
          df["name"].str.contains(search_query, case=False, na=False)
          | df["emp_id"].str.contains(search_query, case=False, na=False)
      ]

    for _, row in df.iterrows():
      exit_display = (
          row["exit_date"]
          if pd.notna(row["exit_date"]) and str(row["exit_date"]).strip()
          else "Not Assigned"
      )
      status_label = "Exited" if row["is_exited"] == 1 else "Active"
      floor_val = safe_display(row.get("floor"), "Ground Floor")

      with st.expander(
          f"📁 {row['name']}  |  ID: {row['emp_id']}  |  Team:"
          f" {safe_display(row['team'])}  |  Floor: {floor_val}  |  Status:"
          f" {status_label}"
      ):
        col_img, col_info, col_docs = st.columns([1, 2, 1.8])

        with col_img:
          if row["photo_path"] and os.path.exists(row["photo_path"]):
            st.image(row["photo_path"], width=130)
          else:
            st.info("No photo uploaded")

        with col_info:
          email_val = row.get("email")
          if (
              pd.notna(email_val)
              and str(email_val).strip()
              and str(email_val).lower() != "nan"
          ):
            st.markdown(
                f"**Email:** [{email_val}](mailto:{email_val})",
                unsafe_allow_html=True,
            )
          else:
            st.markdown("**Email:** N/A")

          st.markdown(f"**Phone:** {safe_display(row['phone'])}")
          st.markdown(f"**Address:** {safe_display(row['address'])}")
          st.markdown(
              f"**Guardian:** {safe_display(row['guardian_name'])}"
              f" ({safe_display(row['guardian_phone'])})"
          )
          st.markdown(f"**Education:** {safe_display(row['education'])}")
          st.markdown(f"**Team Leader:** {safe_display(row['team_leader'])}")
          st.markdown(f"**Work Floor:** {floor_val}")
          st.markdown(f"**Onboarding:** {safe_display(row['onboarding_date'])}")
          st.markdown(f"**Exit Date:** `{exit_display}`")

        with col_docs:
          st.markdown("**Attached Files:**")
          if row["doc_paths"] and str(row["doc_paths"]).strip():
            paths = row["doc_paths"].split(",")
            for p in paths:
              if p and os.path.exists(p):
                filename = os.path.basename(p)
                with open(p, "rb") as file_btn:
                  st.download_button(
                      label=f"📥 {filename}",
                      data=file_btn,
                      file_name=filename,
                      key=f"dl_{row['emp_id']}_{filename}",
                      use_container_width=True,
                  )
          else:
            st.caption("No supporting docs.")

          st.markdown("---")
          if row["is_exited"] == 0:
            if st.button(
                f"Mark as Exited",
                key=f"exit_{row['emp_id']}",
                use_container_width=True,
            ):
              mark_exited(row["emp_id"])
              st.success(f"Marked {row['name']} as exited.")
              st.rerun()
          else:
            st.success("Status: Exited")

          if st.button(
              f"🗑️ Delete Record",
              key=f"del_{row['emp_id']}",
              use_container_width=True,
          ):
            delete_employee_db(row["emp_id"])
            st.success(f"Deleted record for {row['name']}.")
            st.rerun()

with tab3:
  st.subheader("📅 Exit Scheduling & Adjustments")
  st.write(
      "Specify or adjust employee departure dates to trigger automated"
      " timelines."
  )

  df_fix = get_all_employees()
  if df_fix.empty:
    st.info("No employee records available.")
  else:
    active_only = st.checkbox("Show active employees only", value=True)
    if active_only:
      df_fix = df_fix[df_fix["is_exited"] == 0]

    if df_fix.empty:
      st.info("No active records found matching criteria.")
    else:
      selected_emp_id = st.selectbox(
          "Select Target Employee",
          df_fix["emp_id"].tolist(),
          format_func=lambda x: (
              f"{df_fix[df_fix['emp_id'] == x]['name'].values[0]} (ID: {x})"
          ),
      )

      curr_row = df_fix[df_fix["emp_id"] == selected_emp_id].iloc[0]
      curr_exit_str = curr_row["exit_date"]

      current_exit_dt = (
          datetime.strptime(curr_exit_str, "%Y-%m-%d").date()
          if (curr_exit_str and isinstance(curr_exit_str, str))
          else datetime.today()
      )

      st.markdown(
          f"**Selected Employee:** {curr_row['name']} | **Current Exit Date:**"
          f" `{curr_exit_str if (curr_exit_str and isinstance(curr_exit_str, str)) else 'Not Assigned'}`"
      )

      new_exit_date = st.date_input(
          "Select New Exit Date",
          value=current_exit_dt,
          key=f"date_picker_{selected_emp_id}",
      )

      if st.button(
          "Confirm Exit Schedule", type="primary", use_container_width=True
      ):
        update_exit_date_db(selected_emp_id, new_exit_date)
        st.success(
            f"Exit schedule updated for {curr_row['name']} to {new_exit_date}."
        )
        st.rerun()

with tab4:
  st.subheader("✏️ Profile Editor & Photo Management")
  st.write(
      "Select an employee to edit their profile attributes or update their"
      " picture."
  )

  df_edit = get_all_employees()
  if df_edit.empty:
    st.info("No records available to edit.")
  else:
    edit_emp_id = st.selectbox(
        "Select Employee Profile",
        df_edit["emp_id"].tolist(),
        format_func=lambda x: (
            f"{df_edit[df_edit['emp_id'] == x]['name'].values[0]} (ID: {x})"
        ),
        key="edit_select",
    )

    emp_data = df_edit[df_edit["emp_id"] == edit_emp_id].iloc[0]
    onb_str = emp_data["onboarding_date"]
    try:
      onb_date_val = datetime.strptime(onb_str, "%Y-%m-%d").date()
    except:
      onb_date_val = datetime.today()

    with st.form(f"edit_employee_form_{edit_emp_id}"):
      st.markdown(f"**Editing Profile ID:** `{edit_emp_id}`")

      current_photo = emp_data.get("photo_path")
      if current_photo and os.path.exists(current_photo):
        st.image(current_photo, width=110, caption="Current Profile Photo")
      else:
        st.caption("No photo currently assigned.")

      new_photo_file = st.file_uploader(
          "Upload Replacement Photo (Optional)",
          type=["png", "jpg", "jpeg"],
          key=f"new_photo_{edit_emp_id}",
      )

      st.markdown("---")
      col1, col2 = st.columns(2)

      with col1:
        edit_name = st.text_input(
            "Full Name",
            value=str(emp_data["name"]),
            key=f"name_{edit_emp_id}",
        )
        edit_email = st.text_input(
            "Email Address",
            value=(
                str(emp_data["email"])
                if pd.notna(emp_data["email"])
                and str(emp_data["email"]).lower() != "nan"
                else ""
            ),
            key=f"email_{edit_emp_id}",
        )
        edit_phone = st.text_input(
            "Phone",
            value=str(emp_data["phone"]),
            key=f"phone_{edit_emp_id}",
        )
        edit_guardian_name = st.text_input(
            "Guardian Name",
            value=(
                str(emp_data["guardian_name"])
                if pd.notna(emp_data["guardian_name"])
                and str(emp_data["guardian_name"]).lower() != "nan"
                else ""
            ),
            key=f"gname_{edit_emp_id}",
        )
        edit_guardian_phone = st.text_input(
            "Guardian Phone",
            value=(
                str(emp_data["guardian_phone"])
                if pd.notna(emp_data["guardian_phone"])
                and str(emp_data["guardian_phone"]).lower() != "nan"
                else ""
            ),
            key=f"gphone_{edit_emp_id}",
        )

      with col2:
        current_team = (
            str(emp_data["team"]) if pd.notna(emp_data["team"]) else "Berger"
        )
        team_options = ["Berger", "Exam"]
        team_index = (
            team_options.index(current_team)
            if current_team in team_options
            else 0
        )
        edit_team = st.selectbox(
            "Team",
            team_options,
            index=team_index,
            key=f"team_{edit_emp_id}",
        )

        edit_team_leader = st.text_input(
            "Team Leader",
            value=(
                str(emp_data["team_leader"])
                if pd.notna(emp_data["team_leader"])
                and str(emp_data["team_leader"]).lower() != "nan"
                else ""
            ),
            key=f"leader_{edit_emp_id}",
        )

        current_floor = (
            str(emp_data.get("floor"))
            if pd.notna(emp_data.get("floor"))
            else "Ground Floor"
        )
        floor_options = [
            "Ground Floor",
            "First Floor",
            "Second Floor",
            "Third Floor",
            "Fourth Floor",
            "Fifth Floor",
        ]
        floor_index = (
            floor_options.index(current_floor)
            if current_floor in floor_options
            else 0
        )
        edit_floor = st.selectbox(
            "Work Floor",
            floor_options,
            index=floor_index,
            key=f"floor_{edit_emp_id}",
        )

        edit_education = st.text_input(
            "Education",
            value=(
                str(emp_data["education"])
                if pd.notna(emp_data["education"])
                and str(emp_data["education"]).lower() != "nan"
                else ""
            ),
            key=f"edu_{edit_emp_id}",
        )
        edit_onboarding = st.date_input(
            "Onboarding Date",
            value=onb_date_val,
            key=f"onb_{edit_emp_id}",
        )
        edit_address = st.text_area(
            "Address",
            value=(
                str(emp_data["address"])
                if pd.notna(emp_data["address"])
                and str(emp_data["address"]).lower() != "nan"
                else ""
            ),
            key=f"addr_{edit_emp_id}",
        )

      update_btn = st.form_submit_button(
          "Save Changes", type="primary", use_container_width=True
      )

      if update_btn:
        if not edit_name or not edit_phone or not edit_team_leader:
          st.error("Please fill out all required fields.")
        else:
          saved_photo_path = None
          if new_photo_file:
            saved_photo_path = os.path.join(
                PHOTO_DIR, f"{edit_emp_id}_{new_photo_file.name}"
            )
            with open(saved_photo_path, "wb") as f:
              f.write(new_photo_file.getbuffer())

          updated_data = {
              "name": edit_name,
              "address": edit_address,
              "phone": edit_phone,
              "email": edit_email,
              "guardian_name": edit_guardian_name,
              "guardian_phone": edit_guardian_phone,
              "education": edit_education,
              "team": edit_team,
              "team_leader": edit_team_leader,
              "floor": edit_floor,
              "onboarding_date": str(edit_onboarding),
          }
          update_employee_details(
              edit_emp_id, updated_data, new_photo_path=saved_photo_path
          )
          st.success(f"Successfully updated records for {edit_name}!")
          st.rerun()

with tab5:
  st.subheader("⚙️ System & Email Configurations")
  st.write("Configure notification target endpoints for automated alerts.")

  with st.form("email_form"):
    new_email = st.text_input("Notification Recipient Email")
    email_submit = st.form_submit_button("Add Email Target", type="primary")
    if email_submit:
      if not new_email or "@" not in new_email:
        st.error("Please provide a valid email.")
      else:
        added = add_notification_email(new_email.strip())
        if added:
          st.success(f"Added endpoint {new_email} successfully.")
          st.rerun()
        else:
          st.error("Email already exists in registry.")

  st.markdown("### Active Routing Endpoints")
  current_emails = get_notification_emails()
  if not current_emails:
    st.info("No endpoints registered.")
  else:
    for em in current_emails:
      c1, c2 = st.columns([3, 1])
      c1.text(em)
      if c2.button("Remove", key=f"rem_{em}", use_container_width=True):
        remove_notification_email(em)
        st.success(f"Removed endpoint {em}.")
        st.rerun()
