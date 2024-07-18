import os
import json
import requests
from flask import (Flask, request, redirect, session, 
                   url_for, render_template, flash, make_response)

''''
Import our Classes
'''
from user_session import UserSession
from spotify_client import SpotifyClient
from openai_client import OpenAIClient

'''
Import our modules
'''
from user_form import UserForm
from pull_playlist import *
from insights_module import *


app = Flask(__name__) # static_folder="static", static_url_path=""
app.config['SECRET_KEY'] = os.urandom(64)   # generate random session key


CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
USER_KEY = os.environ.get("USER_KEY")
SCOPE = 'playlist-read-private user-library-read user-read-recently-played'
REDIECT_URI = 'http://localhost:3000/callback'

# Connect to the spotify API
spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIECT_URI, SCOPE)
# Connect to OpenAI API
openai_client = OpenAIClient(USER_KEY)
# Start user session
user_session = UserSession()

# Route to start the authorization process
@app.route('/')
def login():
    return redirect(spotify_client.get_auth_url())

# Callback route to handle the redirect from Spotify
@app.route('/callback')
def callback():
    code = request.args.get('code')
    spotify_client.get_token(code)
    user_session.set_token(spotify_client.token)
    return redirect(url_for('home'))

@app.route('/home')
def home():
  return render_template('home.html')


@app.route('/mood')
def mood():
    # Dictioanry of songs and artists
    tracks_artists = {}
    # Readable string of playlist songs
    tracks_artists_str = ""
    prompt = (
            f"Give me a mood (an emotion) " 
            f"based on my favorite recent songs: "
            f"{tracks_artists_str}. "
            f"Please give me a one or two word mood."
            )
    response = openai_client.get_chat_response(prompt)
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

        recommendations = openai_client.get_chat_response(prompt)
        song_list = spotify_client.extract_song_titles(recommendations)

        song_with_preview = []
        for song in song_list:
            track_id, preview_url, artist_name = spotify_client.get_song_data(song)
            if track_id and preview_url and artist_name:
               song_with_preview.append({'song': song, 'artist': artist_name, 'track_id': track_id, 'preview_url': preview_url})

        for song in song_with_preview:
            song['link'] = spotify_client.get_song_link(song['track_id'])

        return render_template('submit_page.html', 
                               title='Submitted Data', 
                               user_data = user_data, 
                               recommendations = song_with_preview
                               )
    else:
        return redirect(url_for('user_form'))

              
@app.route('/', methods=['GET', 'POST'])
@app.route('/insights', methods=['GET', 'POST'])
def insights():
    if request.method == 'POST':
        print("Form submitted")
        playlist_url = request.form.get('playlist_url')
        print(f"Received playlist URL: {playlist_url}")
        
        if playlist_url:
            track_artist = spotify_client.get_public_playlist_data(playlist_url)
            
            if track_artist:
                tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in track_artist.items()])
                
                prompt = (f'Here is my playlist: {tracks_artists_str}. '
                          f'I want to know what these songs say about my: '
                          f'1. Musical preferences,'
                          f'2. Personal insights, and '
                          f'3. Personality. '
                          f'Be concise and format with line breaks between '
                          f'each insight.')
                
                chat_response = openai_client.get_chat_response(prompt)
                chat_response = chat_response.replace('\n', '<br>')


                return render_template('result.html', chat_response=chat_response)
        
        flash("Please enter a valid playlist URL.")
        return redirect(url_for('insights'))
    
    return render_template('insights.html')
            

if __name__ == '__main__': 
    app.run(debug=True, host="0.0.0.0", port=3000)
