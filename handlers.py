import os
import logging
import time
from utils.utils import simplify_pdf_filename_v2
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated, MessageCallback
# F - это вспомогательный фильтр для атрибутов, он может пригодиться
from maxapi import F

from config import PDF_FOLDER, ACTION_BUTTONS, ITEMS_PER_PAGE, MAIN_MENU_BUTTONS
from data_loader import doc_loader
from keyboards import (
    get_main_menu, get_actions_menu, get_documents_menu,
    get_document_card, get_back_keyboard, get_search_number_keyboard,
    get_help_keyboard
)

logger = logging.getLogger(__name__)

# Создаём диспетчер
dp = Dispatcher()

# Хранилище избранного и истории
user_favorites = {}
user_history = {}
search_states = {}


# ==================== Обработчики ====================

@dp.bot_started()
async def bot_started(event: BotStarted):
    """Обработчик нажатия кнопки 'Начать'"""
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="🔧 *Система поиска ТНК/КТП*\n\n"
             "📋 Инструкция ОАО «РЖД» №3168р\n"
             "📄 Всего документов: *540*\n\n"
             "👇 Выберите устройство:",
        attachments=[get_main_menu()]
        # reply_markup=get_main_menu()
    )


@dp.message_created(Command('start'))
async def cmd_start(event: MessageCreated):
    """Обработчик команды /start"""
    print('start')
    await event.message.answer(
        text="🔧 *Система поиска ТНК/КТП*\n\n"
             "👇 Выберите устройство:",
        attachments=[get_main_menu()]
    )


