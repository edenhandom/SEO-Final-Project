import unittest
import requests
import pandas as pd
import sqlite3
from main import (connectSpotifyAPI, getPlaylistID, getUserData,
                  makeEmptySQLDB, appendSQLDB, promptChat, addMoreSongs)

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'


class test(unittest.TestCase):

    def HELPER_getUserData(self, auth_response_data, playlistURL):

        playlistID = getPlaylistID(playlistURL)

        if playlistID is None:
            return None

        # Use the stored ID with the "Get Playlist Items" Spotify API Endpoint
        # to access all of the songs (Testable Function) --------------------

        # Check if 'access_token' is in the response
        if 'access_token' in auth_response_data:
            access_token = auth_response_data['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            # Get Playlist Items (GET) request
            response = requests.get(f"{BASE_URL}playlists/{playlistID}/tracks",
                                    headers=headers)

            # Get Album Items (GET) request
            response = requests.get(f"{BASE_URL}playlists/{playlistID}",
                                    headers=headers)

            if response.status_code == 200:
                albumData = response.json()

                # Create a list to store track details
                print("Playlist Title: ", albumData['name'])
                tracks = []

                for item in albumData['tracks']['items']:
                    track_name = item['track']['name']
                    artist_names = [artist['name'] for artist in
                                    item['track']['artists']]
                    tracks.append({'name': track_name,
                                   'artists': artist_names})

                # Convert to DataFrame
                tracks_df = pd.DataFrame(tracks)

                return tracks_df

            else:
                print("Attempt to retrieve album tracks failed :(")
                print("Status Code: ", response.status_code)

                if response.status_code == 404:
                    print("The URL you provided may"
                          "belong to a private playlist.")
                    print("Try making the playlist public, or providing"
                          "the URL of a different (public) playlist.")
                return None

        else:
            error = auth_response_data.get('error', 'No error key')
            error_description = auth_response_data.get('error_description',
                                                       'No error description')

            print("Error: 'access_token' not found in the response.")
            print("Response contains error: ", error)
            print("Error description: :", error_description)

    def test_connectSpotifyAPI(self):
        def HELPER_connectSpotifyAPI(
                client_id="4ec20579f49049ca9197877b90005e2a",
                client_secret="f3047a0f01ea4195b5da9de036382a81"):

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

                # Checks if client credentials are correctly loaded
                print("Client ID: Found")
                print("Client Secret: Found")

                return auth_response
            else:
                print("Post request failed :(")
                print("Status Code: ", auth_response.status_code)
                return None

        self.assertEqual(HELPER_connectSpotifyAPI().status_code, 200)
        self.assertEqual(HELPER_connectSpotifyAPI("error", "error"), None)

    def test_getPlaylistID(self):  # Done
        testSongURL = ("https://open.spotify.com/track/"
                       "7AzlLxHn24DxjgQX73F9fU?si=98b4c56eb56f4f65")
        self.assertEqual(getPlaylistID(testSongURL), None)

        testAlbumURL = ("https://open.spotify.com/album/"
                        "7z4GhRfLqfSkqrj5F3Yt2B?si=cMKUcbYbQKa_-xFyTR8NLg")
        self.assertEqual(getPlaylistID(testAlbumURL), None)

        testPublicPlaylistURL = ("https://open.spotify.com/playlist/"
                                 "0I4PTtWuqYVcVfVUPat2jT?si=4176e6499f0f46dd")
        self.assertEqual(getPlaylistID(testPublicPlaylistURL),
                         "0I4PTtWuqYVcVfVUPat2jT")

    def test_getUserData(self):
        # Takes in auth_response_data
        # Outputs a pandas dataframe of songs and artists
        self.assertEqual(self.HELPER_getUserData(None, ""), None)

    def test_makeEmptySQLDB(self):
        # Takes in nothing
        # Returns nothing but
        # creates an empty Database with columns songs and artists
        # Connect to the SQLite database
        makeEmptySQLDB()
        connection = sqlite3.connect('track_list.db')

        # Create a cursor object
        crsr = connection.cursor()

        # Execute a query to check if the 'tracks' table exists
        crsr.execute("SELECT name FROM sqlite_master "
                     "WHERE type='table' AND name='tracks'")

        # Fetch the result
        table_exists = crsr.fetchone()

        # Check if the table exists
        if table_exists:
            print("\nThe table 'tracks' exists.")
        else:
            return None

        # Execute a query to count the number of rows in the table
        crsr.execute("SELECT COUNT(*) FROM tracks")

        # Fetch the result
        row_count = crsr.fetchone()[0]

        # Close the connection
        connection.close()

        self.assertEqual(row_count, 0)

    def test_appendSQLDBB(self):  # Done ???
        # Takes in a list of dictionaries of song and artists
        # returns nothing but appends data to an existing SQL DB

        makeEmptySQLDB()

        # Gain Access to Spotify API
        requestResponse = connectSpotifyAPI()

        # Make an SQL Data Base out of the playlist data
        dummy = ("https://open.spotify.com/playlist/"
                 "6GpsdAG2IV16mvlGdj3eor?si=f41a8282fd1a4099")
        playlistData = self.HELPER_getUserData(requestResponse, dummy)

        appendSQLDB(playlistData)

        connection = sqlite3.connect('track_list.db')

        # Create a cursor object
        cursor = connection.cursor()

        # Execute a query to count the number of rows in the table
        cursor.execute("SELECT COUNT(*) FROM tracks")

        # Fetch the result
        row_count = cursor.fetchone()[0]

        # Close the connection
        connection.close()

        self.assertEqual(row_count, 5)

    def test_promptChat(self):

        # Takes in nothing
        # Outputs the generated response from ChatGPT

        makeEmptySQLDB()

        # Gain Access to Spotify API
        requestResponse = connectSpotifyAPI()

        # Make an SQL Data Base out of the playlist data
        dummy = ""
        playlistData = self.HELPER_getUserData(requestResponse, dummy)

        if playlistData is not None:

            appendSQLDB(playlistData)

        self.assertEqual(promptChat(), None)

    def test_addMoreSongs(self):
        # Takes in nothing
        # Outputs the generated response from ChatGPT
        def HELPER_addMoreSongs(input):
            try:
                response = input
                if response == "yes" or response == "no":
                    return response
                else:
                    raise ValueError("Invalid response")
            except ValueError as e:
                print(f"Error: {e}. Please enter 'yes' or 'no'.")

        self.assertEqual(HELPER_addMoreSongs("yes"), "yes")
        self.assertEqual(HELPER_addMoreSongs("no"), "no")
        self.assertEqual(HELPER_addMoreSongs(""), None)
