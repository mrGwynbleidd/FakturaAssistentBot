#keywords for bot when he can use api      

def should_use_faktura_api(question: str) -> bool:

    q = question.lower()

    api_keywords = [
        "api",
        "json",
        "тип документа",
        "типы документов",
        "document types",
        "код документа",
        "getdocumenttypes",
        "getdocumentcreationtypes",
        "проверить инн",
        "проверь инн",
        "инн",
        "компания зарегистрирована",
        "check company",
        "check employee",
        "getemployees",
        "getcompanyroles",
        "check roles",
        "получить роли в компании",
        "роли",
        "roles",
    ]

    return any(keyword in q for keyword in api_keywords)

#detect specific api-move
def detect_api_intent(question: str) -> str | None:

    q = question.lower()

    if any(
        x in q
        for x in  [
            "тип документа", 
            "типы документов", 
            "document types", 
            "getdocumenttypes"
            ]
    ):
        
        return "get_document_types"
    
    if any(
        x in q 
        for x in [
            "типы создания", 
            "creation types", 
            "getdocumentcreationtypes"
            ]
    ):
        return "get_document_creation_types"

    if any(
        x in q 
        for x in [
            "проверить инн",
            "проверь инн",
            "инн",
            "check company",
            "компания зарегистрирована",
        ]
    ):
        return "check_company_exists"
    
    if any(
        x in q
        for x in [
            "check employee",
            "getemployees",
            "проверить сотрудника",
            "Получение сотрудников организации"
        ]
    ): 
        return "get_employees"
    
    if any(
        x in q
        for x in [
            "getcompanyroles",
            "check roles",
            "получить роли в компании",
            "роли",
            "roles",
        ]
    ): return "get_company_roles"

    return None


