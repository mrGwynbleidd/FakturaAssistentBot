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

#return info about employees
def get_employees(inn: str) -> dict | bool:

    return api_get("/Api/Company/GetEmployees")

#return roles in company
#error 404
def get_company_roles(inn: str) -> list[dict]:
    return api_get("/Api/Company/GetCompanyRoles")

#
def get_company_labels(inn: str) -> list[dict]:
    return api_get("/Api/Company/GetCompanyLabels")

#
def get_company_branch(inn: str) -> list[dict]:
    return api_get("/Api/Company/GetCompanyBranchs/{inn}")

#
def get_product_catalog(inn: str, searchText: str = "all", lang: str = "ru") -> list[dict]:
    return api_get("/Api/Company/ProductCatalogs")

#
def get_lgotas(inn: str, lang: str = "ru") -> dict | bool:
    return api_get("/Api/Company/Lgotas")

#
def get_taxGap(inn: str, date: str, lang: str = "ru"):
    return api_get("/Api/Company/TaxGap")

def get_company_units(inn: str) -> list[dict]:
    return api_get("/Api/Unit/GetCompanyUnits")

def get_unit_id(inn: str, id: int) ->list[dict]:
    return api_get(f"/Api/Unit/GetById/{id}")

def get_uset(inn: str) -> list[dict]:
    return api_get("/api/User")

def get_role(inn: str) -> list[dict]:
    return api_get("/api/Role")

def get_role_id(inn: str, id: int) -> list[dict]:
    return api_get(f"/api/Role/{id}")

def get_document_status() -> dict[list]:
    return api_get("/Api/Document/GetDocumentStatuses")


