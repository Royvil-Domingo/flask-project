from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from ..extensions import db
from ..models.user import User
from ..models.borrower import Borrower

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', category='error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.first_name}!', category='success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Incorrect email or password.', category='error')

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='success')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('firstName', '').strip()
        contact = request.form.get('contact', '').strip()
        password1 = request.form.get('password1', '')
        password2 = request.form.get('password2', '')

        existing_user = User.query.filter_by(email=email).first()

        # Role is never read from the submitted form. Every public
        # registration is hardcoded to 'borrower' below — there is no
        # code path by which a client can request 'admin'.
        if existing_user:
            flash('An account with that email already exists.', category='error')
        elif len(email) < 4 or '@' not in email:
            flash('Please enter a valid email address.', category='error')
        elif len(first_name) < 2:
            flash('Full name must be at least 2 characters.', category='error')
        elif len(contact) < 5:
            flash('Please provide a valid contact number.', category='error')
        elif password1 != password2:
            flash("Passwords don't match.", category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            try:
                new_user = User(email=email, first_name=first_name, role='borrower')
                new_user.set_password(password1)
                db.session.add(new_user)
                db.session.flush()  # assigns new_user.id without committing yet

                new_borrower = Borrower(user_id=new_user.id, name=first_name, contact=contact)
                db.session.add(new_borrower)

                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created successfully! Welcome aboard.', category='success')
                return redirect(url_for('main.dashboard'))
            except Exception:
                db.session.rollback()
                flash('An error occurred while creating your account. Please try again.', category='error')

    return render_template('auth/register.html')