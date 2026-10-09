from flask import Flask, render_template, request, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from database import create_database
from ultralytics import YOLO
import sqlite3
from datetime import datetime
import re


class username:
    """Validated username value used by the authentication workflow."""

    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError("username must be a string")

        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", value):
            raise ValueError(
                "Username must be 3-30 characters and contain only letters, numbers, or underscores."
            )
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"username({self.value!r})"

    def __eq__(self, other):
        if isinstance(other, username):
            return self.value.casefold() == other.value.casefold()
        if isinstance(other, str):
            return self.value.casefold() == other.strip().casefold()
        return NotImplemented

    def __hash__(self):
        return hash(self.value.casefold())

app = Flask(__name__)
app.secret_key = "YOUR_NEW_KEY"
phone_model = YOLO("yolov8n.pt")

create_database()


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")
#------------------------------
#forgot password
#------------------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        security_answer = request.form["security_answer"].strip().lower()
        if len(password) < 8:
            return "Password must be at least 8 characters long."

        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter."

        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter."

        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number."

        if not re.search(r"[!@#$%^&*]", password):
            return "Password must contain at least one special character."

        if password != confirm_password:
            return "Passwords do not match."
        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        # Check whether the username exists
        cursor.execute(
            "SELECT * FROM students WHERE username = ?",
            (username,)
        )

        student = cursor.fetchone()

        if not student:
            connection.close()
            return "Username not found."

        # Check the security answer
        if student[4] != security_answer:
            connection.close()
            return "Incorrect security answer."
      

        
        # Hash the new password
        

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            UPDATE students
            SET password = ?
            WHERE username = ?
            """,
            (hashed_password, username)
        )

        connection.commit()
        connection.close()

        return redirect("/login")

    return render_template("forgot_password.html")


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

            if username == "admin":
                return redirect("/admin")

            return render_template("dashboard.html")

        return "Invalid username or password"

    return render_template("login.html")
#--------------------
#registration
#--------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        security_question = request.form["security_question"]
        security_answer = request.form["security_answer"].strip().lower()

        # Password length check
        if len(password) < 8:
            return "Password must be at least 8 characters long."

        # Uppercase letter check
        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter."

        # Lowercase letter check
        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter."

        # Number check
        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number."

        # Special character check
        if not re.search(r"[!@#$%^&*]", password):
            return "Password must contain at least one special character."

        # Confirm password
        if password != confirm_password:
            return "Passwords do not match."

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        # Check whether username already exists
        cursor.execute(
            "SELECT * FROM students WHERE username = ?",
            (username,)
        )

        existing_student = cursor.fetchone()

        if existing_student:
            connection.close()
            return "Username already exists. Please choose another username."

        # Hash the password before storing it
       
        hashed_password = generate_password_hash(password)
        cursor.execute(
    """
    INSERT INTO students
    (username, password, security_question, security_answer)
    VALUES (?, ?, ?, ?)
    """,
    (
        username,
        hashed_password,
        security_question,
        security_answer
    )
)
       
        

        connection.commit()
        connection.close()

        return redirect("/login")

    return render_template("register.html")
#--------------------------
#  admin
#--------------------------
@app.route("/admin")
def admin_dashboard():

    # Only admin can access
    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, subject, duration, status,question_count
        FROM test_papers
        ORDER BY id DESC
    """)

    test_papers = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        test_papers=test_papers
    )
