# handlers/navigation.py
import logging
from maxapi.types.attachments.buttons import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from models.session import get_session
from keyboards import get_start_menu  # ← добавить импорт
from maxapi.types import BotStarted, Command, MessageCreated
# from keyboards import get_back_keyboard

logger = logging.getLogger(__name__)


async def bot_started(event: BotStarted):
    await event.bot.send_message(  # type: ignore
        chat_id=event.chat_id,
        text="👋 *Добро пожаловать в СЦБ-ДОК!*\n\n"
             "Бот для поиска технической документации:\n\n"
             "📄 *ТНК/КТП* — инструкции ОАО «РЖД» №3168р\n"
             "📚 *Документация* — справочники, руководства, инструкции\n\n"
             "Выберите нужный раздел:",
        attachments=[get_start_menu()]
    )


async def cmd_start(event: MessageCreated):
    await event.message.answer(
        text="👋 *Добро пожаловать!*\n\nВыберите раздел:",
        attachments=[get_start_menu()]
    )


async def show_docs_page(event, user_id, device_name, page):
    """Отображение страницы со списком документов"""
    session = get_session(user_id)
    docs = session.docs_list
    total = len(docs)
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, total)
    page_docs = docs[start:end]
    
    # Текст
    text = f"📄 *{device_name}*\n\n"
    text += f"📋 Всего документов: {total}\n"
    text += "➖" * 20 + "\n\n"
    
    for i, doc in enumerate(page_docs, start=start + 1):
        doc_number = doc.get('file_name') or doc.get('number') or f"Док #{doc['id']}"
        full_name = doc.get('name', 'Без названия')
        text += f"*{i}.* 📄 *{doc_number}*\n"
        text += f"   {full_name}\n\n"
    
    total_pages = (total + items_per_page - 1) // items_per_page
    text += "➖" * 20 + "\n"
    text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    text += "📌 *Нажмите на кнопку с номером для скачивания:*\n"
    
    # Кнопки
    builder = InlineKeyboardBuilder()
    
    row_buttons = []
    for i, doc in enumerate(page_docs, start=start + 1):
        row_buttons.append(CallbackButton(text=f"⤓{i}", payload=f"download:{doc['id']}"))
        if len(row_buttons) == 5:
            builder.row(*row_buttons)
            row_buttons = []
    if row_buttons:
        builder.row(*row_buttons)
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(CallbackButton(text="◀ Назад", payload=f"docs_page:{device_name}:{page-1}"))
    if end < total:
        nav_buttons.append(CallbackButton(text="Вперед ▶", payload=f"docs_page:{device_name}:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(CallbackButton(text="🔙 Назад к устройствам", payload="back_to_devices"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:MAIN"))
    
    await event.bot.edit_message(
        message_id=event.message.body.mid,
        text=text,
        attachments=[builder.as_markup()]
    )


