# Dockerfile для ML Oracle
# Изолированное окружение для обучения и инференса

FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директории для артефактов и логов
RUN mkdir -p artifacts logs

# Expose port (если нужен API сервер)
EXPOSE 8000

# Дефолтная команда
CMD ["python", "ml_oracle.py", "--help"]
