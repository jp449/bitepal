from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)  # Matches the schema
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)  # Plain-text password
    def get_id(self):
        return str(self.user_id)
    
class Recipe(db.Model):
    __tablename__ = 'recipes'
    recipe_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Integer)
    region_category = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    servings = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)