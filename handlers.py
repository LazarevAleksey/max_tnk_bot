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

logger = logging.getLogger(__name__)

dp = Dispatcher()

# Хранилища
user_favorites = {}
user_history = {}
search_states = {}
user_last_device = {}  # для возврата к списку документов


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


@dp.message_callback()
async def handle_callback(event: MessageCallback):
    chat_id, user_id = event.get_ids()
    data = event.callback.payload
    
    if not data:
        return
    
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
    
    # ========== ВЫБОР УСТРОЙСТВА → СРАЗУ СПИСОК ТНК ==========
    elif data.startswith("device:"):
        device_name = data.split(":", 1)[1]  # берём всё после "device:"
        user_last_device[user_id] = device_name
        
        # Получаем все документы для этого устройства (без фильтра по действию)
        docs = doc_loader.get_documents(device=device_name, limit=ITEMS_PER_PAGE, offset=0)
        total = doc_loader.get_documents_count(device=device_name)
        has_more = len(docs) == ITEMS_PER_PAGE
        
        if docs:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📄 *{device_name}*\n\nНайдено документов: {total}\n\nВыберите ТНК/КТП:",
                attachments=[get_documents_menu(docs, device_name, 0, total, has_more)]
            )
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
            file_path = os.path.join(PDF_FOLDER, doc['file_name'])
            
            if os.path.exists(file_path):
                try:
                    await event.bot.send_file(
                        chat_id=chat_id,
                        file_path=file_path,
                        filename=doc['file_name'],
                        caption=f"📎 {doc.get('file_name', doc.get('number', 'Документ'))}\n{doc.get('name', 'Без названия')}"
                    )
                    await event.answer("✅ Файл отправлен")
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await event.answer("❌ Ошибка при отправке файла")
            else:
                await event.answer(f"❌ Файл не найден: {doc['file_name']}")
    
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