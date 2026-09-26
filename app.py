from flask import Flask, render_template, request, session, redirect
from werkzeug.security import check_password_hash
from database import create_database
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = "examguard-secret-key"

create_database()


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE username = ?",
            (username,)
        )

        student = cursor.fetchone()

        connection.close()

        if student and check_password_hash(student[2], password):
            session["username"] = username
            return render_template("dashboard.html")

        return "Invalid username or password"

    return render_template("login.html")
# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    return render_template("dashboard.html")
# =========================
# EXAM PAGE
# =========================

@app.route("/exam")
def exam():

    if "username" not in session:
        return redirect("/login")

    session["exam_start"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    return render_template("exam.html")


# =========================
# RESULTS HISTORY
# =========================

@app.route("/results")
def results():

    if "username" not in session:
        return redirect("/login")


    question_text = {
        "q1": "What is the brain of a computer?",
        "q2": "Which language is used to create the structure of a web page?",
        "q3": "Which data structure follows FIFO?",
        "q4": "Which of the following is an operating system?",
        "q5": "Which protocol is used for web communication?",
        "q6": "Which language is used to manage databases?",
        "q7": "Which data structure follows LIFO?",
        "q8": "Which of the following is a programming language?",
        "q9": "What does RAM stand for?",
        "q10": "Which device connects different networks?",
        "q11": "Which sorting algorithm repeatedly compares adjacent elements?",
        "q12": "What does CPU stand for?",
        "q13": "Which language is used for styling web pages?",
        "q14": "Which of the following is a database management system?",
        "q15": "Which symbol is used for an ID selector in CSS?",
        "q16": "Which HTML tag is used for the largest heading?",
        "q17": "Which symbol represents multiplication in Python?",
        "q18": "What number system uses only 0 and 1?",
        "q19": "Which protocol is commonly used for sending email?",
        "q20": "What is a field of AI that enables computers to learn from data?"
    }

    option_text = {
        "q1": {
            "a": "CPU",
            "b": "RAM",
            "c": "Keyboard",
            "d": "Monitor"
        },
        "q2": {
            "a": "CSS",
            "b": "HTML",
            "c": "Python",
            "d": "SQL"
        },
        "q3": {
            "a": "Stack",
            "b": "Queue",
            "c": "Tree",
            "d": "Graph"
        },
        "q4": {
            "a": "Linux",
            "b": "Windows",
            "c": "Python",
            "d": "Oracle"
        },
        "q5": {
            "a": "HTTP",
            "b": "FTP",
            "c": "SMTP",
            "d": "SSH"
        },
        "q6": {
            "a": "SQL",
            "b": "HTML",
            "c": "CSS",
            "d": "Java"
        },
        "q7": {
            "a": "Queue",
            "b": "Stack",
            "c": "Array",
            "d": "Tree"
        },
        "q8": {
            "a": "Python",
            "b": "HTML",
            "c": "CSS",
            "d": "SQL"
        },
        "q9": {
            "a": "Random Access Memory",
            "b": "Read Access Memory",
            "c": "Run Access Memory",
            "d": "Rapid Access Memory"
        },
        "q10": {
            "a": "Router",
            "b": "Keyboard",
            "c": "Monitor",
            "d": "Printer"
        },
        "q11": {
            "a": "Bubble Sort",
            "b": "Binary Search",
            "c": "Merge Sort",
            "d": "Quick Sort"
        },
        "q12": {
            "a": "Central Processing Unit",
            "b": "Computer Personal Unit",
            "c": "Central Program Utility",
            "d": "Computer Processing Utility"
        },
        "q13": {
            "a": "CSS",
            "b": "HTML",
            "c": "SQL",
            "d": "Python"
        },
        "q14": {
            "a": "MySQL",
            "b": "HTML",
            "c": "CSS",
            "d": "JavaScript"
        },
        "q15": {
            "a": "#",
            "b": ".",
            "c": "@",
            "d": "$"
        },
        "q16": {
            "a": "<h1>",
            "b": "<p>",
            "c": "<head>",
            "d": "<title>"
        },
        "q17": {
            "a": "*",
            "b": "+",
            "c": "-",
            "d": "/"
        },
        "q18": {
            "a": "Binary",
            "b": "Decimal",
            "c": "Octal",
            "d": "Hexadecimal"
        },
        "q19": {
            "a": "SMTP",
            "b": "HTTP",
            "c": "FTP",
            "d": "SSH"
        },
        "q20": {
            "a": "Machine Learning",
            "b": "Web Development",
            "c": "Database Management",
            "d": "Networking"
        }
    }

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM results ORDER BY id DESC"
    )

    results = cursor.fetchall()

    all_answers = {}

    for result in results:

        cursor.execute(
            """
            SELECT question, selected_answer, correct_answer
            FROM answers
            WHERE result_id = ?
            """,
            (result[0],)
        )

        all_answers[result[0]] = cursor.fetchall()

    connection.close()

    return render_template(
        "results.html",
        results=results,
        all_answers=all_answers,
        question_text=question_text,
        option_text=option_text
    )


