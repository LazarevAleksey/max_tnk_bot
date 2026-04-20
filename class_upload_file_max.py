# class_upload_file_max.py
import requests
import time
from config_links import FILES_CONFIG


TIME_UPLOAD_FILE_SERVER = 0.5

class MaxBot:
    def __init__(self, auth_token):
        self.base_url = "https://platform-api.max.ru"
        self.auth_token = auth_token
        self.headers = {
            "Authorization": self.auth_token,
        }
    
    def upload_file(self, file_path):
        """Шаг 1: Получение URL для загрузки файла"""
        print("📤 Запрашиваю URL для загрузки файла...")
        
        upload_url = f"{self.base_url}/uploads?type=file"
        response = requests.post(upload_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Ошибка при получении URL: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
        
        data = response.json()
        file_upload_url = data.get("url")
        
        if not file_upload_url:
            print("❌ Не удалось получить URL для загрузки")
            print(f"Ответ: {data}")
            return None
        
        print(f"✅ URL получен: {file_upload_url[:100]}...")
        return file_upload_url
    
    def send_file_to_storage(self, upload_url, file_path):
        """Шаг 2: Загрузка файла в хранилище"""
        print(f"📁 Загружаю файл: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'data': (file_path, f, 'application/octet-stream')}
            response = requests.post(upload_url, files=files)
        
        if response.status_code != 200:
            print(f"❌ Ошибка при загрузке файла: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
        
        result = response.json()
        file_id = result.get("fileId")
        token = result.get("token")
        
        if not token:
            print("❌ Не удалось получить токен файла")
            print(f"Ответ: {result}")
            return None
        
        print(f"✅ Файл загружен!")
        print(f"   File ID: {file_id}")
        print(f"   Token: {token[:50]}...")
        
        return {
            "file_id": file_id,
            "token": token
        }
    
    def send_message_with_file(self, user_id, text, file_token):
        """Шаг 3: Отправка сообщения с файлом пользователю"""
        print(f"💬 Отправляю сообщение пользователю {user_id}...")
        # Даём время на обработку файла на сервере
        print(f"⏳ Ждём {TIME_UPLOAD_FILE_SERVER} секунды перед отправкой...")
        time.sleep(TIME_UPLOAD_FILE_SERVER)
        
        url = f"{self.base_url}/messages?user_id={user_id}"
        
        payload = {
            "text": text,
            "attachments": [
                {
                    "type": "file",
                    "payload": {"token": file_token}
                }
            ]
        }
        
        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("✅ Сообщение успешно отправлено!")
            return True
        else:
            print(f"❌ Ошибка при отправке сообщения: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
    
    def send_file_to_user(self, user_id, file_path, message_text=None):
        """Полный процесс: загрузка и отправка файла пользователю"""
        # Если message_text не передан, берем из конфига
        if message_text is None:
            file_info = FILES_CONFIG.get(file_path, {})
            message_text = file_info.get("message_text", "Файл")
        
        print("🚀 Начинаю отправку файла...")
        print(f"👤 Пользователь: {user_id}")
        print(f"📄 Файл: {file_path}")
        print(f"💬 Текст: {message_text}")
        print("-" * 50)
        
        # Шаг 1: Получаем URL для загрузки
        upload_url = self.upload_file(file_path)
        if not upload_url:
            return False
        
        # Шаг 2: Загружаем файл и получаем токен
        file_info = self.send_file_to_storage(upload_url, file_path)
        if not file_info:
            return False
        
        # Шаг 3: Отправляем сообщение с файлом
        success = self.send_message_with_file(user_id, message_text, file_info["token"])
        
        return success


def main():
    # Ваши данные (теперь можно брать из конфига)
    from config_links import BOT_TOKEN, ADMIN_USER_IDS, FILES_CONFIG
    
    AUTH_TOKEN = BOT_TOKEN
    USER_ID = ADMIN_USER_IDS[0]  # Берем первого админа
    FILE_PATH = "opis.pdf"  # Путь к вашему файлу
    MESSAGE_TEXT = FILES_CONFIG.get(FILE_PATH, {}).get("message_text", "opis_4_gorka")
    
    # Создаем экземпляр бота
    bot = MaxBot(AUTH_TOKEN)
    
    # Отправляем файл
    result = bot.send_file_to_user(USER_ID, FILE_PATH, MESSAGE_TEXT)
    
    if result:
        print("\n🎉 Готово! Файл отправлен успешно.")
    else:
        print("\n❌ Произошла ошибка при отправке файла.")


if __name__ == "__main__":
    main()