# Faktura API endpoint wrappers
# Full reference: https://api.faktura.uz/swagger

from app.faktura_api.client import api_get, api_post


# ── Company ────────────────────────────────────────────────────────────────────

def check_company_exists(inn: str) -> dict | bool:
    """Check if company with given INN is registered in Faktura."""
    return api_get(f"/Api/CheckCompanyExist/{inn}")


def get_company_details(inn: str) -> dict:
    """Full company info (name, address, director, etc.) by INN."""
    return api_get("/Api/Company/GetCompanyBasicDetails", params={"companyInn": inn})


def check_nds_payer(inn: str) -> object:
    """Returns true/false — is company a VAT (NDS) payer."""
    return api_get(f"/Api/Company/IsNdsPayer/{inn}")


def get_nds_vat_code(inn: str) -> str:
    """Returns the NDS/VAT code for the company."""
    return api_get(f"/Api/Company/GetNdsVatCode/{inn}")


def get_employees(inn: str = "") -> list[dict]:
    """List employees of a company."""
    params = {"companyInn": inn} if inn else {}
    return api_get("/Api/Company/GetEmployees", params=params)


def get_company_roles(inn: str) -> list[dict]:
    """List roles in a company (INN required)."""
    return api_get("/Api/Company/GetCompanyRoles", params={"companyInn": inn})


def get_company_labels(inn: str = "") -> list[dict]:
    """List document labels/tags of the company."""
    params = {"companyInn": inn} if inn else {}
    return api_get("/Api/Company/GetCompanyLabels", params=params)


def get_company_branches(inn: str) -> list[dict]:
    """List branches of a company registered via tax authority."""
    return api_get(f"/Api/Company/GetCompanyBranchs/{inn}")


def get_company_lgotas(inn: str = "") -> dict:
    """Tax benefits (льготы) for the company."""
    return api_get("/Api/Company/Lgotas")


def search_product_catalog(search_text: str, lang: str = "ru") -> list[dict]:
    """Search IKPU product catalog by name or code."""
    return api_get("/Api/Company/ProductCatalogs/Search", params={"searchText": search_text, "lang": lang})


def get_product_catalog_info(ikpu_code: str) -> dict:
    """Get detailed info about a specific IKPU code."""
    return api_get("/Api/Company/ProductCatalogs/GetInfo", params={"ikpu": ikpu_code})


# ── Document ───────────────────────────────────────────────────────────────────

def get_document_types() -> list[dict]:
    """List all document types available in Faktura."""
    return api_get("/Api/Document/GetDocumentTypes")


def get_document_creation_types() -> list[dict]:
    """List document creation method types."""
    return api_get("/Api/Document/GetDocumentCreationTypes")


def get_document_statuses() -> list[dict]:
    """List all possible document statuses."""
    return api_get("/Api/Document/GetDocumentStatuses")


def get_measurements() -> list[dict]:
    """List units of measurement used in documents."""
    return api_get("/Api/Document/GetMeasurements")


# ── Document sync / status check ───────────────────────────────────────────────

def get_document_status(inn: str, doc_uid: str) -> list:
    """
    Check document status in Faktura for a specific UID.
    POST /Api/GetDocumentStatus?companyInn={inn}
    Body: {"DocumentUniqueIds": ["uid"]}
    Returns a list of status objects.
    """
    return api_post(
        "/Api/GetDocumentStatus",
        params={"companyInn": inn},
        json_data={"DocumentUniqueIds": [doc_uid]},
    )


def get_document_details(inn: str, doc_uid: str) -> dict:
    """
    Get full document details including all status fields (Faktura + Soliq).
    GET /Api/Document/GetDetails/{uid}?companyInn={inn}
    """
    return api_get(f"/Api/Document/GetDetails/{doc_uid}", params={"companyInn": inn})



def get_sync(inn: str, doc_uid: str, modelType: str, contractorType: str) -> dict:

    return api_get(f"/Api/Patch/SyncRoamingDocument/{doc_uid}?inn={inn}&contractorType={contractorType}&modelType={modelType}")
