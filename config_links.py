# config_links.py
"""Конфигурационный файл для хранения всех ссылок и URL бота"""

# ========== ССЫЛКИ ДЛЯ КНОПОК ==========

# Ссылки для главного меню
GUIDE_LINKS = {
    "google_drive": "https://drive.google.com/drive/folders/1-q2cKPTeoPFATwFS1372B2x-ME3zlwOm",
    "yandex_disk": "https://disk.yandex.ru/d/wFEd1GHt9NiCOg"
}

REFERENCE_LINKS = {
    "spravochnik": "https://drive.google.com/drive/folders/1pwrniORd4uj2Br-QPWFClhcuHNz9mTGz",
    "instructions": "https://drive.google.com/drive/folders/1IfL-7X5ICDDSDQYhdPlXty6V0EmEKVpS"
}

# Если нужно больше двух ссылок в строке
GUIDE_URLS = [
    "https://drive.google.com/drive/folders/1-q2cKPTeoPFATwFS1372B2x-ME3zlwOm",
    "https://disk.yandex.ru/d/wFEd1GHt9NiCOg"
]

REFERENCE_URLS = [
    "https://drive.google.com/drive/folders/1pwrniORd4uj2Br-QPWFClhcuHNz9mTGz",
    "https://drive.google.com/drive/folders/1IfL-7X5ICDDSDQYhdPlXty6V0EmEKVpS"
]

# ========== КОНФИГУРАЦИЯ ФАЙЛОВ ==========

# Файлы для отправки (пути и текст сообщения)
FILES_CONFIG = {
    "opis.pdf": {
        "message_text": "opis_4_gorka",
        "description": "Описание горки"
    },
    "tera.pdf": {
        "message_text": "Инструкция TERA",
        "description": "Инструкция по работе с TERA"
    },
    # Добавляйте новые файлы сюда
    # "new_file.pdf": {
    #     "message_text": "Текст сообщения",
    #     "description": "Описание"
    # }
}

# ========== НАСТРОЙКИ БОТА ==========

# ID пользователей (можно вынести сюда)
ADMIN_USER_IDS = [
    "232299786",  # Основной администратор
    # "123456789",  # Дополнительные администраторы
]

# Токен бота (лучше хранить в .env, но для примера оставлю здесь)
# BOT_TOKEN = "f9LHodD0cOLPGaxUVnHXUh9LJ3SqubxZrPWh-Tt2HwRrcRUbBJ-WaTeFYpkjBq0CJJL6n2BHOb4TkRIgXnR5"    # Первый бот
BOT_TOKEN = "f9LHodD0cOLJMc6-7amUwp-y_WUTH-j58Ks5JcJlOycF4og9z7DbwhMoB_pBZeWrbqY_b_dSJDEQypHe8kSH"

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_guide_buttons():
    """Возвращает список ссылок для кнопки 'Руководство'"""
    return GUIDE_URLS

def get_reference_buttons():
    """Возвращает список ссылок для кнопки 'Справочник/Инструкции'"""
    return REFERENCE_URLS

def get_file_info(filename):
    """Возвращает информацию о файле по его имени"""
    return FILES_CONFIG.get(filename)

def get_all_files():
    """Возвращает список всех доступных файлов"""
    return list(FILES_CONFIG.keys())