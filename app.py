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
import random
from collections import Counter

''''
Import our Classes
'''
from user_session import UserSession
from spotify_client import SpotifyClient
from openai_client import OpenAIClient

'''
Import our modules
'''

# Initialize an empty DataFrame with the appropriate columns
recommended_songs_df = pd.DataFrame(
    columns=['song', 
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

# First page that User sees. A login page


@app.route('/')
def login_page():
    return render_template('login_page.html')


# Route to start the authorization process
@app.route('/login')
def login():
    session.permanent = True  # Make the session permanent
    session['user_id'] = str(uuid.uuid4())  # Generate a unique user ID
    return redirect(spotify_client.get_auth_url())

# Callback route to handle the redirect from Spotify

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token = spotify_client.get_token(code)

    # Check for bad login 
    if not token:
        text = "Mood Mix could not Access your music data! </p><br>"
        text += "<p> Try accessing the again site later :["
        return render_template('login_page.html', page='status.html', text=text)
    
    user_session.set_token(spotify_client.token)
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about_us')
def about_us():
    return render_template('about.html')


# Route to provide user with a mood based on their recently played tracks
@app.route('/mood', methods=['GET', 'POST'])
def mood():
    recent_tracks_data = spotify_client.get_recent_tracks()
    tracks_artists = {
        track['track']['name']: ', '.join([artist['name'] for
                                           artist in
                                           track['track']['artists']])
        for track in recent_tracks_data['items']
    }
    tracks_artists_str = '. '.join(
        [f"{track}: {artist}" for track, artist in tracks_artists.items()])

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
                artist = ', '.join([artist['name']
                                   for artist in track['track']['artists']])
                preview_url = track['track']['preview_url']
                song_with_preview.append({'song': song,
                                          'artist': artist,
                                          'track_id': track_id,
                                          'preview_url': preview_url})

            for song in song_with_preview:
                song['link'] = spotify_client.get_song_link(song['track_id'])

            response = song_with_preview

        elif action == 'submit_mood':
            user_mood = request.form.get('user_mood')
            if user_mood:
                prompt = (
                    f"Give me a playlist of songs "
                    f"that match the mood '{user_mood}'. "
                    f"Here are some of my favorite "
                    f"recent songs: {tracks_artists_str}. "
                    f"Do not give me any songs "
                    f"from my recent songs."
                    f"Please list each song on a "
                    f"new line, song title only in quotes. "
                    f"Format like: 'Song1'\n 'Song2'\n..."
                    )


                raw_response = openai_client.get_chat_response(prompt)
                song_list = spotify_client.extract_song_titles(raw_response)

                song_with_preview = []

                for song in song_list:
                    track_id, preview_url, artist_name = spotify_client.get_song_data(song)
                    if track_id and preview_url and artist_name:
                        song_with_preview.append({
                            'song': song,
                            'artist': artist_name,
                            'track_id': track_id,
                            'preview_url': preview_url
                        })
                for song in song_with_preview:
                    song['link'] = spotify_client.get_song_link(
                        song['track_id'])

                response = song_with_preview

    return render_template(
        'mood.html',
        top_tracks=tracks_artists,
        response=response,
        action=action,
        user_mood=user_mood,
        mood_response=mood_response)


@app.route('/clear-session')
def clear_session():
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/top-artists')
def top_artists():

    top_artists_data = spotify_client.get_top_artists()

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

        # Set a unique user ID in the session (if not already set)
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())

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

        if history_prompt == 'yes':
            recent_tracks_data = spotify_client.get_recent_tracks()
            tracks_artists = {
                track['track']['name']:
                ', '.join([artist['name']
                           for artist in track['track']['artists']])
                for track in recent_tracks_data['items']
            }
            tracks_artists_str = '. '.join(
                [f"{track}: "
                 f"{artist}" for track, artist
                 in tracks_artists.items()])


            prompt = (
                f"Give me a playlist of recommended songs based on my "
                f"star sign: {star_sign}, "
                f"personality traits: {personality_traits}, "
                f"these genres: "
                f"{fav_genre1} similar to {example1}, "
                f"{fav_genre2} similar to {example2}, "
                f"{fav_genre3} similar to {example3}, "
                f"and my listening history: "
                f"{tracks_artists_str}. Don't give me "
                f"songs from my listening history."
                f"Please list each song on a new line, "
                f"song title only in quotes. "
                f"Format like: 'Song1'\n 'Song2'\n...'")
        else:
            prompt = (
                f"Give me a playlist of recommended songs based on my "
                f"star sign: {star_sign}, "
                f"personality traits: {personality_traits}, "
                f"and my preference of these genres: "
                f"{fav_genre1} similar to {example1}, "
                f"{fav_genre2} similar to {example2}, "
                f"{fav_genre3} similar to {example3}. "
                f"Please list each song on a new line, "
                f"song title only in quotes. "
                f"Format like: 'Song1'\n 'Song2'\n...'")

        print(prompt)
        recommendations = openai_client.get_chat_response(prompt)
        song_list = spotify_client.extract_song_titles(recommendations)

        song_with_preview = []
        for song in song_list:
            track_id, preview_url, artist_name = spotify_client.get_song_data(
                song)
            if track_id and preview_url and artist_name:
                song_with_preview.append({'song': song,
                                          'artist': artist_name,
                                          'track_id': track_id,
                                          'preview_url': preview_url})

        for song in song_with_preview:
            song['link'] = spotify_client.get_song_link(song['track_id'])

        # Add the recommendations to the DataFrame
        new_rows = pd.DataFrame(song_with_preview)
        new_rows['user_id'] = user_id
        recommended_songs_df = pd.concat(
            [recommended_songs_df, new_rows], ignore_index=True)

        # Debug print to check DataFrame content
        print("Updated DataFrame:\n", recommended_songs_df)

        return render_template('submit_page.html',
                               title='Submitted Data',
                               user_data=user_data,
                               recommendations=song_with_preview
                               )
    else:
        return redirect(url_for('user_form'))


@app.route('/view_recommendations')
def view_recommendations():
    global recommended_songs_df

    # Retrieve user data from session
    user_data = session.get('user_data', None)
    user_id = session.get('user_id')

    # Filter the DataFrame for the current user's recommendations
    user_recommendations = recommended_songs_df[
        recommended_songs_df['user_id'] == user_id
    ]

    # Debug print to check filtered DataFrame content
    print("User Recommendations:\n", user_recommendations)

    return render_template(
        'view_recommendation.html',
        recommendations=user_recommendations.to_dict(orient='records')
    )

# Displays personal insight based on provided playlist
@app.route('/insights', methods=['GET', 'POST'])
def insights():
    if request.method == 'POST':
        print("Form submitted")
        playlist_url = request.form.get('playlist_url')
        print(f"Received playlist URL: {playlist_url}")

        if playlist_url:
            display_name, profile_image_url = spotify_client.get_user_profile_info()
            track_artist = spotify_client.get_public_playlist_data(playlist_url)

            if track_artist:
                tracks_artists_str = '. '.join([f"{track}: {artist}" for track, artist in track_artist.items()])

                prompt = (f'Here is my playlist: {tracks_artists_str}. '
                          f'I want to know what these songs say about my: '
                          f'1. Musical preferences,'
                          f'2. Personal insights, and '
                          f'3. Personality. '
                          f'Be concise and format with line breaks between '
                          f'each insight, and do not use dashes for lists.')

                chat_response = openai_client.get_chat_response(prompt)

                # Process the chat response into sections
                sections = {}
                current_section = None

                for line in chat_response.split('\n'):
                    line = line.strip()
                    if line.startswith('1. '):
                        current_section = "Your Music Taste"
                        sections[current_section] = f"<p>{line[3:].strip()}</p>"
                    elif line.startswith('2. '):
                        current_section = "Personal Insights"
                        sections[current_section] = f"<p>{line[3:].strip()}</p>"
                    elif line.startswith('3. '):
                        current_section = "Your Personality"
                        sections[current_section] = f"<p>{line[3:].strip()}</p>"
                    elif current_section:
                        # Remove any redundant headers within the content
                        if line.startswith('Your musical preferences:') or \
                           line.startswith('Personal insights:') or \
                           line.startswith('Personality:'):
                            continue
                        # Remove leading dashes and extra spaces
                        if line.startswith('- '):
                            line = line[2:].strip()
                        sections[current_section] += f"<p>{line}</p>"

                # Handle the note at the end if present
                note_start = chat_response.find('Note:')
                if note_start != -1:
                    sections["Note"] = f"<p>{chat_response[note_start:].strip()}</p>"

                return render_template(
                    'result.html',
                    sections=sections,
                    display_name=display_name,
                    profile_image_url=profile_image_url
                )

        flash("Please enter a valid playlist URL.")
        return redirect(url_for('insights'))

    return render_template('insights.html')


@app.route('/music_recs', methods=['GET', 'POST'])
def music_recs():
    if request.method == 'POST':
        playlist_url = request.form.get('playlist_url')
        
        if playlist_url:
            try:
                playlist_id = playlist_url.split('/playlist/')[1].split('?')[0]
            except IndexError:
                return "Invalid playlist URL.", 400
            
            # Get track features from playlist
            track_features = spotify_client.get_playlist_tracks(playlist_id)
            
            if track_features:
                # Extract track IDs and popularities
                track_ids = [track['track_id'] for track in track_features]
                track_ids_str = ','.join(track_ids)
                popularities = [track['popularity'] for track in track_features]

                # Calculate average popularity
                average_popularity = int(sum(popularities) / len(popularities)) if popularities else 0
                
                # Get audio features
                audio_features = spotify_client.get_audio_features(','.join(track_ids))
                
                if not audio_features:
                    return "Failed to get audio features.", 500
                
                # Aggregate audio features
                aggregated_features = {
                    'target_danceability': sum([feature['danceability'] for feature in audio_features if feature]) / len(audio_features),
                    'target_energy': sum([feature['energy'] for feature in audio_features if feature]) / len(audio_features),
                    'target_valence': sum([feature['valence'] for feature in audio_features if feature]) / len(audio_features),
                    'target_acousticness': sum([feature['acousticness'] for feature in audio_features if feature]) / len(audio_features),
                    'target_tempo': sum([feature['tempo'] for feature in audio_features if feature]) / len(audio_features),
                    'target_popularity': int(average_popularity)
                }
                
                # Count artists and genres
                artist_ids = []
                for track in track_features:
                    artists_id = track['artist_id']
                    for artist in artists_id:
                        artist_id = artist['id']
                        artist_ids.append(artist_id)
                '''
                - for each track in track features, access artists key
                - for each artist in the artists list, access id
                - append that to artist_ids list
                '''
                artist_count = Counter(artist_ids)
                ''' genre_counter = Counter(
                    genre 
                    for track in track_features 
                    for artist in track['artists'] 
                    for genre in artist.get('genres', [])
                )            
                   '''  
                seed_artists = [artist for artist, _ in artist_count.most_common(2)]
                print(seed_artists)
                # seed_genres = [genre for genre, _ in genre_counter.most_common(5)]
                seed_tracks = random.sample(track_ids, min(3, len(track_ids)))
                # Get recommendations
                try: 
                    recommendations_response = spotify_client.get_recommendations(
                        limit=20,
                        seed_artists=seed_artists,
                        seed_tracks=seed_tracks,
                        # seed_genres=seed_genres,
                        target_danceability=aggregated_features['target_danceability'],
                        target_energy=aggregated_features['target_energy'],
                        target_valence=aggregated_features['target_valence'],
                        target_acousticness=aggregated_features['target_acousticness'],
                        target_tempo=aggregated_features['target_tempo'],
                        target_popularity=average_popularity
                    )
                except:
                    print("Error with recommendations")

                if recommendations_response and 'tracks' in recommendations_response:
                    recommendations = [
                        {
                            'song': track['name'],
                            'artist': ', '.join(artist['name'] for artist in track['artists']),
                            'track_id': track['id'],
                            'preview_url': track['preview_url'],
                            'link': spotify_client.get_song_link(track['id'])
                        }
                        for track in recommendations_response['tracks']
                    ]
                else:
                    recommendations = []

                return render_template('view_music_recs.html', recommendations=recommendations)
            else:
                return "Failed to get track features or no tracks found in the playlist.", 400
    return render_template('music_recs.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3000)