@dp.message_created(Command('help'))
async def cmd_help(event: MessageCreated):
    """Обработчик команды /help"""
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
    """Обработчик нажатий на inline-кнопки"""
    chat_id, user_id = event.get_ids()
    # user_id = event.user.id
    data = event.callback.payload
    print(f'data: {data}')
    
    if not data:
        return
    
    # Обработка главного меню
    if data.startswith("menu:"):
        action = data.split(":")[1]
        
        if action == "MAIN" or action == "BACK_TO_MAIN":
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text="🏠 *Главное меню*\n\nВыберите устройство:",
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
                        text += f"• {doc['number']} - {doc['name'][:40]}\n"
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
        
        elif action in MAIN_MENU_BUTTONS.values():
            device_name = [k for k, v in MAIN_MENU_BUTTONS.items() if v == action][0]
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=f"📁 *{device_name}*\n\nВыберите тип работы:",
                attachments =[get_actions_menu(device_name)]
            )
            # time.sleep(2)
    
    # Обработка выбора вида работ
    elif data.startswith("action:"):
        parts = data.split(":")
        print(f'data: {data}')
        print(f'parts: {parts}')
        if len(parts) >= 3:
            _, device, action_code = parts[:3]
            
            action_name = None
            for text, code in ACTION_BUTTONS.items():
                if code == action_code:
                    action_name = text
                    break
            
            if action_name:
                print('action name')
                docs = doc_loader.get_documents(device, action_name, limit=ITEMS_PER_PAGE, offset=0)
                total = doc_loader.get_documents_count(device, action_name)
                has_more = len(docs) == ITEMS_PER_PAGE
                
                if docs:
                    await event.bot.edit_message(
                        message_id=event.message.body.mid,
                        text=f"📄 *{device} → {action_name}*\n\nНайдено: {total} документов",
                        attachments = [get_documents_menu(docs, device, action_code, 0, total, has_more)]
                    )
                else:
                    await event.bot.edit_message(
                        message_id=event.message.body.mid,
                        text=f"📄 *{device} → {action_name}*\n\n❌ Документы не найдены",
                        attachments = [get_back_keyboard()]
                    )
    
    # Обработка пагинации
    elif data.startswith("page:"):
        parts = data.split(":")
        if len(parts) >= 4:
            _, device, action_code, page_str = parts[:4]
            page = int(page_str)
            
            action_name = None
            for text, code in ACTION_BUTTONS.items():
                if code == action_code:
                    action_name = text
                    break
            
            if action_name:
                docs = doc_loader.get_documents(device, action_name, limit=ITEMS_PER_PAGE, offset=page * ITEMS_PER_PAGE)
                total = doc_loader.get_documents_count(device, action_name)
                has_more = len(docs) == ITEMS_PER_PAGE
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"📄 *{device} → {action_name}*\n\nНайдено: {total} документов",
                    attachments = [get_documents_menu(docs, device, action_code, page, total, has_more)]
                    # reply_markup=get_documents_menu(docs, device, action_code, page, total, has_more)
                )
    
    # Обработка выбора документа
    elif data.startswith("doc:"):
        doc_id = int(data.split(":")[1])
        doc = doc_loader.get_document_by_id(doc_id)
        
        if doc:
            # Сохраняем в историю
            if user_id not in user_history:
                user_history[user_id] = []
            if doc_id not in user_history[user_id]:
                user_history[user_id].append(doc_id)
                if len(user_history[user_id]) > 50:
                    user_history[user_id] = user_history[user_id][-50:]
            
            is_favorite = user_id in user_favorites and doc_id in user_favorites[user_id]
            
            text = (
                f"📄 *{doc['file_name']}*\n\n"
                # f"📄 *{doc['number']}*\n\n"
                f"🏷️ *Название:* {doc['name']}\n"
                f"👥 *Исполнители:* {doc['executors']}\n"
                f"📋 *Оформление:* {doc['design']}\n"
                f"📅 *Введён:* {doc['order_number']}\n\n"
                # f"📅 *Введён:* {doc['date']}\n\n"
                f"⬇️ Нажмите «Скачать файл» для получения документа."
            )
            
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=text,
                attachments = [get_document_card(doc, is_favorite)]
            )
    
    # Обработка скачивания
    elif data.startswith("download:"):
        print('download')
        doc_id = int(data.split(":")[1])
        print(f'doc_id: {doc_id}')
        doc = doc_loader.get_document_by_id(doc_id)
        # print(doc)
        
        if doc and doc.get('file_name'):
            file_path = os.path.join(PDF_FOLDER, doc['file_name'])
            original_file_path = os.path.join(PDF_FOLDER, doc['file_name'])
            print(f'original_file_path: {original_file_path}')
            simplified_path = simplify_pdf_filename_v2(original_file_path) 
            print(f'simplified_path: {simplified_path}')
            if os.path.exists(simplified_path):
                file_path = simplified_path
                print(f'file_path: {file_path}')
            elif os.path.exists(original_file_path):
                file_path = original_file_path
                print(f'file_path: {file_path}')
            else:
            # Файл не найден
                await event.answer(f"❌ Файл не найден")
            
            if os.path.exists(file_path):
                try:
                    # В MAX для отправки файла используется send_file
                    doc_number = doc.get('file_name', doc.get('number', 'Документ'))
                    print(f'doc_number: {doc_number}')
                    await event.bot.send_file(
                        chat_id=chat_id,
                        file_path=file_path,
                        filename=doc['file_name'],
                        caption=f"📎 {doc_number}\n{doc.get('name', 'Без названия')}"
                        # caption=f"📎 {doc['number']}\n{doc['name']}"
                    )
                    print('типо файл отправлен!')
                    await event.answer("✅ Файл отправлен")
                except Exception as e:
                    logger.error(f"Ошибка отправки файла: {e}")
                    await event.answer("❌ Ошибка при отправке файла")
            else:
                print(f"❌ Файл не найден: {doc['file_name']}")
                await event.answer(f"❌ Файл не найден: {doc['file_name']}")
    
    # Обработка избранного
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
            
            # Обновляем карточку
            doc = doc_loader.get_document_by_id(doc_id)
            if doc:
                is_favorite = doc_id in user_favorites.get(user_id, [])
                await event.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=event.message.message_id,
                    attachments = [get_document_card(doc, is_favorite)]
                    # reply_markup=get_document_card(doc, is_favorite)
                )
    
    # Возврат к видам работ
    elif data.startswith("back_to_actions:"):
        device = data.split(":")[1]
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=f"📁 *{device}*\n\nВыберите тип работы:",
            attachments = [get_actions_menu(device)]
            # reply_markup=get_actions_menu(device)
        )
    
    elif data.startswith("back_to_list"):
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text="🔙 Возврат к предыдущему списку..."
        )
    
    # Обработка поиска
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
                    attachments = [get_search_number_keyboard()]
                )
            
            elif action == "backspace":
                current = search_states.get(user_id, "")
                new_number = current[:-1]
                search_states[user_id] = new_number
                
                await event.bot.edit_message(
                    message_id=event.message.body.mid,
                    text=f"🔢 *Поиск по номеру*\n\nВведите номер: `{new_number}`\n\nИспользуйте клавиатуру:",
                    attachments = [get_search_number_keyboard()]
                )
            
            elif action == "submit":
                search_number = search_states.get(user_id, "")
                
                if search_number:
                    results = doc_loader.search_by_number(search_number)
                    
                    if results:
                        text = f"🔍 *Результаты поиска по номеру «{search_number}»:*\n\n"
                        for doc in results[:15]:
                            text += f"📄 {doc['number']}\n   {doc['name'][:50]}\n\n"
                        
                        # Создаём клавиатуру с результатами
                        buttons = []
                        for doc in results[:10]:
                            buttons.append([InlineKeyboardButton(
                                text=f"{doc['number']}",
                                callback_data=f"doc:{doc['id']}"
                            )])
                        buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:MAIN")])
                        
                        await event.bot.edit_message(
                            message_id=event.message.body.mid,
                            text=text,
                            attachments = [InlineKeyboardMarkup(inline_keyboard=buttons)]
                        )
                    else:
                        await event.bot.edit_message(
                            message_id=event.message.body.mid,
                            text=f"❌ *Ничего не найдено* по номеру «{search_number}»\n\nПопробуйте снова:",
                            attachments = [get_main_menu()]
                        )
                    
                    del search_states[user_id]
    
    # await event.answer()