# образ на основе которого создаём контейнер
FROM python:3.10-alpine

# рабочая директория внутри проекта
WORKDIR /usr/src/lct_back

# переменные окружения для python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# устанавливаем зависимости
RUN apt-get -y install libc-dev
RUN \apt-get -y install build-essential
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# копируем содержимое текущей папки в контейнер
COPY . .