from flask import Blueprint, render_template, request, redirect, flash, url_for
from app.models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint('auth', __name__)

# -----------------------------
# SIGNUP (REGISTER) ROUTE
# -----------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already registered. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("✅ Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# -----------------------------
# LOGIN ROUTE
# -----------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Login successful!", "success")
            return redirect(url_for("note.select"))  # 👈 redirect to note selection

        flash("❌ Invalid email or password", "danger")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

# -----------------------------
# LOGOUT ROUTE
# -----------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("✅ Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
