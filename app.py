
from pathlib import Path
import os
import sqlite3
import secrets
import hashlib
import secrets

from datetime import datetime, timedelta, timezone
from contextlib import closing
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, abort
)

from werkzeug.security import check_password_hash, generate_password_hash


# ==========================================
# FLASK CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "mmu_navigator.db"

app = Flask(__name__, template_folder=str(BASE_DIR))

# Change this secret before deploying your website.
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-only-change-this-secret"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Admin registration code
ADMIN_REGISTRATION_CODE = "MMU-Admin-2026"


# ==========================================
# DATABASE
# ==========================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with sqlite3.connect(DATABASE) as db:

        # Create the admins table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
           CREATE TABLE IF NOT EXISTS password_reset_tokens (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           admin_id INTEGER NOT NULL,
           token_hash TEXT NOT NULL UNIQUE,
           expires_at TEXT NOT NULL,
           used INTEGER DEFAULT 0,
           created_at TEXT DEFAULT CURRENT_TIMESTAMP,
           FOREIGN KEY (admin_id) REFERENCES admins(id)
            )
        """)    

        # Check whether the admins table already has a name column
        columns = [
            row[1]
            for row in db.execute("PRAGMA table_info(admins)").fetchall()
        ]

        # Add the name column if it doesn't exist
        if "name" not in columns:
            db.execute("ALTER TABLE admins ADD COLUMN name TEXT")


# Create the database table automatically.
init_db()


# ==========================================
# CSRF PROTECTION FOR FORMS
# ==========================================

def generate_csrf_token():
    token = session.get("_csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token

    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf_token}


def validate_csrf_token():
    submitted_token = request.form.get("csrf_token", "")
    session_token = session.get("_csrf_token", "")

    if (
        not session_token
        or not secrets.compare_digest(submitted_token, session_token)
    ):
        abort(400, description="Invalid or missing CSRF token.")


# ==========================================
# HOMEPAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    # Already logged in? Return to homepage.
    if session.get("admin_id"):
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":

        validate_csrf_token()

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Find the admin account in the database.
        with closing(get_db()) as db:
            admin = db.execute(
                "SELECT * FROM admins WHERE email = ?",
                (email,)
            ).fetchone()

        # Check whether the account exists and password is correct.
        if admin and check_password_hash(
            admin["password_hash"], password
        ):

            # Clear old session data.
            session.clear()

            # Store the admin's information in the session.
            session["admin_id"] = admin["id"]
            session["admin_email"] = admin["email"]

            # Login successful. Return to homepage.
            return redirect(url_for("home"))

        else:
            error = "Incorrect email or password. Please try again."

    return render_template("admin_login.html", error=error)

# ==========================================
# ADMIN REGISTRATION
# ==========================================

@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():

    error = None

    if request.method == "POST":

        validate_csrf_token()

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        # Do NOT strip spaces from passwords
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        registration_code = request.form.get("registration_code", "")

        if not name or not email or not password or not confirm_password:
            error = "Please fill in all fields."

        elif len(password) < 8:
            error = "Password must be at least 8 characters long."

        elif password != confirm_password:
            error = "Passwords do not match."
            
        elif registration_code != ADMIN_REGISTRATION_CODE:
            error = "Invalid admin registration code."

        else:
            with closing(get_db()) as db:

                existing_admin = db.execute(
                    "SELECT id FROM admins WHERE email = ?",
                    (email,)
                ).fetchone()

                if existing_admin:
                    error = "An account with this email already exists."

                else:
                    password_hash = generate_password_hash(password)

                    db.execute(
                        """
                        INSERT INTO admins (name, email, password_hash)
                        VALUES (?, ?, ?)
                        """,
                        (name, email, password_hash)
                    )

                    db.commit()

                    return redirect(url_for("admin_login"))

    return render_template("admin_register.html", error=error)


# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.route("/logout", methods=["POST"])
def logout():

    validate_csrf_token()

    # Clear all session information.
    session.clear()

    # Return to homepage.
    return redirect(url_for("home"))

# ==========================================
# FORGOT PASSWORD
# ==========================================

@app.route("/admin/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None

    if request.method == "POST":
        validate_csrf_token()

        email = request.form.get("email", "").strip().lower()

        if email:
            with closing(get_db()) as db:
                admin = db.execute(
                    "SELECT id FROM admins WHERE email = ?",
                    (email,)
                ).fetchone()

                if admin:
                    # Generate a random token
                    token = secrets.token_urlsafe(32)

                    # Hash the token before storing it
                    token_hash = hashlib.sha256(
                        token.encode()
                    ).hexdigest()

                    # Token expires in 15 minutes
                    expires_at = (
                        datetime.now(timezone.utc) + timedelta(minutes=15)
                    ).isoformat()

                    # Invalidate any previous unused tokens
                    db.execute(
                        """
                        UPDATE password_reset_tokens
                        SET used = 1
                        WHERE admin_id = ? AND used = 0
                        """,
                        (admin["id"],)
                    )

                    # Save the new token
                    db.execute(
                        """
                        INSERT INTO password_reset_tokens
                        (admin_id, token_hash, expires_at)
                        VALUES (?, ?, ?)
                        """,
                        (admin["id"], token_hash, expires_at)
                    )

                    db.commit()

                    reset_url = url_for(
                    "reset_password",
                    token=token,
                    _external=True
                    )

                    print("\n========== PASSWORD RESET ==========")
                    print(f"Admin email: {email}")
                    print(f"Reset URL: {reset_url}")
                    print("Expires in: 15 minutes")
                    print("=================================\n")

        # Same message whether the account exists or not
        message = "If the account exists, a password reset link will be sent."

    return render_template("forgot_password.html", message=message)

# ==========================================
# RESET PASSWORD
# ==========================================

@app.route("/admin/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    error = None

    # Hash the token received from the URL
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with closing(get_db()) as db:
        reset_record = db.execute(
            """
            SELECT *
            FROM password_reset_tokens
            WHERE token_hash = ? AND used = 0
            """,
            (token_hash,)
        ).fetchone()

        # Check whether token exists
        if not reset_record:
            return "Invalid or already used reset link.", 400

        # Check expiration
        expires_at = datetime.fromisoformat(reset_record["expires_at"])

        if datetime.now(timezone.utc) >= expires_at:
            db.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE id = ?",
                (reset_record["id"],)
            )
            db.commit()
            return "This reset link has expired. Please request a new one.", 400

        if request.method == "POST":
            validate_csrf_token()

            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not password or not confirm_password:
                error = "Please fill in both password fields."

            elif len(password) < 8:
                error = "Password must be at least 8 characters long."

            elif password != confirm_password:
                error = "Passwords do not match."

            else:
                # Hash the new password
                new_password_hash = generate_password_hash(password)

                # Update admin password
                db.execute(
                    """
                    UPDATE admins
                    SET password_hash = ?
                    WHERE id = ?
                    """,
                    (new_password_hash, reset_record["admin_id"])
                )

                # Mark reset token as used
                db.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used = 1
                    WHERE id = ?
                    """,
                    (reset_record["id"],)
                )

                db.commit()

                return redirect(url_for("admin_login"))

    return render_template("reset_password.html", error=error)

# ==========================================
# CSS FILES
# ==========================================

@app.route("/style.css")
def stylesheet():
    css_text = (BASE_DIR / "style.css").read_text(
        encoding="utf-8"
    )
    return css_text, 200, {"Content-Type": "text/css"}


@app.route("/admin.css")
def admin_stylesheet():
    css_text = (BASE_DIR / "admin.css").read_text(
        encoding="utf-8"
    )
    return css_text, 200, {"Content-Type": "text/css"}


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
