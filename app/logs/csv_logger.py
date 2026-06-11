#Save user input, answer, time, language, source

import csv
from pathlib import Path
from datetime import datetime

#save base dir
BASE_DIR = Path(__file__).resolve().parents[2]
#dir where to save data
LOG_FILE_PATH = BASE_DIR / "data" / "raw" / "QA_outputs.csv"


FIELDNAMES = [
    "datetime",
    "language",
    "question",
    "answer",
    "sources",
]

#Make text safe for csv, remove extra line breaks within a cell
def clean_text(text: str) -> str:

    #if text is empty
    if not text:
        return ""

    #text in one line
    return " ".join(str(text).split())

#Convert list of sources into one line
def format_sources(sources: list[dict] | None) -> str:

    #if source is empty
    if not sources:
        return ""

    #arr for new source
    unique_sources = []

    for source in sources:
        #get source name
        source_name = source.get("source", "unknown")

        #if source name is new
        if source_name not in unique_sources:
            #add to arr
            unique_sources.append(source_name)
    #return arr of soures
    return "; ".join(unique_sources)

#save user question, model answer and other useful info
def save_qa(
    question: str,
    answer: str,
    language: str = "unknown",
    sources: list[dict] | None = None,
) -> None:


    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_exists = LOG_FILE_PATH.exists()

    
    row = {
        #get time
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        #language
        "language": language,
        #cleaned and safe question
        "question": clean_text(question),
        #clean and safe answer
        "answer": clean_text(answer),
        #safe sources
        "sources": format_sources(sources),
    }

    #insert row in csv
    with open(LOG_FILE_PATH, mode="a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        #if file is empty
        if not file_exists:
            #write fieldnames
            writer.writeheader()

        #write row
        writer.writerow(row)