import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

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
  # Employees Table
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
            onboarding_date TEXT,
            exit_date TEXT,
            photo_path TEXT,
            doc_paths TEXT,
            is_exited INTEGER DEFAULT 0
        )
    """)
  # Safe migration for existing databases missing the 'email' column
  try:
    cursor.execute("ALTER TABLE employees ADD COLUMN email TEXT")
  except sqlite3.OperationalError:
    pass  # Column already exists

  # Notification Emails Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
    """)
  # Users/Credentials Table
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
            INSERT INTO employees (emp_id, name, address, phone, email, guardian_name, guardian_phone, education, team, team_leader, onboarding_date, photo_path, doc_paths, is_exited)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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


def update_employee_details(emp_id, data):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        UPDATE employees 
        SET name = ?, address = ?, phone = ?, email = ?, guardian_name = ?, guardian_phone = ?, education = ?, team = ?, team_leader = ?, onboarding_date = ?
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


# --- Helper to Clean NaN/None values for display ---
def safe_display(val, default="N/A"):
  if pd.notna(val) and str(val).strip() and str(val).lower() != "nan":
    return str(val)
  return default


# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="Employee Management & Exit Tracker", layout="wide"
)

# --- Authentication & Account Flow ---
if not st.session_state["authenticated"]:
  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    st.subheader("🔐 System Access Portal")

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
        login_btn = st.form_submit_button("Login")

        if login_btn:
          if verify_user(username_input.strip(), password_input):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username_input.strip()
            st.success("Login successful!")
            st.rerun()
          else:
            st.error("Invalid username or password.")

    elif auth_action == "Create New Account":
      st.write("Register a new administrator/user account:")
      with st.form("signup_form"):
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        signup_btn = st.form_submit_button("Create Account")

        if signup_btn:
          if not new_user or not new_pass:
            st.error("Please fill in both fields.")
          elif new_pass != confirm_pass:
            st.error("Passwords do not match!")
          else:
            if register_user(new_user.strip(), new_pass):
              st.success(
                  "Account created successfully! Switch to the 'Login' tab"
                  " above to sign in."
              )
            else:
              st.error("Username already exists. Please pick another one.")

    elif auth_action == "Forgot Password":
      st.write("Reset your forgotten password:")
      with st.form("reset_form"):
        reset_user = st.text_input("Enter Your Username")
        new_p1 = st.text_input("New Password", type="password")
        new_p2 = st.text_input("Confirm New Password", type="password")
        reset_btn = st.form_submit_button("Reset Password")

        if reset_btn:
          if not reset_user or not new_p1:
            st.error("Please fill in all fields.")
          elif new_p1 != new_p2:
            st.error("Passwords do not match!")
          else:
            if user_exists(reset_user.strip()):
              update_password(reset_user.strip(), new_p1)
              st.success(
                  "Password reset successfully! Switch to the 'Login' tab to"
                  " sign in."
              )
            else:
              st.error("Username not found in the system.")

  st.stop()

# --- LOGGED IN AREA ---
with st.sidebar:
  st.subheader(f"👤 Welcome, {st.session_state['username']}")
  st.write("Status: **Logged In**")
  if st.button("🚪 Logout"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.rerun()

st.title("👥 Employee Management & Exit Notification System")

# --- Precision Notification Engine ---
df_check = get_all_employees()
registered_emails = get_notification_emails()

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
          "2-Day Prior Alert (11:00 AM Daily Rule)",
      ))
    elif days_left == 0:
      notifications.append((
          row["name"],
          row["emp_id"],
          row["exit_date"],
          (
              "🚨 EXIT DAY ALERT (2-Hour Interval Rule - Active at"
              f" {now.strftime('%H:%M')})"
          ),
      ))
    elif days_left < 0:
      notifications.append((
          row["name"],
          row["emp_id"],
          row["exit_date"],
          "⚠️ OVERDUE EXIT (Unmarked departure)",
      ))

  if notifications:
    st.error("⚠️ **ACTIVE EXIT NOTIFICATIONS & DISPATCH LOG:**")
    if registered_emails:
      st.info(
          "📧 **Automated Dispatch Target:** Alerts routed to"
          f" `{', '.join(registered_emails)}`"
      )
    else:
      st.warning(
          "⚠️ No recipient emails configured. Add them under **'Settings &"
          " Emails'**."
      )

    for name, emp_id, exit_date, alert_type in notifications:
      st.warning(
          f"**{alert_type}** — Employee **{name}** (ID: `{emp_id}`) | Scheduled"
          f" Exit Date: `{exit_date}`"
      )