@app.route("/admin/question/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):

    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    test_id = request.args.get("test_id")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Check whether students have already attempted this test
    cursor.execute("""
        SELECT COUNT(*)
        FROM results
        WHERE test_id = ?
    """, (test_id,))

    attempt_count = cursor.fetchone()[0]

    if attempt_count > 0:
        connection.close()
        return (
            "This question cannot be edited because "
            "students have already attempted this test."
        ), 400

    if request.method == "POST":

        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_answer = request.form["correct_answer"]

        cursor.execute("""
            UPDATE questions
            SET question = ?,
                option_a = ?,
                option_b = ?,
                option_c = ?,
                option_d = ?,
                correct_answer = ?
            WHERE id = ?
        """, (
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer,
            question_id
        ))

        connection.commit()
        connection.close()

        return redirect(
            f"/admin/test/{test_id}/questions"
        )

    cursor.execute("""
        SELECT id,
               question,
               option_a,
               option_b,
               option_c,
               option_d,
               correct_answer
        FROM questions
        WHERE id = ?
    """, (question_id,))

    question_data = cursor.fetchone()

    connection.close()

    if not question_data:
        return "Question not found.", 404

    return render_template(
        "edit_question.html",
        question=question_data
    )
@app.route("/admin/question/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):

    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    test_id = request.args.get("test_id")
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Check whether students have already attempted this test
    cursor.execute("""
        SELECT COUNT(*)
        FROM results
        WHERE test_id = ?
    """, (test_id,))

    attempt_count = cursor.fetchone()[0]

    if attempt_count > 0:
        connection.close()
        return (
            "This question cannot be deleted because "
            "students have already attempted this test."
        ), 400

   

    # Check whether the question belongs to this test
    cursor.execute("""
        SELECT id
        FROM test_questions
        WHERE test_id = ?
        AND question_id = ?
    """, (test_id, question_id))

    link = cursor.fetchone()

    if not link:
        connection.close()
        return "Question does not belong to this test.", 404

    # Remove the test-question relationship
    cursor.execute("""
        DELETE FROM test_questions
        WHERE test_id = ?
        AND question_id = ?
    """, (test_id, question_id))

    # Remove the question itself
    cursor.execute("""
        DELETE FROM questions
        WHERE id = ?
    """, (question_id,))

    connection.commit()
    connection.close()

    return redirect(
        f"/admin/test/{test_id}/questions"
    )

@app.route("/admin/test/<int:test_id>/edit", methods=["GET", "POST"])
def edit_test(test_id):

    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        duration = request.form["duration"]
        question_count = request.form["question_count"]

        cursor.execute("""
            UPDATE test_papers
            SET title = ?,
                subject = ?,
                duration = ?,
                question_count = ?
            WHERE id = ?
        """, (
            title,
            subject,
            duration,
            question_count,
            test_id
        ))

        connection.commit()
        connection.close()

        return redirect("/admin")

    cursor.execute("""
        SELECT id, title, subject, duration, question_count, status
        FROM test_papers
        WHERE id = ?
    """, (test_id,))

    test = cursor.fetchone()

    connection.close()

    if not test:
        return "Test paper not found.", 404

    return render_template(
        "edit_test.html",
        test=test
    )
@app.route("/admin/test/<int:test_id>/delete", methods=["POST"])
def delete_test(test_id):

    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Check whether students have already attempted this test
    cursor.execute("""
        SELECT COUNT(*)
        FROM results
        WHERE test_id = ?
    """, (test_id,))

    result_count = cursor.fetchone()[0]

    if result_count > 0:
        connection.close()
        return (
            "This test cannot be deleted because students "
            "have already submitted attempts for it."
        ), 400

    # Get questions linked to this test
    cursor.execute("""
        SELECT question_id
        FROM test_questions
        WHERE test_id = ?
    """, (test_id,))

    question_ids = cursor.fetchall()

    # Remove test-question relationships
    cursor.execute("""
        DELETE FROM test_questions
        WHERE test_id = ?
    """, (test_id,))

    # Remove the test paper
    cursor.execute("""
        DELETE FROM test_papers
        WHERE id = ?
    """, (test_id,))

    # Remove questions belonging to this test
    for question in question_ids:
        cursor.execute("""
            DELETE FROM questions
            WHERE id = ?
        """, (question[0],))

    connection.commit()
    connection.close()

    return redirect("/admin")

@app.route("/admin/create-test", methods=["POST"])
def create_test():

    # Only admin can create test papers
    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    title = request.form["title"]
    subject = request.form["subject"]
    duration = request.form["duration"]
    question_count = request.form["question_count"]
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO test_papers
        (title, subject, duration, status, question_count)
        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        subject,
        duration,
        "Draft",
        question_count
    ))

    connection.commit()
    connection.close()

    return "Test paper created successfully!"
