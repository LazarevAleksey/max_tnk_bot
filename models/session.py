# models/session.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class UserSearchState:
    """Состояние поиска пользователя"""
    mode: str = "number"  # "text" or "number"
    value: str = ""


@dataclass
class UserSession:
    """Сессия пользователя"""
    favorites: List[int] = field(default_factory=list)
    history: List[int] = field(default_factory=list)
    last_device: Optional[str] = None
    current_page: int = 0
    docs_list: List[Dict] = field(default_factory=list)
    search_state: Optional[UserSearchState] = None
    search_results: List[Dict] = field(default_factory=list)
    search_page: int = 0
    search_mode: Optional[str] = None
    search_query: str = ""
    search_message_id: Optional[str] = None


# Глобальное хранилище
_sessions: Dict[int, UserSession] = {}


def get_session(user_id: int) -> UserSession:
    """Получить или создать сессию пользователя"""
    if user_id not in _sessions:
        _sessions[user_id] = UserSession()
    return _sessions[user_id]


def get_search_state(user_id: int) -> UserSearchState:
    """Получить состояние поиска пользователя"""
    session = get_session(user_id)
    if session.search_state is None:
        session.search_state = UserSearchState()
    return session.search_state