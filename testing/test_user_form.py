import unittest
from unittest.mock import patch, MagicMock
from flask import session
import re
import uuid
import sys
import os

# Get the current script's directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from app import app


class UserFormTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'secret!'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_user_form_get(self):
        response = self.client.get('/user_form')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Star Sign', response.data)
        self.assertIn(b'Personality Traits', response.data)
        self.assertIn(b'Enter a favorite genre:', response.data)
        self.assertIn(b'Include your listening history?', response.data)

    @patch('spotify_client.SpotifyClient.get_recent_tracks')
    def test_user_form_post(self, mock_get_recent_tracks):
        # Mock the get_recent_tracks method
        mock_get_recent_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'id': '1',
                        'name': 'Song1',
                        'artists': [{'name': 'Artist1'}],
                        'preview_url': 'http://example.com/preview1'
                    }
                },
                {
                    'track': {
                        'id': '2',
                        'name': 'Song2',
                        'artists': [{'name': 'Artist2'}],
                        'preview_url': 'http://example.com/preview2'
                    }
                }
            ]
        }

        # Get the CSRF token from the form
        response = self.client.get('/user_form')
        csrf_token = self.get_csrf_token(response.data.decode())

        form_data = {
            'csrf_token': csrf_token,
            'star_sign': 'Aries',
            'personality_traits': 'Bold, Ambitious',
            'fav_genre1': 'Rock',
            'fav_genre2': 'Pop',
            'fav_genre3': 'Jazz',
            'include_history': 'yes'
        }

        response = self.client.post('/user_form', data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.client as client:
            response = client.post('/user_form', data=form_data, follow_redirects=True)
            with client.session_transaction() as sess:
                print(sess)  # Print session content for debugging
                # Check if 'user_data' is in session
                self.assertIn('user_data', sess)
                self.assertEqual(sess['user_data']['star_sign'], 'Aries')
                self.assertEqual(sess['user_data']['personality_traits'], 'Bold, Ambitious')
                self.assertEqual(sess['user_data']['fav_genre1'], 'Rock')
                self.assertEqual(sess['user_data']['fav_genre2'], 'Pop')
                self.assertEqual(sess['user_data']['fav_genre3'], 'Jazz')
                self.assertEqual(sess['user_data']['include_history'], 'yes')

                # Check if 'user_id' is in session
                self.assertIn('user_id', sess)
                # Check if the user_id is a valid UUID
                try:
                    uuid.UUID(sess['user_id'])
                except ValueError:
                    self.fail("user_id is not a valid UUID")

    def get_csrf_token(self, html):
        match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
        if not match:
            raise ValueError("CSRF token not found in form")
        return match.group(1)

if __name__ == '__main__':
    unittest.main()
