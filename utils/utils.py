import re
import os


def simplify_pdf_filename(file_path: str) -> str:
    """
    Преобразует имя PDF файла, оставляя только номер документа.
    
    Пример:
        'pdf/ТНК ЦП 0147-2022.pdf' -> 'pdf/0147.pdf'
        'pdf/КТП ЦП 1024-2019.pdf' -> 'pdf/1024.pdf'
        'pdf/ТНК_ЦП_0077-2017.pdf' -> 'pdf/0077.pdf'
    
    Args:
        file_path: Исходный путь к файлу
        
    Returns:
        Новый путь с упрощённым именем
    """
    # Разделяем путь и имя файла
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    # Ищем 4-значный номер в имени файла (с пробелами, дефисами или подчёркиваниями)
    # Паттерн ищет: любые символы, затем цифры (4 штуки), затем дефис или конец
    match = re.search(r'(\d{4})', filename)    
    if match:
        number = match.group(1)  # Берём первые 4 цифры
        new_filename = f"{number}.pdf"
    else:
        # Если номер не найден, возвращаем исходное имя
        new_filename = filename
    return os.path.join(directory, new_filename)


# Альтернативная версия - более точная для вашего формата
def simplify_pdf_filename_v2(file_path: str) -> str:
    """
    Более точная версия для формата "ТНК ЦП 0147-2022.pdf" или "КТП ЦП 1024-2019.pdf"
    """
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    # Ищем паттерн: пробел, 4 цифры, дефис, 4 цифры
    match = re.search(r'\s(\d{4})-\d{4}\.pdf$', filename)
    if match:
        number = match.group(1)
        new_filename = f"{number}.pdf"
    else:
        # Альтернативный паттерн для имён с подчёркиваниями: _0147-2017.pdf
        match = re.search(r'_(\d{4})-\d{4}\.pdf$', filename)
        if match:
            number = match.group(1)
            new_filename = f"{number}.pdf"
        else:
            new_filename = filename
    return os.path.join(directory, new_filename)


# Примеры использования
if __name__ == "__main__":
    # Пример 1: одиночное преобразование
    path1 = "pdf/ТНК ЦП 0147-2022.pdf"
    print(f"Было: {path1}")
    print(f"Стало: {simplify_pdf_filename_v2(path1)}")
    path2 = "pdf/КТП ЦП 1024-2019.pdf"
    print(f"\nБыло: {path2}")
    print(f"Стало: {simplify_pdf_filename_v2(path2)}")
    path3 = "pdf/ТНК_ЦП_0077-2017.pdf"
    print(f"\nБыло: {path3}")
    print(f"Стало: {simplify_pdf_filename_v2(path3)}")
    # Пример 2: показать что будет переименовано (dry run)
    # Пример 3: реальное переименование (раскомментировать когда будете готовы)
    # print("\n--- Реальное переименование ---")
    # rename_pdf_files_in_folder("pdf/", dry_run=False)
