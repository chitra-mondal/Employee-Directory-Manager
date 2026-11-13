

from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")
# Employee ID mapped to employee details
employees = {
    "E101": ("Rahul", "2003-05-12", "2025-07-10"),
    "E102": ("Priya", "2004-08-20", "2026-06-15")
}

import sqlite3


def init_db():
    conn = sqlite3.connect("employees.db")

    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            post TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            salary REAL DEFAULT 0,
            address TEXT DEFAULT '',
            email TEXT DEFAULT ''
        )
    """)


    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Add new columns to existing databases when needed
    existing_columns = [
        row[1] for row in conn.execute(
            "PRAGMA table_info(employees)"
        ).fetchall()
    ]

    new_columns = {
        "post": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "salary": "REAL DEFAULT 0",
        "address": "TEXT DEFAULT ''",
        "email": "TEXT DEFAULT ''"
    }

    for column, definition in new_columns.items():
        if column not in existing_columns:
            conn.execute(
                f"ALTER TABLE employees ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


init_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = sqlite3.connect("employees.db")
        user = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session.clear()
            session["username"] = username
            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))




@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "emp_id")

    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM employees
            WHERE emp_id LIKE ? OR name LIKE ?
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM employees")

    rows = cursor.fetchall()
    conn.close()

    employees = {
        row[0]: tuple(row[1:])
        for row in rows
    }

    sort_columns = {
        "emp_id": 0,
        "name": 1,
        "salary": 5
    }

    if sort_by in sort_columns:
        if sort_by == "salary":
            employees = dict(sorted(
                employees.items(),
                key=lambda item: float(item[1][5] or 0)
            ))
        else:
            employees = dict(sorted(
                employees.items(),
                key=lambda item: str(
                    item[1][sort_columns[sort_by]]
                ).lower()
            ))

    return render_template(
        "index.html",
        employees=employees,
        search=search,
        sort_by=sort_by
    )






@app.route("/add", methods=["POST"])
def add_employee():
    if "username" not in session:
        return redirect(url_for("login"))

    emp_id = request.form["emp_id"]
    name = request.form["name"]
    birthdate = request.form["birthdate"]
    joining_date = request.form["joining_date"]

    post = request.form.get("post", "").strip()
    phone = request.form.get("phone", "").strip()
    salary = float(request.form.get("salary", "0") or 0)
    address = request.form.get("address", "").strip()
    email = request.form.get("email", "").strip()

    try:
        conn = sqlite3.connect("employees.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO employees
            (emp_id, name, birthdate, joining_date,
             post, phone, salary, address, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp_id, name, birthdate, joining_date,
            post, phone, salary, address, email
        ))


        conn.commit()
        conn.close()

    except sqlite3.IntegrityError:
        conn.close()
        return "Employee ID already exists! <a href='/'>Go Back</a>"

    return redirect("/")





@app.route("/update/<emp_id>", methods=["GET", "POST"])
def update_employee(emp_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM employees WHERE emp_id = ?",
        (emp_id,)
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return redirect("/")

    details = tuple(row[1:])

    if request.method == "POST":
        name = request.form["name"]
        birthdate = request.form["birthdate"]
        joining_date = request.form["joining_date"]
        post = request.form.get("post", "").strip()
        phone = request.form.get("phone", "").strip()
        salary = float(request.form.get("salary", "0") or 0)
        address = request.form.get("address", "").strip()
        email = request.form.get("email", "").strip()

        cursor.execute("""
            UPDATE employees
            SET name = ?, birthdate = ?, joining_date = ?,
                post = ?, phone = ?, salary = ?,
                address = ?, email = ?
            WHERE emp_id = ?
        """, (
            name, birthdate, joining_date,
            post, phone, salary, address, email, emp_id
        ))

        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()

    return render_template(
        "update.html",
        emp_id=emp_id,
        details=details
    )




@app.route("/delete/<emp_id>")
def delete_employee(emp_id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM employees WHERE emp_id = ?",
        (emp_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
