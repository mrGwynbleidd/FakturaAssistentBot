#convert json-response into readable text

import json

#convert json-response into context for LLM
def format_json_context(data: dict | list, title: str = "Faktura API Response") -> str:

    pretty_json = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    return  f"""
SOURCE: Faktura API
TITLE: {title}

JSON:
{pretty_json}
""".strip()


#convert doc type
def format_document_types(data: list[dict]) -> str:

    if not data:
        return "API not return type of docs"
    
    lines = ["Types of documents in Faktura:"]

    for item in data:
        description = item.get("description", "Noname")
        code = item.get("code", "no_code")
        item_id = item.get("id", "")

        lines.append(f"- {description} | id: {item_id}, code: {code}")

    return "\n".join(lines)
