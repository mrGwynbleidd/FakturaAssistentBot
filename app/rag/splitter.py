#Split huge text into chunks with size 1000 symbols

def split_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:

    #crate chunks
    chunks = []
    #start point
    start = 0

    #while we do not achieve end of text
    while start< len(text):
        #take text from start point till size of chunk(1000)
        end = start + chunk_size
        #insert these val
        chunk = text[start:end]

        #if chunk not empty
        if chunk.strip():
            #add these chunk to arr
            chunks.append(chunk.strip())

        #replace start point. overlap needed to understand order of chunks
        start += chunk_size - overlap

    #return arr of chunks
    return chunks        