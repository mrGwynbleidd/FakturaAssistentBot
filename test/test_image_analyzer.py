import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.image_analyzer import analyze_sceenshot

def test_image(image_path: str, language: str = "ru"):
    print(f"\n{'='*50}")
    print(f"File: {image_path}")
    print(f"Language: {language}")
    print('-'*50)

    image_bytes = Path(image_path).read_bytes()
    result = analyze_sceenshot(image_bytes, language=language)

    print(f"\n📋 Извлечённый текст:\n  {result.get('extracted_text', '—')}")
    print(f"\n🔍 Поисковый запрос:\n  {result.get('search_query', '—')}")
    print(f"\n🖼 Описание:\n  {result.get('description', '—')}")

    if result.get("error"):
        print(f"\n❌ Ошибка: {result['error']}")
    else:
        print(f"\n✅ Успешно!")

    return result


if __name__ == "__main__":
    if len(sys.argv) <2:
        print("Использование: python tests/test_image_analyzer.py <путь_к_изображению> [язык]")
        print("Пример: python tests/test_image_analyzer.py screenshot.png ru")
        sys.exit(1)

    image_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "ru"

    test_image(image_path, language)