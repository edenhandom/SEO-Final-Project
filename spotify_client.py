import requests
import base64
import re
from flask import session, redirect, url_for, render_template


class SpotifyClient:
    AUTH_URL = 'https://accounts.spotify.com/api/token'
    BASE_URL = 'https://api.spotify.com/v1/'

    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.token = None

    def get_auth_url(self):
        return (
            "https://accounts.spotify.com/authorize?response_type=code"
            f"&client_id={self.client_id}"
            f"&scope={self.scope}"
            f"&redirect_uri={self.redirect_uri}"
            "&show_dialog=True"
        )

    # Used for user authentication

    def get_token(self, code):
        auth_token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        auth_token_headers = {
            'Authorization': 'Basic ' +
            base64.b64encode((self.client_id + ':' +
                             self.client_secret).encode()).decode()
        }
        response = requests.post(self.AUTH_URL, data=auth_token_data,
                                 headers=auth_token_headers)
        response_data = response.json()
        token = response_data['access_token']
        if not token:
            return redirect(url_for('home'))
        self.token = token

    # Used for general api access
    def connectSpotifyAPI(self):
        auth_response = requests.post(
            self.AUTH_URL,
            {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )
        if auth_response.status_code == 200:
            return auth_response.json()
        else:
            print("Post request failed :(")
            print("Status Code: ", auth_response.status_code)
            return None

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def get_profile_data(self):
        profile_url = f"{self.BASE_URL}me"
        response = requests.get(profile_url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve profile data")
            print("Status Code: ", response.status_code)
            return None

    def get_user_playlists(self):
        playlists_url = f"{self.BASE_URL}me/playlists"
        response = requests.get(playlists_url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve playlist data")
            print("Status Code: ", response.status_code)
            return None

    def get_recent_tracks(self):
        recent_tracks_url = f"{self.BASE_URL}me/player/recently-played"
        response = requests.get(recent_tracks_url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve recent tracks")
            print("Status Code: ", response.status_code)
            return None

    def get_top_artists(self):
        top_artists_url = f"{self.BASE_URL}me/top/artists"
        response = requests.get(top_artists_url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to retrieve top artists")
            print("Status Code: ", response.status_code)
            return None

    def get_public_playlist_data(self, playlist_url):
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            playlist_id = re.findall(r'playlist/([a-zA-Z0-9]+)', playlist_url)

            if playlist_id:
                playlist_id = playlist_id[0]
            else:
                print("Invalid playlist URL")
                return None

            response = requests.get(f'{self.BASE_URL}playlists/{playlist_id}',
                                    headers=headers)
            if response.status_code == 200:
                playlist_data = response.json()

                tracks_artists = {
                    track['track']['name']: ', '.join(
                        [artist['name'] for
                         artist in track['track']['artists']]
                    )
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

    def extract_song_titles(self, input_string):
        pattern = r'"([^"]+)"'
        matches = re.findall(pattern, input_string)
        return matches

    def get_song_link(self, track_id):
        base_url = 'https://open.spotify.com/track/'
        track_link = base_url + track_id
        return track_link

    def get_song_data(self, track_name):
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            response = requests.get(
                f"{self.BASE_URL}search",
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

                    artist_name = [artist['name']
                                   for artist in track['artists']]
                    if len(artist_name) > 1 and type(artist_name) is list:
                        artist_name = ", ".join(artist_name)
                    else:
                        artist_name = artist_name[0]

                    return track_id, preview_url, artist_name

        return None, None, None
