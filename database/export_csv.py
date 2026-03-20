import sqlite3
import csv
import os

# Link to the SQLite DB
db_path = os.path.join(os.path.dirname(__file__), "sessions.db")
output_path = os.path.join(os.path.dirname(__file__), "sessions_data.csv")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM sessions")
    rows = cursor.fetchall()
    
    if rows:
        # Get all 36 column names automatically
        headers = [description[0] for description in cursor.description]
        
        # Write to CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        print(f"✅ Successfully exported all records containing all {len(headers)} fields!")
        print(f"📂 File saved at: {output_path}")
        print("💡 Open this CSV file in Microsoft Excel or directly in VS Code to view the full database easily.")
    else:
        print("The database is currently empty.")
        
except sqlite3.OperationalError as e:
    print(f"Database error: {e}")

finally:
    conn.close()
