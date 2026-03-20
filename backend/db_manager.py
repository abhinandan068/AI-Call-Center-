import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")

CALL_CENTER_DB = os.path.join(DB_DIR, "call_center.db")
SESSION_DB = os.path.join(DB_DIR, "sessions.db")


def init_session_db():
    with sqlite3.connect(SESSION_DB) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            phone_number TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_sec INTEGER,
            issue TEXT,
            summary TEXT,
            mood TEXT DEFAULT 'neutral',
            status TEXT DEFAULT 'unsolved',
            full_name TEXT,
            email TEXT,
            city TEXT,
            plan_type TEXT,
            plan_code TEXT,
            network_type TEXT,
            sim_status TEXT,
            kyc_status TEXT,
            device_type TEXT,
            total_calls_made INTEGER,
            total_call_duration INTEGER,
            tower_location TEXT,
            last_recharge_amount REAL,
            remaining_days_of_plans INTEGER,
            complaint_text TEXT,
            complaint_category TEXT,
            previous_complaints_count INTEGER,
            last_complaint_date TEXT,
            customer_status TEXT,
            priority_level TEXT,
            created_at TEXT
        )
        """)
        conn.commit()


def get_customer_details_by_phone(phone_number):
    if not os.path.exists(CALL_CENTER_DB):
        return {}
        
    with sqlite3.connect(CALL_CENTER_DB) as conn:
        c = conn.cursor()
        try:
            # Match safely if +91 is missing
            c.execute("SELECT * FROM customers WHERE phone_number LIKE ?", ('%'+phone_number.strip(),))
            row = c.fetchone()
            if row:
                columns = [desc[0] for desc in c.description]
                return dict(zip(columns, row))
        except sqlite3.OperationalError:
            pass
        return {}


def get_next_session_id():
    init_session_db()
    with sqlite3.connect(SESSION_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT count(*) FROM sessions")
        count = c.fetchone()[0]
        return f"sess_{count + 1:04d}"


def add_or_update_session(session_id, phone_number, start_time=None, end_time=None,
                          duration_sec=None, issue=None, summary=None,
                          mood='neutral', status='unsolved'):
    init_session_db()
    customer_details = get_customer_details_by_phone(phone_number)

    if not start_time:
        start_time = datetime.now()
    elif isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)

    if end_time:
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
    else:
        end_time = datetime.now()

    if duration_sec is None:
        duration_sec = int((end_time - start_time).total_seconds())

    start_time_str = start_time.isoformat()
    end_time_str = end_time.isoformat()

    with sqlite3.connect(SESSION_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT session_id, start_time FROM sessions WHERE session_id=?", (session_id,))
        exists = c.fetchone()
        
        # Keep original start_time if it exists
        if exists:
            start_time_str = exists[1]
            old_start = datetime.fromisoformat(start_time_str)
            duration_sec = int((end_time - old_start).total_seconds())

        fields = ['session_id', 'phone_number', 'start_time', 'end_time', 'duration_sec', 'issue', 'summary', 'mood', 'status']
        values = [session_id, phone_number, start_time_str, end_time_str, duration_sec, issue, summary, mood, status]

        for k in ['full_name','email','city','plan_type','plan_code','network_type',
                  'sim_status','kyc_status','device_type','total_calls_made','total_call_duration',
                  'tower_location','last_recharge_amount','remaining_days_of_plans',
                  'complaint_text','complaint_category','previous_complaints_count','last_complaint_date',
                  'customer_status','priority_level','created_at']:
            fields.append(k)
            values.append(customer_details.get(k))

        if exists:
            update_str = ",".join([f"{f}=?" for f in fields[1:]])  # exclude session_id
            c.execute(f"UPDATE sessions SET {update_str} WHERE session_id=?", (*values[1:], session_id))
        else:
            placeholders = ",".join(["?"]*len(fields))
            c.execute(f"INSERT INTO sessions ({','.join(fields)}) VALUES ({placeholders})", values)
        conn.commit()
    return session_id


def get_all_sessions():
    init_session_db()
    with sqlite3.connect(SESSION_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sessions ORDER BY start_time DESC")
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in rows]
