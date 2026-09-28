import asyncio
import re
from typing import AsyncGenerator
from src.ai import GoogleGenerativeAI
from logger import logger
SYSTEM_PROMPT = 'Вы — профессиональный редактор текстов для дикторов и систем озвучивания (Text-to-Speech).\nВаша задача — переписать предоставленную информацию о медиафайле (сюжет, факты, вердикты) в устную речь (спич-формат).\n\n### Ключевые правила адаптации:\n1. Исключите все списки и нумерации:\n   - ЗАПРЕЩЕНО писать: "1. ... 2. ...", "Во-первых... Во-вторых...", "• ...".\n   - ЗАПРЕЩЕНО использовать слова "один", "два", "три", "четыре", "первый", "второй", "третий" в качестве перечислений или маркеров пунктов. Вместо этого используйте плавные связки вроде: "Также стоит отметить...", "Кроме того...", "Помимо этого...", "Ещё...", "В то же время...".\n2. Избавьтесь от "бумажного" синтаксиса:\n   - Дробите длинные предложения. Одно предложение должно содержать не более 12-15 слов.\n   - Избегайте причастных и деепричастных оборотов. Заменяйте их на активные глаголы и простые предложения.\n   - Опускайте или раскрывайте скобки. Текст в скобках должен стать частью повествования или удаляться.\n3. Озвучка числительных и аббревиатур:\n   - Все числа пишите словами (например, вместо "в 1982 году" пишите "в тысяча девятьсот восемьдесят втором году").\n   - Избегайте сложных аббревиатур, заменяйте их на полные названия или пишите их транскрипцию (например, "США" -> "Соединенные Штаты").\n4. Женский род для диктора:\n   - Голос озвучивания — женский. Все глаголы, причастия и местоимения первого лица, относящиеся к диктору, должны быть строго в женском роде (например: «я подготовила», «я нашла», «я выбрала»).\n\n### Правила форматирования ответа:\n- Разделяйте текст на небольшие логические части (блоки по 1–3 предложения).\n- Каждый блок пишите с новой строки и ОБЯЗАТЕЛЬНО разделяйте их специальным маркером `[NEXT_CHUNK]`.\n'

async def generate_voiceover_chunks(raw_text: str, api_key: str='', api_key_names: list=()) -> AsyncGenerator[str, None]:
    """
    Принимает сырой текст, sends его в Gemini с системным промптом
    и по мере готовности стримит чанки, разделенные [NEXT_CHUNK].
    """
    model = GoogleGenerativeAI(api_key=api_key, api_key_names=api_key_names, system_instruction=SYSTEM_PROMPT, save_history_chat=False)
    prompt = f'Адаптируй следующий текст для диктора:\n\n{raw_text}'
    try:
        client = model._client
        model_name = model.model_name
        from google.genai import types
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        response_stream = client.models.generate_content_stream(model=model_name, contents=prompt, config=config)
        buffer = ''
        for chunk in response_stream:
            if chunk.text:
                buffer += chunk.text
                while '[NEXT_CHUNK]' in buffer:
                    parts = buffer.split('[NEXT_CHUNK]', 1)
                    clean_chunk = parts[0].strip()
                    buffer = parts[1]
                    if clean_chunk:
                        clean_chunk = re.sub('\\s+', ' ', clean_chunk)
                        yield clean_chunk
                        await asyncio.sleep(0.05)
        remaining = buffer.strip()
        if remaining:
            remaining = re.sub('\\s+', ' ', remaining)
            yield remaining
    except Exception as e:
        logger.error(f'Error during streaming voiceover generation: {e}')
        sentences = re.split('(?<=[.!?])\\s+', raw_text)
        for s in sentences:
            if s.strip():
                yield s.strip()