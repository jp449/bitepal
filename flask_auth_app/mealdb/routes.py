from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify
from .forms import RegistrationForm, LoginForm, RecipeForm, IngredientsForm, ReviewForm
from .models import Recipes, Users, Ingredients, UserRestrictions, DietaryRestrictions, Reviews
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
        existing_user = Users.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('main.register'))
        
        # Create a new user without hashing the password
        new_user = Users(username=form.username.data, password=form.password.data)
        
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
        user = Users.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('You are now logged in.')
            return redirect(url_for('main.home'))
        elif not user:
            flash('User does not exist. Please register user.')
            return redirect(url_for('main.register'))
        else:
            flash('Login info incorrect.')
    return render_template('login.html', form = form)

@main.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))
 

@main.route('/test-db')
def test_db():
    try:
        # Perform a simple query to check the connection
        users = Users.query.all()  # Fetch all users from the 'users' table
        return f"Database connected! Found {len(users)} users."
    except Exception as e:
        return f"Database connection failed: {str(e)}"
    

@main.route('/my_recipes')
@login_required
def my_recipes():
    if current_user.is_admin: 
        return redirect(url_for('main.view_recipes'))
    recipes = Recipes.query.filter_by(user_id=current_user.user_id).all()
    return render_template('my_recipes.html', recipes=recipes)

@main.route('/view_recipes')
@login_required
def view_recipes():
    recipes = Recipes.query.all()
    return render_template('view_recipes.html', recipes=recipes)

@main.route('/view_recipes/<int:recipe_id>',methods = ['GET','POST'])
def recipe_page(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = ReviewForm()
    if form.validate_on_submit():
        new_review = Reviews(
            score=int(form.score.data),
            review_text=form.review_text.data,
            user_id=current_user.user_id,
            recipe_id=recipe.recipe_id
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('main.recipe_page', recipe_id=recipe_id))
    return render_template('recipe.html', recipe=recipe,form=form)

@main.route('/admin/users', methods = ['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    users = Users.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        deleted_user = Users.query.filter_by(username=username)
        if deleted_user:
            db.session.delete(deleted_user)
            db.session.commit()
            flash(f"User {username} deleted.", 'success')
        else:
            flash(f"User {username} not found", 'danger')
    return render_template('admin_users.html', users = users)

@main.route('/delete_recipe/<int:recipe_id>')
@login_required
def delete_recipe(recipe_id):
    try:
        recipe = Recipes.query.get_or_404(recipe_id)
        if not current_user.is_admin and recipe.user_id != current_user.user_id:
            flash("You are not authorized to delete user {recipe.user_id}'s recipe." \
            "You may only delete your recipes.")
            return redirect(url_for('main.my_recipes'))
        
        #delete recipe only if admin or is own recipe
        db.session.delete(recipe)
        db.session.commit()
        flash("Recipe deleted successfully!")
        return jsonify({'success': True, 'message': 'Recipe deleted successfully.'})
    except Exception as e:
        flash("not working")
        print("Error deleting recipe:", str(e))
    return redirect(url_for('main.my_recipes'))
    
@main.route('/create_recipe', methods=['GET', 'POST'])
@login_required
def create_recipe():
    recipe_form = RecipeForm()
    ingredient_form = IngredientsForm()
    if recipe_form.validate_on_submit():
        new_recipe = Recipes(
            title = request.recipe_form.title.data,
            calories = request.recipe_form.calories.data,
            region_category = request.recipe_form.region_category.data,
            instructions = request.recipe_form.instructions.data,
            servings = request.recipe_form.servings.data,
            user_id = current_user.user_id.data
        )  
        db.session.add(new_recipe)
        db.session.commit()
        
        flash("Recipe created successfully!")
        return redirect(url_for('main.my_recipes'))
    return render_template('create_recipe.html', recipe_form = recipe_form, ingredient_form = ingredient_form)

@main.route('/create_ingredient', methods=['GET', 'POST'])
@login_required
def create_ingredients():
    form = IngredientsForm()
    if current_user.is_admin:
        flash("Admins are not allowed to create recipes.", 'danger')
        return redirect(url_for('main.home'))
    if form.validate_on_submit():
        new_ingredient = Ingredients(
            name = request.form.name.data,
            ingredient_type = request.form.ingredient_type.data
        )
        db.session.add(new_ingredient)
        db.session.commit()
        
        flash("Ingredient created successfully!")
        return redirect(url_for('main.my_recipes'))
    return render_template('create_ingredient.html', form = form)

@main.route('/my_preferences', methods = ['GET', 'POST'])
@login_required
def load_preferences():
    user_preferences = db.session.query(UserRestrictions, DietaryRestrictions).join(
        DietaryRestrictions, UserRestrictions.restriction_id == DietaryRestrictions.dietary_restriction_id
    ).filter(UserRestrictions.user_id== current_user.user_id).all()
    
    all_restrictions = DietaryRestrictions.query.all()

    if request.method == 'POST':
        restriction_id = request.form.get('restriction_id')
        new_restriction_name = request.form.get('new_restriction_name')
        new_restriction_type = request.form.get('new_restriction_type')
        if new_restriction_name:  # If the user entered a new restriction
            # Check if the restriction already exists
            existing_restriction = DietaryRestrictions.query.filter_by(name=new_restriction_name).first()
            if not existing_restriction:
                # Add the new restriction to the DietaryRestrictions table
                new_restriction = DietaryRestrictions(
                    dietary_preference=new_restriction_type,
                    name=new_restriction_name
                )
                db.session.add(new_restriction)
                db.session.flush()  # get id of newly created object: https://stackoverflow.com/questions/4201455/sqlalchemy-whats-the-difference-between-flush-and-commit
                restriction_id = new_restriction.dietary_restriction_id
            else:
                restriction_id = existing_restriction.dietary_restriction_id

         # Add the restriction to the UserRestrictions table
        if restriction_id:
            existing_user_restriction = UserRestrictions.query.filter_by(
                user_id=current_user.user_id, restriction_id=restriction_id
            ).first()
            if not existing_user_restriction:
                new_user_restriction = UserRestrictions(
                    user_id=current_user.user_id,
                    restriction_id=restriction_id
                )
                db.session.add(new_user_restriction)
                db.session.commit()
                flash("Preference/Allergy added successfully!", 'success')
            else:
                flash("This preference/allergy is already added.", 'info')
        return redirect(url_for('main.load_preferences'))
    
    return render_template(
        'my_preferences.html',
        user_preferences=user_preferences,
        all_restrictions=all_restrictions
    )
    