# --- Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Add Employee",
    "📋 View & Manage Records",
    "📅 Fix Exit Dates",
    "✏️ Edit Details",
    "⚙️ Settings & Notification Emails",
])

with tab1:
  st.subheader("Manual Data Entry & Document Upload")
  st.info(
      "ℹ️ Exit dates are not required here and can be assigned later in the"
      " 'Fix Exit Dates' tab when an exit is confirmed."
  )

  with st.form("employee_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      emp_id = st.text_input("Employee ID *")
      name = st.text_input("Full Name *")
      email = st.text_input("Employee Email ID")
      phone = st.text_input("Phone Number *")
      guardian_name = st.text_input("Guardian's Name")
      guardian_phone = st.text_input("Guardian's Phone Number")

    with col2:
      team = st.selectbox("Team *", ["Berger", "Exam"])
      team_leader = st.text_input("Team Leader (Manual Entry) *")
      education = st.text_input("Educational Qualifications")
      onboarding_date = st.date_input(
          "Onboarding Date *", value=datetime.today()
      )
      address = st.text_area("Address")

    st.markdown("---")
    st.subheader("Document & Photo Uploads")

    photo_file = st.file_uploader(
        "Upload Employee Photo (png, jpg, jpeg)", type=["png", "jpg", "jpeg"]
    )
    document_files = st.file_uploader(
        "Upload Employee Documents (PDF, images, etc.)",
        type=["pdf", "png", "jpg", "jpeg", "docx", "txt"],
        accept_multiple_files=True,
    )

    submit_btn = st.form_submit_button("Save Employee Record")

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
            "onboarding_date": str(onboarding_date),
        }

        success = add_employee(data, photo_path, doc_paths)
        if success:
          st.success(f"Successfully added record for {name}!")
          st.rerun()
        else:
          st.error(f"Error: Employee ID '{emp_id}' already exists.")

with tab2:
  st.subheader("All Employee Records")
  df = get_all_employees()

  if df.empty:
    st.info("No employee records found.")
  else:
    search_query = st.text_input("🔍 Search by Name or Employee ID")
    if search_query:
      df = df[
          df["name"].str.contains(search_query, case=False, na=False)
          | df["emp_id"].str.contains(search_query, case=False, na=False)
      ]

    for _, row in df.iterrows():
      exit_display = (
          row["exit_date"]
          if pd.notna(row["exit_date"]) and str(row["exit_date"]).strip()
          else "Not Set"
      )
      is_exited_status = "Yes" if row["is_exited"] == 1 else "No"

      with st.expander(
          f"{row['name']} (ID: {row['emp_id']} | Team:"
          f" {safe_display(row['team'])}) - Exit Date: {exit_display} -"
          f" Exited: {is_exited_status}"
      ):
        col_img, col_info, col_docs = st.columns([1, 2, 2])

        with col_img:
          if row["photo_path"] and os.path.exists(row["photo_path"]):
            st.image(row["photo_path"], width=120)
          else:
            st.info("No photo uploaded")

        with col_info:
          # Clickable email link opening the default mail client (Outlook, etc.)
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
          st.markdown(f"**Onboarding:** {safe_display(row['onboarding_date'])}")
          st.markdown(f"**Exit Date:** `{exit_display}`")

        with col_docs:
          st.markdown("**Uploaded Documents:**")
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
                  )
          else:
            st.write("No documents attached.")

          st.markdown("---")
          if row["is_exited"] == 0:
            if st.button(f"Mark as Exited", key=f"exit_{row['emp_id']}"):
              mark_exited(row["emp_id"])
              st.success(f"Marked {row['name']} as exited.")
              st.rerun()
          else:
            st.success("Status: Exited")

          st.markdown("---")
          if st.button(
              f"🗑️ Delete Employee Record", key=f"del_{row['emp_id']}"
          ):
            delete_employee_db(row["emp_id"])
            st.success(f"Deleted record for {row['name']}.")
            st.rerun()

