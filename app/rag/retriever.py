# Find info from Chroma 
# get question -> upgrade it by query_rewriter -> 
# embending question -> find similar chunks in Chroma -> 
# return context and source

import chromadb
from app.rag.query_rewriter import rewrite_query
from app.rag.embedding import get_embedding

#path to db
CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "faktura_pdf_knowledge"

#find most simillar fragments from pdf-base
def retrieve_context(question: str, n_results: int = 5) -> tuple[str, list[dict]]:

    #create loacal client
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    #check if collection exist
    existing_collection = [collection.name for collection in client.list_collections()]

    if COLLECTION_NAME not in existing_collection:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' not found!"
            f"Firstly launch: python build_index.py"
        )


    #get collection
    collection = client.get_collection(name=COLLECTION_NAME)

    

    #extend question
    search_query = rewrite_query(question)

    print("Original question: ", question)
    print("Search query: ", search_query)

    #embedding user question
    question_embedding = get_embedding(search_query)
    
    
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return "", []

    context_parts = []
    sources = []

    for i, doc_text in enumerate(documents):
        #safely get metadatas
        if i < len(metadatas) and metadatas[i]:
            metadata = metadatas[i]
        else:
            metadata = {}

        if i<len(distances):
            distance = distances[i]
        else:
            distance = None        


        source = metadata.get("source", "unknown")
        source_type = metadata.get("source_type", "unknown")
        category = metadata.get("category", "unknown")

        context_parts.append(
            f"""
SOURCE {i + 1}
FILE: {source}
TYPE: {source_type}
CATEGOTY:  {category}
DISTANCE: {distance}

TEXT:
{doc_text}
"""
        )

        sources.append(
            {
                "source": source,
                "source_type": source_type,
                "category": category,
                "distance": distance
            }
        )

    context = "\n\n".join(context_parts)

    return context, sources