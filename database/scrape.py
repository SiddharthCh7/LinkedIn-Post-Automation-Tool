import os
import re
import requests
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()

class Scrape:
    def __init__(self, query):
        self.query = query
        self.service = build("customsearch", "v1", developerKey=os.getenv('GOOGLE_SEARCH_API_KEY'))
    
    def google_search(self, query, **kwargs):
        try:
            res = self.service.cse().list(q=query, cx=os.getenv('SEARCH_ENGINE_ID'), **kwargs).execute()
            return res
        except Exception as e:
            print(f"Exception in google_search: {e}")
            return None

    def clean_text(self, text):
        unwanted_phrases = [
            r'\b(sign up|sign in|log in|login|register)\b',
            r'\b(copyright|terms of service|privacy policy)\b',
            r'\b(advertisement|sponsored|promoted)\b',
            r'\b(contact|about us|subscribe|share|follow)\b'
        ]

        pattern = '|'.join(unwanted_phrases)
        cleaned_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text

    def get_page_content(self, url):
        try:
            session = requests.Session()
            session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
})
            response = session.get(url)
            response.raise_for_status()
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                paragraphs = soup.find_all('p')
                text = " ".join([para.get_text() for para in paragraphs if para.get_text().strip() != ''])

                cleaned_text = self.clean_text(text)
                return cleaned_text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current url, trying another one......\n{url}")
            return False

    def search_internet(self):
        try:
            res = self.google_search(self.query)
            top_results = res.get("items", [])
            return top_results
        except Exception as e:
            print(f"Exception in search_internet: {e}")
            return None

    def scrape_results(self):
        try:
            top_results = self.search_internet()
            document_objs = []
            
            for item in top_results:
                link = item['link']
                content = self.get_page_content(link)
                if not content:
                    continue
                document = Document(
                    page_content=content,
                    metadata={"source": link}
                )
                if content:
                    document_objs.append(document)
            return document_objs
        except Exception as e:
            print(f"Exception in scrape_results: {e}")
            return None
