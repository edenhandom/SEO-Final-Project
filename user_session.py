# Manages user sessions and tokens

class UserSession:
    def __init__(self):
        self.data = {}

    def set_token(self, token):
        self.data['token'] = token

    def get_token(self):
        return self.data.get('token')
    
    def clear(self):
      self.data.clear()