#!/usr/bin/env python3
import asyncio
import logging
import sys
from maxapi import Bot

from config import BOT_TOKEN
from handlers import dp


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Запуск бота в MAX"""
    if not BOT_TOKEN:
        logger.error("MAX_BOT_TOKEN не найден в переменных окружения!")
        print("❌ Ошибка: MAX_BOT_TOKEN не найден!")
        print("Создайте файл .env и добавьте: MAX_BOT_TOKEN=ваш_токен")
        return
    
    logger.info("Запуск бота в MAX...")
    
    # Создаём бота
    bot = Bot(token=BOT_TOKEN)
    print("Токен передан в бота")
    
    # Запускаем polling (удаляем webhook если был)
    # await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")