#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

Этот скрипт используется для выполнения различных административных задач Django,
таких как запуск сервера разработки, применение миграций, создание суперпользователя и т.д.
"""

import os
import sys


def main():
    """Run administrative tasks.
    
    Основная функция, которая настраивает окружение Django и выполняет команды управления.
    """
    # Установка переменной окружения для настроек Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        # Импорт функции выполнения команд Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Обработка ошибки импорта Django
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Выполнение команды из командной строки
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Запуск основной функции при выполнении скрипта напрямую
    main()