import os
import time
import base64
import requests

class EbayService:
    def __init__(self, oauth_url=None, search_url=None, item_url=None, category_url=None, timeout=10):
        self.app_id = os.environ.get('EBAY_APP_ID')
        self.client_secret = os.environ.get('EBAY_CLIENT_SECRET')
        self.oauth_url = oauth_url or os.environ.get('EBAY_OAUTH_URL', 'https://api.ebay.com/identity/v1/oauth2/token')
        self.search_url = search_url or os.environ.get('EBAY_SEARCH_URL', 'https://api.ebay.com/buy/browse/v1/item_summary/search')
        self.item_url = item_url or os.environ.get('EBAY_ITEM_URL', 'https://api.ebay.com/buy/browse/v1/item/')
        self.category_url = category_url or os.environ.get('EBAY_CATEGORY_URL', 'https://api.ebay.com/commerce/taxonomy/v1/category_tree/0/get_category_suggestions')
        self.timeout = timeout

        self._access_token = None
        self._token_expiry = 0
        self._expiry_buffer = int(os.environ.get('TOKEN_EXPIRY_BUFFER', 300))

    def _get_token(self):
        now = time.time()
        if self._access_token and self._token_expiry > now:
            return self._access_token

        if not self.app_id or not self.client_secret:
            raise Exception('EBAY_APP_ID or EBAY_CLIENT_SECRET not set in environment')

        auth_string = f"{self.app_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_auth}'
        }
        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }

        r = requests.post(self.oauth_url, headers=headers, data=data, timeout=self.timeout)
        r.raise_for_status()
        jd = r.json()
        self._access_token = jd['access_token']
        self._token_expiry = now + jd.get('expires_in', 7200) - self._expiry_buffer
        return self._access_token

    def _auth_headers(self):
        token = self._get_token()
        return {'Authorization': f'Bearer {token}', 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'}

    def search_products(self, q, limit=5):
        headers = self._auth_headers()
        params = {'q': q, 'limit': limit}
        r = requests.get(self.search_url, headers=headers, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_item_details(self, item_id):
        headers = self._auth_headers()
        r = requests.get(f'{self.item_url}{item_id}', headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def suggest_category(self, q):
        headers = self._auth_headers()
        params = {'q': q}
        r = requests.get(self.category_url, headers=headers, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
