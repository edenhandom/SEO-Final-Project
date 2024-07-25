import requests
import base64
import re
from flask import session, redirect, url_for, render_template
from pprint import pprint
import pandas as pd
import json

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

        # In case of login errors
        try:
            token = response_data['access_token']
            if not token:
                return None
            else:
                self.token = token
                return token
        except: 
            return None


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


    # Use if you only have playlist ID of playlist
    def get_playlist_items_with_id(self, playlist_id):
        # Authenticate with Spotify API
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            # Request to get playlist tracks
            response = requests.get(
                f'{self.BASE_URL}playlists/{playlist_id}/tracks', 
                headers=headers
            )

            if response.status_code == 200:
                playlist_data = response.json()

                # Extract track names and artist names
                tracks_artists = {
                    track['track']['name']: ', '.join(
                        [artist['name'] for artist in track['track']['artists']]
                    )
                    for track in playlist_data['items']
                }

                return tracks_artists
            else:
                print("Failed to retrieve playlist items")
                print("Status Code:", response.status_code)
                return None
        else:
            print("Failed to authenticate with Spotify API")
            return None


    def get_public_playlist_data(self, playlist_url):
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            playlist_id = re.findall(r'playlists/([a-zA-Z0-9]+)', playlist_url)

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

    #get playlist detail
    def get_playlist_details(self,playlist_id):
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}
            playlistdetails_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
            response = requests.get(playlistdetails_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print("Failed to retrieve playlist details")
                print("Status Code: ", response.status_code)
                return None


    # track ids to uris
    def convert_ids_to_uris(self, track_ids):
        base_uri = "spotify:track:"
        return [base_uri + track_id for track_id in track_ids]

    #need
    def get_audio_features(self, track_ids_str):
        # Get a token
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            audio_features_url = f"{self.BASE_URL}audio-features?ids={track_ids_str}"
            response = requests.get(audio_features_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()['audio_features']
            
            else:
                print("Failed to retrieve audio features")
                print("Status Code: ", response.status_code)
                return None

    #need
    def get_playlist_tracks(self, playlist_id):
        # Get a token
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}
            playlist_tracks_url = f"{self.BASE_URL}playlists/{playlist_id}/tracks"
            
            response = requests.get(playlist_tracks_url, headers=headers)
            
            # Debugging Step: Print the URL and response status code
            print(f"Request URL: {playlist_tracks_url}")
            print(f"Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                playlist_data = response.json()
                tracks = playlist_data.get('items', [])
                
                # Extract desired features: track_id, artist names, popularity, and genres
                track_features = []
                for item in tracks:
                    track = item.get('track', {})
                    track_info = {
                        "track_id": track.get("id"),
                        "name": track.get("name"),
                        "popularity": track.get("popularity"),
                        "artists": [{"name": artist.get("name")} for artist in track.get("artists", [])],
                        "artist_id": [{ "id": artist.get("id", [])} for artist in track.get("artists", [])],
                    }
                    track_features.append(track_info)

                return track_features
            else:
                print("Failed to retrieve playlist tracks")
                print("Status Code: ", response.status_code)
                print("Response Content: ", response.content)
                return None
        else:
            print("Failed to get access token")
            return None

    #need
    def get_recommendations(self, seed_tracks, seed_artists=None, limit=20, **kwargs):
        auth_response_data = self.connectSpotifyAPI()

        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            # Base URL for recommendations
            recommendations_url = f"{self.BASE_URL}recommendations"
            print(recommendations_url)
            print("hi :D")
            # Build the query parameters
            params = {
                'limit': limit,
                'seed_artists': ','.join(seed_artists) if seed_artists else '',
                'seed_tracks': ','.join(seed_tracks),
            }
            print(params)
            # Add optional parameters
            for key, value in kwargs.items():
                params[key] = value
            print(kwargs)
            
            response = requests.get(recommendations_url, headers=headers, params=params)
            print(response.request.url)
            if response.status_code == 200:
                return response.json()  # Returning the entire JSON response for further processing
            else:
                print("Failed to retrieve recommendations")
                print("Status Code: ", response.status_code)
                return None
        else:
            print("Failed to retrieve access token")
            return None
    #need

    def get_user_profile_info(self):
        url = f"{self.BASE_URL}me"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            user_data = response.json()
            display_name = user_data.get('display_name')
            profile_image_url = user_data.get('images')[0]['url'] if user_data.get('images') else None
            return display_name, profile_image_url
        else:
            raise Exception(f"Error {response.status_code}: {response.json()}")
   
    # Convert a json of user's playlists into a list, then a pandas df
    def json_to_db(self, playlist_json):
        playlists = []  # {id, name}

        for playlist in playlist_json["items"]:
            playlists.append({
                'playlist_href': playlist['href'],
                'playlist_name': playlist['name'],
                # Include other relevant fields
            })

        # convert to pandas DF
        #playlists_df = pd.DataFrame(list(playlists.items()), columns=['id', 'name'])
        return pd.DataFrame(playlists)
        #return playlists_df

    # convert and store in db