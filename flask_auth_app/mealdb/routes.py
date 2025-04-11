from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from .forms import RegistrationForm, LoginForm
from .models import Recipe, User
from . import db

from flask_login import login_user,  login_required, current_user, logout_user
from functools import wraps

#admin only access message
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

#subpages defined-may need to modularize later

main = Blueprint('main', __name__)
@main.route('/')
@login_required
def home():
    return render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already in db
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('main.register'))
        
        # Create a new user without hashing the password
        new_user = User(username=form.username.data, password=form.password.data)
        
        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        #return user if in db already
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('You are now logged in.')
            return redirect(url_for('main.home'))
        else:
            flash('Login info incorrect.')
    return render_template('login.html', form = form)

@main.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.login"))
 

@main.route('/test-db')
def test_db():
    try:
        # Perform a simple query to check the connection
        users = User.query.all()  # Fetch all users from the 'users' table
        return f"Database connected! Found {len(users)} users."
    except Exception as e:
        return f"Database connection failed: {str(e)}"
    

@main.route('/my_recipes')
@login_required
def my_recipes():
    recipes = Recipe.query.filter_by(user_id=current_user.user_id).all()
    return render_template('my_recipes.html', recipes=recipes)

@main.route('/admin/users', methods = ['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        deleted_user = User.query.filter_by(username=username)
        if deleted_user:
            db.session.delete(deleted_user)
            db.session.commit()
            flash(f"User {username} deleted.", 'success')
        else:
            flash(f"User {username} no found", 'danger')
    return render_template('admin_users.html', users = users)