@app.route("/admin/test/<int:test_id>/questions", methods=["GET", "POST"])
def admin_test_questions(test_id):
    # Only admin can access
    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if request.method == "POST":
        cursor.execute("""
            SELECT question_count
            FROM test_papers
            WHERE id = ?
        """, (test_id,))

        required_questions = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM test_questions
            WHERE test_id = ?
        """, (test_id,))

        actual_questions = cursor.fetchone()[0]

        if actual_questions >= required_questions:
            connection.close()
            return "Question limit reached. You cannot add more questions to this test."
        question = request.form["question"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_answer = request.form["correct_answer"]

        cursor.execute("""
            INSERT INTO questions
            (question, option_a, option_b, option_c, option_d, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        ))

        question_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO test_questions
            (test_id, question_id)
            VALUES (?, ?)
        """, (
            test_id,
            question_id
        ))

        connection.commit()

    cursor.execute("""
        SELECT title, subject, duration, question_count
        FROM test_papers
        WHERE id = ?
    """, (test_id,))

    test = cursor.fetchone()
    test_question_count = test[3] if test else 0

    cursor.execute("""
        SELECT q.id, q.question, q.option_a, q.option_b,
               q.option_c, q.option_d, q.correct_answer
        FROM questions q
        JOIN test_questions tq
        ON q.id = tq.question_id
        WHERE tq.test_id = ?
        ORDER BY q.id
    """, (test_id,))

    questions = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_test_questions.html",
        test=test,
        test_id=test_id,
        questions=questions,
        test_question_count=test_question_count
    )
@app.route("/admin/test/<int:test_id>/publish", methods=["POST"])
def publish_test(test_id):

    # Only admin can publish tests
    if "username" not in session or session["username"] != "admin":
        return "Access denied. Admins only.", 403

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Get the required question count
    cursor.execute("""
        SELECT question_count
        FROM test_papers
        WHERE id = ?
    """, (test_id,))

    test = cursor.fetchone()

    if not test:
        connection.close()
        return "Test paper not found."

    required_questions = test[0]

    # Count questions currently added
    cursor.execute("""
        SELECT COUNT(*)
        FROM test_questions
        WHERE test_id = ?
    """, (test_id,))

    actual_questions = cursor.fetchone()[0]

    # Require exact number of questions
    if actual_questions != required_questions:

        connection.close()

        return (
            f"Cannot publish this test. "
            f"Required: {required_questions} questions. "
            f"Currently added: {actual_questions}."
        )

    # Publish the test
    cursor.execute("""
        UPDATE test_papers
        SET status = 'Published'
        WHERE id = ?
    """, (test_id,))

    connection.commit()
    connection.close()

    return redirect("/admin")
# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    return render_template("dashboard.html")
#-----------------------------------
#logout
#-----------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# =========================
# EXAM PAGE
# =========================

@app.route("/exam")
def exam():

    if "username" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, subject, duration, question_count
        FROM test_papers
        WHERE status = 'Published'
        ORDER BY id DESC
    """)

    tests = cursor.fetchall()

    connection.close()
    return render_template(
    "available_tests.html",
    tests=tests
)
@app.route("/start-test/<int:test_id>")
def start_test(test_id):

    if "username" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, subject, duration, question_count
        FROM test_papers
        WHERE id = ?
        AND status = 'Published'
    """, (test_id,))

    test = cursor.fetchone()

    if not test:
        connection.close()
        return "Test not found or not published.", 404

    cursor.execute("""
        SELECT q.id,
               q.question,
               q.option_a,
               q.option_b,
               q.option_c,
               q.option_d
        FROM questions q
        JOIN test_questions tq
        ON q.id = tq.question_id
        WHERE tq.test_id = ?
        ORDER BY q.id
    """, (test_id,))

    questions = cursor.fetchall()

    connection.close()

    session["exam_start"] = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    session["test_id"] = test_id

    return render_template(
        "dynamic_exam.html",
        test=test,
        questions=questions
    )
 
    
# =========================
# RESULTS HISTORY
# =========================

@app.route("/results")
def results():

    if "username" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT r.id,
       r.username,
       r.score,
       r.total,
       r.proctoring_status,
       r.tab_switches,
       r.test_id,
       t.title
    FROM results r
    LEFT JOIN test_papers t
    ON r.test_id = t.id
    WHERE r.username = ?
    ORDER BY r.id DESC
""", (session["username"],))

    results = cursor.fetchall()

    all_answers = {}

    for result in results:

        cursor.execute("""
            SELECT question, selected_answer, correct_answer
            FROM answers
            WHERE result_id = ?
        """, (result[0],))

        all_answers[result[0]] = cursor.fetchall()

    connection.close()

    return render_template(
        "results.html",
        results=results,
        all_answers=all_answers
    )

