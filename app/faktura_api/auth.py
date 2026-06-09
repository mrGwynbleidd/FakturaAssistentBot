# Get accsess token from user

#import libs
import time
import requests

#import variables

from app.config import (
    FAKTURA_USERNAME,
    FAKTURA_PASSWORD,
    FAKTURA_CLIENT_ID,
    FAKTURA_CLIENT_SECRET,
    FAKTURA_ACCOUNT_URL,
)

_cached_token = None
_token_expires_at = 0


#get access token from api
#use cache to not request one more time
def get_access_token() -> str:

    global _cached_token, _token_expires_at

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
        "Accept": "applecation/json",
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
    
    #get json response
    data = response.json()

    #get access token
    access_token = data.get("access_token")
    #time when access token will disapear 168 hours
    expires_in = data.get("expires_in", 3600)

    #if access_token is empty
    if not access_token:
        raise RuntimeError(f"access_token not founded in response: {data}")
    
    #save in cache access token
    _cached_token = access_token

    #updata token
    _token_expires_at = time.time() + int(expires_in) - 60

    return _cached_token





