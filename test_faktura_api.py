#test how faktura api works

from app.faktura_api.endpoints import *
from app.faktura_api.formatter import format_document_types
from app.faktura_api.client import api_get
from datetime import datetime

def get_employees(inn: str) -> list[dict]:

    return api_get("/Api/Company/GetEmployees")

# def get_company_labels(inn: str) -> list[dict]:
#     return api_get("/Api/Company/GetCompanyLabels")

def main():
    print("Testing Faktura API...")

    

    # res = get_document_status()
    # print(format_document_types(res))

    #print(get_role_id("489043363", 3325))

    #print(get_uset("489043363"))

    # res = get_unit_id("489043363", 3050)
    # print(res)

    # res = get_company_units("489043363")
    # #format kills text
    # print(res)


    # a = get_lgotas(489043363)
    # print(format_document_types(a))

    #???
    # res = get_product_catalog(489043363)
    # print(format_document_types(res))

    #???
    # res = get_company_branch(489043363)
    # print(res)

    # res = get_company_labels(489043363)
    # print(format_document_types(res))

    # print("Получение роли по указанному id\n")
    # res = get_role_id(106584)
    # print(format_document_types(res))


    # print("Получение ролей в организации\n")
    # res = get_company_roles("489043363")
    # print(format_document_types(res))

    # print("Получение сотрудников организации\n")
    # res = get_employees("489043363")
    # print(format_document_types(res))

    # print("\n* Document types:")
    # document_types = get_document_types()
    # print(format_document_types(document_types))

    # print("\n* Document creation type:")
    # creation_types = get_document_creation_types()
    # print(creation_types[:3])

    # print("\n* Check company exist:")
    # result = check_company_exists("489043363")
    # print(result)

if __name__ == "__main__":
    main()


