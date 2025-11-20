#!/bin/bash
# Скрипт инициализации для Docker

echo "Применение миграций..."
python manage.py migrate

echo "Заполнение базы данных фейковыми данными..."
python manage.py fill_fake_data

echo "Настройка ролей пользователей..."
python manage.py setup_roles

echo "Создание суперпользователя..."
python manage.py shell < ../create_superuser.py

echo "Запуск сервера разработки..."
python manage.py runserver 0.0.0.0:8000