import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create a table to store user information
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    face_data BLOB,
    mobile_number TEXT NOT NULL CHECK (length(mobile_number) = 13)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    face_data BLOB NOT NULL,
    username TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tokenlog (
    tokenid INTEGER NOT NULL UNIQUE,
    token TEXT NOT NULL UNIQUE
)
""")

conn.commit()
conn.close()