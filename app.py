from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_file,
)
from models import db, User, Entry
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange

app = Flask(__name__)
app.config["SECRET_KEY"] = "mani"  # Change this in production!
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///D:/databases/budget.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )


class loginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("password", validators=[DataRequired()])


class EntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    amount = FloatField("Amount", validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField(
        "Category",
        choices=[
            ("food", "Food"),
            ("transport", "Transport"),
            ("bills", "Bills"),
            ("entertainment", "Entertainment"),
            ("shopping", "Shopping"),
            ("healthcare", "Healthcare"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    entry_type = SelectField(
        "Type",
        choices=[("income", "Income"), ("expense", "Expense")],
        validators=[DataRequired()],
    )
    date = DateField("Date", validators=[DataRequired()], default=date.today)
