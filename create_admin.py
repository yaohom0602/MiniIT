
from pathlib import Path
import sqlite3
from getpass import getpass

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "mmu_navigator.db"


def create_admin():

    email = input("Enter admin email: ").strip().lower()

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if not email:
        print("Email cannot be empty.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    # Hash the password before storing it.
    password_hash = generate_password_hash(password)

    try:
        with sqlite3.connect(DATABASE) as db:

            # Create the table if it doesn't exist.
            db.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert the new admin.
            db.execute("""
                INSERT INTO admins (email, password_hash)
                VALUES (?, ?)
            """, (email, password_hash))

        print("\nAdmin account created successfully!")

    except sqlite3.IntegrityError:
        print("\nAn admin with this email already exists.")


if __name__ == "__main__":
    create_admin()
