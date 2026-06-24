#checks whether any active admin-created incident matches the user question
#returns a formatted result dict if a match is found, or None otherwise
#used in bot_engine.py as step 1 of the processing pipeline

from app.admin.services.incident_service import find_matching_incident


#looks up active incidents matching the question, returns formatted result dict or None
#used in bot_engine.process_user_question
def check_active_incidents(
        question: str,
        language: str = "ru",
) -> dict | None:

    incident = find_matching_incident(
        question=question,
        language=language,
    )

    if not incident:
        return None

    #wrap incident data in the standard result format expected by bot_engine
    return {
        "answer": incident.get("answer", ""),
        "sources": [
            {
                "source": "Admin incident: " + incident.get("incident_id", ""),
                "source_type": "incident",
                "title": incident.get("title", ""),
            }
        ],
        "incident_id": incident.get("incident_id", ""),
        "incident_title": incident.get("title", ""),
    }
