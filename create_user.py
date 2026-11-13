
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash

username = input("Enter login username: ").strip()
password = getpass("Enter password: ")

if not username or not password:
    print("Username and password cannot be empty.")
else:
    conn = sqlite3.connect("employees.db")

    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        conn.commit()
        print("User account created successfully!")

    except sqlite3.IntegrityError:
        print("This username already exists.")

    finally:
        conn.close()
