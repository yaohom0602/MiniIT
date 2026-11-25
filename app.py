import os
from pathlib import Path

from flask import Flask, render_template

from admin import admin_bp, init_db

from database import create_table
from location import location_bp

app = Flask(__name__)
app.secret_key = "MMU"

# Register location routes
app.register_blueprint(location_bp)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR))

# Flask configuration
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-only-change-this-secret"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Register Blueprints
app.register_blueprint(admin_bp)



@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    create_table()
    app.run(debug=True)
