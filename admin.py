from __main__ import app
from flask import render_template, jsonify, request, session, redirect, url_for
import functools
from marshmallow import Schema, fields, validate, EXCLUDE, ValidationError
from user import PASSWORD_REGEX

# from db import db, Admin, Location, Booking , User
from db import Admin, Location, Booking, User, Review
import bcrypt

# Schema validation from https://stackoverflow.com/a/61648076


class CreateAccountSchema(Schema):
    username = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    password = fields.String(
        required=True,
        validate=validate.Regexp(
            regex=PASSWORD_REGEX,
            error="password must contain a minimum of eight characters, at least one letter, one number and one special character",
        ),
        error_messages={"required": "required"},
    )

    class Meta:
        # Strip unknown values from output
        unknown = EXCLUDE


class LoginSchema(Schema):
    username = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    password = fields.String(
        required=True,
        error_messages={"required": "required"},
    )

    class Meta:
        # Strip unknown values from output
        unknown = EXCLUDE


class CreateLocationSchema(Schema):
    name = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    address = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    main_photo = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    additional_photos = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    description = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    website = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    maps = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    email = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    phone_number = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    opening_hours = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    checkin_instructions = fields.String(
        required=True, error_messages={"required": "required", "invalid": "invalid"}
    )
    features = fields.String(
        required=False, error_messages={"required": "required", "invalid": "invalid"}
    )

    class Meta:
        # Strip unknown values from output
        unknown = EXCLUDE


class UpdateLocationSchema(Schema):
    name = fields.String(
        required=False,
    )
    featured = fields.Integer(
        required=False,
        validate=[validate.Range(min=0, max=1, error="Value must be between 1 and 0")],
    )
    status = fields.String(
        required=False, validate=[validate.OneOf(["AVAILABLE", "UNAVAILABLE"])]
    )
    address = fields.String(
        required=False,
    )
    main_photo = fields.String(
        required=False,
    )
    additional_photos = fields.String(
        required=False,
    )
    description = fields.String(
        required=False,
    )
    website = fields.String(
        required=False,
    )
    maps = fields.String(
        required=False,
    )
    email = fields.String(
        required=False,
    )
    phone_number = fields.String(
        required=False,
    )
    opening_hours = fields.String(
        required=False,
    )
    checkin_instructions = fields.String(
        required=False,
    )

    class Meta:
        # Strip unknown values from output
        unknown = EXCLUDE


class UpdateBookingSchema(Schema):
    status = fields.String(
        required=True, validate=[validate.OneOf(["CONFIRMED", "DECLINED"])]
    )

    class Meta:
        # Strip unknown values from output
        unknown = EXCLUDE


def ensure_login(func):
    @functools.wraps(func)
    def check_login(*args, **kwargs):
        logged_in = False
        sess = session.get("admin_id")
        if not sess == None:
            logged_in = True
        if not logged_in and not "/_/auth/login" in request.path:
            return redirect(url_for("admin_login"))
        if logged_in and "/_/auth/login" in request.path:
            return redirect(url_for("admin_homepage"))
        db_admin = Admin.get(sess)
        if db_admin == None and logged_in:
            session.clear()
            return redirect("/_/")
        return func(db_admin, *args, **kwargs)

    return check_login


@app.get("/_/")
@ensure_login
def admin_homepage(admin):
    db_users = User.getAll()
    db_bookings = Booking.getAll()
    db_locations = Location.getAll()
    db_pending_bookings = Booking.getAll(status="PENDING")
    return render_template(
        "admin/index.html",
        total_users=len(db_users),
        bookings=db_bookings,
        locations=db_locations,
        pending_bookings=len(db_pending_bookings),
        admin=admin,
        page="/",
    )


@app.get("/_/bookings")
@ensure_login
def admin_view_bookings(admin):
    db_bookings = Booking.getAll()
    return render_template(
        "admin/bookings table.html", admin=admin, page="/bookings", bookings=db_bookings
    )


@app.route("/_/booking/<id>", methods=["GET", "PATCH"])
@ensure_login
def admin_manage_individual_booking(admin, id):
    db_booking = Booking.get(id)
    if db_booking == None:
        return "Not found", 404
    if request.method == "GET":
        return render_template(
            "admin/manage-booking.html",
            admin=admin,
            page="/bookings/manage",
            booking=db_booking,
        )
    if request.method == "PATCH":
        schema = UpdateBookingSchema()
        try:
            body = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400  # Return errors in json
        Booking.update(db_booking["id"], **body)
        return "success"


@app.get("/_/settings")
@ensure_login
def admin_settings(admin):
    return render_template("admin/index.html", admin=admin, page="/settings")


@app.get("/_/members")
@ensure_login
def view_members(admin):
    db_users = User.query.all()
    return render_template("admin/members.html", users=db_users, admin=admin)


@app.get("/_/locations")
@ensure_login
def admin_view_locations(admin):
    db_locations = Location.getAll()
    joined_locations = []
    for location in db_locations:
        joined_location = dict(location)
        bookings = Booking.getAll(location_id=location["id"])
        reviews = [i for i in bookings if not (i["review"] == None)]
        joined_location["avg_rating"] = 0
        if len(reviews) > 0:
            joined_location["avg_rating"] = sum(
                review["rating"] for review in reviews
            ) / len(reviews)
        joined_location["total_bookings"] = len(bookings)
        joined_locations.append(joined_location)
    return render_template(
        "admin/locations.html",
        admin=admin,
        page="/locations",
        locations=joined_locations,
    )