# =========================
# SUBMIT EXAM
# =========================

@app.route("/result", methods=["POST"])
def result():

    if "username" not in session:
        return redirect("/login")

    answers = {
        "q1": "a",
        "q2": "b",
        "q3": "b",
        "q4": "a",
        "q5": "a",
        "q6": "a",
        "q7": "b",
        "q8": "a",
        "q9": "a",
        "q10": "a",
        "q11": "a",
        "q12": "a",
        "q13": "a",
        "q14": "a",
        "q15": "a",
        "q16": "a",
        "q17": "a",
        "q18": "a",
        "q19": "a",
        "q20": "a"
    }

    score = 0

    for question, correct_answer in answers.items():

        selected_answer = request.form.get(question)

        if selected_answer == correct_answer:
            score += 1

    total = len(answers)

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM proctoring_events
        WHERE username = ?
        AND event = 'tab_switch'
        AND timestamp >= ?
    """, (session["username"], session["exam_start"]))

    tab_switches = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM proctoring_events
        WHERE username = ?
        AND event = 'multiple_faces'
        AND timestamp >= ?
    """, (session["username"], session["exam_start"]))

    multiple_faces = cursor.fetchone()[0]

    if tab_switches >= 3 or multiple_faces > 0:
        proctoring_status = "Suspicious"
    else:
        proctoring_status = "Normal"


  

   
    cursor.execute(
    """
    INSERT INTO results
    (username, score, total, proctoring_status)
    VALUES (?, ?, ?, ?)
    """,
    (
        session["username"],
        score,
        total,
        proctoring_status
    )
)
    result_id = cursor.lastrowid

    for question, correct_answer in answers.items():

   
        selected_answer = request.form.get(question)

        cursor.execute(
            """
            INSERT INTO answers
            (result_id, question, selected_answer, correct_answer)
            VALUES (?, ?, ?, ?)
            """,
            (
                result_id,
                question,
                selected_answer,
                correct_answer
            )
        )

    connection.commit()
    connection.close()
    return render_template(
    "result.html",
    score=score,
    total=total,
    proctoring_status=proctoring_status,
    tab_switches=tab_switches
)

    

    
# =========================
# PROCTORING EVENT
# =========================

@app.route("/proctoring-event", methods=["POST"])
def proctoring_event():

    if "username" not in session:
        return {"status": "unauthorized"}, 401

    data = request.get_json()

    event = data.get("event")
    warning_count = data.get("warning_count", 0)

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO proctoring_events
        (username, event, warning_count)
        VALUES (?, ?, ?)
    """, (
        session["username"],
        event,
        warning_count
    ))

    connection.commit()
    connection.close()

    print("PROCTORING EVENT SAVED:", event)

    return {"status": "received"}

# =========================
# RUN FLASK APPLICATION
# =========================
@app.route("/proctoring-logs")
def proctoring_logs():

    if "username" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT event, warning_count, timestamp
        FROM proctoring_events
        WHERE username = ?
        ORDER BY id DESC
    """, (session["username"],))

    events = cursor.fetchall()

    connection.close()

    return render_template(
        "proctoring_logs.html",
        events=events
    )
if __name__ == "__main__":
    app.run(debug=True)

    