import requests
from openai import OpenAI
import re

# Spotify

CLIENT_ID = 'ad91a46157df4ba080456f92c7a74ef8'
CLIENT_SECRET= '9d4140d511c64467a582b075b990cbfe'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

redirect_uri = 'http://localhost:3000/callback'

# Open AI

USER_KEY = ''
client = OpenAI(api_key=USER_KEY)

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