async def show_search_results_in_message(bot, chat_id, message_id, user_id, query, page):
    """Отображение результатов поиска в существующем сообщении"""    
    session = get_session(user_id)
    results = session.search_results
    total = len(results)
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, total)
    page_results = results[start:end]
    
    mode = session.search_mode or "text"
    mode_icon = "🔍" if mode == "text" else "🔢"
    mode_name = "названию" if mode == "text" else "номеру"
    
    text = f"{mode_icon} *Результаты поиска по {mode_name} «{query}»:*\n\n"
    text += f"📋 Всего найдено: {total}\n"
    text += "➖" * 20 + "\n\n"
    
    for i, doc in enumerate(page_results, start=start + 1):
        doc_number = doc.get('file_name') or doc.get('number') or f"Док #{doc['id']}"
        full_name = doc.get('name', 'Без названия')
        text += f"*{i}.* 📄 *{doc_number}*\n"
        text += f"   {full_name[:80]}{'...' if len(full_name) > 80 else ''}\n\n"
    
    total_pages = (total + items_per_page - 1) // items_per_page
    text += "➖" * 20 + "\n"
    text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    text += "📌 *Нажмите на кнопку с номером для скачивания:*\n"
    
    builder = InlineKeyboardBuilder()
    
    row_buttons = []
    for i, doc in enumerate(page_results, start=start + 1):
        row_buttons.append(CallbackButton(text=f"⤓{i}", payload=f"download:{doc['id']}"))
        if len(row_buttons) == 5:
            builder.row(*row_buttons)
            row_buttons = []
    if row_buttons:
        builder.row(*row_buttons)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(CallbackButton(text="◀ Назад", payload=f"search_page:{page-1}"))
    if end < total:
        nav_buttons.append(CallbackButton(text="Вперед ▶", payload=f"search_page:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(CallbackButton(text="🔍 Новый поиск", payload="menu:SEARCH"))
    builder.row(CallbackButton(text="🔤 Поиск по названию", payload="menu:TEXT_SEARCH"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:MAIN"))
    
    await bot.edit_message(
        message_id=message_id,
        text=text,
        attachments=[builder.as_markup()]
    )


async def show_search_results(event, user_id, query, page):
    """Отображение результатов поиска"""
    session = get_session(user_id)
    results = session.search_results
    total = len(results)
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, total)
    page_results = results[start:end]
    
    mode = session.search_mode or "text"
    mode_icon = "🔍" if mode == "text" else "🔢"
    mode_name = "названию" if mode == "text" else "номеру"
    
    text = f"{mode_icon} *Результаты поиска по {mode_name} «{query}»:*\n\n"
    text += f"📋 Всего найдено: {total}\n"
    text += "➖" * 20 + "\n\n"
    
    for i, doc in enumerate(page_results, start=start + 1):
        doc_number = doc.get('file_name') or doc.get('number') or f"Док #{doc['id']}"
        full_name = doc.get('name', 'Без названия')
        text += f"*{i}.* 📄 *{doc_number}*\n"
        text += f"   {full_name[:199]}{'...' if len(full_name) > 199 else ''}\n\n"
    
    total_pages = (total + items_per_page - 1) // items_per_page
    text += "➖" * 20 + "\n"
    text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    text += "📌 *Нажмите на кнопку с номером для скачивания:*\n"
    
    builder = InlineKeyboardBuilder()
    
    row_buttons = []
    for i, doc in enumerate(page_results, start=start + 1):
        row_buttons.append(CallbackButton(text=f"⤓{i}", payload=f"download:{doc['id']}"))
        if len(row_buttons) == 5:
            builder.row(*row_buttons)
            row_buttons = []
    if row_buttons:
        builder.row(*row_buttons)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(CallbackButton(text="◀ Назад", payload=f"search_page:{page-1}"))
    if end < total:
        nav_buttons.append(CallbackButton(text="Вперед ▶", payload=f"search_page:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(CallbackButton(text="🔍 Поиск по номеру", payload="menu:SEARCH"))
    builder.row(CallbackButton(text="🔤 Поиск по названию", payload="menu:TEXT_SEARCH"))
    builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:MAIN"))
    
    # Если это первый показ (нет сохранённого ID сообщения) — отправляем новое
    if session.search_message_id is None:
        sent = await event.message.answer(
            text=text,
            attachments=[builder.as_markup()]
        )
        session.search_message_id = sent.message.body.mid
    else:
        # Редактируем существующее сообщение
        try:
            await event.bot.edit_message(
                message_id=session.search_message_id,
                text=text,
                attachments=[builder.as_markup()]
            )
        except Exception as e:
            # Если сообщение не найдено (например, после перезапуска бота)
            logger.error(f"Ошибка редактирования сообщения: {e}")
            sent = await event.message.answer(
                text=text,
                attachments=[builder.as_markup()]
            )
            # session.search_message_id = sent.message_id
            session.search_message_id = sent.message.body.mid