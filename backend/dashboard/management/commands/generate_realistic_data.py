from django.core.management.base import BaseCommand
from dashboard.models import Shop, KPIRecord, InventoryCategory, InventoryItem, InventoryRecord
import random
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    """
    Команда управления Django для генерации реалистичных данных для дашборда.
    
    Создает цеха и заполняет таблицу KPIRecord реалистичными данными с учетом
    взаимосвязей между различными метриками.
    """
    help = 'Генерация реалистичных данных для дашборда'

    def add_arguments(self, parser):
        """
        Добавляет аргументы командной строки.
        """
        parser.add_argument(
            '--start-date',
            type=str,
            default='2025-04-01',
            help='Дата начала генерации данных (ГГГГ-ММ-ДД)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default='2025-04-30',
            help='Дата окончания генерации данных (ГГГГ-ММ-ДД)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед генерацией'
        )

    def handle(self, *args, **options):
        """
        Основной метод выполнения команды.
        """
        # Парсим даты
        start_date = date.fromisoformat(options['start_date'])
        end_date = date.fromisoformat(options['end_date'])
        
        # Очищаем существующие данные, если нужно
        if options['clear']:
            self.stdout.write('Очистка существующих данных...')
            KPIRecord.objects.all().delete()
            InventoryRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Существующие данные удалены'))

        # Создание цехов
        shops_data = [
            {"name": "Цех №1", "capacity": 15000, "base_downtime": 5.0},
            {"name": "Цех №2", "capacity": 12000, "base_downtime": 6.5},
            {"name": "Цех №3", "capacity": 18000, "base_downtime": 4.0},
            {"name": "Цех №4", "capacity": 10000, "base_downtime": 7.0},
            {"name": "Цех №5", "capacity": 14000, "base_downtime": 5.5},
        ]
        
        shop_objects = []
        for shop_data in shops_data:
            shop, created = Shop.objects.get_or_create(
                name=shop_data["name"],
                defaults={
                    "name": shop_data["name"]
                }
            )
            shop.capacity = shop_data["capacity"]
            shop.base_downtime = shop_data["base_downtime"]
            shop_objects.append(shop)

        # Создание категорий складских позиций (если еще не созданы)
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

        # Создание складских позиций (если еще не созданы)
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

        # Генерация KPI с учетом реалистичных зависимостей
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        # Инициализируем базовые значения для каждого цеха
        shop_inventory = {shop.id: random.randint(15000, 25000) for shop in shop_objects}
        
        self.stdout.write(f'Генерация данных с {start_date} по {end_date}...')
        
        day_counter = 0
        total_inventory_records = 0
        while current_date <= end_date:
            for shop in shop_objects:
                # Базовые параметры цеха
                capacity = shop.capacity
                base_downtime = shop.base_downtime
                
                # Добавляем сезонные и случайные колебания
                seasonal_factor = 1 + 0.1 * abs((current_date.timetuple().tm_yday - 90) / 90)  # Пик в июне
                random_factor = random.uniform(0.9, 1.1)
                
                # Расчет базовых метрик с учетом зависимостей
                equipment_load = min(98, max(70, 85 + random.uniform(-5, 5) + (day_counter % 7 == 0) * -5))
                downtime_hours = max(1, base_downtime * (100 - equipment_load) / 100 * random_factor)
                output = int(capacity * equipment_load / 100 * seasonal_factor * random_factor)
                
                # Процент брака зависит от загрузки оборудования и простоя
                defect_rate = max(0.5, min(8, 2.0 + (100 - equipment_load) / 20 + downtime_hours / 5))
                
                # Общий уровень остатков на складе
                inventory_change = int(output * 0.2) - int(output * 0.15)  # Производство минус потребление
                shop_inventory[shop.id] = max(0, shop_inventory[shop.id] + inventory_change)
                inventory_level = shop_inventory[shop.id]
                
                # Объем ДСЕ (деталей, сборочных единиц)
                dse_volume = int(output * random.uniform(0.8, 1.2))
                
                # Количество изготовленных шкафов
                cabinets_produced = int(output * random.uniform(0.1, 0.3))
                
                # Выполнение плана
                plan_completion = max(0, min(100, equipment_load - (downtime_hours * 1.5)))
                
                # Индекс качества
                quality_index = max(0, min(100, 100 - defect_rate * 3))
                
                # Индекс производительности
                productivity_index = max(0, min(100, equipment_load - downtime_hours * 0.5))
                
                # Потребление энергии
                energy_consumption = equipment_load * output / 1000 * random.uniform(0.95, 1.05)
                
                # Использование материалов
                material_utilization = max(0, min(100, 90 + (100 - quality_index) * 0.05))
                
                # Создаем запись KPI
                KPIRecord.objects.create(
                    shop=shop,
                    date=current_date,
                    output=output,
                    downtime_hours=round(downtime_hours, 2),
                    defect_rate=round(defect_rate, 2),
                    equipment_load=round(equipment_load, 2),
                    inventory_level=inventory_level,
                    dse_volume=dse_volume,
                    cabinets_produced=cabinets_produced,
                    plan_completion=round(plan_completion, 2),
                    quality_index=round(quality_index, 2),
                    productivity_index=round(productivity_index, 2),
                    energy_consumption=round(energy_consumption, 2),
                    material_utilization=round(material_utilization, 2)
                )
                
                # Генерация складских записей для текущего дня
                for item in items:
                    # Генерируем реалистичные остатки для каждой позиции
                    # Разные категории имеют разные уровни потребления
                    category_factor = 1.0
                    if item.category.name == "Провода и кабели":
                        category_factor = 1.5  # Провода потребляются больше
                    elif item.category.name == "Комплектующие для шкафов":
                        category_factor = 1.2  # Комплектующие тоже востребованы
                    elif item.category.name == "Измерительные приборы":
                        category_factor = 0.7   # Приборы потребляются меньше
                    
                    # Генерируем остатки с учетом потребления
                    base_quantity = random.randint(50, 500)
                    quantity = max(0, int(base_quantity * category_factor * random.uniform(0.8, 1.2)))
                    reserved = random.randint(0, quantity // 3)  # Зарезервировано (до трети от общего)
                    min_threshold = max(5, int(quantity * 0.1))  # Минимальный порог 10% от остатка
                    
                    InventoryRecord.objects.create(
                        item=item,
                        shop=shop,
                        date=current_date,
                        quantity=quantity,
                        reserved=reserved,
                        min_threshold=min_threshold
                    )
                    total_inventory_records += 1
            
            # Переходим к следующему дню
            current_date += timedelta(days=1)
            day_counter += 1
            
            # Показываем прогресс
            if day_counter % 5 == 0 or current_date > end_date:
                progress = int(day_counter / total_days * 100)
                self.stdout.write(f'Прогресс: {progress}%')

        # Выводим сообщение об успешном завершении
        self.stdout.write(self.style.SUCCESS(f'✅ Реалистичные данные успешно сгенерированы!'))
        self.stdout.write(self.style.SUCCESS(f'Создано {total_inventory_records} складских записей'))