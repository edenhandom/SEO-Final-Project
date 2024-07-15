
import os
import json
import openai
import requests
from openai import OpenAI
import re
import sys
import io
import base64

from flask import (Flask, request, redirect, session, 
                   url_for, render_template, flash)

from user_form import UserForm

from pull_playlist import *

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


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


def connectSpotifyAPI():

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    # Make a POST request to get the access token
    auth_response = requests.post(
        AUTH_URL,
        {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    )
    # Check that the status code of the POST request is valid
    if auth_response.status_code == 200:
        return auth_response.json()
    else:
        print("Post request failed :(")
        print("Status Code: ", auth_response.status_code)
        return None


# FOR OPEN AI API
#USER_KEY = os.environ.get("USER_KEY")
USER_KEY = ''
# Create an OpenAPI client
client = OpenAI(api_key=USER_KEY)


# Get response from Chat GPT
def get_chat_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": 
            ("You are a musical genius that's good at reading people.")},
            {"role": "user", "content": prompt}
            ]
    )
    message = response.choices[0].message.content
    return message


@app.route('/')
def login():
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={redirect_uri}"
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
    return redirect(url_for('mood'))

@app.route('/mood')
def mood():
    token = session.get('token')
    if not token:
        return redirect(url_for('home'))
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    profile_url = 'https://api.spotify.com/v1/me'
    profile_response = requests.get(profile_url, headers=headers)
    profile_data = profile_response.json()
    
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
            f"Give me a mood (like an emotional feeling) " 
            f"based on my favorite recent songs: "
            f"{tracks_artists_str}. "
            f"Please give me a one word mood."
            )

    response = get_chat_response(prompt)

    return render_template('mood.html', top_tracks = tracks_artists, response = response)



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


# Get response from Chat GPT
def get_chat_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": 
            ("You are a musical genius that's good at reading people.")},
            {"role": "user", "content": prompt}
            ]
    )
    message = response.choices[0].message.content
    return message


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


# Extract a song title from Chat GPT response
def extract_song_titles(input_string):

    # Regular expression pattern to match the song titles
    pattern = r'"([^"]+)"'
    # Using re.findall to extract all occurrences of the pattern
    matches = re.findall(pattern, input_string)
    # Return the list of song titles
    return matches


# Get a song link from a track ID
def get_song_link(track_id):
    base_url = 'https://open.spotify.com/track/'
    track_link = base_url + track_id
    return track_link


# Get track id, artist, and song preview url from track name
def get_song_data(track_name):

    auth_response_data = connectSpotifyAPI()

    if 'access_token' in auth_response_data:
        access_token = auth_response_data['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(
            f"{BASE_URL}search",
            headers=headers,
            params={'q': f'track:{track_name}',
                    'type': 'track',
                    'limit': 1}
                )
        if response.status_code == 200:
            search_results = response.json()
            tracks = search_results.get('tracks', {}).get('items', [])

            if tracks:
                track = tracks[0]
                track_id = track['id']
                preview_url = track.get('preview_url')
                artist_name = [artist['name'] for artist in track['artists']]

                return track_id, preview_url, artist_name
        
    return None, None, None

              
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
