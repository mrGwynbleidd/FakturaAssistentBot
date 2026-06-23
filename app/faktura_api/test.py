
from google import genai
import json

from app.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


from app.faktura_api.endpoints import get_sync

#get_sync("489043363" ,"4c1f1ff8ec9b4073abe92c68ba1ed7ca", "1", "0")


from app.faktura_api.client import api_get

# uid = "698989dddf36efe6674c4076"
# inn = "489043363"
# ct = 1
# mt = 0

#data = api_get(f"/Api/Patch/SyncRoamingDocument/{uid}?inn={inn}&contractorType={ct}&modelType={mt}")

#print(data)
print("\n")


print("="*50)
uid = input("Введите Rouming Id документа: ")
inn = input("Введите свой инн: ")
print("Тип Документа: ")
print("0 - Счет-фактура")
print("1 - Доверенность")
print("2 - Акт")
print("3 - Накладной")
print("4 - Акт сверки")
print("5 - Договор")
mt = input("Введите тип документа: ")

# for i in range(2):
#     ct = 0
#     result = get_sync(inn, uid, mt, ct)
#     ct +=1
#     print(result)

result = get_sync(inn, uid, mt, 1)

print(result)
    
json_string = json.dumps(result)

# Craft the instruction prompt
prompt = f"""
Преобразуйте следующие данные в формате JSON в профессиональную биографию в повествовательной форме, написанную в виде абзацев на естественном языке:

Возможный вид ответа:
Бери key с {json_string}

Расшифровка mt, используй эти названия вместо цифр
Тип Документа:
0 - Счет-фактура
1 - Доверенность
2 - Акт
3 - Накладной
4 - Акт сверки
5 - Договор

Документ {mt} с uid: (возьми с json-ответа под заголвком uniqueId)
Отправитель: (otpravitelInn) в состоянии (otpravitelStatus)
Получатель: (poluchatelInn) в состоянии (poluchatelStatus)
Статус документа (roamingStatus)

{json_string}
"""

# Generate the text response
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print(response.text)



# a = get_sync(inn, uid, mt, ct)

# print(a)



# json_string = json.dumps(a)

# prompt = f"""
# Конвертирую json ответ в читабельный текст в виде меленького текста с информацией

# {json_string}
# """

# response = client.models.generate_content(
#     model = "gemini-2.5-flash",
#     contents=prompt
# )

# print(response)


# #d = api_get(f"/Api/Patch/SyncRoamingDocument/{uid}?inn={inn}&contractorType=1&modelType=0")


# #print(d)