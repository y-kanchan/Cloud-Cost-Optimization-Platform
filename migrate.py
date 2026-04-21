import sqlite3
import os

db_path = 'database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of columns to add with their types and default values
    new_columns = [
        ('email', 'TEXT'),
        ('display_name', 'TEXT'),
        ('cost_alerts', 'BOOLEAN DEFAULT 1'),
        ('weekly_reports', 'BOOLEAN DEFAULT 1'),
        ('opt_tips', 'BOOLEAN DEFAULT 0'),
        ('sec_alerts', 'BOOLEAN DEFAULT 1'),
        ('enable_2fa', 'BOOLEAN DEFAULT 0'),
        ('login_notify', 'BOOLEAN DEFAULT 1'),
        ('session_timeout', 'TEXT DEFAULT "1 hour"')
    ]
    
    for col_name, col_type in new_columns:
        try:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError as e:
            # Column might already exist
            print(f"Column {col_name} already exists or error: {e}")
            
    conn.commit()
    conn.close()
    print("Migration complete!")
else:
    print("database.db not found. Running app.py will create it automatically with new schema.")
