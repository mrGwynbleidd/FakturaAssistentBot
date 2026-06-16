#Save tickets from call center api

#import libs
import csv
import time
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

from app.config import EMAIL, API_PARAM, CALL_CENTER_DOMAIN

from app.learning.review_manager import clean_text

#base dir
BASE_DIR = Path(__file__).resolve().parents[2]

#Domain


CLOSED_STATUS = "closed,resolved"
OUTPUT_CSV = BASE_DIR / "data" / "learning" / "call_center_cases_raw.csv"
REQUEST_PAUSE=0.4

BASE_URL = f"{CALL_CENTER_DOMAIN.rstrip('/')}/api/v2"

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

auth = HTTPBasicAuth(EMAIL, API_PARAM)

#remove HTML tags
def strip_html(html: str)-> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)

#universal get list of el from api response
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

#get list ticket
def get_tickets(page: int)->dict:
    params = {"page": page}
    if CLOSED_STATUS:
        params["status_list"] = CLOSED_STATUS
    
    response = requests.get(f"{BASE_URL}/tickets/", params=params, auth=auth, timeout=30)
    response.raise_for_status()

    return response.json()

#get text from ticket

def get_posts(ticket_id: int)-> list:

    response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}/posts/",
        params={"page": 1},
        auth= auth,
        timeout=30,
    )

    response.raise_for_status()

    return extract_items(response.json())


#collect q/a
def build_qa(ticket: dict) -> dict | None:

    ticket_id = ticket.get("id")

    if not ticket_id:
        return None

    client_id = ticket.get("user_id")

    posts = get_posts(ticket_id)

    if not posts:
        return None
    
    if not isinstance(posts, dict):
        return {}

    ###
    posts.sort(key=lambda post: post.get("id", 0))

    questions = []
    answers = []

    for post in posts:

        if not isinstance(post, dict):
            return post

        text = strip_html(post.get("text", ""))

        if not text:
            continue

        if post.get("user_id") == client_id:
            questions.append(text)
        else:
            answers.append(text)

    question = clean_text(f"{ticket.get('title', '')} {' '.join(questions)}")

    answer = clean_text(" ".join(answers))

    if not question or not answer:
        return None
    
    return{
        "case_id": f"call_center_{ticket_id}",
        "ticket_id": ticket_id,
        "datetime": ticket.get("date_created", ""),
        "language": "ru",
        "question": question,
        "admin_answer": answer,
        "category": "call_center",
        "soure_type": "call_center",
        "source_id": str(ticket_id),
        "status": "raw",
    }

#save real cases from call center in raw.csv
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
                print(f"Ticket {qa["ticket_id"]}: {qa["question"][:60]}...")

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
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES, quoting=csv.QUOTE_ALL,)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nReady: {len(rows)} cases was saved in {OUTPUT_CSV}")


if __name__ == "__main__":
    save_callcenter_cases(10)