'''
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

class PlaylistForm(FlaskForm):
    playlist_url = StringField('Spotify Playlist URL', validators=[DataRequired(), URL(message='Must be a valid URL')])
    submit = SubmitField('Submit')

'''