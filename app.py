from pathlib import Path
from flask import Flask

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent


@app.route("/")
def home():
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")


@app.route("/style.css")
def stylesheet():
    css_text = (BASE_DIR / "style.css").read_text(encoding="utf-8")
    return css_text, 200, {"Content-Type": "text/css"}


if __name__ == "__main__":
    app.run(debug=True)