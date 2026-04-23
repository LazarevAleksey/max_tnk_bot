# services/file_sender.py (переименовать из class_upload_file_max.py)
import aiohttp
import asyncio
from typing import Optional
from config import BOT_TOKEN, FILES_CONFIG

TIME_UPLOAD_FILE_SERVER = 0.5


class FileSender:
    def __init__(self, auth_token: str | None = BOT_TOKEN):
        if auth_token is None:
            raise ValueError("auth_token cannot be None")
        self.auth_token = auth_token
        self.base_url = "https://platform-api.max.ru"
    
    async def upload_file(self, file_path: str) -> str | None:
        """Шаг 1+2: Получение URL и загрузка файла"""
        async with aiohttp.ClientSession() as session:
            # Получаем URL для загрузки
            async with session.post(
                f"{self.base_url}/uploads?type=file",
                headers={"Authorization": self.auth_token}
            ) as resp:
                if resp.status != 200:
                    print(f"❌ Ошибка при получении URL: {resp.status}")
                    return None
                data = await resp.json()
                upload_url = data.get("url")

            print(f"✅ URL получен")

            # Загружаем файл
            print(f"📁 Загружаю файл: {file_path}")
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('data', f)
                async with session.post(upload_url, data=form) as resp:
                    if resp.status != 200:
                        print(f"❌ Ошибка при загрузке файла: {resp.status}")
                        return None
                    result = await resp.json()
                    token = result.get("token")
                    if token:
                        print(f"✅ Файл загружен, токен получен")
                    return token
    
    async def send_message_with_file(self, user_id: int, text: str, file_token: str) -> bool:
        """Шаг 3: Отправка сообщения с файлом"""
        await asyncio.sleep(TIME_UPLOAD_FILE_SERVER)
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": text,
                "attachments": [{"type": "file", "payload": {"token": file_token}}]
            }
            headers = {
                "Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            async with session.post(
                f"{self.base_url}/messages?user_id={user_id}",
                headers=headers,
                json=payload
            ) as resp:
                return resp.status == 200
    
    async def send_file_to_user(self, user_id: int, file_path: str, message_text: Optional[str] = None) -> bool:
        """Полный процесс: загрузка и отправка файла"""
        if message_text is None:
            file_info = FILES_CONFIG.get(file_path, {})
            message_text = file_info.get("message_text", "Файл")
        
        file_token = await self.upload_file(file_path)
        if not file_token:
            return False
        
        return await self.send_message_with_file(user_id, message_text, file_token)
    