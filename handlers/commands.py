# handlers/commands.py
from maxapi.types import BotStarted, Command, MessageCreated
from keyboards import get_main_menu, get_help_keyboard


# async def bot_started(event: BotStarted):
#     await event.bot.send_message(
#         chat_id=event.chat_id,
#         text="🔧 *Система поиска ТНК/КТП*\n\n"
#              "📋 Инструкция ОАО «РЖД» №3168р\n"
#              "👇 Выберите категорию:",
#         attachments=[get_main_menu()]
#     )


async def cmd_start(event: MessageCreated):
    await event.message.answer(
        text="🔧 *Система поиска ТНК/КТП*\n\n👇 Выберите категорию:",
        attachments=[get_main_menu()]
    )


async def cmd_help(event: MessageCreated):
    help_text = (
        "ℹ️ *Помощь*\n\n"
        "🔹 *Навигация:* кнопки меню\n"
        "🔹 *Поиск:* по номеру или названию\n"
        "🔹 *Скачивание:* нажмите на документ → «Скачать файл»\n"
        "🔹 *Избранное:* ⭐ в карточке документа"
    )
    await event.message.answer(text=help_text, attachments=[get_help_keyboard()])
    