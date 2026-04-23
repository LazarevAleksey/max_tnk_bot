# handlers/navigation.py
from maxapi.types.attachments.buttons import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from models.session import get_session
from keyboards import get_back_keyboard



async def show_docs_page(event, user_id, device_name, page):
    """Отображение страницы со списком документов"""
    from maxapi.types.attachments.buttons import CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
    
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


async def show_search_results(event, user_id, query, page):
    """Отображение результатов поиска"""
    from maxapi.types.attachments.buttons import CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
    
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
    
    await event.message.answer(
        text=text,
        attachments=[builder.as_markup()]
    )
    