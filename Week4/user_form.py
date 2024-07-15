from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class UserForm(FlaskForm):
    star_sign = StringField('Star Sign', validators=[DataRequired()])
    personality_traits = TextAreaField('Personality Traits', validators=[DataRequired()])
    fav_genre1 = StringField('Favorite Genre 1', validators=[DataRequired()])
    fav_genre2 = StringField('Favorite Genre 2', validators=[DataRequired()])
    fav_genre3 = StringField('Favorite Genre 3', validators=[DataRequired()])
    submit = SubmitField('Submit')
