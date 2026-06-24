#low-level http client for faktura.uz api — wraps requests with auth headers
#used by all endpoint functions in endpoints.py

import requests

from app.config import FAKTURA_API_BASE_URL


from app.faktura_api.auth import get_access_token

#builds authorization and content-type headers using a fresh or cached bearer token
#used in api_get and api_post
def build_headers() ->dict:

    token = get_access_token()

    return{
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

#sends an authenticated GET request to the given endpoint with optional query params
#raises RuntimeError on 4xx/5xx responses, returns parsed json
#used in endpoints.py for all read operations
def api_get(endpoint: str, params: dict | None = None) -> dict:
    
    url = f"{FAKTURA_API_BASE_URL.strip('/')}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=build_headers(),
        params=params,
        timeout=30,
    )

    #raise on any error status
    if response.status_code >= 400:
        raise RuntimeError(
            f"Faktura API GET error"
            f"Status: {response.status_code}, URL: {url}, Response: {response.text}"
        )

    return response.json()


#sends an authenticated POST request with optional json body and query params
#raises RuntimeError on 4xx/5xx responses, returns parsed json or empty dict on empty body
#used in endpoints.py for write and action operations
def api_post(endpoint: str, json_data: dict | list | None = None, params: dict | None = None) -> dict:

    url = f"{FAKTURA_API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    response = requests.post(
        url,
        headers=build_headers(),
        json=json_data,
        params=params,
        timeout=30,
    )

    #raise on any error status
    if response.status_code >= 400:
        raise RuntimeError(
            f"Faktura API POST error"
            f"Status: {response.status_code}, URL: {url}, Response: {response.text}"
        )
    
    #some endpoints return empty body on success
    if not response.text.strip():
        return {}
    
    return response.json()
