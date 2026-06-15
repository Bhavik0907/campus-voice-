"""
init_db.py – Run this once to create the database and seed admin account.
Usage: python init_db.py
"""
import sqlite3, os
from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(__file__), 'database.db')

conn = sqlite3.connect(DB)

conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        email      TEXT    UNIQUE NOT NULL,
        password   TEXT    NOT NULL,
        role       TEXT    NOT NULL DEFAULT 'student',
        points     INTEGER NOT NULL DEFAULT 0,
        created_at TEXT    DEFAULT (datetime('now'))
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL,
        title           TEXT    NOT NULL,
        description     TEXT    NOT NULL,
        category        TEXT    NOT NULL,
        image           TEXT,
        status          TEXT    NOT NULL DEFAULT 'Pending',
        priority        TEXT    NOT NULL DEFAULT 'Low',
        reward_points   INTEGER NOT NULL DEFAULT 0,
        assigned_points INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT    DEFAULT (datetime('now')),
        updated_at      TEXT    DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
if 'points' not in cols:
    conn.execute("ALTER TABLE users ADD COLUMN points INTEGER NOT NULL DEFAULT 0")
cols = [row[1] for row in conn.execute("PRAGMA table_info(complaints)").fetchall()]
if 'reward_points' not in cols:
    conn.execute("ALTER TABLE complaints ADD COLUMN reward_points INTEGER NOT NULL DEFAULT 0")
if 'assigned_points' not in cols:
    conn.execute("ALTER TABLE complaints ADD COLUMN assigned_points INTEGER NOT NULL DEFAULT 0")

existing = conn.execute("SELECT id FROM users WHERE email='admin@campus.edu'").fetchone()
if not existing:
    conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
        ('Admin', 'admin@campus.edu', generate_password_hash('Admin@123'), 'admin')
    )
    print("✅ Admin account created: admin@campus.edu / Admin@123")
else:
    print("ℹ️  Admin account already exists.")

conn.commit()
conn.close()
print("✅ Database initialized successfully:", DB)
