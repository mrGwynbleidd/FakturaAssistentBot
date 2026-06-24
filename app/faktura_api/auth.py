#obtains and caches an OAuth2 bearer token from faktura account service
#used by client.build_headers for all authenticated api requests

#import libs
import time
import requests

#import credentials from config
from app.config import (
    FAKTURA_USERNAME,
    FAKTURA_PASSWORD,
    FAKTURA_CLIENT_ID,
    FAKTURA_CLIENT_SECRET,
    FAKTURA_ACCOUNT_URL,
)

#module-level token cache — avoids requesting a new token on every api call
_cached_token = None
_token_expires_at = 0


#returns a valid access token, using cached value if it has not expired
#requests a new token from /token endpoint with password grant when cache is stale
#used in client.build_headers
def get_access_token() -> str:

    global _cached_token, _token_expires_at

    #return cached token if still valid
    if _cached_token and time.time() < _token_expires_at:
        return _cached_token
    
    if not all ([
        FAKTURA_USERNAME,
        FAKTURA_PASSWORD,
        FAKTURA_CLIENT_ID,
        FAKTURA_CLIENT_SECRET,
    ]):
        raise ValueError(
            "Not filled FAKTURA_USERNAME, FAKTURA_PASSWORD, FAKTURA_CLIENT_ID or FAKTURA_CLIENT_SECRET in .env"
        )
    
    url = f"{FAKTURA_ACCOUNT_URL}/token"

    payload = {
        "grant_type": "password",
        "username": FAKTURA_USERNAME,
        "password": FAKTURA_PASSWORD,
        "client_id": FAKTURA_CLIENT_ID,
        "client_secret": FAKTURA_CLIENT_SECRET,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        timeout=20,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Error in getting Faktura API"
            f"Status: {response.status_code}, Response: {response.text}"
        )
    
    #parse token response
    data = response.json()

    #extract token and expiry
    access_token = data.get("access_token")
    #token lifetime in seconds — default 3600, but typically 168 hours
    expires_in = data.get("expires_in", 3600)

    if not access_token:
        raise RuntimeError(f"access_token not founded in response: {data}")
    
    #store token in module cache
    _cached_token = access_token

    #subtract 60 seconds buffer to refresh slightly before actual expiry
    _token_expires_at = time.time() + int(expires_in) - 60

    return _cached_token
