from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
from db import db

app = Flask(__name__)
app.secret_key = "smart-campus-secret-key"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user[3], password):
            session["user"] = user[1]
            session["role"] = user[4]
            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html", name=session["user"])


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        db.execute(
            "INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)",
            (title, description, due_date)
        )
        db.commit()
        return redirect("/tasks")

    task_list = db.execute(
        "SELECT * FROM tasks ORDER BY id DESC"
    ).fetchall()

    return render_template("tasks.html", tasks=task_list)


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    if "user" not in session:
        return redirect("/login")

    db.execute(
        "UPDATE tasks SET status = 'Completed' WHERE id = ?",
        (task_id,)
    )
    db.commit()
    return redirect("/tasks")


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "user" not in session:
        return redirect("/login")

    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect("/tasks")


@app.route("/announcements")
def announcements():
    if "user" not in session:
        return redirect("/login")

    announcement_list = db.execute(
        "SELECT * FROM announcements ORDER BY id DESC"
    ).fetchall()

    return render_template(
        "announcements.html",
        announcements=announcement_list
    )


@app.route("/add_announcement", methods=["POST"])
def add_announcement():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access denied"

    title = request.form["title"]
    message = request.form["message"]

    db.execute(
        "INSERT INTO announcements (title, message) VALUES (?, ?)",
        (title, message)
    )
    db.commit()
    return redirect("/announcements")


@app.route("/events")
def events():
    if "user" not in session:
        return redirect("/login")

    event_list = db.execute(
        "SELECT * FROM events ORDER BY event_date"
    ).fetchall()

    return render_template("events.html", events=event_list)


@app.route("/add_event", methods=["POST"])
def add_event():
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access denied"

    title = request.form["title"]
    description = request.form["description"]
    event_date = request.form["event_date"]

    db.execute(
        "INSERT INTO events (title, description, event_date) VALUES (?, ?, ?)",
        (title, description, event_date)
    )
    db.commit()
    return redirect("/events")


@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        subject = request.form["subject"]
        message = request.form["message"]

        db.execute(
            "INSERT INTO complaints (user_name, subject, message) VALUES (?, ?, ?)",
            (session["user"], subject, message)
        )
        db.commit()
        return redirect("/complaints")

    if session.get("role") == "Admin":
        complaint_list = db.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
        ).fetchall()
    else:
        complaint_list = db.execute(
            "SELECT * FROM complaints WHERE user_name = ? ORDER BY id DESC",
            (session["user"],)
        ).fetchall()

    return render_template("complaints.html", complaints=complaint_list)


@app.route("/update_complaint/<int:complaint_id>", methods=["POST"])
def update_complaint(complaint_id):
    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access denied"

    status = request.form["status"]

    if status not in ["Pending", "In Progress", "Resolved"]:
        return "Invalid status"

    db.execute(
        "UPDATE complaints SET status = ? WHERE id = ?",
        (status, complaint_id)
    )
    db.commit()
    return redirect("/complaints")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if len(password) < 8:
            return "Password must be at least 8 characters long"

        existing_user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            return "Email already registered"

        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), "Student")
        )
        db.commit()
        return redirect("/login")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