# =========================
# SUBMIT EXAM
# =========================

@app.route("/result", methods=["POST"])
def result():

    if "username" not in session:
        return redirect("/login")

    test_id = session.get("test_id")

    if not test_id:
        return "No test selected.", 400

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Get questions for this test
    cursor.execute("""
        SELECT q.id,
               q.question,
               q.correct_answer
        FROM questions q
        JOIN test_questions tq
        ON q.id = tq.question_id
        WHERE tq.test_id = ?
        ORDER BY q.id
    """, (test_id,))

    questions = cursor.fetchall()

    score = 0
    attempted = 0

    for question in questions:

        question_id = question[0]
        correct_answer = question[2]

        selected_answer = request.form.get(
            f"q{question_id}"
        )

        if selected_answer:
            attempted += 1

        if selected_answer and correct_answer:
            if selected_answer.strip().lower() == correct_answer.strip().lower():
                score += 1

    total = len(questions)

    # Count tab switches
    cursor.execute("""
        SELECT COUNT(*)
        FROM proctoring_events
        WHERE username = ?
        AND event = 'tab_switch'
        AND timestamp >= ?
    """, (
        session["username"],
        session["exam_start"]
    ))

    tab_switches = cursor.fetchone()[0]

    # Count multiple-face events
    cursor.execute("""
        SELECT COUNT(*)
        FROM proctoring_events
        WHERE username = ?
        AND event = 'multiple_faces'
        AND timestamp >= ?
    """, (
        session["username"],
        session["exam_start"]
    ))

    multiple_faces = cursor.fetchone()[0]

    # Determine proctoring status
    if tab_switches >= 3 or multiple_faces > 0:
        proctoring_status = "Suspicious"
    else:
        proctoring_status = "Normal"

    # Save result
    cursor.execute("""
        INSERT INTO results
        (username, score, total, proctoring_status, tab_switches, test_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["username"],
        score,
        total,
        proctoring_status,
        tab_switches,
        test_id
    ))

    result_id = cursor.lastrowid

    # Save individual answers
    for question in questions:

        question_id = question[0]
        question_text = question[1]
        correct_answer = question[2]

        selected_answer = request.form.get(
            f"q{question_id}"
        )

        cursor.execute("""
            INSERT INTO answers
            (result_id, question, selected_answer, correct_answer)
            VALUES (?, ?, ?, ?)
        """, (
            result_id,
            question_text,
            selected_answer,
            correct_answer
        ))

    connection.commit()
    connection.close()

    # Get test information
    test_connection = sqlite3.connect("database.db")
    test_cursor = test_connection.cursor()

    test_cursor.execute("""
        SELECT title, subject, duration
        FROM test_papers
        WHERE id = ?
    """, (test_id,))

    test_info = test_cursor.fetchone()

    test_connection.close()

    if not test_info:
        return "Test information not found.", 404

    test_name = test_info[0]
    test_subject = test_info[1]
    test_duration = test_info[2]
    session.pop("test_id", None)
    session.pop("exam_start", None)

    return render_template(
        "result.html",
        score=score,
        total=total,
        attempted=attempted,
        proctoring_status=proctoring_status,
        tab_switches=tab_switches,
        test_name=test_name,
        test_subject=test_subject,
        test_duration=test_duration
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

    allowed_events = {
        "tab_switch",
        "no_face",
        "multiple_faces",
        "mobile_phone_detected"
    }

    if event not in allowed_events:
        return {"status": "invalid event"}, 400
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
@app.route("/detect-phone", methods=["POST"])
def detect_phone():
    print("PHONE DETECTION REQUEST RECEIVED")
    if "username" not in session:
        return {"error": "Unauthorized"}, 401

    image_file = request.files.get("image")
    if not image_file:
        return {"error": "No image received"}, 400

    import cv2
    import numpy as np

    image_bytes = image_file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return {"error": "Invalid image"}, 400

    results = phone_model(frame, verbose=False)
    print("DETECTED CLASSES:", [
    phone_model.names[int(box.cls[0])]
    for result in results
    for box in result.boxes
])
    phone_detected = any(
        phone_model.names[int(box.cls[0])] == "cell phone"
        and float(box.conf[0]) >= 0.40
        for result in results
        for box in result.boxes
    )

    return {"phone_detected": phone_detected}

if __name__ == "__main__":
    app.run(debug=True)

    