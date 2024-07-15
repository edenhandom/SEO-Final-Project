#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 14 16:43:29 2024

@author: pocketpuppy
"""

import os
import json
import openai
import requests
from openai import OpenAI
import re
import sys
import io
import pandas as pd
import sqlalchemy as db
import sqlite3

from flask import (Flask, request, redirect, session, 
                   url_for, render_template, flash)

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


# FOR SPOTIFY API
CLIENT_ID = 'ad91a46157df4ba080456f92c7a74ef8'
CLIENT_SECRET = '9d4140d511c64467a582b075b990cbfe'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

redirect_uri = 'http://localhost:3000/callback'




def connectSpotifyAPI():

    client_id = 'ad91a46157df4ba080456f92c7a74ef8'
    client_secret = '9d4140d511c64467a582b075b990cbfe'

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
    
 