
from dataclasses import dataclass
from typing import Any

from app.importers.call_center_mapping import GOOD_STATUSES
from app.importers.text_cleaner import normalize_ticket_fields, get_ticket_quality_reasons


DESTINATION_APPROVED = "approved"
DESTINATION_NEEDS_REVIEW = "needs_review"
DESTINATION_IMPORT_ERRORS = "import_errors"

FATAL_REASONS = {
    "empty_question",
    "empty_answer",
    "question_too_short",
}

REVIEW_REASONS = {
    "answer_too_short",
    "bad_answer_phrase",
    "personal_data_in_question",
    "personal_data_in_answer",
}

@dataclass
class TicketClassification:
    destination: str
    normalized_ticket: dict[str, str]
    reasons: list[str]
    approved_ready: bool


def is_good_status(status: str) -> bool:
    status = str(status or "").strip().lower()

    if not status:
        return False
    
    return status in GOOD_STATUSES


def has_fatal_reasons(reasons: list[str]) -> bool:
    return any(reason in FATAL_REASONS for reason in reasons)

def has_review_reasons(reasons: list[str]) -> bool:
    return any(reason in REVIEW_REASONS for reason in reasons )

def classify_ticket(raw_ticket: dict[str, Any])-> TicketClassification:

    normalized = normalize_ticket_fields(raw_ticket)
    reasons = get_ticket_quality_reasons(raw_ticket)

    status = normalized.get("status", "")

    if has_fatal_reasons(reasons):
        return TicketClassification(
            destination=DESTINATION_IMPORT_ERRORS,
            normalized_ticket=normalized,
            reasons=reasons,
            approved_ready=False,
        )
    
    if not is_good_status(status):
        reasons.append("status_not_approved_for_direct_import")

        return TicketClassification(
            destination=DESTINATION_NEEDS_REVIEW,
            normalized_ticket=normalized,
            reasons=reasons,
            approved_ready=False,
        )
    
    if has_review_reasons(reasons):
        return TicketClassification(
            destination=DESTINATION_NEEDS_REVIEW,
            normalized_ticket=normalized,
            reasons=reasons,
            approved_ready=False,
        )
    
    return TicketClassification(
        destination=DESTINATION_APPROVED,
        normalized_ticket=normalized,
        reasons= [],
        approved_ready=True,
    )


def classification_to_dict(classification: TicketClassification) -> dict[str, Any]:
    ticket = classification.normalized_ticket

    return {
        "destination": classification.destination,
        "approved_ready": classification.approved_ready,
        "reasons": ";".join(classification.reasons),
        "ticket_id": ticket.get("ticket_id", ""),
        "created_at": ticket.get("created_at", ""),
        "language": ticket.get("language", ""),
        "question": ticket.get("question", ""),
        "answer": ticket.get("answer", ""),
        "category": ticket.get("category", ""),
        "status": ticket.get("status", ""),
    }
    

