from django.core.management.base import BaseCommand
from dashboard.models import Shop, KPIRecord, InventoryCategory, InventoryItem, InventoryRecord
import random
from datetime import date, timedelta


class Command(BaseCommand):
    """
    Команда управления Django для генерации реалистичных данных склада с учетом потребности.
    
    Создает категории, позиции, остатки и потребность для склада.
    """
    help = 'Генерация реалистичных складских данных с учетом потребности'

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
            InventoryRecord.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Существующие данные удалены'))

        # Получаем все цеха
        shops = list(Shop.objects.all())
        if not shops:
            self.stdout.write(self.style.ERROR('Не найдены цеха. Сначала создайте цеха.'))
            return
            
        # Получаем все складские позиции
        items = list(InventoryItem.objects.all())
        if not items:
            self.stdout.write(self.style.ERROR('Не найдены складские позиции. Сначала создайте позиции.'))
            return

        # Генерация складских записей с учетом потребности
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        self.stdout.write(f'Генерация складских данных с {start_date} по {end_date}...')
        
        day_counter = 0
        total_records = 0
        while current_date <= end_date:
            for shop in shops:
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
                    
                    # Генерируем базовые остатки
                    base_quantity = random.randint(50, 500)
                    quantity = max(0, int(base_quantity * category_factor * random.uniform(0.8, 1.2)))
                    
                    # Генерируем зарезервированное количество (до трети от общего)
                    reserved = random.randint(0, quantity // 3)
                    
                    # Минимальный порог 10% от остатка
                    min_threshold = max(5, int(quantity * 0.1))
                    
                    # Генерируем потребность (может быть больше, чем остатки)
                    demand = max(0, int(quantity * random.uniform(0.5, 2.0)))
                    
                    # Рассчитываем дефицит
                    available = max(0, quantity - reserved)
                    shortage = max(0, demand - available)
                    
                    # Создаем запись остатков
                    InventoryRecord.objects.create(
                        item=item,
                        shop=shop,
                        date=current_date,
                        quantity=quantity,
                        reserved=reserved,
                        min_threshold=min_threshold,
                        demand=demand,  # Потребность
                        shortage=shortage  # Дефицит
                    )
                    total_records += 1
            
            # Переходим к следующему дню
            current_date += timedelta(days=1)
            day_counter += 1
            
            # Показываем прогресс
            if day_counter % 5 == 0 or current_date > end_date:
                progress = int(day_counter / total_days * 100)
                self.stdout.write(f'Прогресс: {progress}%')

        # Выводим сообщение об успешном завершении
        self.stdout.write(self.style.SUCCESS(f'✅ Реалистичные складские данные успешно сгенерированы!'))
        self.stdout.write(self.style.SUCCESS(f'Создано {total_records} складских записей'))