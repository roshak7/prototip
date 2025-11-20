from django.core.management.base import BaseCommand
from dashboard.models import Shop, InventoryCategory, InventoryItem, InventoryRecord
import random
from datetime import date, timedelta


class Command(BaseCommand):
    """
    Команда управления Django для заполнения базы данных фейковыми складскими данными.
    
    Создает категории, позиции и остатки для склада.
    """
    help = 'Заполнение базы данных фейковыми складскими данными'

    def handle(self, *args, **kwargs):
        """
        Основной метод выполнения команды.
        """
        # Создание категорий складских позиций
        categories_data = [
            {"name": "Автоматические выключатели", "description": "Автоматические выключатели для защиты электрических цепей"},
            {"name": "Розетки и выключатели", "description": "Розетки, выключатели и рамки для электромонтажа"},
            {"name": "Провода и кабели", "description": "Электрические провода и кабели различного сечения"},
            {"name": "Щитовое оборудование", "description": "Щиты, DIN-рейки, клеммы, предохранители"},
            {"name": "Осветительное оборудование", "description": "Лампы, светильники, прожекторы"},
            {"name": "Измерительные приборы", "description": "Мультиметры, амперметры, вольтметры"},
            {"name": "Комплектующие для шкафов", "description": "Ручки, замки, вентиляторы для шкафов"},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = InventoryCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "description": cat_data["description"]
                }
            )
            categories.append(category)
        
        self.stdout.write(f'Создано/обновлено {len(categories)} категорий')

        # Создание складских позиций
        items_data = [
            # Автоматические выключатели
            {"category": categories[0], "name": "Автоматический выключатель 1P 16A", "sku": "AV-1P-16A", "unit": "pcs"},
            {"category": categories[0], "name": "Автоматический выключатель 1P 25A", "sku": "AV-1P-25A", "unit": "pcs"},
            {"category": categories[0], "name": "Автоматический выключатель 3P 32A", "sku": "AV-3P-32A", "unit": "pcs"},
            {"category": categories[0], "name": "Дифференциальный автомат 2P 16A", "sku": "DA-2P-16A", "unit": "pcs"},
            {"category": categories[0], "name": "Дифференциальный автомат 4P 25A", "sku": "DA-4P-25A", "unit": "pcs"},
            
            # Розетки и выключатели
            {"category": categories[1], "name": "Розетка однофазная с заземлением", "sku": "RZ-1F-Z", "unit": "pcs"},
            {"category": categories[1], "name": "Выключатель одноклавишный", "sku": "VK-1", "unit": "pcs"},
            {"category": categories[1], "name": "Выключатель двухклавишный", "sku": "VK-2", "unit": "pcs"},
            {"category": categories[1], "name": "Выключатель трехклавишный", "sku": "VK-3", "unit": "pcs"},
            {"category": categories[1], "name": "Рамка одноклавишная", "sku": "RK-1", "unit": "pcs"},
            
            # Провода и кабели
            {"category": categories[2], "name": "Провод ВВГнг 3x2.5", "sku": "VVGN-3x2.5", "unit": "m"},
            {"category": categories[2], "name": "Провод ВВГнг 5x4", "sku": "VVGN-5x4", "unit": "m"},
            {"category": categories[2], "name": "Кабель КГ 3x1.5", "sku": "KG-3x1.5", "unit": "m"},
            {"category": categories[2], "name": "Кабель КГ 4x2.5", "sku": "KG-4x2.5", "unit": "m"},
            {"category": categories[2], "name": "Провод СИП 4x16", "sku": "SIP-4x16", "unit": "m"},
            
            # Щитовое оборудование
            {"category": categories[3], "name": "Щит распределительный 12 модулей", "sku": "SH-12", "unit": "pcs"},
            {"category": categories[3], "name": "DIN-рейка 35мм 1м", "sku": "DIN-1M", "unit": "m"},
            {"category": categories[3], "name": "Клеммы Phoenix 2P 10A", "sku": "KL-PH-2P-10A", "unit": "pcs"},
            {"category": categories[3], "name": "Предохранитель ножевой ПН2", "sku": "PN-2", "unit": "pcs"},
            {"category": categories[3], "name": "Шина PE 32A", "sku": "SH-PE-32A", "unit": "pcs"},
            
            # Осветительное оборудование
            {"category": categories[4], "name": "Лампа светодиодная 12W", "sku": "LED-12W", "unit": "pcs"},
            {"category": categories[4], "name": "Лампа светодиодная 20W", "sku": "LED-20W", "unit": "pcs"},
            {"category": categories[4], "name": "Светильник точечный", "sku": "SV-TCH", "unit": "pcs"},
            {"category": categories[4], "name": "Прожектор светодиодный 50W", "sku": "PR-50W", "unit": "pcs"},
            {"category": categories[4], "name": "Лента светодиодная 5м", "sku": "LED-LN-5M", "unit": "m"},
            
            # Измерительные приборы
            {"category": categories[5], "name": "Мультиметр цифровой", "sku": "MM-CIF", "unit": "pcs"},
            {"category": categories[5], "name": "Амперметр аналоговый 10A", "sku": "AM-10A", "unit": "pcs"},
            {"category": categories[5], "name": "Вольтметр цифровой", "sku": "VM-CIF", "unit": "pcs"},
            {"category": categories[5], "name": "Тестер прозвонки", "sku": "TP-PRZ", "unit": "pcs"},
            {"category": categories[5], "name": "Измеритель RCD", "sku": "IZM-RCD", "unit": "pcs"},
            
            # Комплектующие для шкафов
            {"category": categories[6], "name": "Ручка дверная", "sku": "RK-DOOR", "unit": "pcs"},
            {"category": categories[6], "name": "Замок навесной", "sku": "ZM-NAV", "unit": "pcs"},
            {"category": categories[6], "name": "Вентилятор 12V 0.5A", "sku": "VENT-12V", "unit": "pcs"},
            {"category": categories[6], "name": "Уголок металлический", "sku": "UG-MET", "unit": "pcs"},
            {"category": categories[6], "name": "Крепеж М4x20", "sku": "KR-M4x20", "unit": "pack"},
        ]
        
        items = []
        for item_data in items_data:
            item, created = InventoryItem.objects.get_or_create(
                sku=item_data["sku"],
                defaults={
                    "category": item_data["category"],
                    "name": item_data["name"],
                    "unit": item_data["unit"]
                }
            )
            items.append(item)
        
        self.stdout.write(f'Создано/обновлено {len(items)} складских позиций')

        # Получаем все цеха
        shops = list(Shop.objects.all())
        if not shops:
            self.stdout.write(self.style.ERROR('Не найдены цеха. Сначала создайте цеха.'))
            return
        
        # Создаем записи остатков для каждой позиции по каждому цеху
        start_date = date(2025, 4, 1)
        end_date = date(2025, 4, 30)
        current_date = start_date
        
        total_records = 0
        while current_date <= end_date:
            for shop in shops:
                for item in items:
                    # Генерируем случайные остатки
                    quantity = random.randint(0, 1000)  # Общее количество
                    reserved = random.randint(0, quantity // 2)  # Зарезервировано (до половины от общего)
                    min_threshold = random.randint(10, 100)  # Минимальный порог
                    
                    InventoryRecord.objects.create(
                        item=item,
                        shop=shop,
                        date=current_date,
                        quantity=quantity,
                        reserved=reserved,
                        min_threshold=min_threshold
                    )
                    total_records += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Создано {total_records} записей остатков для {len(shops)} цехов'))