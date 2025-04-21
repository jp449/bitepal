from . import db
from flask_login import UserMixin
from sqlalchemy import (
    CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint,
    Integer, Text, Identity
)
from sqlalchemy.orm import Mapped, mapped_column, relationship



class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)  # Matches the schema
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)  # Plain-text password
    is_admin = db.Column(db.Boolean, default = False)
    def get_id(self):
        return str(self.user_id)

    reviews = db.relationship('Reviews', back_populates='user')


class Reviews(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 5', name='reviews_score_check'),
        ForeignKeyConstraint(['recipe_id'], ['recipes.recipe_id'], name='reviews_recipe_id_fkey', ondelete='CASCADE'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], name='reviews_user_id_fkey', ondelete='CASCADE'),
        PrimaryKeyConstraint('review_id', name='reviews_pkey')
    )

    review_id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    score: Mapped[int] = mapped_column(Integer)
    review_text: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable = False)
    recipe_id: Mapped[int] = mapped_column(Integer)

    recipe: Mapped['Recipes'] = relationship('Recipes', back_populates='reviews')
    user: Mapped['Users'] = relationship('Users', back_populates='reviews')


class Recipes(db.Model):
    __tablename__ = 'recipes'
    recipe_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Integer, nullable = False, default = 0)
    region_category = db.Column(db.String(50), nullable = False, default = 'Unknown')
    instructions = db.Column(db.Text, nullable = False)
    servings = db.Column(db.Integer, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)

    reviews = db.relationship('Reviews', back_populates='recipe', lazy=True)
    author = db.relationship('Users', backref='recipes')
    
class Ingredients(db.Model):
    __tablename__='ingredients'
    name = db.Column(db.Text, nullable = False)
    ingredient_id = db.Column(db.Integer, primary_key = True)
    ingredient_type = db.Column(db.Text, nullable = False)
    
class DietaryRestrictions(db.Model):
    __tablename__ = 'dietary_restrictions'
    dietary_restriction_id = db.Column(db.Integer, primary_key = True)
    dietary_preference = db.Column(db.String, nullable = False)
    name = db.Column(db.Text, nullable = False)
    __table_args__ = (CheckConstraint("dietary_preference IN ('allergy', 'preference')", name = 'dietary_preference_check'))
    
class UserRestrictions(db.Model):
    __tablename__ = 'user_restrictions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete = 'CASCADE'), nullable = False)
    restriction_id = db.Column(db.Integer. db.ForeignKey('dietary_restrictions.dietary_restriction_id'), nullable = False)
    __table_args__ = (PrimaryKeyConstraint('user_id', 'restriction_id', name = 'user_restrictions_pkey'))