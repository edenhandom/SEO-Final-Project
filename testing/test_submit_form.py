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

from app import app, recommended_songs_df
import pandas as pd

class SubmitPageTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'secret!'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Set up initial session data
        with self.client.session_transaction() as sess:
            sess['user_data'] = {
                'star_sign': 'Aries',
                'personality_traits': 'Bold, Ambitious',
                'fav_genre1': 'Rock',
                'optional_field1': 'Led Zeppelin',
                'fav_genre2': 'Pop',
                'optional_field2': 'Taylor Swift',
                'fav_genre3': 'Jazz',
                'optional_field3': 'Miles Davis',
                'include_history': 'yes'
            }
            sess['user_id'] = 'test_user_id'

        # Initialize the global DataFrame
        global recommended_songs_df
        recommended_songs_df = pd.DataFrame(columns=['song', 'artist', 'track_id', 'preview_url', 'link', 'user_id'])

    def tearDown(self):
        self.ctx.pop()

    @patch('spotify_client.SpotifyClient.get_recent_tracks')
    @patch('openai_client.OpenAIClient.get_chat_response')
    @patch('spotify_client.SpotifyClient.get_song_data')
    @patch('spotify_client.SpotifyClient.get_song_link')
    @patch('spotify_client.SpotifyClient.extract_song_titles')
    def test_submit_page_with_history(self, mock_extract_song_titles, mock_get_song_link, mock_get_song_data, mock_get_chat_response, mock_get_recent_tracks):
        # Mock the get_recent_tracks method
        mock_get_recent_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'id': '1',
                        'name': 'Recent Song 1',
                        'artists': [{'name': 'Artist 1'}],
                        'preview_url': 'http://example.com/preview1'
                    }
                },
                {
                    'track': {
                        'id': '2',
                        'name': 'Recent Song 2',
                        'artists': [{'name': 'Artist 2'}],
                        'preview_url': 'http://example.com/preview2'
                    }
                }
            ]
        }

        # Mock the OpenAI response
        mock_get_chat_response.return_value = (
            "'Recommended Song 1'\n"
            "'Recommended Song 2'\n"
            "'Recommended Song 3'"
        )

        # Mock the extract_song_titles method
        mock_extract_song_titles.return_value = [
            'Recommended Song 1',
            'Recommended Song 2',
            'Recommended Song 3'
        ]

        # Mock the get_song_data method
        mock_get_song_data.side_effect = [
            ('track_id_1', 'http://example.com/preview1', 'Artist 1'),
            ('track_id_2', 'http://example.com/preview2', 'Artist 2'),
            ('track_id_3', 'http://example.com/preview3', 'Artist 3')
        ]

        # Mock the get_song_link method
        mock_get_song_link.side_effect = [
            'http://open.spotify.com/track/track_id_1',
            'http://open.spotify.com/track/track_id_2',
            'http://open.spotify.com/track/track_id_3'
        ]

        # Make a request to the submit_page
        response = self.client.get('/submit_page')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Recommended Song 1', response.data)
        self.assertIn(b'Recommended Song 2', response.data)
        self.assertIn(b'Recommended Song 3', response.data)

    '''
        # Check if the DataFrame was updated correctly
        print("Current DataFrame content:\n", recommended_songs_df)  # Debug print
        self.assertIn('test_user_id', recommended_songs_df['user_id'].values)
        self.assertIn('Recommended Song 1', recommended_songs_df['song'].values)
        self.assertIn('Recommended Song 2', recommended_songs_df['song'].values)
        self.assertIn('Recommended Song 3', recommended_songs_df['song'].values)
    '''
    
if __name__ == '__main__':
    unittest.main()
