import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, session, url_for, get_flashed_messages
from flask.testing import FlaskClient
from app import app, get_song_data, connectSpotifyAPI, UserForm
from app import *

# Mocking constants for API URLs
AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

# Mock the connectSpotifyAPI function
def mock_connectSpotifyAPI():
    return {'access_token': 'mock_access_token'}

class TestSongRec(unittest.TestCase):
    @patch('requests.get')
    @patch('app.connectSpotifyAPI', side_effect=mock_connectSpotifyAPI)
    def test_get_song_data(self, mock_connect_spotify_api, mock_requests_get):
        # Mock response data
        mock_response_data = {
            'tracks': {
                'items': [
                    {
                        'id': '5gS8whHdcpbkdz0qonQZF8',
                        'preview_url': 'https://p.scdn.co/mp3-preview/ebf3cde3969df2a5c6382cde52c67c2729a7d26a?cid=ad91a46157df4ba080456f92c7a74ef8',
                        'artists': [{'name': 'Talking Heads'}]
                    }
                ]
            }
        }
        # Mock the requests.get() response
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = mock_response_data

        # Test the function
        track_id, preview_url, artist_name = get_song_data('Road to Nowhere')

        # Assertions
        self.assertEqual(track_id, '5gS8whHdcpbkdz0qonQZF8')
        self.assertEqual(preview_url, 'https://p.scdn.co/mp3-preview/ebf3cde3969df2a5c6382cde52c67c2729a7d26a?cid=ad91a46157df4ba080456f92c7a74ef8')
        self.assertEqual(artist_name, ['Talking Heads'])

    @patch('requests.get')
    @patch('app.connectSpotifyAPI', side_effect=mock_connectSpotifyAPI)
    def test_get_song_data_no_tracks(self, mock_connect_spotify_api, mock_requests_get):
        # Mock response data with no tracks
        mock_response_data = {'tracks': {'items': []}}

        # Mock the requests.get() response
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = mock_response_data

        # Test the function
        track_id, preview_url, artist_name = get_song_data('Unknown Song')

        # Assertions
        self.assertIsNone(track_id)
        self.assertIsNone(preview_url)
        self.assertIsNone(artist_name)


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
        self.assertIn(b'Favorite Genre 1', response.data)
        self.assertIn(b'Favorite Genre 2', response.data)
        self.assertIn(b'Favorite Genre 3', response.data)


    def test_user_form_post(self):
        form_data = {
            'star_sign': 'Aries',
            'personality_traits': 'Bold, Ambitious',
            'fav_genre1': 'Rock',
            'fav_genre2': 'Pop',
            'fav_genre3': 'Jazz',
            'submit': 'Submit'
        }
        response = self.client.post('/user_form', data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        with self.client as client:
            response = client.post('/user_form', data=form_data, follow_redirects=True)
            with client.session_transaction() as sess:
                self.assertIn('user_data', sess)  # Check if 'user_data' is in session
                self.assertEqual(sess['user_data']['star_sign'], 'Aries')
                self.assertEqual(sess['user_data']['personality_traits'], 'Bold, Ambitious')
                self.assertEqual(sess['user_data']['fav_genre1'], 'Rock')
                self.assertEqual(sess['user_data']['fav_genre2'], 'Pop')
                self.assertEqual(sess['user_data']['fav_genre3'], 'Jazz')


class TestChatGPTResponses(unittest.TestCase):

    @patch('app.client.chat.completions.create')  # Adjust the patch location according to your project setup
    def test_get_chat_response(self, mock_create):
        # Create a mock response object with the necessary nested structure
        mock_choice = MagicMock()
        mock_choice.message.content = 'This is a test response based on your musical preferences.'
        
        # Set up the outer structure
        mock_create.return_value = MagicMock()
        mock_create.return_value.choices = [mock_choice]

        # Define the prompt
        prompt = "Give me a playlist based on indie and folk music genres."
        
        # Call the function from your app module
        from app import get_chat_response  # Import here to use the patched version
        response = get_chat_response(prompt)
        
        # Check that the response matches what you expect
        self.assertEqual(response, 'This is a test response based on your musical preferences.')



class TestExtractSongTitles(unittest.TestCase):

    def test_multiple_song_titles(self):
        input_string = 'Here are some songs "Song One", "Song Two", and "Song Three" you might like.'
        expected = ['Song One', 'Song Two', 'Song Three']
        result = extract_song_titles(input_string)
        self.assertEqual(result, expected)

    def test_single_song_title(self):
        input_string = 'My favorite song is "Single Hit Wonder".'
        expected = ['Single Hit Wonder']
        result = extract_song_titles(input_string)
        self.assertEqual(result, expected)

    def test_no_song_titles(self):
        input_string = 'There are no songs mentioned here.'
        expected = []
        result = extract_song_titles(input_string)
        self.assertEqual(result, expected)

    def test_song_titles_with_special_characters(self):
        input_string = 'Some unusual song titles might include "Crazy@Night", "What?! No Way!", and "Yes, This & That".'
        expected = ['Crazy@Night', 'What?! No Way!', 'Yes, This & That']
        result = extract_song_titles(input_string)
        self.assertEqual(result, expected)



if __name__ == '__main__':
    unittest.main()
