@login_required
def inventory(request):
    """
    Представление для отображения страницы склада.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Отображает информацию о складских остатках и диаграммы.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон inventory_new.html
    """
    from django.core.paginator import Paginator
    from datetime import datetime, timedelta
    
    # Получаем параметры фильтрации из GET-запроса
    period = request.GET.get('period', 'month')  # day, week, month, quarter, year
    shop_ids = request.GET.getlist('shop', [])  # список ID цехов
    category_ids = request.GET.getlist('category', [])  # список ID категорий
    page_number = request.GET.get('page', 1)  # номер страницы для пагинации
    
    # Фильтрация по цехам
    shops = Shop.objects.all()
    if shop_ids:
        shops = shops.filter(id__in=shop_ids)
    
    # Фильтрация по категориям
    categories = InventoryCategory.objects.all()
    if category_ids:
        categories = categories.filter(id__in=category_ids)
    
    # Фильтрация по дате в зависимости от периода
    # Используем максимальную дату из данных как "текущую" для фильтрации
    max_date = InventoryRecord.objects.order_by('-date').first().date if InventoryRecord.objects.exists() else datetime.now().date()
    
    if period == 'day':
        start_date = max_date
    elif period == 'week':
        start_date = max_date - timedelta(days=7)
    elif period == 'month':
        start_date = max_date - timedelta(days=30)
    elif period == 'quarter':
        start_date = max_date - timedelta(days=90)
    elif period == 'year':
        start_date = max_date - timedelta(days=365)
    else:
        start_date = max_date - timedelta(days=30)  # по умолчанию месяц
    
    # Получаем записи складских остатков с фильтрацией
    inventory_records = InventoryRecord.objects.filter(
        date__gte=start_date
    ).select_related('item', 'item__category', 'shop')
    
    if shop_ids:
        inventory_records = inventory_records.filter(shop_id__in=shop_ids)
    
    if category_ids:
        inventory_records = inventory_records.filter(item__category_id__in=category_ids)
    
    # Сортировка по дате и цеху
    inventory_records = inventory_records.order_by('-date', 'shop__name')
    
    # Пагинация
    paginator = Paginator(inventory_records, 20)  # 20 записей на страницу
    page_obj = paginator.get_page(page_number)
    
    # Рассчитываем агрегированные показатели
    total_inventory = sum([record.quantity for record in inventory_records])
    deficit_positions = sum([1 for record in inventory_records if record.shortage > 0])
    turnover_rate = 3.2  # условное значение, в реальности нужно рассчитывать
    total_value = total_inventory * 100  # условное значение, в реальности нужно использовать стоимость
    
    # Подготовка данных для графиков
    # Группировка остатков по категориям
    inventory_by_category = {}
    for record in inventory_records:
        category_name = record.item.category.name
        if category_name not in inventory_by_category:
            inventory_by_category[category_name] = 0
        inventory_by_category[category_name] += record.quantity

    # Форматируем данные в нужный формат для Chart.js
    inventory_by_category_formatted = [
        {'name': name, 'quantity': quantity}
        for name, quantity in inventory_by_category.items()
    ]

    # Группировка дефицитных позиций
    shortage_items = inventory_records.filter(shortage__gt=0)
    shortage_by_item = {}
    for record in shortage_items:
        item_name = record.item.name
        if item_name not in shortage_by_item:
            shortage_by_item[item_name] = 0
        shortage_by_item[item_name] += record.shortage

    # Форматируем данные в нужный формат для Chart.js
    shortage_by_category_formatted = [
        {'name': name, 'shortage': shortage}
        for name, shortage in shortage_by_item.items()
    ]

    # Подготовка данных для динамики остатков
    inventory_trend = {}
    for record in inventory_records:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in inventory_trend:
            inventory_trend[date_str] = {'total': 0, 'shortage': 0}
        inventory_trend[date_str]['total'] += record.quantity
        inventory_trend[date_str]['shortage'] += record.shortage

    # Форматируем данные в нужный формат для Chart.js
    inventory_trend_formatted = [
        {'date': date, 'total': values['total'], 'shortage': values['shortage']}
        for date, values in inventory_trend.items()
    ]

    # Оборачиваем данные в JSON для передачи в JavaScript
    import json
    chart_data = {
        'inventory_by_category': inventory_by_category_formatted,
        'shortage_by_category': shortage_by_category_formatted,
        'inventory_trend': inventory_trend_formatted,
    }

    # Передаем данные в шаблон
    context = {
        'page_obj': page_obj,
        'shops': shops,
        'categories': categories,
        'selected_period': period,
        'selected_shops': [int(id) for id in shop_ids if id.isdigit()],
        'selected_categories': [int(id) for id in category_ids if id.isdigit()],
        'total_inventory': total_inventory,
        'deficit_positions': deficit_positions,
        'turnover_rate': turnover_rate,
        'total_value': total_value,
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'inventory_new.html', context)