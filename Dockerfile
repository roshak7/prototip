# Используем официальный образ Python
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /code

# Копируем файл зависимостей
COPY requirements.txt /code/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . /code/

# Делаем скрипт инициализации исполняемым
RUN chmod +x /code/init.sh

# Открываем порт 8000
EXPOSE 8000

# Команда для запуска приложения
CMD ["/code/init.sh"]