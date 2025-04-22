from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, NumberRange


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    
# class LogoutForm(FlaskForm):
#     submit = SubmitField('Logout')

class RecipeForm(FlaskForm):
    title = StringField('Title', validators = [DataRequired()])
    calories = IntegerField('Calories', validators=[Optional(), NumberRange(min=0)], default=0)
    region_category = StringField('Region of Origin', validators = [Optional()], default = 'Unknown')
    instructions = TextAreaField('Instructions', validators = [DataRequired()])
    servings = IntegerField('Servings', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Create Recipe')
    
class IngredientsForm(FlaskForm):
    ingredient_id = IntegerField('Ingredient ID', validators=[DataRequired()])
    amount = StringField('Amount', validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired()])