from openai import OpenAI
import openai


class OpenAIClient:

    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key

    # Provide prompt to Chat GPT then receive response

    def get_chat_response(self, prompt):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content":
                 ("You are a musical genius that's good at reading people.")},
                {"role": "user", "content": prompt}
            ]
        )
        message = response.choices[0].message.content
        return message
