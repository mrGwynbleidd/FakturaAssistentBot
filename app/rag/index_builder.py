# #Get pdf -> Get its text -> Divid into chunks -> Make embending -> Save it in Chroma

# from app.rag.approved_loader import load_approved_cases

# from app.rag.admin_knowledge_loader import load_admin_knowledge

# #import our function load_pdf step 1,2
# from app.rag.pdf_loader import load_pdfs
# #import our function split text step 3
# #from app.rag.splitter import split_text
# from app.rag.splitter import split_documents
# #import our function get_embeddings step 4
# from app.rag.embedding import embed_texts   

# from app.rag.chroma_client import reset_collection, get_or_create_collection

# from app.rag.settings import COLLECTION_APPROVED, COLLECTION_ADMIN_KNOWLEDGE, COLLECTION_PDF

# #import vector database, step 5
# import chromadb

# from app.learning.approved_loader import load_approved_cases
# from app.rag.admin_knowledge_loader import load_admin_knowledge


# #path to save data from embedding
# CHROMA_PATH = "data/chroma_db"
# COLLECTION_NAME = "faktura_pdf_knowledge"


# def build_index() -> None:

#     # ── 1. Admin Q/A (highest priority) ──────────────────────────────────────
#     print("Load Admin Q/A...")
#     admin_knowledge = load_admin_knowledge()
#     print(f"Founded admin Q/A: {len(admin_knowledge)}")

#     # ── 2. Approved cases (review + group + call center) ─────────────────────
#     print("Load Approved cases...")
#     approved_cases = load_approved_cases()
#     print(f"Founded approved cases: {len(approved_cases)}")

#     # ── 3. PDF instructions (lowest priority) ────────────────────────────────
#     print("Load PDF-files...")
#     pdf_doc = load_pdfs("data/pdf")
#     print(f"Founded PDF-files: {len(pdf_doc)}")

#     all_docs = []

#     # Admin Q/A — indexed first so their chunk IDs come first
#     for doc in admin_knowledge:
#         all_docs.append(doc)

#     # Approved cases
#     for case in approved_cases:
#         all_docs.append(case)

#     # PDFs
#     for doc in pdf_doc:
#         all_docs.append(
#             {
#                 "source": doc["source"],
#                 "text": doc["text"],
#                 "metadata": {
#                     "source": doc["source"],
#                     "source_type": "pdf",
#                     "language": "unknown",
#                     "category": "official_instruction",
#                 },
#             }
#         )

#     #if path is empty
#     if not all_docs:
#         print("No documents for indexing")
#         return

#     #create loacal database automatically load and save
#     client = chromadb.PersistentClient(path=CHROMA_PATH)

#     try:
#         client.delete_collection(COLLECTION_NAME)
#     except Exception:
#         pass
    
#     #create collection
#     collection = client.create_collection(name=COLLECTION_NAME)

#     #id of chunk
#     ids = []
#     #text from chunk
#     texts = []
#     #source
#     metadatas = []

#     #id counter
#     counter = 0

#     for doc in all_docs:
#         #get source from doc
#         source = doc["source"]
#         #divid text from doc into chunks
#         chunks = split_text(doc["text"])

#         for chunk in chunks:
#             counter += 1

#             #add chunks id
#             ids.append(f"chunk_{counter}")
#             #add chunk
#             texts.append(chunk)

#             chunk_metadata = doc.get("metadata", {}).copy()
#             chunk_metadata["source"] = source
#             #add source
#             metadatas.append(chunk_metadata)

#     print(f"Creating embeddings for {len(texts)} fragments...")
    

#     #embedding chunks
#     embeddings = get_embeddings(texts)

#     print("Example metadat: ", metadatas[0])

#     #add info in collection
#     collection.add(
#         #id of chunk
#         ids=ids,
#         #text
#         documents=texts,
#         #embedding values
#         embeddings=embeddings,
#         #source
#         metadatas=metadatas,
#     )

#     print(f"Ready! In Chroma was saved {len(texts)} fragments.")


#builds chroma indexes from approved cases, admin knowledge, and pdf chunks
#each index can be rebuilt independently or all at once
#used by build_index.py and admin knowledge management

from app.rag.approved_loader import load_approved_cases
from app.rag.admin_knowledge_loader import load_admin_knowledge
from app.rag.pdf_loader import load_pdfs
from app.rag.splitter import split_documents
from app.rag.embedding import embed_texts
from app.rag.chroma_client import reset_collection, get_or_create_collection
from app.rag.settings import COLLECTION_APPROVED, COLLECTION_ADMIN_KNOWLEDGE, COLLECTION_PDF


#adds a list of document dicts to a named chroma collection in batches
#returns count of documents added
#used by build_approved_index, build_admin_knowledge_index, build_pdf_index
def add_documents_to_collection(collection_name: str, documents: list[dict], reset: bool=True, batch_size: int = 64) -> int:

    #reset drops and recreates the collection, otherwise append to existing
    collection = reset_collection(collection_name) if reset else get_or_create_collection(collection_name)

    if not documents:
        return 0
    
    total = 0
    for start in range(0, len(documents), batch_size):
        batch = documents[start:start + batch_size]
        ids = [item["id"] for item in batch]
        texts = [item["text"] for item in batch]
        metadatas = [item.get("metadata", {}) for item in batch]
        embeddings = embed_texts(texts)
        collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
        total += len(batch)
    
    return total


#rebuilds the approved cases chroma collection from approved.csv, returns document count
def build_approved_index(reset: bool = True) -> int:
    count = add_documents_to_collection(COLLECTION_APPROVED, load_approved_cases(), reset=reset)
    print(f"Approved cases indexed: {count}")
    return count

#rebuilds the admin knowledge chroma collection from admin_knowledge.csv, returns document count
def build_admin_knowledge_index(reset: bool = True) -> int:
    count = add_documents_to_collection(COLLECTION_ADMIN_KNOWLEDGE, load_admin_knowledge(), reset=reset)
    print(f"Admin knowledge indexed: {count}")
    return count


#loads pdfs, splits into chunks, rebuilds the pdf chroma collection, returns chunk count
def build_pdf_index(reset: bool =True) -> int:
    pdf_chunks = split_documents(load_pdfs())
    count = add_documents_to_collection(COLLECTION_PDF, pdf_chunks, reset=reset)
    print(f"PDF chunks indexed: {count}")
    return count

#rebuilds all three indexes and returns a dict with counts per collection
#used in build_index.py as the main entry point
def build_all_indexes(reset: bool = True) -> dict:
    result = {
        "approved": build_approved_index(reset=reset),
        "admin_knowledge": build_admin_knowledge_index(reset=reset),
        "pdf": build_pdf_index(reset=reset),
    }
    print("Index build finished:", result)
    return result

if __name__ == "__main__":
    build_all_indexes(reset=True)
