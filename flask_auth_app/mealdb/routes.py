import os

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify, current_app
from werkzeug.utils import secure_filename

from .forms import RegistrationForm, LoginForm, RecipeForm, IngredientsForm, ReviewForm, RecipeIngredientsForm
from .models import Recipes, Users, Ingredients, UserRestrictions, DietaryRestrictions, Reviews, RecipeIngredients, \
    AvgRecipeRating, SavedRecipeList
from . import db

from sqlalchemy.sql.expression import any_
from sqlalchemy import exists

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
    average_ratings = {r.recipe_id: r.average_score for r in AvgRecipeRating.query.all()}
    return render_template('my_recipes.html', recipes=recipes,average_ratings=average_ratings)

@main.route('/view_recipes')
@login_required
def view_recipes():
    recipes = Recipes.query.all()
    average_ratings = {r.recipe_id: r.average_score for r in AvgRecipeRating.query.all()}
    return render_template('view_recipes.html', recipes=recipes,average_ratings=average_ratings)

@main.route('/view_recipes/<int:recipe_id>',methods = ['GET','POST'])
def recipe_page(recipe_id):
    recipe = Recipes.query.get_or_404(recipe_id)
    form = ReviewForm()
    #no review form if admin
    if current_user.is_admin:
        return render_template('recipe.html', recipe=recipe, form=None)
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
    rating_entry = AvgRecipeRating.query.filter_by(recipe_id=recipe_id).first()
    average_rating = rating_entry.average_score if rating_entry else None
    return render_template('recipe.html', recipe=recipe,form=form,average_rating=average_rating)

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
        
    except Exception as e:
        flash("not working")
        print("Error deleting recipe:", str(e))
    return redirect(url_for('main.my_recipes'))
    
@main.route('/create_recipe', methods=['GET', 'POST'])
@login_required
def create_recipe():
    recipe_form = RecipeForm()
    if current_user.is_admin:
        flash("Admins are not allowed to create recipes.", 'danger')
        return redirect(url_for('main.home'))
    ingredient_form = IngredientsForm()
    recipe_ingredient = RecipeIngredientsForm()
    if recipe_form.validate_on_submit():
        filename = None

        if recipe_form.image.data:
            image = recipe_form.image.data
            print("Content-Type:", image.content_type)
            print("Filename:", image.filename)

            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.root_path, 'static/uploads', filename))
        if recipe_form.validate_on_submit():
            new_recipe = Recipes(
                title = recipe_form.title.data,
                calories = recipe_form.calories.data,
                region_category = recipe_form.region_category.data,
                instructions = recipe_form.instructions.data,
                servings = recipe_form.servings.data,
                user_id = current_user.user_id,
                image_path=f'uploads/{filename}' if filename else None
            )
        db.session.add(new_recipe)
        db.session.flush()
        
        names = request.form.getlist('name')
        types = request.form.getlist('type')
        amounts = request.form.getlist('amount')
        units = request.form.getlist('unit')
        
        for name, type_, amount, unit in zip(names, types, amounts, units):
            if name.strip() == "" or unit.strip() == "":
                continue
            if ingredient_form.validate_on_submit():
                new_ingredient = Ingredients(
                    name = name,
                    type = type_
                )
                
                db.session.add(new_ingredient)
                db.session.flush()
                
                new_recipe_ingredient = RecipeIngredients(
                    recipe_id = new_recipe.recipe_id,
                    ingredient_id = new_ingredient.ingredient_id,
                    amount = amount,
                    unit = unit
                )
                db.session.add(new_recipe_ingredient )
        db.session.commit()
        
        return redirect(url_for('main.my_recipes'))

    return render_template('create_recipe.html', form = recipe_form, ingredient_form = ingredient_form, recipe_ingredient = recipe_ingredient)


