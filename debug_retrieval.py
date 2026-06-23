
import sys

from app.rag.priority_retriever import retrieve_priority_context

def main() -> None:
    if len(sys.argv) <2:
        print('Usage: python debug_retrieval.py "your question"')
        return
    
    question = " ".join(sys.argv[1:])
    result = retrieve_priority_context(question=question, language="ru")
    print("MODE:", result.get("mode"))
    print("ANSWER:", result.get("answer", ""))
    print("SOURCES:")
    for source in result.get("sources", []):
        print(source)
    
    print("CONTEXT")
    print(result.get("context_text", ""))


if __name__ == "__main__":
    main()