from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

def create_test_superuser():
    # Проверяем, существует ли уже суперпользователь с именем admin
    if not User.objects.filter(username='admin').exists():
        # Создаем суперпользователя
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Создан суперпользователь: admin / admin")
    else:
        print("Суперпользователь admin уже существует")

if __name__ == "__main__":
    create_test_superuser()