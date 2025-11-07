import sqlite3

conn = sqlite3.connect('database/ev_stations.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=== Database Tables ===")
for table in tables:
    print(f"\n📋 Table: {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
users_table = cursor.fetchone()

if users_table:
    print("\n\n=== Users Table Data ===")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if users:
        for user in users:
            print(user)
    else:
        print("No users found")
else:
    print("\n\n❌ Users table does NOT exist!")

conn.close()
