# logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Конфигурация форматирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Создаём директорию для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Имя файла лога с датой
LOG_FILE = LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(
    name: str = "max_bot",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Настройка логгера с выводом в консоль и файл
    
    Args:
        name: Имя логгера
        level: Уровень логирования (logging.INFO, DEBUG, ERROR и т.д.)
        log_to_file: Записывать ли в файл
        log_to_console: Выводить ли в консоль
        log_file: Путь к файлу лога (если None, используется стандартный)
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Очищаем существующие обработчики, чтобы избежать дублирования
    if logger.handlers:
        logger.handlers.clear()
    
    # Форматтер
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Вывод в консоль
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Вывод в файл
    if log_to_file:
        file_handler = logging.FileHandler(
            log_file or LOG_FILE,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер по имени (создаёт новый, если не существует)
    """
    return logging.getLogger(name)


# Создаём основной логгер для бота
main_logger = setup_logger("max_bot", log_to_file=True, log_to_console=True)


# Декоратор для логирования ошибок в функциях
def log_error(logger: logging.Logger):
    """Декоратор для логирования ошибок в функциях"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# Контекстный менеджер для замера времени выполнения
import time
from contextlib import contextmanager

@contextmanager
def log_execution_time(logger: logging.Logger, operation_name: str):
    """Контекстный менеджер для замера времени выполнения операции"""
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.debug(f"{operation_name} выполнена за {elapsed:.3f} сек")