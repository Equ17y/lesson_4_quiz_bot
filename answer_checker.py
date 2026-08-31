import re


def extract_main_answer(text):
    """
    Извлекает основную часть ответа для мягкой проверки.
    """
    if not text:
        return ""
    
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    text = re.sub(r'\([^)]*\)', '', text)
    if '.' in text:
        text = text.split('.')[0]
    
    return ' '.join(text.lower().split())