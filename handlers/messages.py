# handlers/messages.py
import logging
from maxapi.types import MessageCreated
from models.session import get_session
from data_loader import doc_loader
from .navigation import show_search_results

logger = logging.getLogger(__name__)


async def handle_text_input(event: MessageCreated):
    chat_id, user_id = event.get_ids()
    text = event.message.body.text.strip()
    
    session = get_session(user_id)
    
    # Поиск по тексту (если ожидаем)
    if session.search_state and session.search_state.mode == "text":
        logger.info(f"🔍 Поиск по тексту: {text}")
        results = doc_loader.search_by_text(text)
        logger.info(f"Найдено результатов: {len(results)}")
        
        if results:
            session.search_results = results
            session.search_page = 0
            session.search_mode = "text"
            session.search_query = text
            await show_search_results(event, user_id, text, 0)
        else:
            await event.message.answer(f"❌ Ничего не найдено по запросу «{text}»")
        
        session.search_state = None
        return
    
    # Ввод номера документа из списка
    if session.docs_list and text.isdigit():
        doc_num = int(text)
        docs = session.docs_list
        
        if 1 <= doc_num <= len(docs):
            doc = docs[doc_num - 1]
            
            # Добавляем в историю
            if doc['id'] not in session.history:
                session.history.append(doc['id'])
                if len(session.history) > 50:
                    session.history = session.history[-50:]
            
            is_favorite = doc['id'] in session.favorites
            
            from keyboards import get_document_card
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
        return
    
    # Обычный поиск по номеру
    results = doc_loader.search_by_number(text)
    if results:
        session.search_results = results
        session.search_page = 0
        session.search_mode = "number"
        session.search_query = text
        await show_search_results(event, user_id, text, 0)
    else:
        docs_len = len(session.docs_list)
        await event.message.answer(
            f"❌ Ничего не найдено.\n\n"
            f"Введите номер документа из списка (1-{docs_len})\n"
            f"или номер ТНК/КТП для поиска."
        )