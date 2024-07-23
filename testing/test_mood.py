import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, request
import sys
import os

# Get the current script's directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from app import app, spotify_client, openai_client  

''''
Import our Classes
'''
from user_session import UserSession
from spotify_client import SpotifyClient
from openai_client import OpenAIClient


class TestMoodRoute(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.spotify_client.get_recent_tracks')
    @patch('app.openai_client.get_chat_response')
    @patch('app.spotify_client.get_song_link')
    @patch('app.spotify_client.get_song_data')
    def test_mood_route_request_mood(self, mock_get_song_data, mock_get_song_link, mock_get_chat_response, mock_get_recent_tracks):
        # Mocking the SpotifyClient methods
        mock_get_recent_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Test Song',
                        'id': 'test_id',
                        'artists': [{'name': 'Test Artist'}],
                        'preview_url': 'http://testurl.com/preview'
                    }
                }
            ]
        }
        mock_get_song_data.return_value = ('test_id', 'http://testurl.com/preview', 'Test Artist')
        mock_get_song_link.return_value = 'http://spotify.com/track/test_id'
        
        # Mocking the OpenAIClient method
        mock_get_chat_response.return_value = 'Happy'

        # Simulate POST request to /mood with action 'request_mood'
        response = self.app.post('/mood', data={'action': 'request_mood'})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Happy', response.data)

    @patch('app.spotify_client.get_recent_tracks')
    @patch('app.openai_client.get_chat_response')
    @patch('app.spotify_client.get_song_link')
    @patch('app.spotify_client.get_song_data')
    def test_mood_route_submit_mood(self, mock_get_song_data, mock_get_song_link, mock_get_chat_response, mock_get_recent_tracks):
        # Mocking the SpotifyClient methods
        mock_get_recent_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Test Song',
                        'id': 'test_id',
                        'artists': [{'name': 'Test Artist'}],
                        'preview_url': 'http://testurl.com/preview'
                    }
                }
            ]
        }
        mock_get_song_data.return_value = ('test_id', 'http://testurl.com/preview', 'Test Artist')
        mock_get_song_link.return_value = 'http://spotify.com/track/test_id'
        
        # Mocking the OpenAIClient method
        mock_get_chat_response.return_value = "'Song1'\n'Song2'"

        # Simulate POST request to /mood with action 'submit_mood'
        response = self.app.post('/mood', data={'action': 'submit_mood', 'user_mood': 'Happy'})

     

if __name__ == '__main__':
    unittest.main()
