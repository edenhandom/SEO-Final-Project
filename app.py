
import os
import json
import openai
import requests
from openai import OpenAI
import re
import sys
import io
import base64
import logging

#from spotipy import Spotify
#from spotipy.oauth2 import SpotifyOAuth

from flask import (Flask, request, redirect, session, 
                   url_for, render_template, flash, make_response)


'''
Import our modules
'''
from user_form import UserForm
from pull_playlist import *


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__) # static_folder="static", static_url_path=""
app.config['SECRET_KEY'] = os.urandom(64)


# FOR SPOTIFY API
#CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_ID = 'ad91a46157df4ba080456f92c7a74ef8'
#CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
CLIENT_SECRET= '9d4140d511c64467a582b075b990cbfe'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

redirect_uri = 'http://localhost:3000/callback'
SCOPE = 'playlist-read-private user-library-read user-read-recently-played'


# FOR OPEN AI API
#USER_KEY = os.environ.get("USER_KEY")
USER_KEY = ''
client = OpenAI(api_key=USER_KEY)


@app.route('/')
def login():
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={redirect_uri}&show_dialog=True"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_token_url = 'https://accounts.spotify.com/api/token'
    auth_token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
    }
    auth_token_headers = {
        'Authorization': 'Basic ' + base64.b64encode((CLIENT_ID + ':' + CLIENT_SECRET).encode()).decode()
    }
    response = requests.post(auth_token_url, data=auth_token_data, headers=auth_token_headers)
    response_data = response.json()
    session['token'] = response_data['access_token']
    return redirect(url_for('home'))

@app.route('/mood')
def mood():
    token = session.get('token')
    if not token:
        return redirect(url_for('home'))
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    profile_url = 'https://api.spotify.com/v1/me'

    try: 
        profile_response = requests.get(profile_url, headers=headers)
        profile_data = profile_response.json()

    except requests.exceptions.JSONDecodeError:
        print(profile_response.status_code)
        print("HTTP RESPONSE")

    # profile_data = profile_response.json()
    
    playlists_url = 'https://api.spotify.com/v1/me/playlists'
    playlists_response = requests.get(playlists_url, headers=headers)
    playlists_data = playlists_response.json()

    recent_tracks_url = 'https://api.spotify.com/v1/me/player/recently-played'
    recent_tracks_response = requests.get(recent_tracks_url, headers=headers)
    recent_tracks_data = recent_tracks_response.json()

    tracks_artists = {
        track['track']['name']: ', '.join([artist['name'] for artist in track['track']['artists']])
        for track in recent_tracks_data['items']
    }
    tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in tracks_artists.items()])
    prompt = (
            f"Give me a mood (like an emotion) " 
            f"based on my favorite recent songs: "
            f"{tracks_artists_str}. "
            f"Please give me a one or two word mood."
            )

    response = get_chat_response(prompt)

    return render_template('mood.html', top_tracks = tracks_artists, response = response)


@app.route('/clear-session')
def clear_session():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/top-artists')
def top_artists():
    token = session.get('token')
    if not token:
        return redirect(url_for('home'))
    headers = {
        'Authorization': f'Bearer {token}'
    }

    top_artists_url = 'https://api.spotify.com/v1/me/top/artists'
    top_artists_response = requests.get(top_artists_url, headers=headers)
    top_artists_data = top_artists_response.json()

    artist_names = [artist['name'] for artist in top_artists_data['items']]

    return f"Top Artists: {json.dumps(artist_names, indent=4)}"


@app.route('/home')
def home():
  return render_template('home.html')


# Adding User Form page to website
@app.route('/user_form', methods=['GET', 'POST'])
def user_form():
    form = UserForm()
    if form.validate_on_submit():
        # Store form data in session
        session['user_data'] = {
            'star_sign': form.star_sign.data,
            'personality_traits': form.personality_traits.data,
            'fav_genre1': form.fav_genre1.data,
            'fav_genre2': form.fav_genre2.data,
            'fav_genre3': form.fav_genre3.data
            }
        return redirect(url_for('submit_page'))
    
    return render_template('user_form.html', title='Info', form=form)


# For submission page, brings user here after they submit form
@app.route('/submit_page')
def submit_page():
    # Retrieve user data from session
    user_data = session.get('user_data', None)
    
    if user_data:
        star_sign = user_data.get('star_sign', 'Unknown')
        personality_traits = user_data.get('personality_traits', 'Unknown')
        fav_genre1 = user_data.get('fav_genre1', 'Unknown')
        fav_genre2 = user_data.get('fav_genre2', 'Unknown')
        fav_genre3 = user_data.get('fav_genre3', 'Unknown')

        prompt = (
            f"Give me a playlist of recommended songs based on my "
            f"star sign: {star_sign}, personality traits: {personality_traits}, "
            f"and my preference of these genres: {fav_genre1}, {fav_genre2}, {fav_genre3}. "
            f"Please list each song on a new line, song title only in quotes. "
            f"Format like: 'Song1'\n 'Song2'\n...'"
            )

        recommendations = get_chat_response(prompt)
        song_list = extract_song_titles(recommendations)

        song_with_preview = []
        for song in song_list:
            track_id, preview_url, artist_name = get_song_data(song)
            if track_id and preview_url and artist_name:
               song_with_preview.append({'song': song, 'artist': artist_name, 'track_id': track_id, 'preview_url': preview_url})

        for song in song_with_preview:
            song['link'] = get_song_link(song['track_id'])

        return render_template('submit_page.html', 
                               title='Submitted Data', 
                               user_data = user_data, 
                               recommendations = song_with_preview
                               )
    else:
        return redirect(url_for('user_form'))

              
@ app.route('/', methods=['GET', 'POST'])
@app.route('/insights', methods=['GET', 'POST'])
def insights():
    if request.method == 'POST':
        print("Form submitted")
        playlist_url = request.form.get('playlist_url')
        print(f"Received playlist URL: {playlist_url}")
        
        if playlist_url:
            track_artist = get_playlist_data(playlist_url)
            
            if track_artist:
                tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in track_artist.items()])
                
                prompt = (f'Here is my playlist: {tracks_artists_str}. '
                          f'I want to know what these songs say about my: '
                          f'1. Musical preferences,'
                          f'2. Personal insights, and '
                          f'3. Personality. '
                          f'Be concise and format with line breaks between '
                          f'each insight.')
                
                chat_response = get_chat_response(prompt)
                chat_response = chat_response.replace('\n', '<br>')


                return render_template('result.html', chat_response=chat_response)
        
        flash("Please enter a valid playlist URL.")
        return redirect(url_for('insights'))
    
    return render_template('insights.html')
            

if __name__ == '__main__': 
    app.run(debug=True, host="0.0.0.0", port=3000)
