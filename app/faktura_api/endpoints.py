# Function for specific api methods

from app.faktura_api.client import api_get

#return type of faktura docs
#API: GET /Api/Document/GetDocumentTypes
def get_document_types() -> list[dict]:

    return api_get("/Api/Document/GetDocumentTypes")


#return type of doc creation
#API: GET /Api/Document/GetDocumentCreationTypes
def get_document_creation_types() -> list[dict]:

    return api_get("/Api/Document/GetDocumentCreationTypes")


#check company registration by INN
#API: GET /Api/CheckCompanyExist/:inn
def check_company_exists(inn: str) -> dict | bool:

    return api_get(f"/Api/CheckCompanyExist/{inn}")
