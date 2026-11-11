"""
Hospital Management System
Database: MySQL
"""

import mysql.connector as sql
import getpass

# ------------------------------------------------------------------
# 1. CONNECTION AND DATABASE SETUP
# ------------------------------------------------------------------
HOST = "localhost"
USER = "root"
PASSWD = "your_password"  # <-- Change this to your MySQL root password

def get_connection():
    """Attempt connection with default credentials or prompt user if it fails."""
    global PASSWD
    try:
        connection = sql.connect(host=HOST, user=USER, password=PASSWD)
        return connection
    except sql.Error as e:
        print(f"Could not connect using default credentials: {e}")
        print("Please enter your MySQL credentials:")
        user = input(f"MySQL Username [{USER}]: ").strip() or USER
        passwd = getpass.getpass("MySQL Password: ")
        try:
            connection = sql.connect(host=HOST, user=user, password=passwd)
            return connection
        except sql.Error as err:
            print("Connection failed:", err)
            raise SystemExit

con = get_connection()
cur = con.cursor()

# Database and Table Setup
cur.execute("CREATE DATABASE IF NOT EXISTS hospital_db")
cur.execute("USE hospital_db")

cur.execute("""CREATE TABLE IF NOT EXISTS patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(40) NOT NULL,
    age INT,
    gender CHAR(1),
    phone VARCHAR(15),
    address VARCHAR(60),
    admit_date DATE
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(40) NOT NULL,
    specialization VARCHAR(30),
    phone VARCHAR(15),
    fees DECIMAL(8,2)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS appointments (
    appt_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT,
    doctor_id INT,
    appt_date DATE,
    status VARCHAR(15) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS billing (
    bill_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT,
    amount DECIMAL(10,2),
    bill_date DATE,
    paid CHAR(1) DEFAULT 'N',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(20),
    role VARCHAR(15)
)""")

# Default admin and receptionist accounts (only inserted if table is empty)
cur.execute("SELECT COUNT(*) FROM users")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO users VALUES('admin','admin123','Admin')")
    cur.execute("INSERT INTO users VALUES('reception','rec123','Receptionist')")
con.commit()


# ------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ------------------------------------------------------------------
def get_int(msg):
    """Keep asking until the user types a valid integer."""
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Please enter a valid whole number.")


def get_float(msg):
    """Keep asking until the user types a valid float/decimal."""
    while True:
        try:
            return float(input(msg))
        except ValueError:
            print("Please enter a valid amount.")


def show(rows, headings):
    """Print rows neatly as a formatted table."""
    if not rows:
        print("\nNo records found.")
        return
    widths = []
    for i in range(len(headings)):
        w = len(headings[i])
        for r in rows:
            val_len = len(str(r[i])) if r[i] is not None else 4
            if val_len > w:
                w = val_len
        widths.append(w + 2)
    line = "+" + "+".join("-" * w for w in widths) + "+"
    print("\n" + line)
    print("|" + "|".join(str(headings[i]).center(widths[i])
                         for i in range(len(headings))) + "|")
    print(line)
    for r in rows:
        formatted_row = [str(item) if item is not None else "NULL" for item in r]
        print("|" + "|".join(formatted_row[i].center(widths[i])
                             for i in range(len(formatted_row))) + "|")
    print(line)


def exists(table, column, value):
    """Check whether a record exists (used for foreign key checks)."""
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {column}=%s", (value,))
    return cur.fetchone()[0] > 0


# ------------------------------------------------------------------
# 3. PATIENT MODULE
# ------------------------------------------------------------------
def add_patient():
    print("\n--- ADD PATIENT ---")
    name = input("Name: ").strip()
    while not name:
        print("Name cannot be empty.")
        name = input("Name: ").strip()
    age = get_int("Age: ")
    gender = input("Gender (M/F/O): ").strip().upper()[:1]
    if gender not in ["M", "F", "O"]:
        gender = "O"
    phone = input("Phone: ").strip()
    address = input("Address: ").strip()
    try:
        cur.execute(
            "INSERT INTO patients(name,age,gender,phone,address,admit_date) "
            "VALUES(%s,%s,%s,%s,%s,CURDATE())",
            (name, age, gender, phone, address)
        )
        con.commit()
        print("Patient added successfully. Patient ID =", cur.lastrowid)
    except sql.Error as e:
        print("Error:", e)


def view_patients():
    cur.execute("SELECT * FROM patients ORDER BY admit_date DESC")
    show(cur.fetchall(),
         ["ID", "Name", "Age", "Gender", "Phone", "Address", "Admit Date"])


