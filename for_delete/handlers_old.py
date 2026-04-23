import os
import logging
from maxapi import Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, MessageCallback
from maxapi.types.attachments.buttons import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from config import PDF_FOLDER, CATEGORIES, ITEMS_PER_PAGE, BOT_TOKEN
from data_loader import doc_loader
from keyboards import (
    get_main_menu, get_documents_menu, get_document_card,
    get_back_keyboard, get_search_number_keyboard, get_help_keyboard,
    get_devices_menu
)
from for_delete.class_upload_file_max import MaxBot


# Создайте экземпляр MaxBot (после импортов, до обработчиков)
max_bot = MaxBot(BOT_TOKEN)

logger = logging.getLogger(__name__)

dp = Dispatcher()

# Хранилища
user_favorites = {}
user_history = {}
search_states = {}
user_last_device = {}  # для возврата к списку документов
user_docs_list = {}      # список документов для текущего пользователя
user_current_page = {}   # текущая страница
user_search_results = {}      # результаты поиска
user_search_page = {}         # текущая страница поиска
user_search_mode = {}         # режим поиска ("text" или "number")
user_search_query = {}        # текст запроса
user_search_message_id = {}  # ID сообщения с результатами поиска



def convert_filename_to_pdf(file_name: str) -> str:
    """
    Преобразует имя файла из ТНК ЦШ 0147-2022 в 0147.pdf
    Примеры:
        ТНК ЦШ 0147-2022 -> 0147.pdf
        ТНК ЦШ 0150-2017 -> 0150.pdf
        КТП ЦШ 1024-2019 -> 1024.pdf
        КТП ЦШ 0884-2018 -> 0884.pdf
    """
    import re
    
    # Ищем 4-значное число в имени файла
    match = re.search(r'\b(\d{4})\b', file_name)
    if match:
        number = match.group(1)  # '0147'
        return f"{number}.pdf"
    
    # Если не нашли 4 цифры, ищем 3 цифры (для старых форматов)
    match = re.search(r'\b(\d{3})\b', file_name)
    if match:
        number = match.group(1)
        return f"{number}.pdf"
    
    # Если ничего не нашли, возвращаем исходное имя (как запасной вариант)
    return file_name


# ==================== Обработчики ====================

@dp.bot_started()
async def bot_started(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="🔧 *Система поиска ТНК/КТП*\n\n"
             "📋 Инструкция ОАО «РЖД» №3168р\n"
             "👇 Выберите категорию:",
        attachments=[get_main_menu()]
    )


@dp.message_created(Command('start'))
async def cmd_start(event: MessageCreated):
    await event.message.answer(
        text="🔧 *Система поиска ТНК/КТП*\n\n👇 Выберите категорию:",
        attachments=[get_main_menu()]
    )


@dp.message_created(Command('help'))
async def cmd_help(event: MessageCreated):
    help_text = (
        "ℹ️ *Помощь*\n\n"
        "🔹 *Навигация:* кнопки меню\n"
        "🔹 *Поиск:* по номеру или названию\n"
        "🔹 *Скачивание:* нажмите на документ → «Скачать файл»\n"
        "🔹 *Избранное:* ⭐ в карточке документа"
    )
    await event.message.answer(text=help_text, attachments=[get_help_keyboard()])


async def show_docs_page(event, user_id, device_name, page):
    from maxapi.types.attachments.buttons import CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
    
    docs = user_docs_list.get(user_id, [])
    total = len(docs)
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, total)
    page_docs = docs[start:end]
    
    # ТЕКСТОВЫЙ СПИСОК с полными названиями
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
    
    # КНОПКИ ТОЛЬКО С НОМЕРАМИ (без пробела после иконки)
    builder = InlineKeyboardBuilder()
    
    row_buttons = []
    for i, doc in enumerate(page_docs, start=start + 1):
        row_buttons.append(CallbackButton(text=f"⤓{i}", payload=f"download:{doc['id']}"))
        
        # Группируем по 5 кнопок в строку
        if len(row_buttons) == 5:
            builder.row(*row_buttons)
            row_buttons = []
    
    # Оставшиеся кнопки
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
    from maxapi.types.attachments.buttons import CallbackButton
    from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
    
    results = user_search_results.get(user_id, [])
    total = len(results)
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, total)
    page_results = results[start:end]
    
    mode = user_search_mode.get(user_id, "text")
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
    
    # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ (не редактируем)
    await event.message.answer(
        text=text,
        attachments=[builder.as_markup()]
    )


