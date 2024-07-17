import os
import json
import openai
import requests
import re
import sys
import io


from insights_module import *

# FOR SPOTIFY API
CLIENT_ID = 'ad91a46157df4ba080456f92c7a74ef8'
CLIENT_SECRET = '9d4140d511c64467a582b075b990cbfe'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

redirect_uri = 'http://localhost:3000/callback'



def get_playlist_data(playlist_url):

    auth_response_data = connectSpotifyAPI()

    if 'access_token' in auth_response_data:
        access_token = auth_response_data['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}

        playlist_id = re.findall(r'playlist/([a-zA-Z0-9]+)', playlist_url)

        if playlist_id:
            playlist_id = playlist_id[0]
        else:
            print("Invalid playlist URL")
            return None

        response = requests.get(f'{BASE_URL}playlists/{playlist_id}', headers=headers)
        if response.status_code == 200:
            playlist_data = response.json()
            tracks_artists = {
                track['track']['name']: ', '.join([artist['name'] for artist in track['track']['artists']])
                for track in playlist_data['tracks']['items']
            }
            return tracks_artists
        else:
            print("Failed to retrieve playlist data")
            print("Status Code: ", response.status_code)
            return None
    else:
        print("Failed to authenticate with Spotify API")
        return None
    
 