def search_patient():
    print("\n1. Search by ID\n2. Search by name")
    ch = input("Choice: ").strip()
    if ch == "1":
        pid = get_int("Enter patient ID: ")
        cur.execute("SELECT * FROM patients WHERE patient_id=%s", (pid,))
    else:
        nm = input("Enter name (or part of it): ").strip()
        cur.execute("SELECT * FROM patients WHERE name LIKE %s", ("%" + nm + "%",))
    show(cur.fetchall(),
         ["ID", "Name", "Age", "Gender", "Phone", "Address", "Admit Date"])


def update_patient():
    print("\n--- UPDATE PATIENT ---")
    pid = get_int("Enter patient ID: ")
    if not exists("patients", "patient_id", pid):
        print("Patient not found.")
        return
    print("1. Name 2. Age 3. Phone 4. Address")
    ch = input("What do you want to update? ").strip()
    fields = {"1": "name", "2": "age", "3": "phone", "4": "address"}
    if ch not in fields:
        print("Invalid choice.")
        return
    if ch == "2":
        new = get_int("Enter new age: ")
    else:
        new = input("Enter new value: ").strip()
    try:
        cur.execute(f"UPDATE patients SET {fields[ch]}=%s WHERE patient_id=%s",
                    (new, pid))
        con.commit()
        print("Record updated successfully.")
    except sql.Error as e:
        print("Error:", e)


def delete_patient():
    print("\n--- DELETE PATIENT ---")
    pid = get_int("Enter patient ID: ")
    if not exists("patients", "patient_id", pid):
        print("Patient not found.")
        return
    sure = input("This also deletes the patient's appointments and bills. "
                 "Continue? (y/n): ").strip().lower()
    if sure == "y":
        try:
            cur.execute("DELETE FROM appointments WHERE patient_id=%s", (pid,))
            cur.execute("DELETE FROM billing WHERE patient_id=%s", (pid,))
            cur.execute("DELETE FROM patients WHERE patient_id=%s", (pid,))
            con.commit()
            print("Patient and related records deleted successfully.")
        except sql.Error as e:
            print("Error deleting records:", e)


def patient_menu():
    while True:
        print("\n===== PATIENT MENU =====")
        print("1. Add patient")
        print("2. View all patients")
        print("3. Search patient")
        print("4. Update patient")
        print("5. Delete patient")
        print("6. Back")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            add_patient()
        elif ch == "2":
            view_patients()
        elif ch == "3":
            search_patient()
        elif ch == "4":
            update_patient()
        elif ch == "5":
            delete_patient()
        elif ch == "6":
            break
        else:
            print("Invalid choice.")


# ------------------------------------------------------------------
# 4. DOCTOR MODULE
# ------------------------------------------------------------------
def add_doctor():
    print("\n--- ADD DOCTOR ---")
    name = input("Name: ").strip()
    spec = input("Specialization: ").strip()
    phone = input("Phone: ").strip()
    fees = get_float("Consultation fees: ")
    try:
        cur.execute("INSERT INTO doctors(name,specialization,phone,fees) "
                    "VALUES(%s,%s,%s,%s)", (name, spec, phone, fees))
        con.commit()
        print("Doctor added successfully. Doctor ID =", cur.lastrowid)
    except sql.Error as e:
        print("Error:", e)


def view_doctors():
    cur.execute("SELECT * FROM doctors ORDER BY specialization")
    show(cur.fetchall(), ["ID", "Name", "Specialization", "Phone", "Fees"])


def search_doctor():
    sp = input("Enter specialization (or part of it): ").strip()
    cur.execute("SELECT * FROM doctors WHERE specialization LIKE %s", ("%" + sp + "%",))
    show(cur.fetchall(), ["ID", "Name", "Specialization", "Phone", "Fees"])


def update_doctor_fees():
    did = get_int("Enter doctor ID: ")
    if not exists("doctors", "doctor_id", did):
        print("Doctor not found.")
        return
    fees = get_float("Enter new fees: ")
    try:
        cur.execute("UPDATE doctors SET fees=%s WHERE doctor_id=%s", (fees, did))
        con.commit()
        print("Fees updated successfully.")
    except sql.Error as e:
        print("Error:", e)


