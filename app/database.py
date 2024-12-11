import sqlite3

# Initialize database connection
conn = sqlite3.connect('cloud_access.db', check_same_thread=False)
cursor = conn.cursor()

# Create required tables
def initialize_database():
    cursor.execute('''CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        api_permissions TEXT,
        api_limits TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS permissions (
        id TEXT PRIMARY KEY,
        name TEXT,
        endpoint TEXT,
        description TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        plan_id TEXT,
        start_date TEXT,
        end_date TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS usage (
        user_id TEXT PRIMARY KEY,
        api_calls TEXT
    )''')

    conn.commit()

# Helper functions
def fetch_all(query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()

def execute_query(query, params=()):
    cursor.execute(query, params)
    conn.commit()
