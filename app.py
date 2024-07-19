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
from user_form import UserForm

# Initialize a global DataFrame to store recommended songs
recommended_songs_df = pd.DataFrame(columns=['song', 'artist', 'track_id', 'preview_url', 'user_id'])


app = Flask(__name__) # static_folder="static", static_url_path=""
app.config['SECRET_KEY'] = os.urandom(64)   # generate random session key
# Configure session to use filesystem (server-side session storage)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime to 7 days
Session(app)

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
    session.permanent = True  # Make the session permanent
    session['user_id'] = str(uuid.uuid4())  # Generate a unique user ID
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



# Route to provide user with a mood based on their recently played tracks
@app.route('/mood', methods=['GET', 'POST'])
def mood():
    recent_tracks_data = spotify_client.get_recent_tracks()
    tracks_artists = {
            track['track']['name']: ', '.join([artist['name'] for artist in track['track']['artists']])
            for track in recent_tracks_data['items']
        }
    tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in tracks_artists.items()])
    
    action = None
    response = None
    user_mood = None
    mood_response = ''

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'request_mood':
            prompt = (
                    f"Give me a mood (an emotion) " 
                    f"based on my favorite recent songs: "
                    f"{tracks_artists_str}. "
                    f"Please give me a one or two word mood."
                    )
            mood_response = openai_client.get_chat_response(prompt)
            
            # Transform recent tracks into the same format as the playlist
            song_with_preview = []
            for track in recent_tracks_data['items']:
                track_id = track['track']['id']
                song = track['track']['name']
                artist = ', '.join([artist['name'] for artist in track['track']['artists']])
                preview_url = track['track']['preview_url']
                song_with_preview.append({'song': song, 'artist': artist, 'track_id': track_id, 'preview_url': preview_url})
            
            for song in song_with_preview:
                song['link'] = spotify_client.get_song_link(song['track_id'])

            response = song_with_preview

        
        elif action == 'submit_mood':
            user_mood = request.form.get('user_mood')
            if user_mood:
                prompt = (
                    f"Give me a playlist of songs that match the mood '{user_mood}'. "
                    f"Here are some of my favorite recent songs: {tracks_artists_str}. "
                    f"Do not give me any songs from my recent songs."
                    f"Please list each song on a new line, song title only in quotes. "
                    f"Format like: 'Song1'\n 'Song2'\n..."
                )

                raw_response = openai_client.get_chat_response(prompt)
                song_list = spotify_client.extract_song_titles(raw_response)
                
                song_with_preview = []
                for song in song_list:
                    track_id, preview_url, artist_name = spotify_client.get_song_data(song)
                    if track_id and preview_url and artist_name:
                        song_with_preview.append({'song': song, 'artist': artist_name, 'track_id': track_id, 'preview_url': preview_url})

                for song in song_with_preview:
                    song['link'] = spotify_client.get_song_link(song['track_id'])

                response = song_with_preview

    return render_template('mood.html', top_tracks=tracks_artists, response=response, action=action, user_mood=user_mood, mood_response=mood_response)


@app.route('/clear-session')
def clear_session():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/top-artists')
def top_artists():

    top_artists_data = SpotifyClient.get_top_artists()

    artist_names = [artist['name'] for artist in top_artists_data['items']]

    return f"Top Artists: {json.dumps(artist_names, indent=4)}"


# Form to take in user's self description
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
            'fav_genre3': form.fav_genre3.data,
            'include_history': form.include_history.data
            }
        return redirect(url_for('submit_page'))
    
    return render_template('user_form.html', title='Info', form=form)


# For submission page, brings user here after they submit form
# Displays playlist based on input
@app.route('/submit_page')
def submit_page():
    
    global recommended_songs_df  # Access the global DataFrame
    
    # Retrieve user data from session
    user_data = session.get('user_data', None)
    user_id = session.get('user_id')
    
    if user_data:
        star_sign = user_data.get('star_sign', 'Unknown')
        personality_traits = user_data.get('personality_traits', 'Unknown')
        fav_genre1 = user_data.get('fav_genre1', 'Unknown')
        example1 = user_data.get('optional_field1', fav_genre1)
        fav_genre2 = user_data.get('fav_genre2', 'Unknown')
        example2 = user_data.get('optional_field2', fav_genre2)
        fav_genre3 = user_data.get('fav_genre3', 'Unknown')
        example3 = user_data.get('optional_field3', fav_genre3)

        history_prompt = user_data.get('include_history', 'Unknown')
        print(history_prompt)

        if history_prompt=='yes':
            recent_tracks_data = spotify_client.get_recent_tracks()
            tracks_artists = {
                track['track']['name']: ', '.join([artist['name'] for artist in track['track']['artists']])
                for track in recent_tracks_data['items']
             }
            tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in tracks_artists.items()])

            prompt = (
                f"Give me a playlist of recommended songs based on my "
                f"star sign: {star_sign}, "
                f"personality traits: {personality_traits}, "
                f"these genres: "
                f"{fav_genre1} similar to {example1}, " 
                f"{fav_genre2} similar to {example2}, "
                f"{fav_genre3} similar to {example3}, "
                f"and my listening history: "
                f"{tracks_artists_str}. Don't give me songs from my listening history."
                f"Please list each song on a new line, song title only in quotes. "
                f"Format like: 'Song1'\n 'Song2'\n...'"
                )        
        else:
            prompt = (
                f"Give me a playlist of recommended songs based on my "
                f"star sign: {star_sign}, "
                f"personality traits: {personality_traits}, "
                f"and my preference of these genres: "
                f"{fav_genre1} similar to {example1}, " 
                f"{fav_genre2} similar to {example2}, "
                f"{fav_genre3} similar to {example3}. "
                f"Please list each song on a new line, song title only in quotes. "
                f"Format like: 'Song1'\n 'Song2'\n...'"
                )

        print(prompt)
        recommendations = openai_client.get_chat_response(prompt)
        song_list = spotify_client.extract_song_titles(recommendations)

        song_with_preview = []
        for song in song_list:
            track_id, preview_url, artist_name = spotify_client.get_song_data(song)
            if track_id and preview_url and artist_name:
               song_with_preview.append({'song': song, 'artist': artist_name, 'track_id': track_id, 'preview_url': preview_url})

        for song in song_with_preview:
            song['link'] = spotify_client.get_song_link(song['track_id'])

        # Add the recommendations to the DataFrame
        new_rows = pd.DataFrame(song_with_preview)
        new_rows['user_id'] = user_id
        print("New rows to be added:")
        print(new_rows)

        recommended_songs_df = pd.concat([recommended_songs_df, new_rows], ignore_index=True)
        print("Updated DataFrame:")
        print(recommended_songs_df)

        return render_template('submit_page.html', 
                               title='Submitted Data', 
                               user_data = user_data, 
                               recommendations = song_with_preview
                               )
    else:
        return redirect(url_for('user_form'))


@app.route('/view_recommendations')
def view_recommendations():
    global recommended_songs_df
    user_id = session.get('user_id')
    
    # Filter the DataFrame for the current user's recommendations
    user_recommendations = recommended_songs_df[recommended_songs_df['user_id'] == user_id]
    print(user_recommendations)
    
    return render_template('view_recommendation.html', recommendations=user_recommendations.to_dict(orient='records'))



# Displays personal insight based on provided playlist 
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
