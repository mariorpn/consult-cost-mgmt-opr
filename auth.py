import os
import requests
from datetime import datetime, timedelta

class RedHatAuth:

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"
        
        self._access_token = None
        self._expires_at = None

    def get_token(self):
        if self._access_token and self._expires_at and datetime.now() < self._expires_at:
            return self._access_token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(self.token_url, data=payload, headers=headers, timeout=10)
        
        response.raise_for_status()
        
        data = response.json()
        self._access_token = data.get("access_token")
        expires_in = data.get("expires_in", 300)
        
        self._expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        
        return self._access_token
