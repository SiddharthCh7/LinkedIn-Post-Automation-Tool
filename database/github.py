import requests, os, base64
from dotenv import load_dotenv
from .scrape import Scrape
from bs4 import BeautifulSoup
load_dotenv()

class Github:
    def __init__(self):
        self.access_token = os.getenv('GITHUB_API_KEY')
        self.headers = {
            'Authorization': f'token {self.access_token}'
        }
        self.scraper = Scrape()
    
    def read_readme(self, url):
        print(url)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            text = " ".join([para.get_text() for para in paragraphs if para.get_text().strip() != ''])
            cleaned_text = self.scraper.clean_text(text)
            return cleaned_text
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            print(response.content)
            return None