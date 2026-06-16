#Get pdf -> Get its text -> Divid into chunks -> Make embending -> Save it in Chroma


#import our function load_pdf step 1,2
from app.rag.pdf_loader import load_pdfs
#import our function split text step 3
from app.rag.splitter import split_text
#import our function get_embeddings step 4
from app.rag.embedding import get_embeddings
#import vector database, step 5
import chromadb

from app.learning.approved_loader import load_approved_cases


#path to save data from embedding
CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "faktura_pdf_knowledge"


def build_index() -> None:

    print("Load PDF-files...")
    #load pdf files from data/pdf
    pdf_doc = load_pdfs("data/pdf")

    print(f"Founded PDF-files: {len(pdf_doc)}")

    print("Load Approved cases...")
    approved_cases = load_approved_cases()

    print(f"Founded approved cases: {len(approved_cases)}")

    all_docs = []

    #add pdf_docs
    for doc in pdf_doc:
        all_docs.append(
            {
                "source": doc["source"],
                "text": doc["text"],
                "metadata": {
                    "source": doc["source"],
                    "source_type": "pdf",
                    "language": "unknown",
                    "category": "official_instruction",
                },
            }
        )

    #add approved cases
    for case in approved_cases:
        all_docs.append(case)

    #if path is empty
    if not all_docs:
        print("No documents for indexing")
        return

    #create loacal database automatically load and save
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    
    #create collection
    collection = client.create_collection(name=COLLECTION_NAME)

    #id of chunk
    ids = []
    #text from chunk
    texts = []
    #source
    metadatas = []

    #id counter
    counter = 0

    for doc in all_docs:
        #get source from doc
        source = doc["source"]
        #divid text from doc into chunks
        chunks = split_text(doc["text"])

        for chunk in chunks:
            counter += 1

            #add chunks id
            ids.append(f"chunk_{counter}")
            #add chunk
            texts.append(chunk)

            if not isinstance(doc, dict):
                return doc
            

            chunk_metadata = doc.get("matadata", {}).copy()
            chunk_metadata["source"] = source
            #add source
            metadatas.append(chunk_metadata)

    print(f"Creating embeddings for {len(texts)} fragments...")
    

    #embedding chunks
    embeddings = get_embeddings(texts)

    print("Example metadat: ", metadatas[0])

    #add info in collection
    collection.add(
        #id of chunk
        ids=ids,
        #text
        documents=texts,
        #embedding values
        embeddings=embeddings,
        #source
        metadatas=metadatas,
    )

    print(f"Ready! In Chroma was saved {len(texts)} fragments.")