#test how faktura api works

from app.faktura_api.endpoints import(
    get_document_types,
    get_document_creation_types,
    check_company_exists,
)
from app.faktura_api.formatter import format_document_types

def main():
    print("Testing Faktura API...")

    print("\n* Document types:")
    document_types = get_document_types()
    print(format_document_types(document_types))

    print("\n* Document creation type:")
    creation_types = get_document_creation_types()
    print(creation_types[:3])

    print("\n* Check company exist:")
    result = check_company_exists("489043363")
    print(result)

if __name__ == "__main__":
    main()


