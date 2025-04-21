from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ReviewForm(FlaskForm):
    score = SelectField('Score (1–5)',
                        choices=[(str(i), i) for i in range(1, 6)],
                        validators=[DataRequired()])
    review_text = TextAreaField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit Review')
    
# class LogoutForm(FlaskForm):
#     submit = SubmitField('Logout')
    