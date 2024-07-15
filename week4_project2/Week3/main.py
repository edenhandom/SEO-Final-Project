import json
import re
import os
import requests
import pandas as pd
import sqlalchemy as db
import sqlite3
import openai
from openai import OpenAI

# Gain Access to Spotify API --------------------------------------------------

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'


def connectSpotifyAPI():

    # Get client credentials from environment variables
    # client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    # client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    client_id = 'ad91a46157df4ba080456f92c7a74ef8'
    client_secret = '9d4140d511c64467a582b075b990cbfe'

    # Make sure to run envir. var. (source ~/.bashrc)

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
        # print("Client ID: Found")
        # print("Client Secret: Found")

        # Return response
        return auth_response.json()
    else:
        print("Post request failed :(")
        print("Status Code: ", auth_response.status_code)
        return None


# Takes a URL and uses REGEX to return ID in URL ----------------------
def getPlaylistID(playlistURL: str) -> str:
    matches = re.findall(r'playlist/(\w+)', playlistURL)
    if matches:
        return matches[0]
    else:
        print("\nFailed to find ID in URL.")
        print("Are you sure you provided the URL to a playlist? Try Again.\n")
        return None


# Ask user to enter the playlist URL
# Returns the songs/artists in json format
def getUserData(auth_response_data):

    playlist_URL = input("\nEnter the URL of your " +
                         "desired Spotify playlist: ")

    playlistID = getPlaylistID(playlist_URL)

    if playlistID is None:
        return None

    # Use the stored ID with the "Get Playlist Items" Spotify API Endpoint to
    # access all of the songs (Testable Function) --------------------

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
            print("")
            print(f"Adding playlist \" {albumData['name']} \" to database ...")
            tracks = []

            for item in albumData['tracks']['items']:
                track_name = item['track']['name']
                artist_names = [artist['name'] for artist
                                in item['track']['artists']]
                tracks.append({'name': track_name, 'artists': artist_names})

            # Convert to DataFrame
            tracks_df = pd.DataFrame(tracks)

            # print(tracks_df) # Test to see if outputted correctly

            return tracks_df

        else:
            print("\nAttempt to retrieve album tracks failed :(")
            print(f"Status Code: {response.status_code}\n")

            if response.status_code == 404:
                print("The URL you provided may belong to a private playlist.")
                print("Try making the playlist public, or providing "
                      "the URL of a different (public) playlist.\n")
            return None

    else:
        error = auth_response_data.get('error', 'No error key')
        error_description = auth_response_data.get('error_description',
                                                   'No error description')

        print("Error: 'access_token' not found in the response.")
        print("Response contains error: ", error)
        print("Error description: :", error_description)

# Store the songs respectively with their titles,
        # artists and genres into an SQL Database ------------------------


def makeEmptySQLDB():
    # Create Engine Object
    engine = db.create_engine(f'sqlite:///track_list.db')

    # Connect to the database
    with engine.connect() as connection:
        # Retrieve all table names
        inspector = db.inspect(engine)
        tables = inspector.get_table_names()

        # Drop each table
        for table in tables:
            drop_table_query = db.text(f"DROP TABLE IF EXISTS {table};")
            connection.execute(drop_table_query)

    print("The database 'track_list.db' has been emptied...")
    print("Tune Teller is ready to go!")

# Append track data to an existing Database


def appendSQLDB(trackData):
    # Convert the list of artists to a JSON string
    trackData['artists'] = trackData['artists'].apply(json.dumps)

    # Create Engine Object
    engine = db.create_engine('sqlite:///track_list.db')

    # Write DataFrame to SQL database
    trackData.to_sql('tracks', con=engine, if_exists='append', index=False)

    # Read data back from SQL database and print it
    with engine.connect() as connection:
        query = db.text("SELECT * FROM tracks;")
        result = connection.execute(query)
        query_result = result.fetchall()
        df = pd.DataFrame(query_result, columns=['name', 'artists'])

# Give ChatGPT this database as input and
    # ask it to tell the user about their: ---------------

# Formats a prompt for the ChatGPT API based of the user's playlist data.
# Function Returns ChatGPT's insights.


def promptChat():

    connection = sqlite3.connect('track_list.db')

    crsr = connection.cursor()

    # Execute a query to check if the 'tracks' table exists
    crsr.execute("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name='tracks'")

    # Fetch the result
    table_exists = crsr.fetchone()

    # Check if the table exists
    if not table_exists:
        return None

    # execute the command to fetch all the data from the table emp
    crsr.execute("SELECT name, artists FROM tracks")

    # store all the fetched data in the ans variable
    tracks = crsr.fetchall()

    prompt_str = "\nTell me about myself based on my songs:\n"
    songs = ""

    count = 1
    for song, artists in tracks:
        # convert `artists`` into readable format
        matches = re.findall(r'"\s*([^"]+?)\s*"', artists)
        readable_artist = ', '.join(matches)
        songs += f"{count}. {song} by {readable_artist}\n"
        count += 1

    print(songs)

    prompt_str += songs
    prompt_str += ("\nI want to know what these songs say about my:")
    prompt_str += ("\n1. Musical preferences")
    prompt_str += ("\n2. Personal insights")
    prompt_str += ("\n3. Personality\n")

    # ChatGPT Stuff

    my_api_key = os.environ.get('OPENAI_KEY')
    openai.api_key = my_api_key

    client = OpenAI(api_key=my_api_key)

    # Specify the model to use and the messages to send
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content":
             "You are a musical genius that's good at reading people."},
            {"role": "user", "content": prompt_str}
        ]
    )

    return completion.choices[0].message.content


def addMoreSongs(prompt):
    while True:
        try:
            response = input(prompt).strip().lower()
            if response == "yes" or response == "no":
                return response
            else:
                raise ValueError("Invalid response")
        except ValueError as e:
            print(f"Error: {e}. Please enter 'yes' or 'no'.")

# Main (Only run when necessary)


if __name__ == "__main__":

    # Introductory Blerb
    print("\n::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

    print("\nHello! Welcome to Tune Teller.")

    print("Tune Teller will provide users with meaningful insights into what" +
          " their music taste says about their:\n")
    print("\t1. Musical Preferences")
    print("\t2. Personal Insights")
    print("\t3. Personality\n")
    print("All Tune Teller needs in exchange is the URL to your favorite " +
          "(public) Spotify playlists :) \n")

    # Make an empty SQL Database with columns song and artist
    print("-----------------------------------------------------------------")
    makeEmptySQLDB()
    print("-----------------------------------------------------------------")

    # Gain Access to Spotify API
    requestResponse = connectSpotifyAPI()

    if requestResponse is not None:

        get_another_playlist = "yes"

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
