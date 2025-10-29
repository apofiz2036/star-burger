# Используем официальный Python
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем зависимости системы для psycopg
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
	
# Копируем файлы проекта
COPY . /app/

# Устанавливаем python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт для Django
EXPOSE 8000

# Команда по умолчанию — запуск Django сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]