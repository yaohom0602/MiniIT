from flask import Flask, render_template,flash,redirect,url_for,request

from database import (
    create_table,
    add_location,
    view_locations,
    update_location,
    delete_location 
)
app = Flask(__name__)
app.secret_key = "MMU"

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/manage_locations")
def manage_locations():
    locations = view_locations()

    return render_template(
        "manage_locations.html",
        locations = locations
    )

@app.route("/add_locations" ,methods =["POST"])
def add_new_location():
    room_code = request.form.get("room_code")
    category = request.form.get("category")

    success = add_location(room_code,category)

    if success:
        flash("Location added")
    else:
        flash("This location is already exists")

    return redirect(url_for("manage_locations"))

@app.route("/edit_location/<location_id>" , methods = ["POST"])
def edit_location(location_id):
    room_code = request.form.get("room_code")
    category = request.form.get("category")
    description = request.form.get("location_description")

    success = update_location(
        location_id,
        room_code,
        category,
        description,
    )

    if success:
        flash("Location updated")
    else:
        flash("Unable to update location for some reason")

    return redirect(url_for("manage_locations"))

@app.route("/delete_location/<int:location_id>", methods= ["POST"])
def remove_location(location_id):
    success = delete_location(location_id)

    if success:
        flash("Location deleted")
    else:
        flash("Location not found")

    return redirect(url_for("manage_locations"))

if __name__ == "__main__":
    create_table()
    app.run(debug=True)