@app.route("/_/locations/add", methods=["GET", "POST"])
@ensure_login
def add_locations(admin):
    if request.method == "GET":
        return render_template("admin/add/location.html")
    if request.method == "POST":
        schema = CreateLocationSchema()
        try:
            body = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400  # Return errors in json

        db_location = Location.new(**body)  # Turn input into db object

        return "/_/location/" + db_location["id"]


@app.route("/_/location/<id>", methods=["GET", "POST", "PATCH", "DELETE"])
@ensure_login
def confirm_details(admin, id):
    if request.method == "DELETE":
        db_location = Location.get(id)
        if db_location == None:
            return "Not found", 404
        Location.delete(db_location["id"])

        return "success"

    if request.method == "GET":
        db_location = Location.get(id)
        db_bookings = Booking.getAll(location_id=db_location["id"])
        reviews = [
            booking["review"]
            for booking in db_bookings
            if not (booking["review"] == None)
        ]
        return render_template(
            "admin/location.html",
            page="/locations",
            location=db_location,
            reviews=reviews,
        )

    if request.method == "PATCH":
        schema = UpdateLocationSchema()
        try:
            body = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400  # Return errors in json
        Location.update(id, **body)
        return "success"


@app.route("/_/review/<id>", methods=["DELETE"])
@ensure_login
def manage_reviews(admin, id):
    db_review = Review.get(id)
    if db_review == None:
        return "Not found", 404
    if request.method == "DELETE":
        Review.delete(id)

        return "success"


@app.route("/_/bookings/manage", methods=["GET"])
@ensure_login
def manage_bookings(admin):
    if request.method == "GET":
        db_bookings = Booking.getAll()
        if not request.args.get("status") == None:
            db_bookings = Booking.getAll(status=request.args.get("status"))
        return render_template(
            "admin/bookings.html", page="/bookings/manage", bookings=db_bookings
        )


@app.route("/_/bookings/manage?status=PENDING", methods=["GET"])
@ensure_login
def pending_bookings(admin):
    if request.method == "GET":
        return render_template("admin/bookings.html", admin=admin)


@app.route("/_/bookings/manage?status=APPROVED", methods=["GET"])
@ensure_login
def approved_bookings(admin):
    return render_template("admin/bookings.html")


@app.route("/_/bookings/manage?status=CANCELLED", methods=["GET"])
@ensure_login
def cancelled_bookings(admin):
    if request.method == "GET":
        return render_template("admin/bookings.html")


@app.route("/_/bookings/declined", methods=["GET"])
@ensure_login
def declined_bookings(admin):
    if request.method == "GET":
        db_bookings = Booking.query.filter_by(status="DECLINED")
        if not request.args.get("status") == None:
            db_bookings = Booking.query.filter_by(
                status=request.args.get('status="DECLINED"')
            )
        return render_template("admin/bookings.html", bookings=db_bookings)


@app.route("/_/booking/<id>/approve", methods=["POST"])
@ensure_login
def approve_booking(admin, id):
    if request.method == "POST":
        Booking.update(id, status="APPROVED")
        return "/_/bookings/manage"


@app.route("/_/booking/<id>/decline", methods=["POST"])
@ensure_login
def decline_booking(admin, id):
    if request.method == "POST":
        Booking.update(id, status="DECLINED")
        return "/_/bookings/manage"


@app.route("/_/location/<id>/unavailable", methods=["POST"])
@ensure_login
def unavailable(admin, id):
    if request.method == "POST":
        Location.update(id, status="UNAVAILABLE")
        return "/_/locations"


@app.route("/_/booking/<id>/available", methods=["POST"])
@ensure_login
def available(admin, id):
    if request.method == "POST":
        Location.update(id, status="AVAILABLE")
        return "/_/locations"


@app.get("/_/auth/logout")
def admin_logout():
    # Clear session and redirect
    session.clear()
    return redirect("/")


@app.route("/_/auth/login", methods=["GET", "POST"])
@ensure_login
def admin_login(admin):
    if request.method == "GET":
        db_admins = Admin.getAll()
        if len(db_admins) < 1:
            return redirect(url_for("admin_create"))
        return render_template("admin/login.html")
    if request.method == "POST":
        schema = LoginSchema()
        try:
            body = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400  # Return errors in json
        db_admin = Admin.getAll(username=body["username"])
        if len(db_admin) < 1 or not bcrypt.checkpw(
            str(body["password"]).encode("utf-8"), db_admin[0]["password"]
        ):  # Check if user in db and also if password matches
            return ({"status": "error", "message": "Invalid credentials"}), 401
        session["admin_id"] = db_admin["id"]

        return jsonify({"status": "success"})


@app.route("/_/auth/create", methods=["GET", "POST"])
def admin_create():
    db_admins = Admin.getAll()
    if len(db_admins) > 0:
        return redirect("/_/auth/login")
    if request.method == "GET":
        return render_template("admin/create.html")
    if request.method == "POST":
        schema = CreateAccountSchema()
        try:
            body = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400  # Return errors in json

        salt = bcrypt.gensalt()
        body["password"] = bcrypt.hashpw(str(body["password"]).encode("utf-8"), salt)

        db_admin = Admin.new(**body)  # Turn input into db object

        session["admin_id"] = db_admin["id"]  # log user in after create account
        return jsonify({"status": "success"})