def delete_doctor():
    did = get_int("Enter doctor ID: ")
    if not exists("doctors", "doctor_id", did):
        print("Doctor not found.")
        return
    if exists("appointments", "doctor_id", did):
        print("Cannot delete: this doctor has appointments on record.")
        return
    try:
        cur.execute("DELETE FROM doctors WHERE doctor_id=%s", (did,))
        con.commit()
        print("Doctor deleted successfully.")
    except sql.Error as e:
        print("Error:", e)


def doctor_menu():
    while True:
        print("\n===== DOCTOR MENU =====")
        print("1. Add doctor")
        print("2. View all doctors")
        print("3. Search by specialization")
        print("4. Update fees")
        print("5. Delete doctor")
        print("6. Back")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            add_doctor()
        elif ch == "2":
            view_doctors()
        elif ch == "3":
            search_doctor()
        elif ch == "4":
            update_doctor_fees()
        elif ch == "5":
            delete_doctor()
        elif ch == "6":
            break
        else:
            print("Invalid choice.")


# ------------------------------------------------------------------
# 5. APPOINTMENT MODULE
# ------------------------------------------------------------------
def book_appointment():
    print("\n--- BOOK APPOINTMENT ---")
    pid = get_int("Patient ID: ")
    if not exists("patients", "patient_id", pid):
        print("Patient not found. Add the patient first.")
        return
    did = get_int("Doctor ID: ")
    if not exists("doctors", "doctor_id", did):
        print("Doctor not found.")
        return
    d = input("Appointment date (YYYY-MM-DD): ").strip()
    try:
        cur.execute("INSERT INTO appointments(patient_id,doctor_id,appt_date) "
                    "VALUES(%s,%s,%s)", (pid, did, d))
        con.commit()
        print("Appointment booked successfully. Appointment ID =", cur.lastrowid)
    except sql.Error as e:
        print("Error (check date format YYYY-MM-DD):", e)


def view_appointments():
    cur.execute("""SELECT a.appt_id, p.name, d.name, d.specialization,
                          a.appt_date, a.status
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   JOIN doctors d ON a.doctor_id = d.doctor_id
                   ORDER BY a.appt_date""")
    show(cur.fetchall(),
         ["Appt ID", "Patient", "Doctor", "Specialization", "Date", "Status"])


def update_appointment_status():
    aid = get_int("Enter appointment ID: ")
    if not exists("appointments", "appt_id", aid):
        print("Appointment not found.")
        return
    print("1. Scheduled 2. Completed 3. Cancelled")
    ch = input("New status: ").strip()
    status = {"1": "Scheduled", "2": "Completed", "3": "Cancelled"}
    if ch not in status:
        print("Invalid choice.")
        return
    try:
        cur.execute("UPDATE appointments SET status=%s WHERE appt_id=%s",
                    (status[ch], aid))
        con.commit()
        print("Status updated successfully.")
    except sql.Error as e:
        print("Error:", e)


def cancel_appointment():
    aid = get_int("Enter appointment ID to delete: ")
    if not exists("appointments", "appt_id", aid):
        print("Appointment not found.")
        return
    try:
        cur.execute("DELETE FROM appointments WHERE appt_id=%s", (aid,))
        con.commit()
        print("Appointment deleted successfully.")
    except sql.Error as e:
        print("Error:", e)


def appointment_menu():
    while True:
        print("\n===== APPOINTMENT MENU =====")
        print("1. Book appointment")
        print("2. View all appointments")
        print("3. Update appointment status")
        print("4. Delete appointment")
        print("5. Back")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            book_appointment()
        elif ch == "2":
            view_appointments()
        elif ch == "3":
            update_appointment_status()
        elif ch == "4":
            cancel_appointment()
        elif ch == "5":
            break
        else:
            print("Invalid choice.")


# ------------------------------------------------------------------
# 6. BILLING MODULE
# ------------------------------------------------------------------
def generate_bill():
    print("\n--- GENERATE BILL ---")
    pid = get_int("Patient ID: ")
    if not exists("patients", "patient_id", pid):
        print("Patient not found.")
        return
    amt = get_float("Bill amount: ")
    paid = input("Paid? (Y/N): ").strip().upper()[:1]
    if paid != "Y":
        paid = "N"
    try:
        cur.execute("INSERT INTO billing(patient_id,amount,bill_date,paid) "
                    "VALUES(%s,%s,CURDATE(),%s)", (pid, amt, paid))
        con.commit()
        print("Bill generated successfully. Bill ID =", cur.lastrowid)
    except sql.Error as e:
        print("Error:", e)


