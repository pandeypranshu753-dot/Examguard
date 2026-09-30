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

    try:
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN security_question TEXT
        """)
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN security_answer TEXT
        """)
    except sqlite3.OperationalError:
        pass
    
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

    try:
        cursor.execute("""
            ALTER TABLE results
            ADD COLUMN tab_switches INTEGER DEFAULT 0
        """)
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            ALTER TABLE results
            ADD COLUMN test_id INTEGER
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
    hashed_password = generate_password_hash("Admin@123")

    cursor.execute("""
        SELECT id FROM students
        WHERE username = ?
    """, ("admin",))

    admin_exists = cursor.fetchone()

    if not admin_exists:
        cursor.execute("""
            INSERT INTO students
            (username, password)
            VALUES (?, ?)
        """, ("admin", hashed_password))
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    """)
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT DEFAULT 'Draft'
        )
    """)
    try:
        cursor.execute("""
            ALTER TABLE test_papers
            ADD COLUMN question_count INTEGER DEFAULT 0
        """)
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            FOREIGN KEY (test_id) REFERENCES test_papers(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
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