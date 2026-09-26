import sqlite3
from werkzeug.security import generate_password_hash


def create_database():

    connection = sqlite3.connect("database.db")

    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        proctoring_status TEXT DEFAULT 'Normal'
    )
""")
    try:
        cursor.execute("""
            ALTER TABLE results
            ADD COLUMN proctoring_status TEXT DEFAULT 'Normal'
        """)
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            selected_answer TEXT,
            correct_answer TEXT NOT NULL
        )
    """)
    hashed_password = generate_password_hash("1234")

    cursor.execute("""
    INSERT OR IGNORE INTO students (username, password)
    VALUES (?, ?)
""", ("admin", hashed_password))
    cursor.execute("""
    UPDATE students
    SET password = ?
    WHERE username = ?
""", (hashed_password, "admin"))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proctoring_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        event TEXT,
        warning_count INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
    connection.commit()

    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")