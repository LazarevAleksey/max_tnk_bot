# Правильные импорты из документации MAX API
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types.attachments.buttons import CallbackButton, LinkButton
# Константы меню остаются без изменений
from config import MAIN_MENU_BUTTONS, ACTION_BUTTONS, ITEMS_PER_PAGE

# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ (чтобы не дублировать код)
def _build_keyboard(buttons_rows):
    """Принимает список строк кнопок и возвращает готовую разметку."""
    builder = InlineKeyboardBuilder()
    for row in buttons_rows:
        builder.row(*row)
    return builder.as_markup() # .as_markup() создаёт объект для вставки в attachments

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu():
    buttons_rows = []
    # Кнопки устройств (по 2 в ряд для удобства)
    device_buttons = list(MAIN_MENU_BUTTONS.items())
    for i in range(0, len(device_buttons), 2):
        row = []
        for text, callback in device_buttons[i:i+2]:
            row.append(CallbackButton(text=text, payload=f"menu:{callback}"))
        buttons_rows.append(row)
    
    # Отдельные кнопки поиска, истории
    buttons_rows.append([CallbackButton(text="🔢 Поиск по номеру", payload="menu:SEARCH"),
                         CallbackButton(text="🔍 Поиск по названию", payload="menu:TEXT_SEARCH")])
    buttons_rows.append([CallbackButton(text="📅 История", payload="menu:HISTORY"),
                         CallbackButton(text="❓ Помощь", payload="menu:HELP")])
    
    return _build_keyboard(buttons_rows)

# --- МЕНЮ ВИДОВ РАБОТ ---
def get_actions_menu(device: str):
    # print('+++get_actions_menu+++')
    buttons_rows = []
    for text, callback in ACTION_BUTTONS.items():
        # print(f'device: {device}')
        # print(f'text: {text}')
        # print(f'callback: {callback}')
        buttons_rows.append([CallbackButton(text=text, payload=f"action:{device}:{callback}")])
    buttons_rows.append([CallbackButton(text="🔙 Назад", payload="menu:BACK_TO_MAIN")])
    return _build_keyboard(buttons_rows)

# --- МЕНЮ СО СПИСКОМ ДОКУМЕНТОВ ---
def get_documents_menu(docs: list, device: str, action_code: str, page: int = 0, total: int = 0, has_more: bool = False):
    buttons_rows = []
    for doc in docs:
        short_name = doc['name'][:35] + "..." if len(doc['name']) > 35 else doc['name']
        doc_number = doc.get('file_name') or doc.get('number') or f"Документ #{doc['id']}"
        text = f"📄 {doc_number} - {short_name}"    
        # short_name = doc['name'][:35] + "..." if len(doc['name']) > 35 else doc['name']
        # text = f"📄 {doc['number']} - {short_name}"
        buttons_rows.append([CallbackButton(text=text, payload=f"doc:{doc['id']}")])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(CallbackButton(text="◀ Назад", payload=f"page:{device}:{action_code}:{page-1}"))
    if has_more:
        nav_buttons.append(CallbackButton(text="Вперед ▶", payload=f"page:{device}:{action_code}:{page+1}"))
    if nav_buttons:
        buttons_rows.append(nav_buttons)
    
    buttons_rows.append([CallbackButton(text="🔙 Назад к видам работ", payload=f"back_to_actions:{device}")])
    buttons_rows.append([CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")])
    return _build_keyboard(buttons_rows)

# --- КАРТОЧКА ДОКУМЕНТА ---
def get_document_card(doc: dict, is_favorite: bool = False):
    buttons_rows = []
    buttons_rows.append([CallbackButton(text="📎 Скачать файл", payload=f"download:{doc['id']}")])
    
    fav_text = "⭐ В избранное" if not is_favorite else "❌ Удалить из избранного"
    fav_action = "add" if not is_favorite else "remove"
    buttons_rows.append([CallbackButton(text=fav_text, payload=f"favorite:{fav_action}:{doc['id']}")])
    buttons_rows.append([CallbackButton(text="🔙 Назад к списку", payload="back_to_list")])
    buttons_rows.append([CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")])
    return _build_keyboard(buttons_rows)

# --- КНОПКА "НАЗАД" ---
def get_back_keyboard():
    return _build_keyboard([[CallbackButton(text="🔙 Назад", payload="menu:BACK_TO_MAIN")]])

# --- КЛАВИАТУРА ДЛЯ ПОИСКА ПО НОМЕРУ ---
def get_search_number_keyboard(current_number: str = ""):
    buttons_rows = [
        [CallbackButton(text="1", payload="search_number:digit:1"),
         CallbackButton(text="2", payload="search_number:digit:2"),
         CallbackButton(text="3", payload="search_number:digit:3")],
        [CallbackButton(text="4", payload="search_number:digit:4"),
         CallbackButton(text="5", payload="search_number:digit:5"),
         CallbackButton(text="6", payload="search_number:digit:6")],
        [CallbackButton(text="7", payload="search_number:digit:7"),
         CallbackButton(text="8", payload="search_number:digit:8"),
         CallbackButton(text="9", payload="search_number:digit:9")],
        [CallbackButton(text="0", payload="search_number:digit:0"),
         CallbackButton(text="⌫", payload="search_number:backspace"),
         CallbackButton(text="🔍 Искать", payload="search_number:submit")],
        [CallbackButton(text="🔙 Отмена", payload="menu:MAIN")]
    ]
    return _build_keyboard(buttons_rows)

# --- КЛАВИАТУРА ПОМОЩИ ---
def get_help_keyboard():
    return _build_keyboard([[CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")]])


# Главное меню
builder_start = InlineKeyboardBuilder()

# Кнопки ТНК
builder_start.row(
    CallbackButton(text="ТНК СЦБ", payload="scb"),
    CallbackButton(text="ТНК ГАЦ", payload="gac")
)