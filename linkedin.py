from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient


class LinkedIn:
    def __init__(self):
        self.CLIENT_ID = '86jz9u3cqsznsq'
        self.CLIENT_SECRET = 'WPL_AP1.tEJ51YCsRJRxkjFh.AE2FYQ=='
        self.REDIRECT_URI = 'http://localhost:5000/callback'
        self.AUTHORIZATION_BASE_URL = 'https://www.linkedin.com/oauth/v2/authorization'
        self.TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.client = WebApplicationClient(self.CLIENT_ID)
        self.linkedin = OAuth2Session(self.CLIENT_ID, redirect_uri=self.REDIRECT_URI)
        self.authorization_url, state = self.linkedin.authorization_url(self.AUTHORIZATION_BASE_URL)
        self.PROFILE_URL = 'https://api.linkedin.com/v2/me'
        
        # print("Please go to this URL and authorize access:", self.authorization_url)
        # self.redirect_response = input("Paste the full redirect URL here: ")

    def fetch_token(self):
        self.linkedin.fetch_token(self.TOKEN_URL, authorization_response=self.redirect_response, client_secret=self.CLIENT_SECRET)

    def redirect(self):
        return self.authorization_url
    
    def callback(self):
        profile_response = self.linkedin.get(self.PROFILE_URL)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            first_name = profile_data.get("localizedFirstName", "Unknown")
            last_name = profile_data.get("localizedLastName", "Unknown")
            headline = profile_data.get("headline", "No headline")
        
            return f"""
                <h1>Welcome, {first_name} {last_name}!</h1>
                <p>Headline: {headline}</p>
                <p>Your profile data: {profile_data}</p>
            """
        else:
            return f"Error fetching profile data: {profile_response.status_code}"

    def getter(self):
        return {"CLIENT_ID": self.CLIENT_ID,
                "CLIENT_SECRET": self.CLIENT_SECRET}