# -*- coding: utf-8 -*-
import asyncio
import re
from typing import AsyncGenerator
from core.ai import GoogleGenerativeAI
from core.logger import logger

SYSTEM_PROMPT = """Вы — профессиональный редактор текстов для дикторов и систем озвучивания (Text-to-Speech).
Ваша задача — переписать предоставленную информацию о медиафайле (сюжет, факты, вердикты) в устную речь (спич-формат).

### Ключевые правила адаптации:
1. Исключите все списки и нумерации:
   - ЗАПРЕЩЕНО писать: "1. ... 2. ...", "Во-первых... Во-вторых...", "• ...".
   - ЗАПРЕЩЕНО использовать слова "один", "два", "три", "четыре", "первый", "второй", "третий" в качестве перечислений или маркеров пунктов. Вместо этого используйте плавные связки вроде: "Также стоит отметить...", "Кроме того...", "Помимо этого...", "Ещё...", "В то же время...".
2. Избавьтесь от "бумажного" синтаксиса:
   - Дробите длинные предложения. Одно предложение должно содержать не более 12-15 слов.
   - Избегайте причастных и деепричастных оборотов. Заменяйте их на активные глаголы и простые предложения.
   - Опускайте или раскрывайте скобки. Текст в скобках должен стать частью повествования или удаляться.
3. Озвучка числительных и аббревиатур:
   - Все числа пишите словами (например, вместо "в 1982 году" пишите "в тысяча девятьсот восемьдесят втором году").
   - Избегайте сложных аббревиатур, заменяйте их на полные названия или пишите их транскрипцию (например, "США" -> "Соединенные Штаты").
4. Женский род для диктора:
   - Голос озвучивания — женский. Все глаголы, причастия и местоимения первого лица, относящиеся к диктору, должны быть строго в женском роде (например: «я подготовила», «я нашла», «я выбрала»).

### Правила форматирования ответа:
- Разделяйте текст на небольшие логические части (блоки по 1–3 предложения).
- Каждый блок пишите с новой строки и ОБЯЗАТЕЛЬНО разделяйте их специальным маркером `[NEXT_CHUNK]`.
"""

async def generate_voiceover_chunks(raw_text: str, api_key: str = "", api_key_names: list = ()) -> AsyncGenerator[str, None]:
    """
    Принимает сырой текст, отправляет его в Gemini с системным промптом
    и по мере готовности стримит чанки, разделенные [NEXT_CHUNK].
    """
    model = GoogleGenerativeAI(
        api_key=api_key,
        api_key_names=api_key_names,
        system_instruction=SYSTEM_PROMPT,
        save_history_chat=False
    )
    
    prompt = f"Адаптируй следующий текст для диктора:\n\n{raw_text}"
    
    try:
        # Поскольку GoogleGenerativeAI в проекте использует genai.Client из нового SDK (google-genai),
        # мы можем получить стриминг через его клиента.
        client = model._client
        # Используем модель по умолчанию или 'gemini-2.5-flash' / 'gemini-2.0-flash-exp'
        model_name = model.model_name
        
        # Запускаем потоковую генерацию
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
        response_stream = client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        buffer = ""
        for chunk in response_stream:
            if chunk.text:
                buffer += chunk.text
                
                # Обрабатываем накопившийся буфер
                while "[NEXT_CHUNK]" in buffer:
                    parts = buffer.split("[NEXT_CHUNK]", 1)
                    clean_chunk = parts[0].strip()
                    buffer = parts[1]
                    if clean_chunk:
                        # Убираем возможные артефакты разметки вроде лишних переносов строк
                        clean_chunk = re.sub(r'\s+', ' ', clean_chunk)
                        yield clean_chunk
                        # Небольшая пауза для стабилизации потока
                        await asyncio.sleep(0.05)
                        
        # Выдаем остаток, если он есть
        remaining = buffer.strip()
        if remaining:
            remaining = re.sub(r'\s+', ' ', remaining)
            yield remaining
            
    except Exception as e:
        logger.error(f"Error during streaming voiceover generation: {e}")
        # Фолбек на обычный генератор предложений, если API стриминга упал
        sentences = re.split(r'(?<=[.!?])\s+', raw_text)
        for s in sentences:
            if s.strip():
                yield s.strip()
