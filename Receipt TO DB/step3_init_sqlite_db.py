"""
Step 3: Initialize SQLite Database
Creates/connects to buysel.db and creates all required tables
Based on the optimized JSON schema
"""

import sqlite3
import os

DATABASE_PATH = "buysel.db"
SCHEMA_FILE = os.path.join("sql_schemas", "sqlite_schema.sql")

def init_database():
    """Initialize SQLite database with schema"""
    print("=" * 60)
    print("STEP 3: Initializing SQLite Database")
    print("=" * 60)

    # Check if schema file exists
    if not os.path.exists(SCHEMA_FILE):
        print(f"[ERROR] Schema file not found: {SCHEMA_FILE}")
        print("Please run generate_sql_schemas.py first.")
        return False

    # Remove existing database if it exists (to start fresh)
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"[INFO] Removed existing database: {DATABASE_PATH}")

    # Connect to SQLite (creates the file if not exists)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    print(f"[OK] Connected to database: {DATABASE_PATH}")

    # Read and execute the schema SQL
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Execute the schema (remove DROP TABLE statements for fresh start)
    # We already delete the file above, so we can use the full schema
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("[OK] Schema executed successfully")
    except sqlite3.Error as e:
        print(f"[ERROR] Schema execution failed: {e}")
        conn.close()
        return False

    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    print(f"\n[OK] Tables created: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    # Show table structures
    print("\n" + "-" * 40)
    print("Table Structures:")
    print("-" * 40)

    for table_name in ['receipts', 'receipt_items', 'receipt_tax_breakdown']:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"\n{table_name}:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

    conn.close()
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = init_database()
    if not success:
        exit(1)