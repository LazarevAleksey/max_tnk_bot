from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types.attachments.buttons import CallbackButton
from config import CATEGORIES, CATEGORY_DEVICES, ITEMS_PER_PAGE


def _build_keyboard(buttons_rows):
    builder = InlineKeyboardBuilder()
    for row in buttons_rows:
        builder.row(*row)
    return builder.as_markup()


# ========== ГЛАВНОЕ МЕНЮ (10 КАТЕГОРИЙ) ==========
def get_main_menu():
    buttons_rows = []
    
    # Каждая категория на отдельной строке
    for text, callback in CATEGORIES.items():
        buttons_rows.append([CallbackButton(text=text, payload=f"cat:{callback}")])
    
    # Отдельные кнопки
    buttons_rows.append([
        CallbackButton(text="🔢 Поиск по номеру", payload="menu:SEARCH"),
        CallbackButton(text="🔍 Поиск по названию", payload="menu:TEXT_SEARCH")
    ])
    buttons_rows.append([
        CallbackButton(text="📅 История", payload="menu:HISTORY"),
        CallbackButton(text="❓ Помощь", payload="menu:HELP")
    ])
    
    return _build_keyboard(buttons_rows)


# ========== ПОДМЕНЮ: УСТРОЙСТВА В КАТЕГОРИИ ==========
def get_devices_menu(category_code: str):
    devices = CATEGORY_DEVICES.get(category_code, [])
    buttons_rows = []
    
    for device in devices:
        short_name = device[:40] + "..." if len(device) > 40 else device
        buttons_rows.append([CallbackButton(text=f"📟 {short_name}", payload=f"device:{device}")])
    
    buttons_rows.append([CallbackButton(text="🔙 Назад в главное меню", payload="menu:MAIN")])
    
    return _build_keyboard(buttons_rows)


# ========== МЕНЮ СО СПИСКОМ ДОКУМЕНТОВ (ТНК/КТП) ==========
def get_documents_menu(docs: list, device: str, page: int = 0, total: int = 0, has_more: bool = False):
    buttons_rows = []
    
    for doc in docs:
        doc_number = doc.get('file_name') or doc.get('number') or f"Документ #{doc['id']}"
        short_name = doc['name'][:37] + "..." if len(doc['name']) > 37 else doc['name']
        
        # Две кнопки в строке: [📄 краткое_название] [ℹ️]
        # buttons_rows.append([
        #     # CallbackButton(text=f"📄 {doc_number}", payload=f"doc:{doc['id']}"),
        #     CallbackButton(text=f"📄 {short_name}", payload=f"doc:{doc['id']}"),
        #     # CallbackButton(text="ℹ️", payload=f"doc_preview:{doc['id']}")
        # ])

        buttons_rows.append([CallbackButton(text=f"📄 {short_name}", payload=f"doc:{doc['id']}")])
        # buttons_rows.append([CallbackButton(text="ℹ️ Показать описание", payload=f"doc_preview:{doc['id']}")])   
    
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(CallbackButton(text="◀ Назад", payload=f"page:{device}:{page-1}"))
    if has_more:
        nav_buttons.append(CallbackButton(text="Вперед ▶", payload=f"page:{device}:{page+1}"))
    if nav_buttons:
        buttons_rows.append(nav_buttons)
    
    buttons_rows.append([CallbackButton(text="🔙 Назад к устройствам", payload="back_to_devices")])
    buttons_rows.append([CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")])
    
    return _build_keyboard(buttons_rows)


# ========== КАРТОЧКА ДОКУМЕНТА ==========
def get_document_card(doc: dict, is_favorite: bool = False):
    buttons_rows = []
    buttons_rows.append([CallbackButton(text="📎 Скачать файл", payload=f"download:{doc['id']}")])
    
    fav_text = "⭐ В избранное" if not is_favorite else "❌ Удалить из избранного"
    fav_action = "add" if not is_favorite else "remove"
    buttons_rows.append([CallbackButton(text=fav_text, payload=f"favorite:{fav_action}:{doc['id']}")])
    buttons_rows.append([CallbackButton(text="🔙 Назад к списку", payload="back_to_list")])
    buttons_rows.append([CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")])
    
    return _build_keyboard(buttons_rows)


# ========== ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ ==========
def get_back_keyboard():
    return _build_keyboard([[CallbackButton(text="🔙 Назад", payload="menu:MAIN")]])


# def get_search_number_keyboard():
#     buttons_rows = [
#         [CallbackButton(text="1", payload="search_number:digit:1"),
#          CallbackButton(text="2", payload="search_number:digit:2"),
#          CallbackButton(text="3", payload="search_number:digit:3")],
#         [CallbackButton(text="4", payload="search_number:digit:4"),
#          CallbackButton(text="5", payload="search_number:digit:5"),
#          CallbackButton(text="6", payload="search_number:digit:6")],
#         [CallbackButton(text="7", payload="search_number:digit:7"),
#          CallbackButton(text="8", payload="search_number:digit:8"),
#          CallbackButton(text="9", payload="search_number:digit:9")],
#         [CallbackButton(text="0", payload="search_number:digit:0"),
#          CallbackButton(text="⌫", payload="search_number:backspace"),
#          CallbackButton(text="🔍 Искать", payload="search_number:submit")],
#         [CallbackButton(text="🔙 Отмена", payload="menu:MAIN")]
#     ]
#     return _build_keyboard(buttons_rows)

def get_search_number_keyboard():
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
         CallbackButton(text="🗑️ Очистить", payload="search_number:clear")],  # ← новая кнопка
        [CallbackButton(text="🔍 Искать", payload="search_number:submit"),
         CallbackButton(text="🔙 Отмена", payload="menu:MAIN")]
    ]
    return _build_keyboard(buttons_rows)


def get_help_keyboard():
    return _build_keyboard([[CallbackButton(text="🏠 Главное меню", payload="menu:MAIN")]])