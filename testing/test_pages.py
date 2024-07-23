from app import app  # imports flask app object
import unittest
import sys
# from app import app, get_song_data, connectSpotifyAPI, UserForm
# from app import *

# Mocking constants for API URLs
AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

# imports python file from parent directory
sys.path.append('../SEO-Final-Project')


class PageExistenceTests(unittest.TestCase):

    # executed prior to each test
    def setUp(self):
        self.app = app.test_client()

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_home_page(self):
        response = self.app.get('/home', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_about_us_page(self):
        response = self.app.get('/about_us', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_insights_page(self):
        response = self.app.get('/insights', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_user_form_page(self):
        response = self.app.get('/user_form', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_submit_page(self):
        response = self.app.get('/submit_page', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_recommendations_page(self):
        response = self.app.get('/view_recommendations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
