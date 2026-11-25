
from flask import Flask, render_template

from database import create_table
from location import location_bp

app = Flask(__name__)
app.secret_key = "MMU"

# Register location routes
app.register_blueprint(location_bp)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
