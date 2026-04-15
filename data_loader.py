import openpyxl
import os
import json
from typing import List, Dict, Optional
from config import EXCEL_PATH

class DocumentLoader:
    def __init__(self):
        self.documents = []
        self.load_data()
    
    def load_data(self):
        print('load_data')
        """Загружает данные из Excel-файла без pandas"""
        if not os.path.exists(EXCEL_PATH):
            print(f"⚠️ Файл {EXCEL_PATH} не найден. Создаю тестовую структуру...")
            self.create_sample_data()
            return
        
        try:
            # Загружаем Excel через openpyxl
            workbook = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
            sheet = workbook.active
            
            # Получаем заголовки (первая строка)
            headers = []
            for cell in sheet[1]:
                if cell.value:
                    headers.append(str(cell.value).strip())
                else:
                    headers.append(f"col_{len(headers)}")
            
            # Читаем данные со 2 строки
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                # Пропускаем полностью пустые строки
                if not any(row):
                    continue
                
                doc = {}
                for i, header in enumerate(headers):
                    if i < len(row) and row[i] is not None:
                        value = row[i]
                        # Преобразуем числа в строки если нужно
                        if isinstance(value, (int, float)) and header not in ['id']:
                            value = str(value)
                        doc[header] = value
                
                # Добавляем ID если нет
                if 'id' not in doc or not doc['id']:
                    doc['id'] = len(self.documents) + 1
                
                # Пропускаем документы без названия
                if doc.get('name'):
                    self.documents.append(doc)
            
            print(f"✅ Загружено {len(self.documents)} документов из {EXCEL_PATH}")
            workbook.close()
            
        except Exception as e:
            print(f"❌ Ошибка загрузки Excel: {e}")
            print("📝 Создаю тестовые данные...")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Создаёт тестовые данные для демонстрации"""
        self.documents = [
            {
                'id': 1,
                'device': 'Светофоры',
                'action': 'Замена',
                'number': 'ТНК ЦП 0077-2017',
                'name': 'Смена ламп линзовых светофоров',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-61',
                'date': '02.10.2023',
                'order_number': 'ИСХ-43687/ЦДИ',
                'file_name': 'ТНК_ЦП_0077-2017.pdf',
                'instruction_point': '1.1.4, 1.5'
            },
            {
                'id': 2,
                'device': 'Светофоры',
                'action': 'Замена',
                'number': 'ТНК ЦП 0111-2022',
                'name': 'Замена светодиодного модуля',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-61, ДУ-46',
                'date': '18.07.2022',
                'order_number': 'ИСХ-32333/ЦДИ',
                'file_name': 'ТНК_ЦП_0111-2022.pdf',
                'instruction_point': '2'
            },
            {
                'id': 3,
                'device': 'Светофоры',
                'action': 'Замена',
                'number': 'КТП ЦП 1024-2019',
                'name': 'Замена линзового комплекта или ССС',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-61, ДУ-46',
                'date': '29.05.2019',
                'order_number': 'ИСХ-20449/ЦДИ',
                'file_name': 'КТП_ЦП_1024-2019.pdf',
                'instruction_point': '2'
            },
            {
                'id': 4,
                'device': 'Светофоры',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0147-2022',
                'name': 'Проверка видимости сигнальных огней',
                'executors': 'ШНС, ШН',
                'design': 'ДУ-46',
                'date': '18.07.2022',
                'order_number': 'ИСХ-32333/ЦДИ',
                'file_name': 'ТНК_ЦП_0147-2022.pdf',
                'instruction_point': '1.2'
            },
            {
                'id': 5,
                'device': 'Светофоры',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0167-2019',
                'name': 'Проверка с локомотива видимости огней',
                'executors': 'ШНС, машинист',
                'design': 'Акт ШУ-60',
                'date': '01.11.2019',
                'order_number': 'ИСХ-42983/ЦДИ',
                'file_name': 'ТНК_ЦП_0167-2019.pdf',
                'instruction_point': '1.3'
            },
            {
                'id': 6,
                'device': 'Стрелки ЭЦ',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0001-2017',
                'name': 'Проверка состояния электроприводов и гарнитур',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-2, ДУ-46',
                'date': '2017',
                'order_number': '',
                'file_name': 'ТНК_ЦП_0001-2017.pdf',
                'instruction_point': '2.1.1'
            },
            {
                'id': 7,
                'device': 'Стрелки ЭЦ',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0124-2015',
                'name': 'Проверка электроприводов с внешними замыкателями',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-2, ДУ-46',
                'date': '27.05.2015',
                'order_number': 'ЦПЦ-4/119',
                'file_name': 'ТНК_ЦП_0124-2015.pdf',
                'instruction_point': '2.1.1'
            },
            {
                'id': 8,
                'device': 'Рельсовые цепи',
                'action': 'Измерение',
                'number': 'ТНК ЦП 0180-2022',
                'name': 'Измерение напряжения на путевых рельсовых цепей',
                'executors': 'ШН',
                'design': 'ШУ-64, ШУ-79',
                'date': '18.07.2022',
                'order_number': 'ИСХ-32333/ЦДИ',
                'file_name': 'ТНК_ЦП_0180-2022.pdf',
                'instruction_point': '3.5'
            },
            {
                'id': 9,
                'device': 'Рельсовые цепи',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0176-2020',
                'name': 'Проверка состояния изолирующих элементов',
                'executors': 'ШН, ПДБ',
                'design': 'ДУ-46, ШУ-2',
                'date': '07.09.2020',
                'order_number': 'ИСХ-35450/ЦДИ',
                'file_name': 'ТНК_ЦП_0176-2020.pdf',
                'instruction_point': '3.1'
            },
            {
                'id': 10,
                'device': 'Переезд (АПС)',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0882-2019',
                'name': 'Техническое обслуживание АПС',
                'executors': 'ШН, ШЦМ',
                'design': 'ПУ-67, ШУ-2, ШУ-63',
                'date': '27.09.2019',
                'order_number': 'ИСХ-37586/ЦДИ',
                'file_name': 'ТНК_ЦП_0882-2019.pdf',
                'instruction_point': '9.1.1'
            },
            {
                'id': 11,
                'device': 'Питание / АКБ',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0522-2016',
                'name': 'Внешний осмотр питающей установки',
                'executors': 'ШНС, ШН',
                'design': 'ШУ-2',
                'date': '18.08.2016',
                'order_number': '',
                'file_name': 'ТНК_ЦП_0522-2016.pdf',
                'instruction_point': '11.1.2'
            },
            {
                'id': 12,
                'device': 'Кабельная сеть',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0591-2018',
                'name': 'Осмотр трассы подземных кабелей',
                'executors': 'ШН, ШЦМ',
                'design': 'ШУ-2',
                'date': '31.08.2018',
                'order_number': 'ИСХ-35836/ЦДИ',
                'file_name': 'ТНК_ЦП_0591-2018.pdf',
                'instruction_point': '10.1.1'
            },
            {
                'id': 13,
                'device': 'МПЦ / ДЦ / ПО',
                'action': 'Проверка',
                'number': 'ТНК ЦП 0138-2015',
                'name': 'Проверка управляющего комплекса',
                'executors': 'ШН',
                'design': 'ШУ-2',
                'date': '13.07.2015',
                'order_number': 'ИСХ-25032/ЦДИ',
                'file_name': 'ТНК_ЦП_0138-2015.pdf',
                'instruction_point': '7.1'
            }
        ]
        print(f"✅ Создано {len(self.documents)} тестовых документов")
    
    def get_devices(self) -> List[str]:
        """Возвращает список уникальных устройств"""
        devices = set()
        for doc in self.documents:
            device = doc.get('device')
            if device:
                devices.add(device)
        return sorted(list(devices))
    
    def get_actions(self, device: str) -> List[str]:
        """Возвращает виды работ для устройства"""
        actions = set()
        for doc in self.documents:
            if doc.get('device') == device:
                action = doc.get('action')
                if action:
                    actions.add(action)
        return sorted(list(actions))
    
    def get_documents(self, device: str = None, action: str = None, 
                      limit: int = 10, offset: int = 0) -> List[Dict]:
        """Возвращает список документов с фильтрацией и пагинацией"""
        print('get_documents')
        def clean_value(value):
            if not value:
                return value
            # Удаляем эмодзи (🚦, ✅ и т.д.) и лишние пробелы
            import re
            # Удаляем все emoji (простой способ)
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # смайлики
                u"\U0001F300-\U0001F5FF"  # символы
                u"\U0001F680-\U0001F6FF"  # транспорт
                u"\U0001F1E0-\U0001F1FF"  # флаги
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE)
            cleaned = emoji_pattern.sub('', value).strip()
            return cleaned
        print(f'device: {device}, action: {action}')
        filtered = self.documents
        # print(f'filtered: {filtered}')
        
        if device:
            clean_device = clean_value(device)
            filtered = [d for d in filtered if d.get('device') == clean_device]
        
        if action:
            clean_action = clean_value(action)
            filtered = [d for d in filtered if d.get('action') == clean_action]
        # print(f'filtered_after: {filtered}')
        return filtered[offset:offset+limit]
    
    def get_documents_count(self, device: str = None, action: str = None) -> int:
        """Возвращает количество документов по фильтру"""
        filtered = self.documents
        
        if device:
            filtered = [d for d in filtered if d.get('device') == device]
        
        if action:
            filtered = [d for d in filtered if d.get('action') == action]
        
        return len(filtered)
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Возвращает документ по ID"""
        print('get_document_by_id')
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return doc
        return None
    
    def search_by_number(self, query: str) -> List[Dict]:
        """Поиск по номеру документа"""
        query_lower = query.lower().strip()
        results = []
        
        for doc in self.documents:
            number = doc.get('number', '')
            if query_lower in number.lower():
                results.append(doc)
        
        return results[:20]
    
    def search_by_text(self, query: str) -> List[Dict]:
        """Поиск по тексту названия"""
        query_lower = query.lower().strip()
        results = []
        
        for doc in self.documents:
            name = doc.get('name', '')
            if query_lower in name.lower():
                results.append(doc)
        
        return results[:20]
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику по документам"""
        devices = self.get_devices()
        stats = {
            'total': len(self.documents),
            'devices': {},
            'actions': {}
        }
        
        for device in devices:
            stats['devices'][device] = self.get_documents_count(device=device)
        
        all_actions = set()
        for doc in self.documents:
            action = doc.get('action')
            if action:
                all_actions.add(action)
        
        for action in sorted(all_actions):
            stats['actions'][action] = self.get_documents_count(action=action)
        
        return stats

# Глобальный экземпляр
doc_loader = DocumentLoader()

# Выводим статистику при загрузке
if __name__ == "__main__":
    stats = doc_loader.get_statistics()
    print(f"\n📊 Статистика:")
    print(f"   Всего документов: {stats['total']}")
    print(f"   Устройств: {len(stats['devices'])}")
    print(f"   Типов работ: {len(stats['actions'])}")