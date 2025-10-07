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
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
    UserMixin,
)
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import csv
import io
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


class LoginForm(FlaskForm):
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
# adding routes for the app
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please log in.", "warning")
            return render_template("register.html", form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken!", "danger")
            return render_template("register.html", form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    # Get current month and year
    current_month = request.args.get("month", datetime.now().strftime("%Y-%m"))

    try:
        # Parse the month parameter
        year, month = map(int, current_month.split("-"))
        start_date = date(year, month, 1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
    except ValueError:
        # If invalid, default to current month
        start_date = date.today().replace(day=1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
        current_month = start_date.strftime("%Y-%m")

    # Get entries for the selected month
    entries = (
        Entry.query.filter(
            Entry.user_id == current_user.id,
            Entry.date >= start_date,
            Entry.date <= end_date,
        )
        .order_by(Entry.date.desc())
        .all()
    )

    # Calculate totals
    total_income = sum(e.amount for e in entries if e.entry_type == "income")
    total_expenses = sum(e.amount for e in entries if e.entry_type == "expense")
    balance = total_income - total_expenses

    # Calculate category-wise expenses
    categories = {}
    for entry in entries:
        if entry.entry_type == "expense":
            categories[entry.category] = (
                categories.get(entry.category, 0) + entry.amount
            )

    # Prepare data for chart
    chart_data = {
        "labels": list(categories.keys()),
        "values": list(categories.values()),
    }

    # Navigation for previous/next month
    prev_month = (start_date - relativedelta(months=1)).strftime("%Y-%m")
    next_month = (start_date + relativedelta(months=1)).strftime("%Y-%m")
    current_month_name = start_date.strftime("%B %Y")

    return render_template(
        "dashboard.html",
        entries=entries,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        chart_data=chart_data,
        current_month=current_month,
        current_month_name=current_month_name,
        prev_month=prev_month,
        next_month=next_month,
    )


@app.route("/add_entry", methods=["GET", "POST"])
@login_required
def add_entry():
    form = EntryForm()
    if form.validate_on_submit():
        entry = Entry(
            title=form.title.data,
            amount=form.amount.data,
            category=form.category.data,
            entry_type=form.entry_type.data,
            date=form.date.data,
            user_id=current_user.id,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Entry added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_entry.html", form=form, title="Add New Entry")


@app.route("/edit_entry/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("You do not have permission to edit this entry.", "danger")
        return redirect(url_for("dashboard"))

    form = EntryForm(obj=entry)
    if form.validate_on_submit():
        form.populate_obj(entry)
        db.session.commit()
        flash("Entry updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "edit_entry.html", form=form, entry=entry, title="Edit Entry"
    )


@app.route("/delete_entry/<int:entry_id>")
@login_required
def delete_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("You do not have permission to delete this entry.", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/export_csv")
@login_required
def export_csv():
    # Create in-memory CSV file
    si = io.StringIO()
    cw = csv.writer(si)

    # Write header
    cw.writerow(["Title", "Amount", "Category", "Type", "Date"])

    # Write entries
    entries = Entry.query.filter_by(user_id=current_user.id).order_by(Entry.date).all()
    for entry in entries:
        cw.writerow(
            [entry.title, entry.amount, entry.category, entry.entry_type, entry.date]
        )

    # Create response
    output = si.getvalue()
    si.close()

    return send_file(
        io.BytesIO(output.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f'budget_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv',
    )


# Create tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
