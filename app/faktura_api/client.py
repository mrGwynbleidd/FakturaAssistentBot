# take user do/post requests

import requests

from app.config import FAKTURA_API_BASE_URL


from app.faktura_api.auth import get_access_token

#form headers from api requests
def build_headers() ->dict:

    token = get_access_token()

    return{
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

#get-request
def api_get(endpoint: str, params: dict | None = None) -> dict:
    
    url = f"{FAKTURA_API_BASE_URL.strip('/')}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=build_headers(),
        params=params,
        timeout=30,
    )

    #error exeption
    if response.status_code >= 400:
        raise RuntimeError(
            f"Faktura API GET error"
            f"Status: {response.status_code}, URL: {url}, Response: {response.text}"
        )

    return response.json()


#post-requests
def api_post(endpoint: str, json_data: dict | list | None = None, params: dict | None = None) -> dict:

    url = f"{FAKTURA_API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    response = requests.post(
        url,
        headers=build_headers(),
        json=json_data,
        params=params,
        timeout=30,
    )


    #error exeption
    if response.status_code >= 400:
        raise RuntimeError(
            f"Faktura API POST error"
            f"Status: {response.status_code}, URL: {url}, Response: {response.text}"
        )
    
    if not response.text.strip():
        return {}
    
    return response.json()



