# utils.py (дополнить)
import re
import os
import asyncio
from config import PREVIEW_MAX_LENGTH


# ========== РАБОТА С ФАЙЛАМИ (уже есть) ==========
def simplify_pdf_filename(file_path: str) -> str:
    """Преобразует имя PDF файла, оставляя только номер документа"""
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    match = re.search(r'(\d{4})', filename)
    if match:
        number = match.group(1)
        new_filename = f"{number}.pdf"
    else:
        new_filename = filename
    return os.path.join(directory, new_filename)


def simplify_pdf_filename_v2(file_path: str) -> str:
    """Более точная версия для формата 'ТНК ЦП 0147-2022.pdf'"""
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    match = re.search(r'\s(\d{4})-\d{4}\.pdf$', filename)
    if match:
        number = match.group(1)
        new_filename = f"{number}.pdf"
    else:
        match = re.search(r'_(\d{4})-\d{4}\.pdf$', filename)
        if match:
            number = match.group(1)
            new_filename = f"{number}.pdf"
        else:
            new_filename = filename
    return os.path.join(directory, new_filename)


# ========== НОВЫЕ УТИЛИТЫ ==========

def convert_filename_to_pdf(file_name: str) -> str:
    """
    Преобразует имя файла из 'ТНК ЦШ 0147-2022' в '0147.pdf'
    Используется в handlers.py
    """
    match = re.search(r'\b(\d{4})\b', file_name)
    if match:
        return f"{match.group(1)}.pdf"
    match = re.search(r'\b(\d{3})\b', file_name)
    if match:
        return f"{match.group(1)}.pdf"
    return file_name


def clean_value(value: str) -> str:
    """Удаляет эмодзи и лишние пробелы (используется в data_loader.py)"""
    if not value:
        return value
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', value).strip()


def split_long_text(text: str) -> list:
    """Разбивает длинный текст на части для всплывающих сообщений"""
    if len(text) <= PREVIEW_MAX_LENGTH:
        return [text]
    
    parts = []
    remaining = text
    while remaining:
        if len(remaining) <= PREVIEW_MAX_LENGTH:
            parts.append(remaining)
            break
        split_pos = remaining.rfind(' ', 0, PREVIEW_MAX_LENGTH)
        if split_pos == -1:
            split_pos = PREVIEW_MAX_LENGTH
        parts.append(remaining[:split_pos])
        remaining = remaining[split_pos:].lstrip()
    return parts