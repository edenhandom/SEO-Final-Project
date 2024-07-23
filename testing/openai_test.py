import os
import unittest
from unittest.mock import patch, MagicMock
from openai import OpenAI
import openai
import sys

# Get the current script's directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from openai_client import OpenAIClient

USER_KEY = os.environ.get("USER_KEY")
print(f"USER_KEY: {USER_KEY}")  # Print the key to ensure it's being retrieved

class TestOpenAIClient(unittest.TestCase):

    @patch('openai.chat.completions.create')
    @patch('openai.api_key', new_callable=MagicMock)
    def test_get_chat_response(self, mock_api_key, mock_create):
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_create.return_value = mock_response

        # Check if USER_KEY is retrieved correctly
        if not USER_KEY:
            self.fail("USER_KEY environment variable is not set")

        # Create an instance of OpenAIClient
        client = OpenAIClient(USER_KEY)

        # Ensure the api_key is being set
        self.assertEqual(openai.api_key, USER_KEY)

        # Call the method with a test prompt
        prompt = "Test prompt"
        response = client.get_chat_response(prompt)

        # Assert the response is as expected
        self.assertEqual(response, "Test response")

        # Assert the OpenAI API was called with the correct parameters
        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": 
                 "You are a musical genius that's good at reading people."},
                {"role": "user", "content": prompt}
            ]
        )

if __name__ == '__main__':
    unittest.main()