def view_bills():
    cur.execute("""SELECT b.bill_id, p.name, b.amount, b.bill_date, b.paid
                   FROM billing b JOIN patients p
                   ON b.patient_id = p.patient_id
                   ORDER BY b.bill_date DESC""")
    show(cur.fetchall(), ["Bill ID", "Patient", "Amount", "Date", "Paid"])


def mark_paid():
    bid = get_int("Enter bill ID: ")
    if not exists("billing", "bill_id", bid):
        print("Bill not found.")
        return
    try:
        cur.execute("UPDATE billing SET paid='Y' WHERE bill_id=%s", (bid,))
        con.commit()
        print("Bill marked as paid.")
    except sql.Error as e:
        print("Error:", e)


def billing_menu():
    while True:
        print("\n===== BILLING MENU =====")
        print("1. Generate bill")
        print("2. View all bills")
        print("3. Mark bill as paid")
        print("4. Back")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            generate_bill()
        elif ch == "2":
            view_bills()
        elif ch == "3":
            mark_paid()
        elif ch == "4":
            break
        else:
            print("Invalid choice.")


# ------------------------------------------------------------------
# 7. REPORTS (uses GROUP BY, aggregate functions and JOIN)
# ------------------------------------------------------------------
def report_menu():
    while True:
        print("\n===== REPORTS =====")
        print("1. Doctors per specialization")
        print("2. Appointments per doctor")
        print("3. Patients by gender")
        print("4. Total revenue (paid / unpaid)")
        print("5. Today's appointments")
        print("6. Back")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            cur.execute("SELECT specialization, COUNT(*) FROM doctors "
                        "GROUP BY specialization")
            show(cur.fetchall(), ["Specialization", "No. of Doctors"])
        elif ch == "2":
            cur.execute("""SELECT d.name, d.specialization, COUNT(a.appt_id)
                           FROM doctors d LEFT JOIN appointments a
                           ON d.doctor_id = a.doctor_id
                           GROUP BY d.doctor_id, d.name, d.specialization""")
            show(cur.fetchall(), ["Doctor", "Specialization", "Appointments"])
        elif ch == "3":
            cur.execute("SELECT gender, COUNT(*) FROM patients GROUP BY gender")
            show(cur.fetchall(), ["Gender", "Patients"])
        elif ch == "4":
            cur.execute("SELECT paid, SUM(amount), COUNT(*) FROM billing "
                        "GROUP BY paid")
            show(cur.fetchall(), ["Paid (Y/N)", "Total Amount", "No. of Bills"])
        elif ch == "5":
            cur.execute("""SELECT a.appt_id, p.name, d.name, a.status
                           FROM appointments a
                           JOIN patients p ON a.patient_id = p.patient_id
                           JOIN doctors d ON a.doctor_id = d.doctor_id
                           WHERE a.appt_date = CURDATE()""")
            show(cur.fetchall(), ["Appt ID", "Patient", "Doctor", "Status"])
        elif ch == "6":
            break
        else:
            print("Invalid choice.")


# ------------------------------------------------------------------
# 8. LOGIN AND MAIN MENU
# ------------------------------------------------------------------
def login():
    print("=" * 40)
    print(" HOSPITAL MANAGEMENT SYSTEM")
    print("=" * 40)
    for attempt in range(3):
        u = input("Username: ").strip()
        p = getpass.getpass("Password: ")
        cur.execute("SELECT role FROM users WHERE username=%s AND password=%s",
                    (u, p))
        row = cur.fetchone()
        if row:
            print("\nWelcome,", u, "(" + row[0] + ")")
            return row[0]
        print("Wrong username or password.", 2 - attempt, "attempt(s) left.")
    return None


def main():
    try:
        role = login()
        if role is None:
            print("Too many failed attempts. Exiting.")
            return
        while True:
            print("\n========== MAIN MENU ==========")
            print("1. Patients")
            print("2. Doctors")
            print("3. Appointments")
            print("4. Billing")
            print("5. Reports")
            print("6. Exit")
            ch = input("Enter choice: ").strip()
            if ch == "1":
                patient_menu()
            elif ch == "2":
                doctor_menu()
            elif ch == "3":
                appointment_menu()
            elif ch == "4":
                billing_menu()
            elif ch == "5":
                if role == "Admin":
                    report_menu()
                else:
                    print("Only the Admin can view reports.")
            elif ch == "6":
                print("Thank you. Goodbye!")
                break
            else:
                print("Invalid choice.")
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    main()