with tab3:
  st.subheader("📅 Fix or Assign Employee Exit Dates")
  st.write(
      "Assign or update exit dates whenever an employee's exit is confirmed to"
      " activate scheduled alerts."
  )

  df_fix = get_all_employees()
  if df_fix.empty:
    st.info("No employees available to update.")
  else:
    active_only = st.checkbox("Show active employees only", value=True)
    if active_only:
      df_fix = df_fix[df_fix["is_exited"] == 0]

    if df_fix.empty:
      st.info("No active employees found.")
    else:
      selected_emp_id = st.selectbox(
          "Select Employee",
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
          f"**Current Employee:** {curr_row['name']} | **Current Exit Date:**"
          f" `{curr_exit_str if (curr_exit_str and isinstance(curr_exit_str, str)) else 'Not Assigned'}`"
      )

      new_exit_date = st.date_input(
          "Assign/Update Exit Date",
          value=current_exit_dt,
          key=f"date_picker_{selected_emp_id}",
      )

      if st.button("Save Exit Date"):
        update_exit_date_db(selected_emp_id, new_exit_date)
        st.success(
            f"Successfully set exit date for {curr_row['name']} to"
            f" {new_exit_date}!"
        )
        st.rerun()

with tab4:
  st.subheader("✏️ Edit Employee Details")
  st.write(
      "Select an employee to update their personal details, phone, email, team,"
      " or leader."
  )

  df_edit = get_all_employees()
  if df_edit.empty:
    st.info("No employee records found to edit.")
  else:
    edit_emp_id = st.selectbox(
        "Select Employee to Edit",
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
      st.markdown(f"**Editing Record for Employee ID:** `{edit_emp_id}`")
      col1, col2 = st.columns(2)

      with col1:
        edit_name = st.text_input(
            "Full Name",
            value=str(emp_data["name"]),
            key=f"name_{edit_emp_id}",
        )
        edit_email = st.text_input(
            "Employee Email ID",
            value=(
                str(emp_data["email"])
                if pd.notna(emp_data["email"])
                and str(emp_data["email"]).lower() != "nan"
                else ""
            ),
            key=f"email_{edit_emp_id}",
        )
        edit_phone = st.text_input(
            "Phone Number",
            value=str(emp_data["phone"]),
            key=f"phone_{edit_emp_id}",
        )
        edit_guardian_name = st.text_input(
            "Guardian's Name",
            value=(
                str(emp_data["guardian_name"])
                if pd.notna(emp_data["guardian_name"])
                and str(emp_data["guardian_name"]).lower() != "nan"
                else ""
            ),
            key=f"gname_{edit_emp_id}",
        )
        edit_guardian_phone = st.text_input(
            "Guardian's Phone Number",
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
        edit_education = st.text_input(
            "Educational Qualifications",
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

      update_btn = st.form_submit_button("Update Employee Details")

      if update_btn:
        if not edit_name or not edit_phone or not edit_team_leader:
          st.error(
              "Please fill in all mandatory fields (Name, Phone, Team Leader)."
          )
        else:
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
              "onboarding_date": str(edit_onboarding),
          }
          update_employee_details(edit_emp_id, updated_data)
          st.success(
              f"Successfully updated details for {edit_name} (ID:"
              f" {edit_emp_id})!"
          )
          st.rerun()

with tab5:
  st.subheader("⚙️ Notification Email Management")
  st.write("Add destination emails where exit alerts should be routed.")

  with st.form("email_form"):
    new_email = st.text_input("Enter Email Address")
    email_submit = st.form_submit_button("Add Email")
    if email_submit:
      if not new_email or "@" not in new_email:
        st.error("Please enter a valid email address.")
      else:
        added = add_notification_email(new_email.strip())
        if added:
          st.success(f"Added {new_email} successfully!")
          st.rerun()
        else:
          st.error("This email is already registered.")

  st.markdown("### Currently Registered Notification Emails")
  current_emails = get_notification_emails()
  if not current_emails:
    st.info("No email addresses configured yet.")
  else:
    for em in current_emails:
      c1, c2 = st.columns([3, 1])
      c1.text(em)
      if c2.button("Remove", key=f"rem_{em}"):
        remove_notification_email(em)
        st.success(f"Removed {em}")
        st.rerun()
