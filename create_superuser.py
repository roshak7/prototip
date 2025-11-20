from django.contrib.auth.models import User

# Создание суперпользователя
User.objects.create_superuser('admin', 'admin@example.com', 'admin')