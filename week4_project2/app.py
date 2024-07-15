
import os
import json
import openai
import requests
from openai import OpenAI
import re
import sys
import io
import spotify_Input


from flask import (Flask, request, redirect, session, 
                   url_for, render_template, flash)

from user_form import UserForm

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from Week3.main import (connectSpotifyAPI, getPlaylistID, getUserData,
                        makeEmptySQLDB, appendSQLDB, promptChat, addMoreSongs)

app = Flask(__name__) # static_folder="static", static_url_path=""
app.config['SECRET_KEY'] = os.urandom(64)

# FOR SPOTIFY API

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    # 'ad91a46157df4ba080456f92c7a74ef8'
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
    # 9d4140d511c64467a582b075b990cbfe'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

redirect_uri = 'http://localhost:3000/callback'


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
USER_KEY =   os.environ.get("USER_KEY")
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

              
@app.route('/insights')
def insights():
    """
    I want insights to start off with the Tune Teller intro paragraph then have an input 
    form asking for playlist URL. 
    We're going to try with one playlist for now
    Once you input the URL, your insights should be printed in the div 
    """

    return render_template('insights.html')


'''
@app.route('/run_insights', methods=['GET', 'POST'])
def run_insights():
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist_url = form.playlist_url.data
        try:
            requestResponse = connectSpotifyAPI(playlist_url)
            playlistData = getUserData(requestResponse)
            if playlistData:
            # get_chat_response(prompt)
                insights = get_chat_response(prompt)

                return render_template('insights.html', insights=insights)
            else:
                flash('Failed to retrieve data from Spotify.')
        except Exception as e:
            flash(str(e))
        return redirect(url_for('run_insights'))

    return render_template('index.html', form=form)

'''


@app.route('/run_insights', methods=['POST'])
def run_insights():

    output = io.StringIO()
    sys.stdout = output  # Redirect print statements to the output StringIO object

    makeEmptySQLDB()

    get_another_playlist = "yes"
    requestResponse = connectSpotifyAPI()

    while get_another_playlist == "yes":
        # Make an SQL Data Base out of the playlist data
        playlistData = getUserData(requestResponse)

        if playlistData is not None:
            # Update SQL DB if DB already exists
            appendSQLDB(playlistData)
            print("Playlist successfully added to playlist.\n")

        # Will have to add user input error contingency
        question = "Do you want to add more songs? (yes/no): "
        get_another_playlist = addMoreSongs(question)

        # Get AI's insight
        print("--------------------------------------------------------------")

        print("\nTune Teller is generating insights from these songs ... \n")
        read = promptChat()
        print("--------------------------------------------------------------")

        if read:
            print("\nHello! I, Tune Teller, have some insights for you: \n")
            print(read)
        else:
            print("\n... Wait, there is no track data :( !")

    print("\n[ Program Ended ]")
    print("\n::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

    sys.stdout = sys.__stdout__  # Reset redirect.
    output_string = output.getvalue()
    return render_template('insights.html', output=output_string)


if __name__ == '__main__': 
    app.run(debug=True, host="0.0.0.0", port=3000)
