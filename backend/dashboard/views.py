from datetime import datetime, timedelta
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.views import LoginView
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Avg, FloatField, Max, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import InventoryCategory, InventoryRecord, KPIRecord, Shop


class StyledAuthenticationForm(AuthenticationForm):
    """
    Форма авторизации с предустановленными Bootstrap-классами.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Имя пользователя',
            'autocomplete': 'username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
            'autocomplete': 'current-password',
        })


class CustomLoginView(LoginView):
    """
    Пользовательское представление для входа в систему.
    
    Использует шаблон registration/login.html для отображения формы входа.
    """
    template_name = 'registration/login.html'
    authentication_form = StyledAuthenticationForm


@login_required
def dashboard(request):
    """
    Представление для отображения дашборда.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Отображает KPI-виджеты и графики.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон dashboard.html или JSON-ответ для AJAX-запросов
    """
    # Получаем параметры фильтрации из GET-запроса
    period = request.GET.get('period', 'month')  # day, week, month, quarter, year
    shop_ids = request.GET.getlist('shop', [])  # список ID цехов
    # Если индикаторы не переданы, используем все доступные
    indicators = request.GET.getlist('indicator')
    if not indicators:
        indicators = ['output', 'downtime', 'defect', 'load']  # типы показателей по умолчанию
    
    # Фильтрация по цехам
    shops = Shop.objects.all()
    if shop_ids:
        shops = shops.filter(id__in=shop_ids)
    
    # Фильтрация по дате в зависимости от периода
    # Используем максимальную дату из данных как "текущую" для фильтрации
    max_date = KPIRecord.objects.order_by('-date').first().date if KPIRecord.objects.exists() else datetime.now().date()
    
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
    
    # Получаем KPI записи с фильтрацией
    kpi_records = KPIRecord.objects.filter(
        date__gte=start_date
    ).select_related('shop')
    
    if shop_ids:
        kpi_records = kpi_records.filter(shop_id__in=shop_ids)
    
    # Рассчитываем агрегированные KPI
    total_output = sum([record.output for record in kpi_records])
    avg_downtime = sum([record.downtime_hours for record in kpi_records]) / max(len(kpi_records), 1)
    avg_defect_rate = sum([record.defect_rate for record in kpi_records]) / max(len(kpi_records), 1)
    avg_equipment_load = sum([record.equipment_load for record in kpi_records]) / max(len(kpi_records), 1)
    total_inventory = sum([record.inventory_level for record in kpi_records])
    total_cabinets = sum([record.cabinets_produced for record in kpi_records])
    avg_plan_completion = sum([record.plan_completion for record in kpi_records]) / max(len(kpi_records), 1)
    avg_quality_index = sum([record.quality_index for record in kpi_records]) / max(len(kpi_records), 1)
    
    # Подготовка данных для графиков
    chart_data = prepare_chart_data(kpi_records, period)
    
    # Проверяем, является ли запрос AJAX-запросом
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Возвращаем JSON-ответ с обновленными данными
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        
        # Создаем контекст для рендеринга KPI-карточек
        context = {
            'total_output': total_output,
            'avg_downtime': round(avg_downtime, 1),
            'avg_defect_rate': round(avg_defect_rate, 2),
            'avg_equipment_load': round(avg_equipment_load, 1),
            'total_inventory': total_inventory,
            'total_cabinets': total_cabinets,
            'avg_plan_completion': round(avg_plan_completion, 1),
            'avg_quality_index': round(avg_quality_index, 1),
        }
        
        # Рендерим KPI-карточки в HTML
        kpi_cards_html = render_to_string('partials/kpi_cards.html', context, request=request)
        
        return JsonResponse({
            'chart_data': chart_data,
            'kpi_cards_html': kpi_cards_html,
        })
    
    # Передаем данные в шаблон
    context = {
        'total_output': total_output,
        'avg_downtime': round(avg_downtime, 1),
        'avg_defect_rate': round(avg_defect_rate, 2),
        'avg_equipment_load': round(avg_equipment_load, 1),
        'total_inventory': total_inventory,
        'total_cabinets': total_cabinets,
        'avg_plan_completion': round(avg_plan_completion, 1),
        'avg_quality_index': round(avg_quality_index, 1),
        'shops': shops,
        'selected_period': period,
        'selected_shops': [int(id) for id in shop_ids if id.isdigit()],
        'selected_indicators': indicators,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'dashboard.html', context)


def prepare_chart_data(kpi_records, period):
    """
    Подготовка данных для графиков на основе KPI записей
    """
    # Группировка данных по цехам для графика простоев
    downtime_by_shop = {}
    for record in kpi_records:
        shop_name = record.shop.name
        if shop_name not in downtime_by_shop:
            downtime_by_shop[shop_name] = 0
        downtime_by_shop[shop_name] += record.downtime_hours
    
    # Если нет данных для графика простоев, создаем пустой словарь
    if not downtime_by_shop:
        downtime_by_shop = {}
    
    # Группировка данных по датам для графика производства
    # Используем формат YYYY-MM-DD для уникальности дат
    production_by_date = {}
    for record in kpi_records:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in production_by_date:
            production_by_date[date_str] = 0
        production_by_date[date_str] += record.output
    
    # Если нет данных для графика производства, создаем пустой словарь
    if not production_by_date:
        production_by_date = {}
    
    # Группировка данных по цехам для графика выполнения плана
    plan_by_shop = {}
    for record in kpi_records:
        shop_name = record.shop.name
        if shop_name not in plan_by_shop:
            plan_by_shop[shop_name] = []
        plan_by_shop[shop_name].append(record.plan_completion)
    
    # Усреднение значений для каждого цеха
    for shop_name in plan_by_shop:
        if plan_by_shop[shop_name]:
            avg_plan = sum(plan_by_shop[shop_name]) / len(plan_by_shop[shop_name])
            plan_by_shop[shop_name] = round(avg_plan, 1)
        else:
            plan_by_shop[shop_name] = 0
    
    # Если нет данных для графика выполнения плана, создаем пустой словарь
    if not plan_by_shop:
        plan_by_shop = {}
    
    # Группировка данных по датам для графика остатков
    # Используем формат YYYY-MM-DD для уникальности дат
    inventory_by_date = {}
    for record in kpi_records:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in inventory_by_date:
            inventory_by_date[date_str] = 0
        inventory_by_date[date_str] += record.inventory_level
    
    # Если нет данных для графика остатков, создаем пустой словарь
    if not inventory_by_date:
        inventory_by_date = {}
    
    return {
        'downtime_by_shop': downtime_by_shop,
        'production_by_date': production_by_date,
        'plan_by_shop': plan_by_shop,
        'inventory_by_date': inventory_by_date
    }


@login_required
def reports(request):
    """
    Представление для отображения страницы отчетов.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Отображает таблицу с отчетами.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон reports.html
    """
    from django.core.paginator import Paginator
    from datetime import datetime, timedelta
    
    # Получаем параметры фильтрации из GET-запроса
    period = request.GET.get('period', 'month')  # day, week, month, quarter, year
    shop_ids = request.GET.getlist('shop', [])  # список ID цехов
    indicators = request.GET.getlist('indicator', ['output', 'downtime', 'defect', 'load'])  # типы показателей
    page_number = request.GET.get('page', 1)  # номер страницы для пагинации
    
    # Фильтрация по цехам
    shops = Shop.objects.all()
    if shop_ids:
        shops = shops.filter(id__in=shop_ids)
    
    # Фильтрация по дате в зависимости от периода
    # Используем максимальную дату из данных как "текущую" для фильтрации
    max_date = KPIRecord.objects.order_by('-date').first().date if KPIRecord.objects.exists() else datetime.now().date()
    
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
    
    # Получаем KPI записи с фильтрацией
    kpi_records = KPIRecord.objects.filter(
        date__gte=start_date
    ).select_related('shop')
    
    if shop_ids:
        kpi_records = kpi_records.filter(shop_id__in=shop_ids)
    
    # Сортировка по дате и цеху
    kpi_records = kpi_records.order_by('-date', 'shop__name')
    
    # Пагинация
    paginator = Paginator(kpi_records, 20)  # 20 записей на страницу
    page_obj = paginator.get_page(page_number)
    
    # Передаем данные в шаблон
    context = {
        'page_obj': page_obj,
        'shops': shops,
        'selected_period': period,
        'selected_shops': [int(id) for id in shop_ids if id.isdigit()],
        'selected_indicators': indicators,
    }
    
    return render(request, 'reports.html', context)


INVENTORY_PERIOD_CHOICES = [
    ('day', 'День'),
    ('week', 'Неделя'),
    ('month', 'Месяц'),
    ('quarter', 'Квартал'),
    ('year', 'Год'),
]


def _resolve_inventory_period(period: str) -> str:
    valid_periods = {choice[0] for choice in INVENTORY_PERIOD_CHOICES}
    return period if period in valid_periods else 'month'


def _inventory_period_range(period: str):
    latest_record_date = InventoryRecord.objects.aggregate(latest=Max('date'))['latest']
    if latest_record_date is None:
        latest_record_date = timezone.localdate()

    period = _resolve_inventory_period(period)
    if period == 'day':
        start_date = latest_record_date - timedelta(days=1)
    elif period == 'week':
        start_date = latest_record_date - timedelta(days=7)
    elif period == 'quarter':
        start_date = latest_record_date - timedelta(days=90)
    elif period == 'year':
        start_date = latest_record_date - timedelta(days=365)
    else:  # month по умолчанию
        start_date = latest_record_date - timedelta(days=30)

    return start_date, latest_record_date


def _parse_inventory_filters(request):
    period = _resolve_inventory_period(request.GET.get('period', 'month'))

    category_id = request.GET.get('category') or None
    if category_id and not str(category_id).isdigit():
        category_id = None
    category_id = int(category_id) if category_id else None

    shop_ids_raw = request.GET.getlist('shop')
    shop_ids = [int(shop_id) for shop_id in shop_ids_raw if str(shop_id).isdigit()]

    return {
        'period': period,
        'category_id': category_id,
        'shop_ids': shop_ids,
    }


def _prepare_inventory_queryset(filters):
    start_date, end_date = _inventory_period_range(filters['period'])

    queryset = InventoryRecord.objects.select_related('item__category', 'shop').filter(
        date__range=(start_date, end_date)
    )

    if filters['category_id']:
        queryset = queryset.filter(item__category_id=filters['category_id'])

    if filters['shop_ids']:
        queryset = queryset.filter(shop_id__in=filters['shop_ids'])

    return queryset, start_date, end_date


def _number(value, digits=0):
    if value is None:
        return 0 if digits == 0 else 0.0
    numeric_value = float(value)
    if digits == 0:
        return int(round(numeric_value))
    return round(numeric_value, digits)


def _compose_inventory_payload(filters):
    queryset, start_date, end_date = _prepare_inventory_queryset(filters)

    aggregates = queryset.aggregate(
        total_quantity=Coalesce(Sum('quantity', output_field=FloatField()), 0.0),
        total_reserved=Coalesce(Sum('reserved', output_field=FloatField()), 0.0),
        total_shortage=Coalesce(Sum('shortage', output_field=FloatField()), 0.0),
        total_demand=Coalesce(Sum('demand', output_field=FloatField()), 0.0),
    )

    total_available = aggregates['total_quantity'] - aggregates['total_reserved']
    if total_available < 0:
        total_available = 0.0

    category_rows = list(
        queryset.values('item__category__id', 'item__category__name').annotate(
            quantity=Coalesce(Sum('quantity', output_field=FloatField()), 0.0),
            reserved=Coalesce(Sum('reserved', output_field=FloatField()), 0.0),
            demand=Coalesce(Sum('demand', output_field=FloatField()), 0.0),
            shortage=Coalesce(Sum('shortage', output_field=FloatField()), 0.0),
        ).order_by('item__category__name')
    )

    turnover_values = []
    inventory_by_category = []
    shortage_by_category = []
    turnover_by_category = []

    for entry in category_rows:
        category_name = entry['item__category__name'] or 'Без категории'
        quantity = float(entry['quantity'] or 0)
        reserved = float(entry['reserved'] or 0)
        demand = float(entry['demand'] or 0)
        shortage = float(entry['shortage'] or 0)
        available = max(quantity - reserved, 0)

        inventory_by_category.append({
            'name': category_name,
            'quantity': _number(quantity),
        })

        shortage_by_category.append({
            'name': category_name,
            'shortage': _number(shortage),
        })

        turnover = demand / available if available else 0
        turnover_values.append(turnover)
        turnover_by_category.append({
            'name': category_name,
            'turnover': round(turnover, 2),
        })

    trend_data = list(
        queryset.values('date').annotate(
            quantity=Coalesce(Sum('quantity', output_field=FloatField()), 0.0),
            shortage=Coalesce(Sum('shortage', output_field=FloatField()), 0.0),
        ).order_by('date')
    )

    trend = [
        {
            'date': record['date'].isoformat(),
            'quantity': _number(record['quantity']),
            'shortage': _number(record['shortage']),
        }
        for record in trend_data
    ]

    table_qs = queryset.values(
        'item__sku',
        'item__name',
        'item__category__name',
    ).annotate(
        quantity=Coalesce(Sum('quantity', output_field=FloatField()), 0.0),
        reserved=Coalesce(Sum('reserved', output_field=FloatField()), 0.0),
        min_threshold=Coalesce(Avg('min_threshold', output_field=FloatField()), 0.0),
        demand=Coalesce(Sum('demand', output_field=FloatField()), 0.0),
        shortage=Coalesce(Sum('shortage', output_field=FloatField()), 0.0),
    ).order_by('item__name')

    table_rows = []
    deficit_positions = 0
    for row in table_qs:
        quantity = float(row['quantity'] or 0)
        reserved = float(row['reserved'] or 0)
        shortage = float(row['shortage'] or 0)
        min_threshold = float(row['min_threshold'] or 0)
        demand = float(row['demand'] or 0)
        available = max(quantity - reserved, 0)

        if shortage > 0:
            status = 'Дефицит'
            status_class = 'danger'
            deficit_positions += 1
        elif available < min_threshold:
            status = 'Низкий'
            status_class = 'warning'
        else:
            status = 'Норма'
            status_class = 'success'

        table_rows.append({
            'sku': row['item__sku'],
            'name': row['item__name'],
            'category': row['item__category__name'] or 'Без категории',
            'quantity': _number(quantity),
            'reserved': _number(reserved),
            'available': _number(available),
            'min_threshold': _number(min_threshold),
            'demand': _number(demand),
            'shortage': _number(shortage),
            'status': status,
            'status_class': status_class,
        })

    average_turnover = round(sum(turnover_values) / len(turnover_values), 2) if turnover_values else 0

    payload = {
        'filters': {
            'period': filters['period'],
            'category_id': filters['category_id'],
            'shop_ids': filters['shop_ids'],
            'date_from': start_date.isoformat(),
            'date_to': end_date.isoformat(),
        },
        'summary': {
            'total_quantity': _number(aggregates['total_quantity']),
            'total_reserved': _number(aggregates['total_reserved']),
            'total_available': _number(total_available),
            'total_value': _number(aggregates['total_demand']),
            'total_shortage': _number(aggregates['total_shortage']),
            'deficit_positions': deficit_positions,
            'average_turnover': average_turnover,
        },
        'charts': {
            'inventory_by_category': inventory_by_category,
            'shortage_by_category': shortage_by_category,
            'inventory_trend': trend,
            'turnover_by_category': turnover_by_category,
        },
        'table': {
            'rows': table_rows,
        },
    }

    return payload


@login_required
def inventory(request):
    filters = _parse_inventory_filters(request)
    inventory_data = _compose_inventory_payload(filters)

    categories = InventoryCategory.objects.order_by('name')
    shops = Shop.objects.order_by('name')

    context = {
        'categories': categories,
        'shops': shops,
        'period_choices': INVENTORY_PERIOD_CHOICES,
        'selected_filters': filters,
        'inventory_data': inventory_data,
        'inventory_data_json': json.dumps(inventory_data, cls=DjangoJSONEncoder),
    }

    return render(request, 'inventory.html', context)


@login_required
def inventory_data(request):
    filters = _parse_inventory_filters(request)
    payload = _compose_inventory_payload(filters)
    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})


@login_required
def settings(request):
    """
    Представление для отображения страницы настроек.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Доступно только пользователям с ролью администратора.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон settings.html
    """
    # Проверяем, имеет ли пользователь права администратора
    if not (request.user.is_superuser or request.user.groups.filter(name='Администратор').exists()):
        messages.error(request, 'У вас нет прав для доступа к настройкам.')
        return redirect('dashboard')
    
    # Обработка POST-запросов для управления пользователями и группами
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'create_user':
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                group_id = request.POST.get('group')

                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username.strip(),
                        email=email.strip(),
                        password=password
                    )

                    if group_id:
                        group = Group.objects.get(id=group_id)
                        user.groups.add(group)

                messages.success(request, f'Пользователь {username} успешно создан.')

            elif action == 'update_user':
                user_id = request.POST.get('user_id')
                username = request.POST.get('username')
                email = request.POST.get('email')
                group_id = request.POST.get('group')

                with transaction.atomic():
                    user = User.objects.get(id=user_id)
                    user.username = username.strip()
                    user.email = email.strip()
                    user.save()

                    user.groups.clear()
                    if group_id:
                        group = Group.objects.get(id=group_id)
                        user.groups.add(group)

                messages.success(request, f'Данные пользователя {username} успешно обновлены.')

            elif action == 'delete_user':
                user_id = request.POST.get('user_id')
                user = User.objects.get(id=user_id)
                username = user.username
                user.delete()
                messages.success(request, f'Пользователь {username} успешно удален.')

            elif action == 'create_group':
                name = request.POST.get('name', '').strip()
                permission_ids = request.POST.getlist('permissions')
                user_ids = request.POST.getlist('users')

                if not name:
                    raise ValueError('Название группы не может быть пустым.')
                if Group.objects.filter(name__iexact=name).exists():
                    raise ValueError('Группа с таким названием уже существует.')

                with transaction.atomic():
                    group = Group.objects.create(name=name)
                    if permission_ids:
                        perms = Permission.objects.filter(id__in=permission_ids)
                        group.permissions.set(perms)
                    if user_ids:
                        users = User.objects.filter(id__in=user_ids)
                        group.user_set.add(*users)

                messages.success(request, f'Группа {name} успешно создана.')

            elif action == 'update_group':
                group_id = request.POST.get('group_id')
                name = request.POST.get('name', '').strip()
                permission_ids = request.POST.getlist('permissions')
                user_ids = request.POST.getlist('users')

                with transaction.atomic():
                    group = Group.objects.get(id=group_id)
                    if name:
                        if Group.objects.exclude(id=group.id).filter(name__iexact=name).exists():
                            raise ValueError('Группа с таким названием уже существует.')
                        group.name = name
                        group.save()

                    perms = Permission.objects.filter(id__in=permission_ids)
                    group.permissions.set(perms)

                    users = User.objects.filter(id__in=user_ids)
                    group.user_set.set(users)

                messages.success(request, f'Настройки группы {group.name} обновлены.')

            elif action == 'delete_group':
                group_id = request.POST.get('group_id')
                group = Group.objects.get(id=group_id)
                if group.name == 'Администратор':
                    raise ValueError('Системную группу "Администратор" удалять нельзя.')
                name = group.name
                group.delete()
                messages.success(request, f'Группа {name} успешно удалена.')

            elif action == 'save_data_sources':
                data_sources_payload = {
                    'source_1c': {
                        'enabled': request.POST.get('source_1c_enabled') == 'on',
                        'path': request.POST.get('source_1c_path', '').strip(),
                        'schedule': request.POST.get('source_1c_schedule', 'daily'),
                        'last_sync': request.POST.get('source_1c_last_sync', '').strip(),
                    },
                    'source_access': {
                        'enabled': request.POST.get('source_access_enabled') == 'on',
                        'path': request.POST.get('source_access_path', '').strip(),
                        'password': request.POST.get('source_access_password', '').strip(),
                        'last_sync': request.POST.get('source_access_last_sync', '').strip(),
                    },
                }

                request.session['data_sources'] = data_sources_payload
                request.session.modified = True
                messages.success(request, 'Настройки источников данных сохранены.')

            else:
                messages.warning(request, 'Неизвестное действие.')

        except (User.DoesNotExist, Group.DoesNotExist, Permission.DoesNotExist) as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f'Не удалось выполнить действие: {exc}')

        return redirect('settings')
    
    # Получаем данные для отображения
    users = User.objects.prefetch_related('groups').order_by('username')
    groups = Group.objects.prefetch_related('user_set', 'permissions').order_by('name')
    permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    data_sources = request.session.get('data_sources', {
        'source_1c': {
            'enabled': True,
            'path': '',
            'schedule': 'daily',
            'last_sync': '',
        },
        'source_access': {
            'enabled': False,
            'path': '',
            'password': '',
            'last_sync': '',
        },
    })

    permissions_by_app = []
    last_key = None
    for perm in permissions:
        key = perm.content_type.app_label
        label = perm.content_type.name.title()
        if not permissions_by_app or permissions_by_app[-1]['key'] != key:
            permissions_by_app.append({'key': key, 'label': label, 'permissions': []})
        permissions_by_app[-1]['permissions'].append(perm)
    
    # Получаем информацию о базе данных
    import sqlite3
    from django.conf import settings
    import os
    from dashboard.models import KPIRecord, InventoryRecord, AlertRule, UserActionLog
    
    db_path = settings.DATABASES['default']['NAME']
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    # Форматируем размер базы данных
    if db_size > 1024 * 1024:  # больше 1 МБ
        db_size_formatted = f"{db_size / (1024 * 1024):.2f} МБ"
    elif db_size > 1024:  # больше 1 КБ
        db_size_formatted = f"{db_size / 1024:.2f} КБ"
    else:
        db_size_formatted = f"{db_size} байт"
    

    
    context = {
        'users': users,
        'groups': groups,
        'permissions_by_app': permissions_by_app,
        'db_path': db_path,
        'db_size': db_size_formatted,
    }

    return render(request, 'settings.html', context)


@login_required
def alerts(request):
    """
    Представление для отображения страницы уведомлений.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Отображает настройки порогов и историю уведомлений.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон alerts.html
    """
    # TODO: Реализовать страницу уведомлений
    return render(request, 'alerts.html')


@login_required
def profile(request):
    """
    Представление для отображения личного кабинета пользователя.
    
    Только аутентифицированные пользователи могут получить доступ к этой странице.
    Отображает информацию о пользователе и историю его действий.
    
    Args:
        request (HttpRequest): Объект HTTP-запроса
        
    Returns:
        HttpResponse: Отрендеренный шаблон profile.html
    """
    # TODO: Реализовать личный кабинет пользователя
    return render(request, 'profile.html')
