# handlers/__init__.py
from maxapi import Dispatcher
from maxapi.types import Command
from .commands import  cmd_start, cmd_help # bot_started
from .callbacks import handle_callback
from .messages import handle_text_input

dp = Dispatcher()

# Регистрируем обработчики
# dp.bot_started()(bot_started)
dp.message_created(Command('start'))(cmd_start)
dp.message_created(Command('help'))(cmd_help)
dp.message_callback()(handle_callback)
dp.message_created()(handle_text_input)

__all__ = ['dp']