from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class UserForm(FlaskForm):
    star_sign = StringField(
        'Star Sign', 
        validators=[DataRequired()],
        render_kw={"placeholder": "✴ Enter your astrology sign: "}
        )
    personality_traits = TextAreaField(
        'Personality Traits', 
        validators=[DataRequired()],
        render_kw={
          "placeholder": (
              "✰ Enter some personality traits!"
              "ex. silly, mellow, creative, etc."
            )
        }
    )

    fav_genre1 = StringField(
        'Favorite Genre 1', 
        validators=[DataRequired()],
        render_kw={"placeholder": "✴ Enter a favorite genre: "}
        )
    optional_field1 = StringField(
        'Additional Info 1', validators=[Optional()],
        render_kw={"placeholder": "✰ Example song/artist: "}
        )
    fav_genre2 = StringField(
        'Favorite Genre 2', validators=[DataRequired()],
        render_kw={"placeholder": "✴ Enter a favorite genre: "}
        )
    optional_field2 = StringField(
        'Additional Info 2', validators=[Optional()],
        render_kw={"placeholder": "✰ Example song/artist: "}
        )
    fav_genre3 = StringField(
        'Favorite Genre 3', validators=[DataRequired()],
        render_kw={"placeholder": "✴ Enter a favorite genre: "}
        )
    optional_field3 = StringField(
        'Additional Info 3', 
        validators=[Optional()],
        render_kw={"placeholder": "✰ Example song/artist: "}
        )
    
    include_history = SelectField(
        "Use your recent listening history in our recommendations?",
        choices=[('yes','Yes!'),('no','No way!')],
        validators=[DataRequired()]
    )

    submit = SubmitField('Submit')