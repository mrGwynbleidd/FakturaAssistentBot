#wrapper functions for each faktura.uz api endpoint
#full reference: https://api.faktura.uz/swagger
#used in api_answer.py to fetch live data for user questions

from app.faktura_api.client import api_get, api_post


# ── company ────────────────────────────────────────────────────────────────────

#checks if a company with the given inn is registered in faktura, returns bool or dict
def check_company_exists(inn: str) -> dict | bool:
    return api_get(f"/Api/CheckCompanyExist/{inn}")


#returns full company info (name, address, director, etc.) by inn
def get_company_details(inn: str) -> dict:
    return api_get("/Api/Company/GetCompanyBasicDetails", params={"companyInn": inn})


#returns true/false whether the company is a VAT (NDS) payer
def check_nds_payer(inn: str) -> object:
    return api_get(f"/Api/Company/IsNdsPayer/{inn}")


#returns the NDS/VAT code for the company
def get_nds_vat_code(inn: str) -> str:
    return api_get(f"/Api/Company/GetNdsVatCode/{inn}")


#returns a list of employees for the company by inn
def get_employees(inn: str = "") -> list[dict]:
    params = {"companyInn": inn} if inn else {}
    return api_get("/Api/Company/GetEmployees", params=params)


#returns a list of roles defined in the company
def get_company_roles(inn: str) -> list[dict]:
    return api_get("/Api/Company/GetCompanyRoles", params={"companyInn": inn})


#returns a list of document labels/tags used by the company
def get_company_labels(inn: str = "") -> list[dict]:
    params = {"companyInn": inn} if inn else {}
    return api_get("/Api/Company/GetCompanyLabels", params=params)


#returns a list of company branches registered via tax authority
def get_company_branches(inn: str) -> list[dict]:
    return api_get(f"/Api/Company/GetCompanyBranchs/{inn}")


#returns tax benefits (льготы) for the company
def get_company_lgotas(inn: str = "") -> dict:
    return api_get("/Api/Company/Lgotas")


#searches the IKPU product catalog by name or code, returns matching items
def search_product_catalog(search_text: str, lang: str = "ru") -> list[dict]:
    return api_get("/Api/Company/ProductCatalogs/Search", params={"searchText": search_text, "lang": lang})


#returns detailed info about a specific IKPU product catalog code
def get_product_catalog_info(ikpu_code: str) -> dict:
    return api_get("/Api/Company/ProductCatalogs/GetInfo", params={"ikpu": ikpu_code})


# ── document ───────────────────────────────────────────────────────────────────

#returns all document types available in faktura
def get_document_types() -> list[dict]:
    return api_get("/Api/Document/GetDocumentTypes")


#returns all document creation method types
def get_document_creation_types() -> list[dict]:
    return api_get("/Api/Document/GetDocumentCreationTypes")


#returns all possible document status values
def get_document_statuses() -> list[dict]:
    return api_get("/Api/Document/GetDocumentStatuses")


#returns all units of measurement used in documents
def get_measurements() -> list[dict]:
    return api_get("/Api/Document/GetMeasurements")


# ── document sync / status check ───────────────────────────────────────────────

#checks document status in faktura by uid for a specific company inn
#POST /Api/GetDocumentStatus?companyInn={inn} with body {"DocumentUniqueIds": [uid]}
#returns a list of status objects
#used in api_answer._check_document_sync
def get_document_status(inn: str, doc_uid: str) -> list:
    return api_post(
        "/Api/GetDocumentStatus",
        params={"companyInn": inn},
        json_data={"DocumentUniqueIds": [doc_uid]},
    )


#returns full document details including all status fields (Faktura + Soliq)
#GET /Api/Document/GetDetails/{uid}?companyInn={inn}
#used in api_answer._check_document_sync
def get_document_details(inn: str, doc_uid: str) -> dict:
    return api_get(f"/Api/Document/GetDetails/{doc_uid}", params={"companyInn": inn})


#triggers roaming document sync for a given document, contractor type, and model type
#used in sync_roaming_service
def get_sync(inn: str, doc_uid: str, modelType: str, contractorType: str) -> dict:

    return api_get(f"/Api/Patch/SyncRoamingDocument/{doc_uid}?inn={inn}&contractorType={contractorType}&modelType={modelType}")
