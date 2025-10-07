from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.column(db.Integer, primary_key=True)
    user = db.column(db.String(80), unique=True, nullable=False)
    email = db.column(db.String(120), unique=True, nullable=False)
    password_hash = db.column(db.String(128), nullable=False)
    entries = db.relationship("Entry", backref="user", lazy=True)

    def set_password(self, password):
        self.pass_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pass_hash, password)


class Entry(db.model):
    id = db.column(db.Integer, primary_key=True)
    user_id = db.column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.column(db.Float, nullable=False)
    category = db.column(db.String(50), nullable=False)
    entry_type = db.column(db.String(10), nullable=False)  # 'income' or 'expense'
    date = db.column(db.DateTime, default=datetime.utcnow)
    description = db.column(db.String(200))

    def __repr__(self):
        return f"<Entry{self.title}({self.entry_type}, {self.amount} on {self.date})>"
