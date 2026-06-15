import csv
import time
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from app.config import EMAIL
from app.config import API_PARAM

#Domain
DOMAIN = "https://d"
CLOSED_STATUS = "closed,resolved"
OUTPUT_CSV = "daodesk_cases.csv"
REQUEST_PAUSE=0.4

BASE_URL = f"{DOMAIN}/api/v2"
auth = HTTPBasicAuth(EMAIL, API_PARAM)

#remove HTML tags
def strip_html(html: str)-> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)

#get ticket
def get_tickets(page: int)->dict:
    params = {"page": page}
    if CLOSED_STATUS:
        params["status_list"] = CLOSED_STATUS
    
    response = requests.get(f"{BASE_URL}/tickets/", params=params, auth=auth, timeout=30)
    response.raise_for_status()

    return response.json()

#get posts, admin answer

def get_posts(ticket_id: int)-> list:

    response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}/posts/",
        params={"page": 1},
        auth= auth,
        timeout=30,
    )

    response.raise_for_status()

    # resp = response.json()
    
    # if not isinstance(resp, list):
    #     resp = []

    # resp.__getattribute__("data")

    ###
    return response.json().get("data", [])


#collect q/a
def build_qa(ticket: dict) -> dict | None:

    ticket_id = ticket["id"]
    client_id=ticket["user_id"]

    posts = get_posts(ticket_id)

    # if no aswer from admin
    if not posts:
        return None
    
    posts.sort(key=lambda p: p.get("id", 0))

    questions = [strip_html(p.get("text", "")) for p in posts if p.get("user_id") == client_id]
    answers = [strip_html(p.get("text", "")) for p in posts if p.get("user_id") != client_id]

    #question - theame of ticket and text from user
    question = (ticket.get("title", "") + " " + " ".join(q for q in questions if q)).strip()
    #answer - answer from call center
    answer = " ".join(a for a in answers if a).strip()

    if not question or not answer:
        return None
    
    return {
        "ticket_id": ticket_id,
        "question": question,
        "answer": answer,
        "date": ticket.get("date_created", ""),
    }

def save_csv():
    rows = []
    page =1

    while True:
        data = get_tickets(page)
        tickets = get_tickets("data", {})

        if not tickets:
            break

        for ticket in tickets.values():
            qa = build_qa(ticket)

            if qa:
                rows.append(qa)
                print(f"Ticket {qa["ticket_id"]}: {qa["question"][:60]}...")

            time.sleep(REQUEST_PAUSE)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)

        print(f"Page {page}/{total_pages} processed")
        if page >= total_pages:
            break

        page +=1
        time.sleep(REQUEST_PAUSE)

    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["ticket_id", "question", "answer", "date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nReady: {len(rows)} cases was saved in {OUTPUT_CSV}")
