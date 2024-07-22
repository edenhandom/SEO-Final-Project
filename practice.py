from user_form import UserForm
import os
import json
import uuid
import requests
from flask import (Flask, request, redirect, session,
                   url_for, render_template, flash, make_response)
from flask_session import Session
from datetime import timedelta
import pandas as pd


''''
Import our Classes
'''
from user_session import UserSession
from spotify_client import SpotifyClient
from openai_client import OpenAIClient

'''
Import our modules
'''

# Initialize a global DataFrame to store recommended songs
recommended_songs_df = pd.DataFrame(
    columns=[
        'song',
        'artist',
        'track_id',
        'preview_url',
        'user_id'])


app = Flask(__name__)  # static_folder="static", static_url_path=""
app.config['SECRET_KEY'] = os.urandom(64)   # generate random session key
# Configure session to use filesystem (server-side session storage)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    days=7)  # Set session lifetime to 7 days
Session(app)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
USER_KEY = os.environ.get("USER_KEY")
SCOPE = 'playlist-read-private user-library-read user-read-recently-played'
REDIRECT_URI = os.environ.get("REDIRECT_URI")

# Connect to the spotify API
spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE)
# Connect to OpenAI API
openai_client = OpenAIClient(USER_KEY)
# Start user session
user_session = UserSession()

print(spotify_client.get_song_data("Seeing Green"))
print(spotify_client.get_song_data("Joro"))

# lst = []
# print(type(lst) is list)
