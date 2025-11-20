from django.core.management.base import BaseCommand
from dashboard.models import Shop, KPIRecord
import random
from datetime import date, timedelta


class Command(BaseCommand):
    """
    Команда управления Django для заполнения базы данных фейковыми данными.
    
    Создает цеха и заполняет таблицу KPIRecord случайными данными за апрель 2025 года.
    """
    help = 'Заполнение базы данных фейковыми данными'

    def handle(self, *args, **kwargs):
        """
        Основной метод выполнения команды.
        
        Создает 5 цехов и генерирует случайные KPI данные для каждого цеха
        за каждый день апреля 2025 года.
        """
        # Создание цехов
        shops = ["Цех №1", "Цех №2", "Цех №3", "Цех №4", "Цех №5"]
        shop_objects = []
        for name in shops:
            # Создаем цех, если он еще не существует
            shop, created = Shop.objects.get_or_create(name=name)
            shop_objects.append(shop)

        # Генерация KPI за апрель 2025
        start_date = date(2025, 4, 1)
        end_date = date(2025, 4, 30)
        current_date = start_date

        # Проходим по каждому дню апреля
        while current_date <= end_date:
            # Для каждого цеха создаем запись KPI
            for shop in shop_objects:
                # Генерируем базовые KPI значения
                output = random.randint(8000, 15000)
                downtime_hours = random.uniform(2, 10)
                defect_rate = random.uniform(1.0, 5.0)
                equipment_load = random.uniform(75, 98)
                
                # Генерируем дополнительные реалистичные метрики
                # Остатки на складе (уменьшаются с ростом выпуска, увеличиваются с течением времени)
                inventory_level = max(0, random.randint(5000, 20000) - int(output * 0.3) + random.randint(0, 1000))
                
                # Объем ДСЕ (связан с выпуском продукции)
                dse_volume = int(output * random.uniform(0.8, 1.2))
                
                # Количество изготовленных шкафов (часть от общего выпуска)
                cabinets_produced = int(output * random.uniform(0.1, 0.3))
                
                # Выполнение плана (зависит от загрузки оборудования и простоев)
                plan_completion = max(0, min(100, equipment_load - (downtime_hours * 2)))
                
                # Индекс качества (обратно связан с процентом брака)
                quality_index = max(0, min(100, 100 - defect_rate * 5))
                
                # Индекс производительности (связан с загрузкой оборудования и простоями)
                productivity_index = max(0, min(100, equipment_load - downtime_hours))
                
                # Потребление энергии (связано с загрузкой оборудования и выпуском)
                energy_consumption = equipment_load * output / 1000 * random.uniform(0.9, 1.1)
                
                # Использование материалов (связано с выпуском и браком)
                material_utilization = max(0, min(100, 90 + (100 - quality_index) * 0.1))

                KPIRecord.objects.create(
                    shop=shop,
                    date=current_date,
                    # Базовые KPI значения
                    output=output,
                    downtime_hours=downtime_hours,
                    defect_rate=defect_rate,
                    equipment_load=equipment_load,
                    # Дополнительные реалистичные метрики
                    inventory_level=inventory_level,
                    dse_volume=dse_volume,
                    cabinets_produced=cabinets_produced,
                    plan_completion=plan_completion,
                    quality_index=quality_index,
                    productivity_index=productivity_index,
                    energy_consumption=energy_consumption,
                    material_utilization=material_utilization
                )
            # Переходим к следующему дню
            current_date += timedelta(days=1)

        # Выводим сообщение об успешном завершении
        self.stdout.write(self.style.SUCCESS('✅ Фейковые данные успешно загружены!'))