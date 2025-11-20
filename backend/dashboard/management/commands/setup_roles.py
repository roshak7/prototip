from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from dashboard.models import Shop, KPIRecord, AlertRule, UserActionLog


class Command(BaseCommand):
    """
    Команда управления Django для настройки ролей пользователей.
    
    Создает группы пользователей (роли) и назначает им соответствующие права доступа.
    Также добавляет суперпользователя в группу администраторов.
    """
    help = 'Настройка ролей пользователей'

    def handle(self, *args, **kwargs):
        """
        Основной метод выполнения команды.
        
        Создает три группы пользователей (Администратор, Руководитель, Специалист)
        и назначает им соответствующие права доступа.
        """
        # Создание групп (ролей) пользователей
        admin_group, created = Group.objects.get_or_create(name='Администратор')
        manager_group, created = Group.objects.get_or_create(name='Руководитель')
        specialist_group, created = Group.objects.get_or_create(name='Специалист')

        # Получение всех разрешений для моделей dashboard
        content_types = ContentType.objects.filter(app_label='dashboard')
        permissions = Permission.objects.filter(content_type__in=content_types)

        # Назначение разрешений группам
        # Администратор получает все разрешения
        for perm in permissions:
            admin_group.permissions.add(perm)

        # Руководитель получает разрешения на чтение
        read_permissions = Permission.objects.filter(codename__contains='view')
        for perm in read_permissions:
            manager_group.permissions.add(perm)

        # Специалист получает разрешения на чтение только для своего цеха
        # Это будет реализовано на уровне представлений

        # Назначение пользователя admin в группу администраторов
        try:
            admin_user = User.objects.get(username='admin')
            admin_user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS('✅ Пользователь admin добавлен в группу Администратор'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Пользователь admin не найден'))

        # Выводим сообщение об успешном завершении
        self.stdout.write(self.style.SUCCESS('✅ Роли пользователей успешно настроены!'))