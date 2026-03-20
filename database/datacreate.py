import sqlite3
import random
import string
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_IN")

TOTAL_RECORDS = 2000

conn = sqlite3.connect("database/call_center.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS customers")

cursor.execute("""
CREATE TABLE customers (
    phone_number TEXT PRIMARY KEY,
    full_name TEXT,
    email TEXT UNIQUE,
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

# -----------------------------
# TRACKERS
# -----------------------------
used_phones = set()
used_emails = set()

def generate_phone():
    while True:
        phone = "+91" + str(random.randint(6000000000, 9999999999))
        if phone not in used_phones:
            used_phones.add(phone)
            return phone

def generate_email():
    while True:
        email = fake.email()
        if email not in used_emails:
            used_emails.add(email)
            return email

# -----------------------------
# DATA OPTIONS
# -----------------------------
plans = ["Prepaid", "Postpaid"]
plan_codes = ["P499", "P699", "U5G", "D1.5", "D2"]
network_types = ["4G", "5G"]

sim_status_list = ["active", "blocked", "inactive"]
kyc_status_list = ["verified", "pending"]
device_types = ["Android", "iPhone", "Feature Phone"]

complaint_categories = ["Network", "Billing", "Recharge", "Data", "Call Drop"]

def generate_complaint(category):
    data = {
        "Network": "Network is very weak in my area and calls are unstable.",
        "Billing": "My bill shows incorrect charges this month.",
        "Recharge": "Recharge done but not activated.",
        "Data": "Data is getting exhausted quickly.",
        "Call Drop": "Calls are dropping frequently."
    }
    return data[category]

def get_priority(cat):
    if cat in ["Network", "Call Drop"]:
        return "high"
    elif cat == "Billing":
        return "medium"
    return "low"

def get_status(cat):
    if cat in ["Network", "Billing"]:
        return "unsatisfied"
    return "in-progress"

# -----------------------------
# GENERATE DATA
# -----------------------------
for _ in range(TOTAL_RECORDS):
    category = random.choice(complaint_categories)

    cursor.execute("""
INSERT INTO customers (
    phone_number,
    full_name,
    email,
    city,
    plan_type,
    plan_code,
    network_type,
    sim_status,
    kyc_status,
    device_type,
    total_calls_made,
    total_call_duration,
    tower_location,
    last_recharge_amount,
    remaining_days_of_plans,
    complaint_text,
    complaint_category,
    previous_complaints_count,
    last_complaint_date,
    customer_status,
    priority_level,
    created_at
)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (
    generate_phone(),
    fake.name(),
    generate_email(),
    fake.city(),
    random.choice(plans),
    random.choice(plan_codes),
    random.choice(network_types),

    random.choice(sim_status_list),
    random.choice(kyc_status_list),
    random.choice(device_types),

    random.randint(50, 500),
    random.randint(100, 2000),

    fake.city(),

    round(random.uniform(50, 500), 2),
    random.randint(11, 365),

    generate_complaint(category),
    category,
    random.randint(0, 5),
    datetime.now() - timedelta(days=random.randint(1, 60)),

    get_status(category),
    get_priority(category),
    datetime.now()
))
conn.commit()
conn.close()

print("✅ Advanced telecom dataset generated with phone number as primary ID.")