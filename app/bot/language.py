# will detect language of user input

#import language detecter lib
from langdetect import detect, LangDetectException

def detect_language(text: str) -> str:
    #take user input and detect either its ru, en or uz, return one of these val
    #if it detect others return ru

    if not text or not text.strip():
        return "ru"
    
    try:
        detected = detect(text)

        if detected == "ru":
            return "ru"
        
        if detected == "en":
            return "en"
        
        if detected in ["uz", "tr", "id"]:
            return "uz"
        
        #if langdetect was wrong, but text in latin
        #we assume that it is uz or en
        latin_chars = sum(1 for char in text if char.isascii() and char.isalpha())
        cyrillic_chars = sum(1 for char in text if "а" <= char.lower() <= "я")

        if cyrillic_chars > latin_chars:
            return "ru"
        
        return "uz"
    
    except LangDetectException:
        return "ru" 




