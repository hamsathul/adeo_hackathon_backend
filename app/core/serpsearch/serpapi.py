# app/core/serpapi.py
import requests
import json
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class SerperClient:
    BASE_URL = "https://google.serper.dev"
    ENDPOINT_MAPPING = {
        'search': '/search',
        'images': '/images',
        'videos': '/videos',
        'places': '/places',
        'maps': '/maps',
        'news': '/news',
        'scholar': '/scholar',
        'patents': '/patents'
    }

    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY')
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    async def search(self, query: str, search_type: str = 'search') -> Dict[str, Any]:
        if search_type not in self.ENDPOINT_MAPPING:
            raise ValueError(f"Invalid search type: {search_type}")

        endpoint = self.ENDPOINT_MAPPING[search_type]
        url = f"{self.BASE_URL}{endpoint}"
        payload = {"q": query}

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}