

# Используйте официальный образ Python в качестве базового образа
FROM python

# Устанавливаем переменную окружения для вывода сообщений от Python в буфер, не блокируя их
ENV FLASK_APP=run.py

# Устанавливаем рабочую директорию в /app
WORKDIR /app

# Копируем файл зависимостей в текущую директорию
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое текущей директории в /app в контейнере
COPY . /app

# Открываем порт 5000
EXPOSE 5000

# Команда для запуска приложения
CMD ["flask", "run", "--host=0.0.0.0"]
