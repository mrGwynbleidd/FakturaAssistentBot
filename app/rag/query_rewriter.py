#Extend user question with keywoards, Chroma easy to find answer

def rewrite_query(question: str) -> str:

    #load question
    q = question.lower()

    #keywords

    login_keywords = [
        "не могу войти",
        "не входит",
        "вход",
        "логин",
        "аккаунт",
        "пароль",
        "забыл пароль",
        "сброс пароля",
        "восстановить пароль",
        "авторизация",
        "кабинет",
        "не получается зайти",
    ]

    #add extra text in input
    if any(keyword in q for keyword in login_keywords):
        return (
            question
            + " регистрация вход авторизация аккаунт пароль подтверждение код "
              "телефон электронная почта ЭЦП сертификат e-imzo сотрудник приглашение"
        )

    
    employee_keywords = [
        "сотрудник",
        "пригласить сотрудника",
        "добавить сотрудника",
        "роль",
        "права доступа",
    ]

    if any(keyword in q for keyword in employee_keywords):
        return (
            question
            + " сотрудники добавить сотрудника пригласить роль права доступа пароль учетная запись"
        )

    return question