@dp.message_callback()
async def handle_callback(event: MessageCallback):
    chat_id, user_id = event.get_ids()
    data = event.callback.payload
    
    if not data:
        return
    
    elif data.startswith("docs_page:"):
        parts = data.split(":")
        if len(parts) >= 3:
            device_name = parts[1]
            page = int(parts[2])
            user_current_page[user_id] = page
            await show_docs_page(event, user_id, device_name, page)

    # ========== ПАГИНАЦИЯ РЕЗУЛЬТАТОВ ПОИСКА ==========
    elif data.startswith("search_page:"):
        page = int(data.split(":")[1])
        query = user_search_query.get(user_id, "")
        if query:
            user_search_page[user_id] = page
            await show_search_results(event, user_id, query, page)


    elif data.startswith("doc_preview:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc:
            full_name = doc.get('name', 'Без названия')
            doc_number = doc.get('file_name') or doc.get('number') or 'Документ'
            MAX_LENGTH = 100  # максимальная длина одного всплывающего сообщения
        
            if len(full_name) <= MAX_LENGTH:
                # Короткое название — показываем одним сообщением
                print('Имя короче 200')
                await event.answer(full_name)
            else:
                # Длинное название — разбиваем на две части
                # Ищем место разрыва (пробел) в районе середины
                mid = len(full_name) // 2
                # Ищем пробел в пределах ±30 символов от середины
                split_pos = -1
                for i in range(mid - 30, mid + 30):
                    if i >= len(full_name):
                        break
                    if full_name[i] == ' ':
                        split_pos = i
                        break
                
                # Если пробел не найден, режем по середине
                if split_pos == -1:
                    split_pos = mid
                
                part1 = full_name[:split_pos]
                part2 = full_name[split_pos:].lstrip()  # убираем пробел в начале
                print(f'part2: {part2}')
                
                # Показываем первую часть
                await event.answer(part1)            
            
            # Небольшая задержка, чтобы пользователь успел прочитать
                import asyncio
                await asyncio.sleep(2,0)

                await event.answer(part2)
        else:
            await event.answer("❌ Документ не найден")
        return
    
    
    # ========== ГЛАВНОЕ МЕНЮ ==========
    if data.startswith("menu:"):
        action = data.split(":")[1]
        
        if action == "MAIN" or action == "BACK_TO_MAIN":
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="🏠 *Главное меню*\n\nВыберите категорию:",
                attachments=[get_main_menu()]
            )
        

        elif action == "SEARCH":
            search_states[user_id] = {"mode": "number", "value": ""}
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="🔢 *Поиск по номеру документа*\n\n"
                    "Введите номер ТНК или КТП.\n\n"
                    "📝 *Примеры:*\n"
                    "• `0147`\n"
                    "• `ТНК ЦШ 0147-2022`\n\n"
                    "Используйте клавиатуру:",
                attachments=[get_search_number_keyboard()]
            )


        elif action == "TEXT_SEARCH":
            search_states[user_id] = {"mode": "text", "value": ""}
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="🔍 *Поиск по названию документа*\n\n"
                    "Введите слово или фразу из названия.\n\n"
                    "📝 *Пример:*\n"
                    "• `проверка видимости`\n"
                    "• `прибор`\n\n"
                    "✏️ Введите текст:",
                attachments=[get_back_keyboard()]
            )
            
        elif action == "HISTORY":
            history = user_history.get(user_id, [])
            if history:
                text = "📅 *История просмотров (последние 10):*\n\n"
                for doc_id in history[-10:]:
                    doc = doc_loader.get_document_by_id(doc_id)
                    if doc:
                        text += f"• {doc.get('file_name', doc.get('number', '?'))} - {doc['name'][:40]}\n"
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=text,
                    attachments=[get_back_keyboard()]
                )
            else:
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text="📅 *История просмотров*\n\nПока пуста.",
                    attachments=[get_back_keyboard()]
                )
        
        elif action == "HELP":
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="ℹ️ *Помощь*\n\n"
                     "🔹 Выберите категорию → устройство\n"
                     "🔹 Нажмите на документ для просмотра\n"
                     "🔹 «Скачать файл» — получить PDF\n"
                     "🔹 ⭐ — добавить в избранное",
                attachments=[get_help_keyboard()]
            )
    
    # ========== ВЫБОР КАТЕГОРИИ ==========
    elif data.startswith("cat:"):
        category_code = data.split(":")[1]
        
        category_name = [k for k, v in CATEGORIES.items() if v == category_code]
        category_name = category_name[0] if category_name else category_code
        
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=f"📁 *{category_name}*\n\nВыберите устройство:",
            attachments=[get_devices_menu(category_code)]
        )


    # ========== ВЫБОР УСТРОЙСТВА → ТЕКСТОВЫЙ СПИСОК ==========
    elif data.startswith("device:"):
        device_name = data.split(":", 1)[1]
        user_last_device[user_id] = device_name
        
        # Получаем все документы для этого устройства
        docs = doc_loader.get_documents(device=device_name, limit=10000, offset=0)
        total = len(docs)
        
        if docs:
            # Сохраняем список документов для пользователя
            user_docs_list[user_id] = docs
            user_current_page[user_id] = 0
            
            await show_docs_page(event, user_id, device_name, 0)
        else:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📄 *{device_name}*\n\n❌ Документы не найдены",
                attachments=[get_back_keyboard()]
            )
    
    # ========== ПАГИНАЦИЯ ==========
    elif data.startswith("page:"):
        parts = data.split(":")
        if len(parts) >= 3:
            _, device_name, page_str = parts[:3]
            page = int(page_str)
            
            docs = doc_loader.get_documents(device=device_name, limit=ITEMS_PER_PAGE, offset=page * ITEMS_PER_PAGE)
            total = doc_loader.get_documents_count(device=device_name)
            has_more = len(docs) == ITEMS_PER_PAGE
            
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📄 *{device_name}*\n\nНайдено документов: {total}\n\nВыберите ТНК/КТП:",
                attachments=[get_documents_menu(docs, device_name, page, total, has_more)]
            )
    
    # ========== ВОЗВРАТ К СПИСКУ УСТРОЙСТВ ==========
    elif data.startswith("back_to_devices"):
        # Возвращаемся в последнюю выбранную категорию
        # Для простоты — в главное меню
        # Для полноценной работы нужно хранить last_category
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text="🏠 *Главное меню*\n\nВыберите категорию:",
            attachments=[get_main_menu()]
        )
    
    # ========== ВЫБОР ДОКУМЕНТА ==========
    elif data.startswith("doc:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc:
            if user_id not in user_history:
                user_history[user_id] = []
            if doc_id not in user_history[user_id]:
                user_history[user_id].append(doc_id)
                if len(user_history[user_id]) > 50:
                    user_history[user_id] = user_history[user_id][-50:]
            
            is_favorite = user_id in user_favorites and doc_id in user_favorites[user_id]
            
            text = (
                f"📄 *{doc.get('file_name', doc.get('number', 'Документ'))}*\n\n"
                f"🏷️ *Название:* {doc['name']}\n"
                f"👥 *Исполнители:* {doc.get('executors', '—')}\n"
                f"📋 *Оформление:* {doc.get('design', '—')}\n"
                f"📅 *Введён:* {doc.get('order_number', '—')}\n\n"
                f"⬇️ Нажмите «Скачать файл» для получения документа."
            )
            
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=text,
                attachments=[get_document_card(doc, is_favorite)]
            )
    
    
    # ========== СКАЧИВАНИЕ ==========
    elif data.startswith("download:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc and doc.get('file_name'):
            # Преобразуем имя файла из "ТНК ЦШ 0147-2022" в "0147.pdf"
            pdf_filename = convert_filename_to_pdf(doc['file_name'])
            file_path = os.path.join(PDF_FOLDER, pdf_filename)
            
            print(f"Оригинальное имя: {doc['file_name']}")
            print(f"Ищем файл: {file_path}")
            if os.path.exists(file_path):
                try:
                    # Используем MaxBot для отправки файла
                    success = max_bot.send_file_to_user(
                        user_id=user_id,
                        file_path=file_path,
                        message_text=f"📎 {doc.get('file_name', doc.get('number', 'Документ'))}\n{doc.get('name', 'Без названия')}"
                    )
                    
                    if success:
                        await event.answer("✅ Файл отправлен")
                    else:
                        await event.answer("❌ Ошибка при отправке файла")
                        
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await event.answer("❌ Ошибка при отправке файла")
            else:
                await event.answer(f"❌ Файл не найден: {pdf_filename}")
        else:
            await event.answer("❌ Документ не найден")
    
    
    # ========== ИЗБРАННОЕ ==========
    elif data.startswith("favorite:"):
        parts = data.split(":")
        if len(parts) >= 3:
            _, action, doc_id_str = parts[:3]
            doc_id = int(doc_id_str)
            
            if user_id not in user_favorites:
                user_favorites[user_id] = []
            
            if action == "add":
                if doc_id not in user_favorites[user_id]:
                    user_favorites[user_id].append(doc_id)
                    await event.answer("⭐ Добавлено в избранное")
            elif action == "remove":
                if doc_id in user_favorites[user_id]:
                    user_favorites[user_id].remove(doc_id)
                    await event.answer("❌ Удалено из избранного")
            
            doc = doc_loader.get_document_by_id(doc_id)
            if doc:
                is_favorite = doc_id in user_favorites.get(user_id, [])
                await event.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=event.message.body.mid,
                    attachments=[get_document_card(doc, is_favorite)]
                )
    
    # ========== ВОЗВРАТ К СПИСКУ ДОКУМЕНТОВ ==========
    elif data.startswith("back_to_list"):
        device_name = user_last_device.get(user_id)
        print(f'device_name: ')
        if device_name:
            docs = doc_loader.get_documents(device=device_name, limit=ITEMS_PER_PAGE, offset=0)
            total = doc_loader.get_documents_count(device=device_name)
            has_more = len(docs) == ITEMS_PER_PAGE
            
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📄 *{device_name}*\n\nНайдено документов: {total}\n\nВыберите ТНК/КТП:",
                attachments=[get_documents_menu(docs, device_name, 0, total, has_more)]
            )
        else:
            print('get_main_menu!!!')
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="🏠 *Главное меню*\n\nВыберите категорию:",
                attachments=[get_main_menu()]
            )
    
    # ========== ПОИСК ПО НОМЕРУ (ЦИФРЫ) ==========
    elif data.startswith("search_number:"):
        parts = data.split(":")
        
        if len(parts) >= 2:
            action = parts[1]
            
            # Получаем текущее состояние (словарь)
            current_state = search_states.get(user_id, {})
            if isinstance(current_state, str):
                # Если вдруг осталась строка от старой версии — конвертируем
                current_state = {"mode": "number", "value": current_state}
            
            current_value = current_state.get("value", "")
            
            if action == "digit":
                digit = parts[2]
                new_value = current_value + digit
                search_states[user_id] = {"mode": "number", "value": new_value}
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{new_value}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "backspace":
                new_value = current_value[:-1]
                search_states[user_id] = {"mode": "number", "value": new_value}
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{new_value}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "clear":
                search_states[user_id] = {"mode": "number", "value": ""}
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text="🔢 *Поиск по номеру документа*\n\n"
                        "Введите номер ТНК или КТП.\n\n"
                        "📝 *Примеры:*\n"
                        "• `0111`\n"
                        "• `ЦП 0111-2022`\n\n"
                        "Используйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "submit":
                search_number = current_value
                
                if search_number:
                    results = doc_loader.search_by_number(search_number)
                    
                    if results:
                        text = f"🔍 *Результаты поиска по номеру «{search_number}»:*\n\n"
                        for doc in results[:15]:
                            text += f"📄 {doc.get('file_name', doc.get('number', '?'))}\n   {doc['name'][:50]}\n\n"
                        
                        builder = InlineKeyboardBuilder()
                        for doc in results[:10]:
                            builder.row(CallbackButton(text=doc.get('file_name', doc.get('number', f"Док #{doc['id']}"))[:30], payload=f"doc:{doc['id']}"))
                        
                        builder.row(CallbackButton(text="🔍 Новый поиск", payload="menu:SEARCH"))
                        builder.row(CallbackButton(text="🏠 Главное меню", payload="menu:MAIN"))
                        
                        await event.bot.edit_message(
                            message_id=event.message.body.mid,
                            text=text,
                            attachments=[builder.as_markup()]
                        )
                    else:
                        await event.bot.edit_message(
                            message_id=event.message.body.mid,
                            text=f"❌ *Ничего не найдено* по номеру «{search_number}»\n\nПопробуйте снова:",
                            attachments=[get_search_number_keyboard()]
                        )
                    
                    del search_states[user_id]


