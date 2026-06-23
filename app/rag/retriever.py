# # Find info from Chroma 
# # get question -> upgrade it by query_rewriter -> 
# # embending question -> find similar chunks in Chroma -> 
# # return context and source

# import chromadb
# from app.rag.query_rewriter import rewrite_query
# from app.rag.embedding import get_embedding

# #path to db
# CHROMA_PATH = "data/chroma_db"
# COLLECTION_NAME = "faktura_pdf_knowledge"

# #find most simillar fragments from pdf-base
# def retrieve_context(question: str, n_results: int = 5) -> tuple[str, list[dict]]:

#     #create loacal client
#     client = chromadb.PersistentClient(path=CHROMA_PATH)

#     #check if collection exist
#     existing_collection = [collection.name for collection in client.list_collections()]

#     if COLLECTION_NAME not in existing_collection:
#         raise RuntimeError(
#             f"Collection '{COLLECTION_NAME}' not found!"
#             f"Firstly launch: python build_index.py"
#         )


#     #get collection
#     collection = client.get_collection(name=COLLECTION_NAME)

    

#     #extend question
#     search_query = rewrite_query(question)

#     import logging
#     logging.getLogger("bot").info(f"🔍 Поиск: {search_query[:60]}")

#     #embedding user question
#     question_embedding = get_embedding(search_query)
    
    
#     results = collection.query(
#         query_embeddings=[question_embedding],
#         n_results=n_results,
#         include=["documents", "metadatas", "distances"],
#     )

#     documents = results.get("documents", [[]])[0]
#     metadatas = results.get("metadatas", [[]])[0]
#     distances = results.get("distances", [[]])[0]

#     if not documents:
#         return "", []

#     # ── Priority: admin_knowledge=0 > approved cases=1 > pdf=2 ───────────────
#     _APPROVED_TYPES = {"admin_review", "call_center", "group_chat", "group_admin_reply"}

#     def source_priority(source_type: str) -> int:
#         if source_type == "admin_knowledge":
#             return 0
#         if source_type in _APPROVED_TYPES:
#             return 1
#         return 2  # pdf / unknown

#     # Zip into tuples and sort
#     rows = []
#     for i, doc_text in enumerate(documents):
#         meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
#         dist = distances[i] if i < len(distances) else None
#         rows.append((doc_text, meta, dist))

#     rows.sort(key=lambda r: (source_priority(r[1].get("source_type", "")), r[2] or 9999))

#     context_parts = []
#     sources = []

#     for i, (doc_text, metadata, distance) in enumerate(rows):
#         source = metadata.get("source", "unknown")
#         source_type = metadata.get("source_type", "unknown")
#         category = metadata.get("category", "unknown")

#         context_parts.append(
#             f"SOURCE {i + 1}\n"
#             f"FILE: {source}\n"
#             f"TYPE: {source_type}\n"
#             f"CATEGORY: {category}\n"
#             f"DISTANCE: {distance}\n\n"
#             f"TEXT:\n{doc_text}"
#         )

#         sources.append({
#             "source": source,
#             "source_type": source_type,
#             "category": category,
#             "distance": distance,
#         })

#     context = "\n\n".join(context_parts)
#     return context, sources







from app.rag.priority_retriever import (
    retrieve_priority_context,
    retrieve_context,
    search_relevant_documents,
    search_approved_cases,
    search_admin_knowledge,
    search_pdf,
)

def retrieve(query: str, language: str = "ru") -> dict:
    return retrieve_priority_context(question=query, language=language)

def get_repevant_context(query: str, language: str = "ru") -> str:
    return retrieve_context(question=query, language=language)

def retrieve_relevant_chunks(query: str, top_k: int = 5, language: str = "ru") -> list[dict]:
    return search_relevant_documents(question=query, language=language)[:top_k]