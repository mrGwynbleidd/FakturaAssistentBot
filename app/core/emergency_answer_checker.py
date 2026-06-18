
from app.admin.services.incident_service import find_matching_incident

def check_active_incidents(
        question: str,
        language: str = "ru",
)-> dict | None:
    
    incident = find_matching_incident(
        question=question,
        language=language,
    )

    if not incident:
        return None
    
    return {
        "answer": [
            {
                "source": f"Admin incident: {incident.get('incident_id', '')}",
                "source_type": "incident",
                "title": incident.get("title", ""),
            }
        ],
        "incident_id": incident.get("incident_id", ""),
        "incident_title": incident.get("title", ""),
    }
