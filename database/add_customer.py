import sqlite3
import os
from datetime import datetime

# Robust database path relative to this script
DB_PATH = os.path.join(os.path.dirname(__file__), "call_center.db")

def add_customer_interactive():
    print("==================================================")
    print("🏢 Customer CRM Data Entry (call_center.db) 🏢")
    print("==================================================")

    # Collect essential details
    phone = input("📞 Phone Number (e.g. +919876543210): ").strip()
    if not phone:
        print("❌ Phone number is absolutely required.")
        return
        
    name = input("👤 Full Name: ").strip() or "Unknown Caller"
    email = input("✉️ Email: ").strip() or f"temp_{int(datetime.now().timestamp())}@callcenter.com"
    city = input("🏙️ City: ").strip() or "Local"
    
    print("\n--- Plan & Network Metrics ---")
    plan_type = input("📱 Plan Type (Prepaid/Postpaid) [Prepaid]: ").strip().capitalize() or "Prepaid"
    network = input("📶 Network Type (4G/5G) [5G]: ").strip().upper() or "5G"
    days_left = input("📅 Remaining Days of Plan [28]: ").strip()
    days_left = int(days_left) if days_left.isdigit() else 28
    
    print("\n--- Active Complaint Specifics ---")
    category = input("⚠️ Issue Category (Network/Billing/Data/Custom) [Network]: ").strip().capitalize() or "Network"
    complaint = input(f"📝 Brief Description of their {category} issue: ").strip() or f"User reported {category.lower()} problems."

    # Date Timestamps
    current_time_str = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Pushing securely into the CRM
        cursor.execute("""
            INSERT INTO customers (
                phone_number, full_name, email, city, 
                plan_type, plan_code, network_type, 
                sim_status, kyc_status, device_type, 
                total_calls_made, total_call_duration, 
                tower_location, last_recharge_amount, remaining_days_of_plans, 
                complaint_text, complaint_category, previous_complaints_count, 
                last_complaint_date, customer_status, priority_level, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            phone, name, email, city, 
            plan_type, "P-Custom", network, 
            "active", "verified", "Smartphone", 
            1, 20, 
            city, 299.0, days_left, 
            complaint, category, 0, 
            current_time_str, "unsolved", "high", current_time_str
        ))
        conn.commit()
        print("\n✅ Securely stored the customer into `call_center.db`!")
        print(f"💡 You can now use '{phone}' as your identity in the Voice AI tools.")
        
    except sqlite3.IntegrityError as e:
        print(f"\n❌ SQL Error: {e}")
        print("Note: Phone number and Email must be entirely unique between customers.")
    finally:
        conn.close()

if __name__ == "__main__":
    add_customer_interactive()
