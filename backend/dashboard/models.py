from django.db import models
from django.contrib.auth.models import User


class Shop(models.Model):
    """
    Модель цеха производства.
    
    Атрибуты:
        name (str): Название цеха
    """
    name = models.CharField(max_length=100, verbose_name="Название цеха")

    def __str__(self):
        """Возвращает строковое представление цеха (его название)"""
        return self.name

    class Meta:
        verbose_name = "Цех"
        verbose_name_plural = "Цеха"


class KPIRecord(models.Model):
    """
    Модель для хранения ключевых показателей эффективности (KPI) по цехам.
    
    Атрибуты:
        shop (Shop): Ссылка на цех
        date (date): Дата записи показателей
        output (int): Объем выпуска продукции
        downtime_hours (float): Количество часов простоя
        defect_rate (float): Процент брака
        equipment_load (float): Загрузка оборудования в процентах
        inventory_level (int): Общий уровень остатков на складе (ед.)
        dse_volume (int): Объем ДСЕ (деталей, сборочных единиц)
        cabinets_produced (int): Количество изготовленных шкафов
        plan_completion (float): Процесс выполнения плана (%)
        quality_index (float): Индекс качества продукции (%)
        productivity_index (float): Индекс производительности (%)
        energy_consumption (float): Потребление энергии (кВт·ч)
        material_utilization (float): Использование материалов (%)
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="Цех")
    date = models.DateField(verbose_name="Дата")
    output = models.IntegerField(verbose_name="Объем выпуска")
    downtime_hours = models.FloatField(verbose_name="Часы простоя")
    defect_rate = models.FloatField(verbose_name="Процент брака")
    equipment_load = models.FloatField(verbose_name="Загрузка оборудования (%)")
    
    # Производственные метрики
    inventory_level = models.IntegerField(verbose_name="Общий уровень остатков на складе (ед.)", default=0)
    dse_volume = models.IntegerField(verbose_name="Объем ДСЕ", default=0)
    cabinets_produced = models.IntegerField(verbose_name="Изготовлено шкафов", default=0)
    plan_completion = models.FloatField(verbose_name="Выполнение плана (%)", default=0.0)
    quality_index = models.FloatField(verbose_name="Индекс качества (%)", default=0.0)
    productivity_index = models.FloatField(verbose_name="Индекс производительности (%)", default=0.0)
    energy_consumption = models.FloatField(verbose_name="Потребление энергии (кВт·ч)", default=0.0)
    material_utilization = models.FloatField(verbose_name="Использование материалов (%)", default=0.0)

    def __str__(self):
        """Возвращает строковое представление записи KPI"""
        return f"{self.shop.name} - {self.date}"

    class Meta:
        verbose_name = "Запись KPI"
        verbose_name_plural = "Записи KPI"


class InventoryCategory(models.Model):
    """
    Модель для категорий складских позиций.
    
    Атрибуты:
        name (str): Название категории
        description (str): Описание категории
    """
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(verbose_name="Описание категории", blank=True)

    def __str__(self):
        """Возвращает строковое представление категории"""
        return self.name

    class Meta:
        verbose_name = "Категория складских позиций"
        verbose_name_plural = "Категории складских позиций"


class InventoryItem(models.Model):
    """
    Модель для складских позиций.
    
    Атрибуты:
        category (InventoryCategory): Категория позиции
        name (str): Название позиции
        sku (str): Артикул/код позиции
        unit (str): Единица измерения
        description (str): Описание позиции
    """
    # Единицы измерения
    UNIT_CHOICES = [
        ('pcs', 'Штуки'),
        ('m', 'Метры'),
        ('kg', 'Килограммы'),
        ('pack', 'Упаковки'),
        ('set', 'Комплекты'),
    ]
    
    category = models.ForeignKey(
        InventoryCategory, 
        on_delete=models.CASCADE, 
        verbose_name="Категория"
    )
    name = models.CharField(max_length=200, verbose_name="Название позиции")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    unit = models.CharField(
        max_length=10, 
        choices=UNIT_CHOICES, 
        verbose_name="Единица измерения"
    )
    description = models.TextField(verbose_name="Описание", blank=True)

    def __str__(self):
        """Возвращает строковое представление позиции"""
        return f"{self.name} ({self.sku})"

    class Meta:
        verbose_name = "Складская позиция"
        verbose_name_plural = "Складские позиции"


class InventoryRecord(models.Model):
    """
    Модель для учета остатков складских позиций.
    
    Атрибуты:
        item (InventoryItem): Складская позиция
        shop (Shop): Цех (если остатки распределены по цехам)
        date (date): Дата записи остатков
        quantity (int): Количество на складе
        reserved (int): Зарезервированное количество
        min_threshold (int): Минимальный порог (для уведомлений)
        demand (int): Потребность (опционально)
        shortage (int): Дефицит (опционально)
    """
    item = models.ForeignKey(
        InventoryItem, 
        on_delete=models.CASCADE, 
        verbose_name="Складская позиция"
    )
    shop = models.ForeignKey(
        Shop, 
        on_delete=models.CASCADE, 
        verbose_name="Цех"
    )
    date = models.DateField(verbose_name="Дата")
    quantity = models.IntegerField(verbose_name="Количество на складе", default=0)
    reserved = models.IntegerField(verbose_name="Зарезервированное количество", default=0)
    min_threshold = models.IntegerField(verbose_name="Минимальный порог", default=0)
    demand = models.IntegerField(verbose_name="Потребность", default=0)
    shortage = models.IntegerField(verbose_name="Дефицит", default=0)

    @property
    def available(self):
        """Доступное количество (в наличии минус зарезервировано)"""
        return max(0, self.quantity - self.reserved)

    def __str__(self):
        """Возвращает строковое представление записи остатков"""
        return f"{self.item.name} - {self.shop.name} - {self.date}: {self.available}"

    class Meta:
        verbose_name = "Запись остатков"
        verbose_name_plural = "Записи остатков"
        # Уникальность по позиции, цеху и дате
        unique_together = ('item', 'shop', 'date')


class AlertRule(models.Model):
    """
    Модель для определения правил уведомлений.
    
    Атрибуты:
        indicator (str): Тип показателя для отслеживания
        condition (str): Условие срабатывания (>, <, >=, <=, =)
        threshold (float): Пороговое значение
        notify_in_app (bool): Флаг уведомления в интерфейсе
        notify_email (bool): Флаг уведомления по email
    """
    # Варианты выбора для типа показателя
    INDICATOR_CHOICES = [
        ('downtime', 'Простои'),
        ('defect_rate', 'Брак'),
        ('equipment_load', 'Загрузка оборудования'),
        ('output', 'Выпуск'),
        ('inventory_level', 'Общий уровень остатков'),
        ('plan_completion', 'Выполнение плана'),
        ('quality_index', 'Индекс качества'),
    ]
    
    # Варианты выбора для условия
    CONDITION_CHOICES = [
        ('gt', '>'),
        ('lt', '<'),
        ('gte', '>='),
        ('lte', '<='),
        ('eq', '='),
    ]
    
    indicator = models.CharField(
        max_length=20, 
        choices=INDICATOR_CHOICES,
        verbose_name="Показатель"
    )
    condition = models.CharField(
        max_length=3, 
        choices=CONDITION_CHOICES,
        verbose_name="Условие"
    )
    threshold = models.FloatField(verbose_name="Пороговое значение")
    notify_in_app = models.BooleanField(
        default=True, 
        verbose_name="Уведомлять в интерфейсе"
    )
    notify_email = models.BooleanField(
        default=False, 
        verbose_name="Уведомлять по email"
    )
    
    def __str__(self):
        """Возвращает строковое представление правила уведомления"""
        return f"{self.get_indicator_display()} {self.get_condition_display()} {self.threshold}"

    class Meta:
        verbose_name = "Правило уведомления"
        verbose_name_plural = "Правила уведомлений"


class UserActionLog(models.Model):
    """
    Модель для ведения журнала действий пользователей.
    
    Атрибуты:
        user (User): Пользователь, совершивший действие
        action (str): Описание действия
        timestamp (datetime): Время совершения действия
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Пользователь"
    )
    action = models.TextField(verbose_name="Действие")
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Время действия"
    )
    
    def __str__(self):
        """Возвращает строковое представление записи журнала действий"""
        return f"{self.user.username} - {self.action} - {self.timestamp}"

    class Meta:
        verbose_name = "Запись журнала действий"
        verbose_name_plural = "Записи журнала действий"