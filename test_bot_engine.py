#test bot core engine

from app.core.bot_engine import process_user_question

EXIT_COMMANDS = ["exit", "quit", "выход"]

def main():
    print("Faktura Helpear Bot launched locally!")
    print("Write your question. To end programm write - exit/quit/выход")
    print("-"*50)

    while True:
        question = input("\nYour question: ").strip()

        if question.lower() in EXIT_COMMANDS:
            print("Bot was stopped")
            break
        
        if not question:
            print("Please, Write question") 
            continue   

        result = process_user_question(question)

        print("\nLanguage: ", result.get("language"))
        print("\nAnswer: ")
        print(result.get("answer"))

        print("\nSources: ")
        sources = result.get("sources", [])

        if sources:
            for source in sources:
                print(
                    "-",
                    source.get("source", "unknown"),
                    "| distance:",
                    source.get("distance"),
                    "| type:",
                    source.get("source_type"),
                )
        else:
            print("- sources not found")

        print("\nReview:")
        print("sent_to_review:", result.get("sent_to_review"))
        print("review_case_id:", result.get("review_case_id"))
        print("review_reason:", result.get("review_reason"))

        print("-" * 50)


if __name__ == "__main__":
    main()


