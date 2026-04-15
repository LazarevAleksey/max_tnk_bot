import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота MAX
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

# Пути
EXCEL_PATH = "data/documents.xlsx"
PDF_FOLDER = "pdf/"

# Настройки пагинации
ITEMS_PER_PAGE = 10

# Константы меню (эмодзи поддерживаются в MAX)
MAIN_MENU_BUTTONS = {
    # "Светофоры": "DEV_SVET",
    "🚦 Светофоры": "DEV_SVET",
    "🛤️ Стрелки ЭЦ": "DEV_STREL",
    "⚡ Рельсовые цепи": "DEV_RC",
    "🚧 Переезд (АПС)": "DEV_PEREZD",
    "🔋 Питание / АКБ": "DEV_PITANIE",
    "📁 Кабельная сеть": "DEV_KABEL",
    "🧠 МПЦ / ДЦ / ПО": "DEV_MPC",
    "⭐ Избранное": "DEV_IZBR"
}

ACTION_BUTTONS = {
    # "Проверка": "ACTION_PROV",
    "✅ Проверка": "ACTION_PROV",
    "🔧 Регулировка": "ACTION_REG",
    "🔄 Замена": "ACTION_ZAMENA",
    "📏 Измерение": "ACTION_IZMER",
    "🧼 Очистка/Смазка": "ACTION_CHIST"
}

