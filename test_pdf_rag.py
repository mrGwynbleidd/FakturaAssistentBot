from app.rag.retriever import retrieve_context
from app.rag.generator import generate_answer
from app.logs.csv_logger import save_qa

# question = "Как зарегистрироваться?"
# print(f"\n\n---{question} ---")
# context, sources = retrieve_context(question)

# print("Founded sources: ")
# for source in sources:
#     print("-", source["source"])

# print("Answer: ")

# answer = generate_answer(question=question, context=context, language='ru')

# print(answer)

# save_qa(
#     question=question,
#     answer=answer,
#     language='ru',
#     sources=sources,
# )


# question2 = "Xodimni qanday qo'shish kerak"
# print(f"\n\n---{question2} ---")

# context2, sources2 = retrieve_context(question2)

# answer2 = generate_answer(question=question2, context=context2, language='uz')
# print(answer2)

# save_qa(
#     question=question2,
#     answer=answer2,
#     language='uz',
#     sources=sources2,
# )

# question3 = "How to set up access rights?"
# print(f"\n\n---{question3} ---")
# context3, sources3 = retrieve_context(question3)
# answer3 = generate_answer(question=question3, context=context3, language='en')

# print(answer3)

# save_qa(
#     question=question3,
#     answer=answer3,
#     language='en',
#     sources=sources3,
# )


# question4 = "Когда будет работать офис?"
# print(f"\n\n---{question4} ---")
# context4, sources4 = retrieve_context(question4)
# answer4 = generate_answer(question=question4, context=context4, language='ru')

# print(answer4)

# save_qa(
#     question=question4,
#     answer=answer4,
#     language='ru',
#     sources=sources4,
# )

# question4 = "Здравствуйте! Пытаюсь отправить Счет-фактор с лотом, пишет что лот не найден"
# print(f"\n\n---{question4} ---")
# context4, sources4 = retrieve_context(question4)
# answer4 = generate_answer(question=question4, context=context4, language='ru')

# print(answer4)

# save_qa(
#     question=question4,
#     answer=answer4,
#     language='ru',
#     sources=sources4,
# )


question2 = "Фактурадан аккаунтга кириб булмаяпти"
print(f"\n\n---{question2} ---")

context2, sources2 = retrieve_context(question2)

answer2 = generate_answer(question=question2, context=context2, language='uz')
print(answer2)

save_qa(
    question=question2,
    answer=answer2,
    language='uz',
    sources=sources2,
)
