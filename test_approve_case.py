#import function
from app.learning.review_manager import approve_case_manually

#for now admin answer written manually
approve_case_manually(
    #case id
    case_id="manual_login_001",
    #user question
    question="При входе в аккаунт нету ЭЦП",
    #admin answer
    approved_answer=(
        "‼️ С выходом версии Chrome 147 компания Google ужесточила правила защиты личных данных. Это коснулось работы программы E-IMZO."

"""Теперь Chrome считает любое обращение сайта к вашему компьютеру потенциально опасным. Теперь браузер обязан спросить ваше разрешение.

При попытке подключение к E-IMZO Chrome покажет окно с вопросом: «Предоставить доступ к устройствам в вашей локальной сети?» 

Нажмите «Разрешить» (Allow).

Но не во всех сайтах это сработает.
У сайта может не быть такой «репутации» в базе Chrome и он потребует подтверждения на каждое новое соединение, даже если вы нажали «Allow».

Если сайт хотя бы на одном этапе использует незащищенное соединение, Chrome молча блокирует WebSocket, игнорируя ваше нажатие на кнопку «Allow». 

🆘 Как решение в адресной строке: chrome://flags/#local-network-access-check = Disabled

Это ограничение введено компанией Google для всех браузеров на движке Chrome. Оно не является ошибкой программы E-IMZO, а является стандартным этапом проверки безопасности в 2026 году."
 """       "Если доступ восстановить не удалось, обратитесь в поддержку Faktura.uz. 📞 **+998 71 200 00 13**"
    ),
    #language
    language= "ru",
    #type of problem, for now manually
    category="login_problem"
)


# approve_case_manually(
#     case_id="manual_login_002",
#     question=""
# )

print("Approved case added successfully!")