@main.route('/my_preferences', methods = ['GET', 'POST'])
@login_required
def load_preferences():
    if current_user.is_admin:
        flash("Admins do not have dietary_restrictions.", 'danger')
        return redirect(url_for('main.home'))
    user_preferences = db.session.query(UserRestrictions, DietaryRestrictions).join(
        DietaryRestrictions, UserRestrictions.restriction_id == DietaryRestrictions.dietary_restriction_id
    ).filter(UserRestrictions.user_id== current_user.user_id).all()
    
    all_restrictions = DietaryRestrictions.query.all()
    
    allergies = db.session.query(DietaryRestrictions.name).join(UserRestrictions,
        UserRestrictions.restriction_id == DietaryRestrictions.dietary_restriction_id
    ).filter(
        UserRestrictions.user_id == current_user.user_id,
        DietaryRestrictions.dietary_preference == 'allergy'
    ).all()
    allergy_names = [allergy.name for allergy in allergies]

    preferences = db.session.query(DietaryRestrictions.name).join(UserRestrictions,
        UserRestrictions.restriction_id == DietaryRestrictions.dietary_restriction_id
    ).filter(
        UserRestrictions.user_id == current_user.user_id,
        DietaryRestrictions.dietary_preference == 'preference'
    ).all()
    preference_names = [preference.name for preference in preferences]
    
    #for specific preferences, allergies, filter
    excluded_ingredient_types = []
    excluded_ingredients = []
    if 'tree nuts' in allergy_names:
        excluded_ingredient_types.extend(['nut'])
    if 'waters' in allergy_names:
        excluded_ingredient_types.extend(['water'])
    if 'gluten' in allergy_names:
        excluded_ingredient_types.extend(['grain'])
    if 'peanuts' in allergy_names:
        excluded_ingredients.extend(['peanuts'])
    if 'shellfish' in allergy_names:
        excluded_ingredient_types.extend(['seafood'])
    if 'fruit' in allergy_names:
        excluded_ingredient_types.extend(['fruit', 'juice'])
    if 'kiwi' in allergy_names:
        excluded_ingredients.extend(['kiwi'])
    
    #preferences
    if 'vegetarian' in preference_names:
        excluded_ingredient_types.extend(['meat', 'poultry', 'seafood'])

    if 'pescatarian' in preference_names:
        excluded_ingredient_types.extend(['meat', 'poultry'])
    if 'lactose-intolerance' in preference_names:
        excluded_ingredient_types.extend(['dairy', 'egg'])
    if 'keto' in preference_names:
        excluded_ingredient_types.extend(['sugar'])

    print("Excluded Ingredient Types:", excluded_ingredient_types)
    print("Excluded Ingredients:", excluded_ingredients)

    filtered_recipes = Recipes.query

    # only filter if stuff should be excluded
    if excluded_ingredient_types or excluded_ingredients:
        subquery = db.session.query(RecipeIngredients.recipe_id).join(
            Ingredients, RecipeIngredients.ingredient_id == Ingredients.ingredient_id
        )

        if excluded_ingredient_types:
            subquery = subquery.filter(
                Ingredients.type.ilike(any_(excluded_ingredient_types))
            )
        if excluded_ingredients:
            subquery = subquery.filter(
                Ingredients.name.ilike(any_(excluded_ingredients))
            )

        # if recipe doesn't have anything of type/name excluded in its ingredients
        subquery = subquery.subquery()
        filtered_recipes = filtered_recipes.filter(
            ~exists().where(Recipes.recipe_id == subquery.c.recipe_id)
        )
    
    filtered_recipes.distinct().all()

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
                flash("Preference/Allergy added", 'success')
            else:
                flash("This preference/allergy is already added.", 'info')
        
        #deleting own dietary restrictions
        delete_restriction_id = request.form.get('delete_restriction_id')
        if delete_restriction_id:
            user_restriction = UserRestrictions.query.filter_by(
                user_id =current_user.user_id, restriction_id = delete_restriction_id).first()
            if user_restriction:
                db.session.delete(user_restriction)
                db.session.commit()
                flash("Preference/Allergy removed", 'success')
            else:
                flash("Preference/Allergy couldn't be removed", 'danger')
        return redirect(url_for('main.load_preferences'))
    
    return render_template(
        'my_preferences.html',
        user_preferences=user_preferences,
        all_restrictions=all_restrictions, 
        filtered_recipes=filtered_recipes
    )
@main.route('/save_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    saved = SavedRecipeList(user_id=current_user.user_id, recipe_id=recipe_id)
    try:
        db.session.add(saved)
        db.session.commit()
    except:
        db.session.rollback()  # silently skip if already saved
    return redirect(url_for('main.view_recipes'))


@main.route('/saved_recipes')
@login_required
def saved_recipes():
    saved = SavedRecipeList.query.filter_by(user_id=current_user.user_id).all()
    recipe_ids = [s.recipe_id for s in saved]
    recipes = Recipes.query.filter(Recipes.recipe_id.in_(recipe_ids)).all()
    return render_template('saved_recipes.html', recipes=recipes)



    