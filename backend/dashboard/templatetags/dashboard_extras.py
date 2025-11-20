from django import template

register = template.Library()

@register.filter
def model_count(queryset):
    """Возвращает количество записей в QuerySet"""
    try:
        return queryset.count()
    except:
        return 0