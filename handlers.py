import os
import logging
from maxapi import Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, MessageCallback
from maxapi.types.attachments.buttons import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from config import PDF_FOLDER, CATEGORIES, ITEMS_PER_PAGE
from data_loader import doc_loader
from keyboards import (
    get_main_menu, get_documents_menu, get_document_card,
    get_back_keyboard, get_search_number_keyboard, get_help_keyboard,
    get_devices_menu
)
from class_upload_file_max import MaxBot
from config_links import BOT_TOKEN

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
    
    text = f"📄 *{device_name}*\n\n"
    text += f"📋 Всего документов: {total}\n"
    text += "➖" * 20 + "\n\n"
    
    for i, doc in enumerate(page_docs, start=start + 1):
        doc_number = doc.get('file_name') or doc.get('number') or f"Док #{doc['id']}"
        text += f"*{i}.* 📄 *{doc_number}*\n"
        full_name = doc.get('name', 'Без названия')
        text += f"   {full_name}\n\n"
    
    total_pages = (total + items_per_page - 1) // items_per_page
    text += "➖" * 20 + "\n"
    text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    text += "✏️ *Введите номер документа* (например, `5`) для просмотра карточки.\n"
    text += "🔢 Или введите номер ТНК/КТП для поиска."
    
    builder = InlineKeyboardBuilder()
    
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

    # elif data.startswith("doc_preview:"):
    #     doc_id = int(data.split(":")[1])
    #     doc = doc_loader.get_document_by_id(doc_id)
        
    #     if doc:
    #         # Показываем всплывающее уведомление с полным названием
    #         # Максимальная длина answer — 200 символов, поэтому обрезаем если длиннее
    #         full_name = doc.get('name', 'Без названия')
    #         # if len(full_name) > 190:
    #         #     full_name = full_name[:187] + "..."
            
    #         await event.answer(f"📄 {full_name}")
    #         # await event.answer(f"📄 {doc.get('file_name', doc.get('number', 'Документ'))}\n\n{full_name}")
    #     else:
    #         await event.answer("❌ Документ не найден")
        
    #     return  # Не продолжаем дальше, чтобы не открывать карточку

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


            # Первое сообщение: номер документа
            #await event.answer(f"📄 {doc_number}")
            # if len(full_name) > 190:
                #full_name = full_name[:187] + "..."
            
            # Небольшая задержка, чтобы пользователь успел прочитать
                import asyncio
                await asyncio.sleep(2,0)

                await event.answer(part2)
            
            # Второе сообщение: название
            # if len(full_name) > 180:
            #     # Если название очень длинное — разбиваем на части
            #     parts = [full_name[i:i+180] for i in range(0, len(full_name), 180)]
            #     for part in parts:
            #         await event.answer(part)
            #         await asyncio.sleep(0.3)
            # else:
            #     await event.answer(full_name)
        else:
            await event.answer("❌ Документ не найден")
        return
    

    # ========== НОВЫЙ ОБРАБОТЧИК ДЛЯ ПРЕДПРОСМОТРА ==========
    # if data.startswith("doc_preview:"):
    #     doc_id = int(data.split(":")[1])
    #     doc = doc_loader.get_document_by_id(doc_id)
        
    #     if doc:
    #         full_name = doc.get('name', 'Без названия')
    #         if len(full_name) > 180:
    #             full_name = full_name[:177] + "..."
            
    #         preview_text = f"📄 {doc.get('file_name', doc.get('number', 'Документ'))}\n\n{full_name}\n\n👥 {doc.get('executors', '—')}"
    #         await event.answer(preview_text)
    #     else:
    #         await event.answer("❌ Документ не найден")
    #     return  # Важно: не продолжаем обработку
    
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
            search_states[user_id] = "waiting_number"
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
    
    # # ========== ВЫБОР УСТРОЙСТВА → СРАЗУ СПИСОК ТНК ==========
    # elif data.startswith("device:"):
    #     device_name = data.split(":", 1)[1]  # берём всё после "device:"
    #     user_last_device[user_id] = device_name
        
    #     # Получаем все документы для этого устройства (без фильтра по действию)
    #     docs = doc_loader.get_documents(device=device_name, limit=ITEMS_PER_PAGE, offset=0)
    #     total = doc_loader.get_documents_count(device=device_name)
    #     has_more = len(docs) == ITEMS_PER_PAGE
        
    #     if docs:
    #         await event.bot.edit_message(
    #             message_id=event.message.body.mid,
    #             text=f"📄 *{device_name}*\n\nНайдено документов: {total}\n\nВыберите ТНК/КТП:",
    #             attachments=[get_documents_menu(docs, device_name, 0, total, has_more)]
    #         )
    #     else:
    #         await event.bot.edit_message(
    #             message_id=event.message.body.mid,
    #             text=f"📄 *{device_name}*\n\n❌ Документы не найдены",
    #             attachments=[get_back_keyboard()]
    #         )


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

        
            # # ДИАГНОСТИКА: выводим список файлов в папке
            # print(f"📁 Содержимое папки {PDF_FOLDER}:")
            # if os.path.exists(PDF_FOLDER):
            #     for f in os.listdir(PDF_FOLDER):
            #         print(f"   - {f}")
            # else:
            #     print(f"   ❌ Папка {PDF_FOLDER} не существует")

            
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
    
    
    # # ========== СКАЧИВАНИЕ ==========
    # elif data.startswith("download:"):
    #     doc_id = int(data.split(":")[1])
    #     doc = doc_loader.get_document_by_id(doc_id)
        
    #     if doc and doc.get('file_name'):
    #         file_path = os.path.join(PDF_FOLDER, doc['file_name'])
            
    #         if os.path.exists(file_path):
    #             try:
    #                 await event.bot.send_file(
    #                     chat_id=chat_id,
    #                     file_path=file_path,
    #                     filename=doc['file_name'],
    #                     caption=f"📎 {doc.get('file_name', doc.get('number', 'Документ'))}\n{doc.get('name', 'Без названия')}"
    #                 )
    #                 await event.answer("✅ Файл отправлен")
    #             except Exception as e:
    #                 logger.error(f"Ошибка отправки файла: {e}")
    #                 await event.answer("❌ Ошибка при отправке файла")
    #         else:
    #             await event.answer(f"❌ Файл не найден: {doc['file_name']}")
    
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
    
    # ========== ПОИСК ПО НОМЕРУ ==========
    elif data.startswith("search_number:"):
        parts = data.split(":")
        
        if len(parts) >= 2:
            action = parts[1]
            
            if action == "digit":
                digit = parts[2]
                current = search_states.get(user_id, "")
                new_number = current + digit
                search_states[user_id] = new_number
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{new_number}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "backspace":
                current = search_states.get(user_id, "")
                new_number = current[:-1]
                search_states[user_id] = new_number
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{new_number}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "submit":
                search_number = search_states.get(user_id, "")
                
                if search_number:
                    results = doc_loader.search_by_number(search_number)
                    
                    if results:
                        text = f"🔍 *Результаты поиска по номеру «{search_number}»:*\n\n"
                        for doc in results[:15]:
                            text += f"📄 {doc.get('file_name', doc.get('number', '?'))}\n   {doc['name'][:50]}\n\n"
                        
                        builder = InlineKeyboardBuilder()
                        for doc in results[:10]:
                            builder.row(CallbackButton(text=doc.get('file_name', doc.get('number', f"Док #{doc['id']}"))[:30], payload=f"doc:{doc['id']}"))
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
                            attachments=[get_main_menu()]
                        )
                    
                    del search_states[user_id]

@dp.message_created()
async def handle_text_input(event: MessageCreated):
    # user_id = event.message.body.mid
    chat_id, user_id = event.get_ids() 
    text = event.message.body.text.strip()

    print(f'user_id: {user_id}, text: {text}')
    #print(f'user_docs_list: {user_docs_list}')
    
    if user_id in user_docs_list and text.isdigit():
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
        results = doc_loader.search_by_number(text)
        if results:
            result_text = f"🔍 *Результаты поиска по номеру «{text}»:*\n\n"
            for doc in results[:10]:
                result_text += f"📄 {doc.get('file_name', doc.get('number', '?'))}\n"
                result_text += f"   {doc['name'][:80]}\n\n"
            await event.message.answer(result_text)
        else:
            docs_len = len(user_docs_list.get(user_id, []))
            print(f'docs_len: {docs_len}, user_is: {user_id}')
            await event.message.answer(
                f"❌ Ничего не найдено.\n\n"
                f"Введите номер документа из списка (1-{docs_len})\n"
                f"или номер ТНК/КТП для поиска."
            )