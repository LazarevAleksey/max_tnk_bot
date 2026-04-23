# handlers/callbacks.py
import os
import logging
from maxapi.types import MessageCallback
from maxapi.types.attachments.buttons import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from config import PDF_FOLDER, CATEGORIES, ITEMS_PER_PAGE
from data_loader import doc_loader
from keyboards import (
    get_main_menu, get_documents_menu, get_document_card,
    get_back_keyboard, get_search_number_keyboard, get_help_keyboard,
    get_devices_menu
)
from models.session import get_session, get_search_state
from services.file_sender import FileSender
from utils.utils import convert_filename_to_pdf, split_long_text
from .navigation import show_docs_page, show_search_results

logger = logging.getLogger(__name__)
file_sender = FileSender()


async def handle_callback(event: MessageCallback):
    chat_id, user_id = event.get_ids()
    session = get_session(user_id)
    data = event.callback.payload
    
    if not data:
        return
    
    # ========== ПАГИНАЦИЯ ДОКУМЕНТОВ ==========
    if data.startswith("docs_page:"):
        parts = data.split(":")
        if len(parts) >= 3:
            device_name = parts[1]
            page = int(parts[2])
            session.current_page = page
            await show_docs_page(event, user_id, device_name, page)
        return
    
    # ========== ПАГИНАЦИЯ РЕЗУЛЬТАТОВ ПОИСКА ==========
    if data.startswith("search_page:"):
        page = int(data.split(":")[1])
        query = session.search_query
        if query:
            session.search_page = page
            await show_search_results(event, user_id, query, page)
        return
    
    # ========== ПРЕДПРОСМОТР ДОКУМЕНТА ==========
    if data.startswith("doc_preview:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc:
            full_name = doc.get('name', 'Без названия')
            parts = split_long_text(full_name)
            for part in parts:
                await event.answer(part)
                import asyncio
                await asyncio.sleep(0.5)
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
            search_state = get_search_state(user_id)
            search_state.mode = "number"
            search_state.value = ""
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
            search_state = get_search_state(user_id)
            search_state.mode = "text"
            search_state.value = ""
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
            history = session.history
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
        return
    
    # ========== ВЫБОР КАТЕГОРИИ ==========
    if data.startswith("cat:"):
        category_code = data.split(":")[1]
        category_name = [k for k, v in CATEGORIES.items() if v == category_code]
        category_name = category_name[0] if category_name else category_code
        
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=f"📁 *{category_name}*\n\nВыберите устройство:",
            attachments=[get_devices_menu(category_code)]
        )
        return
    
    # ========== ВЫБОР УСТРОЙСТВА ==========
    if data.startswith("device:"):
        device_name = data.split(":", 1)[1]
        session.last_device = device_name
        
        docs = doc_loader.get_documents(device=device_name, limit=10000, offset=0)
        
        if docs:
            session.docs_list = docs
            session.current_page = 0
            await show_docs_page(event, user_id, device_name, 0)
        else:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📄 *{device_name}*\n\n❌ Документы не найдены",
                attachments=[get_back_keyboard()]
            )
        return
    
    # ========== ПАГИНАЦИЯ СТАРАЯ ==========
    if data.startswith("page:"):
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
        return
    
    # ========== ВОЗВРАТ К УСТРОЙСТВАМ ==========
    if data.startswith("back_to_devices"):
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text="🏠 *Главное меню*\n\nВыберите категорию:",
            attachments=[get_main_menu()]
        )
        return
    
    # ========== ВЫБОР ДОКУМЕНТА ==========
    if data.startswith("doc:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc:
            if doc_id not in session.history:
                session.history.append(doc_id)
                if len(session.history) > 50:
                    session.history = session.history[-50:]
            
            is_favorite = doc_id in session.favorites
            
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
        return
    
    # ========== СКАЧИВАНИЕ ==========
    if data.startswith("download:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc and doc.get('file_name'):
            pdf_filename = convert_filename_to_pdf(doc['file_name'])
            file_path = os.path.join(PDF_FOLDER, pdf_filename)
            
            if os.path.exists(file_path):
                try:
                    success = await file_sender.send_file_to_user(
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
        return
    
    # ========== ИЗБРАННОЕ ==========
    if data.startswith("favorite:"):
        parts = data.split(":")
        if len(parts) >= 3:
            _, action, doc_id_str = parts[:3]
            doc_id = int(doc_id_str)
            
            if action == "add":
                if doc_id not in session.favorites:
                    session.favorites.append(doc_id)
                    await event.answer("⭐ Добавлено в избранное")
            elif action == "remove":
                if doc_id in session.favorites:
                    session.favorites.remove(doc_id)
                    await event.answer("❌ Удалено из избранного")
            
            doc = doc_loader.get_document_by_id(doc_id)
            if doc:
                is_favorite = doc_id in session.favorites
                await event.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=event.message.body.mid,
                    attachments=[get_document_card(doc, is_favorite)]
                )
        return
    
    # ========== ВОЗВРАТ К СПИСКУ ==========
    if data.startswith("back_to_list"):
        device_name = session.last_device
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
        return
    
    # ========== ПОИСК ПО НОМЕРУ (ЦИФРЫ) ==========
    if data.startswith("search_number:"):
        parts = data.split(":")
        
        if len(parts) >= 2:
            action = parts[1]
            search_state = get_search_state(user_id)
            current_value = search_state.value
            
            if action == "digit":
                digit = parts[2]
                search_state.value = current_value + digit
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{search_state.value}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "backspace":
                search_state.value = current_value[:-1]
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{search_state.value}`\n\nИспользуйте клавиатуру:",
                    attachments=[get_search_number_keyboard()]
                )
            
            elif action == "clear":
                search_state.value = ""
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
                search_number = search_state.value
                
                if search_number:
                    results = doc_loader.search_by_number(search_number)
                    
                    if results:
                        session.search_results = results
                        session.search_page = 0
                        session.search_mode = "number"
                        session.search_query = search_number
                        
                        await show_search_results(event, user_id, search_number, 0)
                    else:
                        await event.bot.edit_message(
                            message_id=event.message.body.mid,
                            text=f"❌ *Ничего не найдено* по номеру «{search_number}»\n\nПопробуйте снова:",
                            attachments=[get_search_number_keyboard()]
                        )
                    
                    search_state.value = ""
        return