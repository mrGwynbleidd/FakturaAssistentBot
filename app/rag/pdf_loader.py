# #Read files from data/pdf. Get text from each page and save its source

# from pathlib import Path
# from pypdf import PdfReader

# #read files from dir and return list of docs with sources
# def load_pdfs(pdf_dir: str = "data/pdf") -> list[dict]:

#     #get path to pdf files
#     pdf_path = Path(pdf_dir)

#     #not found such path
#     if not pdf_path.exists():
#         raise FileNotFoundError(f"Directory {pdf_dir} not found")

#     #arr contain text from all documents
#     documents = []

#     #will files one by one
#     for file_path in pdf_path.glob("*.pdf"):

#         # read files
#         reader = PdfReader(str(file_path))

#         #arr for text that was taken from file
#         full_text = ""


#         for page_number, page in enumerate(reader.pages, start=1):
#             #get text from page
#             text = page.extract_text()

#             #if text not empty
#             if text:
#                 #add in arr, and page were it was taken
#                 full_text += f"\n\n[Page {page_number}]\n{text}"

#         #if full_text not empty
#         if full_text.strip():
#             #add text from whole doc
#             documents.append(
#                 {
#                     #write where info was taken
#                     "source": file_path.name,
#                     #add text
#                     "text": full_text.strip(),
#                 }
#             )

#     #return arr with all text from docs
#     return documents


#reads pdf files from the pdf directory, extracts text page by page
#returns list of document dicts ready for splitting and indexing
#used in index_builder.build_pdf_index

from pathlib import Path
from app.rag.settings import PDF_DIR
from app.rag.text_utils import clean_text, make_id


#extracts full text from a single pdf file, one labeled block per page
#tries pypdf first then PyPDF2 as fallback
#returns concatenated page texts or empty string if file has no extractable text
def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError as err:
            raise RuntimeError("Для чтения PDF установите pypdf: pip install pypdf") from err
        
    reader = PdfReader(str(path))
    parts: list[str] = []

    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = clean_text(text)
        if text:
            parts.append(f"Page {page_index}:\n{text}")

    #join all pages outside the loop
    return "\n\n".join(parts)


#loads all pdf files from pdf_dir, returns list of document dicts with id, text, and metadata
#skips files with no extractable text
#used in index_builder.build_pdf_index
def load_pdfs(pdf_dir: Path = PDF_DIR) -> list[dict]:
    if not pdf_dir.exists():
        return []
    
    documents: list[dict] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        text = extract_pdf_text(pdf_path)
        if not text:
            continue

        doc_id = make_id("pdf", str(pdf_path.name))
        documents.append({
            "id": doc_id,
            "text": text,
            "metadata": {
                "source_type": "pdf",
                "file_name": pdf_path.name,
                "source_path": str(pdf_path),
                "priority": 10,
              },
        })
    return documents
