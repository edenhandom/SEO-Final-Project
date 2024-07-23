import unittest
from unittest.mock import patch, MagicMock
from flask import session
import sys
import os

# Get the current script's directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from app import app


class InsightsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'secret!'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('spotify_client.SpotifyClient.get_public_playlist_data')
    @patch('openai_client.OpenAIClient.get_chat_response')
    def test_insights_post_valid_playlist(self, mock_get_chat_response, mock_get_public_playlist_data):
        # Mock the Spotify client method
        mock_get_public_playlist_data.return_value = {
            'Song1': 'Artist1',
            'Song2': 'Artist2',
            'Song3': 'Artist3'
        }

        # Mock the OpenAI client method
        mock_get_chat_response.return_value = (
            "1. You like energetic and upbeat music.<br>"
            "2. You are adventurous and outgoing.<br>"
            "3. Your personality is vibrant and lively."
        )

        # Simulate a POST request to the /insights route with a valid playlist URL
        response = self.client.post('/insights', data={'playlist_url': 'http://valid-playlist-url'}, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You like energetic and upbeat music', response.data)
        self.assertIn(b'You are adventurous and outgoing', response.data)
        self.assertIn(b'Your personality is vibrant and lively', response.data)

    @patch('spotify_client.SpotifyClient.get_public_playlist_data')
    def test_insights_post_invalid_playlist(self, mock_get_public_playlist_data):
        # Mock the Spotify client method to return None for an invalid playlist URL
        mock_get_public_playlist_data.return_value = None

        # Simulate a POST request to the /insights route with an invalid playlist URL
        response = self.client.post('/insights', data={'playlist_url': 'http://invalid-playlist-url'}, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter a valid playlist URL.', response.data)

if __name__ == '__main__':
    unittest.main()