@dp.message_created()
async def handle_text_input(event: MessageCreated):
    chat_id, user_id = event.get_ids()
    text = event.message.body.text.strip()

    # Проверяем, ожидаем ли мы поиск (текстовый ввод)
    state = search_states.get(user_id)
    
    if state and isinstance(state, dict) and state.get("mode") == "text":
        # Поиск по тексту
        print(f"🔍 Поиск по тексту: {text}")
        results = doc_loader.search_by_text(text)
        print(f"Найдено результатов: {len(results)}")
        
        if results:
            # Сохраняем результаты поиска
            user_search_results[user_id] = results
            user_search_page[user_id] = 0
            user_search_mode[user_id] = "text"
            user_search_query[user_id] = text
            
            await show_search_results(event, user_id, text, 0)
        else:
            await event.message.answer(f"❌ Ничего не найдено по запросу «{text}»")
        
        del search_states[user_id]
    
    elif user_id in user_docs_list and text.isdigit():
        # Обработка ввода номера документа из списка (существующая логика)
        doc_num = int(text)
        docs = user_docs_list.get(user_id, [])
        
        if 1 <= doc_num <= len(docs):
            doc = docs[doc_num - 1]
            
            if user_id not in user_history:
                user_history[user_id] = []
            if doc['id'] not in user_history[user_id]:
                user_history[user_id].append(doc['id'])
                if len(user_history[user_id]) > 50:
                    user_history[user_id] = user_history[user_id][-50:]
            
            is_favorite = user_id in user_favorites and doc['id'] in user_favorites[user_id]
            
            card_text = (
                f"📄 *{doc.get('file_name', doc.get('number', 'Документ'))}*\n\n"
                f"🏷️ *Название:* {doc['name']}\n"
                f"👥 *Исполнители:* {doc.get('executors', '—')}\n"
                f"📋 *Оформление:* {doc.get('design', '—')}\n"
                f"📅 *Введён:* {doc.get('order_number', '—')}"
            )
            
            await event.message.answer(
                text=card_text,
                attachments=[get_document_card(doc, is_favorite)]
            )
        else:
            await event.message.answer(f"❌ Неверный номер. Введите число от 1 до {len(docs)}")
    
    else:
        # Поиск по номеру (обычный)
        results = doc_loader.search_by_number(text)
        if results:
            user_search_results[user_id] = results
            user_search_page[user_id] = 0
            user_search_mode[user_id] = "number"
            user_search_query[user_id] = text
            
            await show_search_results(event, user_id, text, 0)
        else:
            docs_len = len(user_docs_list.get(user_id, []))
            await event.message.answer(
                f"❌ Ничего не найдено.\n\n"
                f"Введите номер документа из списка (1-{docs_len})\n"
                f"или номер ТНК/КТП для поиска."
            )