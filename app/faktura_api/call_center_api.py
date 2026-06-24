#fetches closed tickets from call center API, extracts Q&A pairs, saves to call_center_cases_raw.csv
#used as a standalone script to collect training data from real support tickets

#import libs
import csv
import time
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

from app.config import EMAIL, API_PARAM, CALL_CENTER_DOMAIN

from app.learning.review_manager import clean_text
from app.faktura_api.call_center_cleaner import clean_question, clean_answer, is_quality_pair

#base dir
BASE_DIR = Path(__file__).resolve().parents[2]

#only fetch tickets with these statuses
CLOSED_STATUS = "closed,resolved"
OUTPUT_CSV = BASE_DIR / "data" / "learning" / "call_center_cases_raw.csv"
#pause between api requests to avoid rate limiting
REQUEST_PAUSE=0.4

BASE_URL = f"{CALL_CENTER_DOMAIN.rstrip('/')}/api/v2"

#csv field names for the raw output file
RAW_FIELDNAMES = [
    "case_id",
    "ticket_id",
    "datetime",
    "language",
    "question",
    "admin_answer",
    "category",
    "source_type",
    "source_id",
    "status",
]

#http basic auth using email and api key from config
auth = HTTPBasicAuth(EMAIL, API_PARAM)

#strips html tags from ticket post text, returns plain text
#used in build_qa to clean post content
def strip_html(html: str)-> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)

#extracts a list of items from an api response that may be a list, dict with data key, or nested
#used in get_tickets and get_posts to normalize response shapes
def extract_items(payload) -> list[dict]:

    if isinstance(payload, list):
        return payload
    
    if not isinstance(payload, dict):
        return []
    
    data = payload.get("data")

    if isinstance(data, list):
        return data
    
    if isinstance(data, dict):
        return list(data.values())
    
    items =payload.get("item")

    if isinstance(items, list):
        return items
    
    return []

#fetches paginated ticket list from api filtered by closed status, returns raw json
#used in save_callcenter_cases
def get_tickets(page: int)->dict:
    params = {"page": page}
    if CLOSED_STATUS:
        params["status_list"] = CLOSED_STATUS
    
    response = requests.get(f"{BASE_URL}/tickets/", params=params, auth=auth, timeout=30)
    response.raise_for_status()

    return response.json()

#fetches all posts (messages) for a ticket by id, returns list of post dicts
#used in build_qa to get the conversation thread
def get_posts(ticket_id: int)-> list:

    response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}/posts/",
        params={"page": 1},
        auth= auth,
        timeout=30,
    )

    response.raise_for_status()

    return extract_items(response.json())


#builds a Q&A dict from a ticket by separating client messages from agent replies
#cleans and validates the pair, returns None if quality check fails
#used in save_callcenter_cases
def build_qa(ticket: dict) -> dict | None:

    ticket_id = ticket.get("id")

    if not ticket_id:
        return None

    client_id = ticket.get("user_id")

    posts = get_posts(ticket_id)

    if not posts:
        return None

    #sort posts chronologically by id
    posts.sort(key=lambda post: post.get("id", 0))

    questions = []
    answers = []

    for post in posts:

        if not isinstance(post, dict):
            continue

        text = strip_html(post.get("text", ""))

        if not text:
            continue

        #posts from the original user are questions; others are agent answers
        if post.get("user_id") == client_id:
            questions.append(text)
        else:
            answers.append(text)

    raw_question = clean_text(f"{ticket.get('title', '')} {' '.join(questions)}")
    raw_answer = clean_text(" ".join(answers))

    question = clean_question(raw_question)
    answer = clean_answer(raw_answer)

    #discard pairs that are too short after cleaning
    if not is_quality_pair(question, answer):
        return None
    
    return{
        "case_id": f"call_center_{ticket_id}",
        "ticket_id": ticket_id,
        "datetime": ticket.get("date_created", ""),
        "language": "ru",
        "question": question,
        "admin_answer": answer,
        "category": "call_center",
        "source_type": "call_center",
        "source_id": str(ticket_id),
        "status": "raw",
    }

#fetches all closed tickets page by page, builds Q&A pairs, writes them to call_center_cases_raw.csv
#max_pages limits how many pages are fetched (None = all)
#used as script entry point and by import pipeline
def save_callcenter_cases(max_pages: int | None) -> None:

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    page =1

    while True:
        data = get_tickets(page)
        tickets = extract_items(data)

        if not tickets:
            break

        for ticket in tickets:
            qa = build_qa(ticket)

            if qa:
                rows.append(qa)
                print(f"Ticket {qa['ticket_id']}: {qa['question'][:60]}...")

            time.sleep(REQUEST_PAUSE)

        pagination = data.get("pagination", {}) if isinstance(data, dict) else {}

        total_pages = pagination.get("total_pages", page)

        print(f"Page {page}/{total_pages} processed")

        if max_pages and page >= max_pages:
            break
        
        if page >= total_pages:
            break

        page +=1
        time.sleep(REQUEST_PAUSE)

    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nReady: {len(rows)} cases was saved in {OUTPUT_CSV}")


if __name__ == "__main__":
    save_callcenter_cases(10)
