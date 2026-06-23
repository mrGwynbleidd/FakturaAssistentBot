#Split huge text into chunks with size 1000 symbols

from app.rag.settings import PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP
from app.rag.text_utils import clean_text, make_id

def split_text(text: str, chunk_size: int = PDF_CHUNK_SIZE, overlap: int = PDF_CHUNK_OVERLAP) -> list[str]:

    text = clean_text(text)
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return[text]
    
    chunks: list[str] = []

    #start point
    start = 0

    #while we do not achieve end of text
    while start< len(text):
        #take text from start point till size of chunk(1000)
        end = start + chunk_size
        #insert these val
        chunk = text[start:end].strip()

        #if chunk not empty
        if chunk:
            #add these chunk to arr
            chunks.append(chunk.strip())

        if end >= len(text):
            break

        #replace start point. overlap needed to understand order of chunks
        start = max(end - overlap, start +1)

    #return arr of chunks
    return chunks        


def split_documents(documents: list[dict]) -> list[dict]:
    result: list[dict] = []
    for document in documents:
        chunks = split_text(document["text"])
        for index, chunk in enumerate(chunks):
            metadata = dict(document.get("metadata", {}))
            metadata["chunk_index"] = index
            chunk_id = make_id("pdf_chunk", f"{document.get('id', '')}_{index}_{chunk[:100]}")
            result.append({"id": chunk_id, "text": chunk,"metadata": metadata})

    return result  # вне цикла — обрабатываем все документы