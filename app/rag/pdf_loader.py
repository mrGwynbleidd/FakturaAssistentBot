#Read files from data/pdf. Get text from each page and save its source

from pathlib import Path
from pypdf import PdfReader

#read files from dir and return list of docs with sources
def load_pdfs(pdf_dir: str = "data/pdf") -> list[dict]:

    #get path to pdf files
    pdf_path = Path(pdf_dir)

    #not found such path
    if not pdf_path.exists():
        raise FileNotFoundError(f"Directory {pdf_dir} not found")

    #arr contain text from all documents
    documents = []

    #will files one by one
    for file_path in pdf_path.glob("*.pdf"):

        # read files
        reader = PdfReader(str(file_path))

        #arr for text that was taken from file
        full_text = ""


        for page_number, page in enumerate(reader.pages, start=1):
            #get text from page
            text = page.extract_text()

            #if text not empty
            if text:
                #add in arr, and page were it was taken
                full_text += f"\n\n[Page {page_number}]\n{text}"

        #if full_text not empty
        if full_text.strip():
            #add text from whole doc
            documents.append(
                {
                    #write where info was taken
                    "source": file_path.name,
                    #add text
                    "text": full_text.strip(),
                }
            )

    #return arr with all text from docs
    return documents