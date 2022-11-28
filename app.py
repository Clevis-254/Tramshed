import functools
from flask import Flask, render_template, session
from flask_migrate import Migrate
from flask_session import Session
from db import db, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045
db.init_app(app)
# https://flask-migrate.readthedocs.io/en/latest/
Migrate(app, db)

app.config["SECRET_KEY"] = "<super secret key used for sessions>"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 12  # Session valid for 12 hrs
# TODO: Work on clearing session from db
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SESSION_SQLALCHEMY"] = db

sess = Session(app)


def use_user(func):
    @functools.wraps(func)
    def get_user(*args, **kwargs):
        sess_user_id = session.get("user_id")
        if sess_user_id == None:
            return func(None, *args, **kwargs)
        db_user = User.query.get(sess_user_id)
        if not db_user == None:
            return func(db_user, *args, **kwargs)

        return func(None, *args, **kwargs)

    return get_user


@app.get("/")
@use_user
def homepage(user):

    return render_template("index.html", user=user)


import user

if __name__ == "__main__":
    with app.app_context():
        # https://stackoverflow.com/a/45887721
        sess.app.session_interface.db.create_all()

    app.run(debug=True)
