#!/usr/bin/env python3
import asyncio
import logging
import sys
from maxapi import Bot

from config import BOT_TOKEN
from handlers import dp  # ← импорт из папки handlers
from logger import setup_logger  # ← импортируем



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# logger = logging.getLogger(__name__)
# Настройка глобального логгера
logger = setup_logger("bot", log_to_file=True, log_to_console=True)



async def main():
    if not BOT_TOKEN:
        logger.error("MAX_BOT_TOKEN не найден!")
        return
    logger.info("Запуск бота...")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")