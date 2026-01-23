Каталог курсов по нейросетям
Проект представляет собой каталог курсов по искусственному интеллекту, машинному обучению и нейросетям с фильтрацией, поиском и партнерскими ссылками.

🚀 Быстрый запуск
Вариант 1: Локальный запуск
Клонируйте репозиторий:

bash
git clone https://github.com/dron1111/neural-courses-catalog.git
cd neural-courses-catalog
Создайте виртуальное окружение и установите зависимости:

bash
# Для Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Для macOS/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Настройте переменные окружения:

bash
# Создайте файл .env
echo "DATABASE_URL=sqlite:///./courses.db" > .env
echo "ADMIN_TOKEN=your-secret-token-here" >> .env
echo "PORT=8000" >> .env
Запустите приложение:

bash
# Способ 1: С помощью uvicorn (рекомендуется)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Способ 2: Через Python
python main.py
Откройте в браузере:

Главная страница: http://localhost:8000

Админка: http://localhost:8000/admin/courses?token=your-secret-token-here

API: http://localhost:8000/api/courses

Вариант 2: Запуск с PostgreSQL (рекомендуется для продакшена)
Установите PostgreSQL и создайте базу данных:

bash
# Для Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Создайте базу данных
sudo -u postgres psql
CREATE DATABASE neural_courses;
CREATE USER neural_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE neural_courses TO neural_user;
\q
Обновите .env файл:

env
DATABASE_URL=postgresql://neural_user:your_password@localhost:5432/neural_courses
ADMIN_TOKEN=your-secret-token-here
PORT=8000
Установите дополнительные зависимости:

bash
pip install psycopg2-binary
☁️ Деплой на Render.com
Шаг 1: Подготовка репозитория
Убедитесь, что в репозитории есть все необходимые файлы:

main.py - основной файл приложения

requirements.txt - зависимости Python

runtime.txt - версия Python (у вас уже есть: python-3.11.0)

render.yaml - конфигурация для Render (опционально)

.env.example или README с настройками

Шаг 2: Создание аккаунта на Render.com
Перейдите на Render.com и зарегистрируйтесь через GitHub

Подключите свой GitHub аккаунт

Шаг 3: Создание Web Service
В Dashboard Render нажмите "New" → "Web Service"

Подключите репозиторий:

Выберите ваш репозиторий neural-courses-catalog

Убедитесь, что ветка main

Настройте конфигурацию:

text
Name: neural-courses-catalog (или любое другое название)
Region: Singapore (или ближайший к вам)
Branch: main
Root Directory: . (если проект в корне)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Добавьте переменные окружения:

text
Key: DATABASE_URL
Value: postgresql://username:password@host:port/database (будет создана на следующем шаге)

Key: ADMIN_TOKEN
Value: your-very-secret-token-12345 (придумайте свой токен)

Key: PYTHON_VERSION
Value: 3.11.0
Шаг 4: Настройка базы данных (PostgreSQL)
Создайте базу данных:

В Dashboard Render нажмите "New" → "PostgreSQL"

Выберите название: neural-courses-db

Выберите регион, совпадающий с Web Service

Нажмите "Create Database"

Получите строку подключения:

После создания базы перейдите в ее настройки

Найдите строку подключения (Connection String)

Скопируйте PostgreSQL connection string

Обновите переменную DATABASE_URL в Web Service:

Вернитесь к настройкам вашего Web Service

В разделе Environment Variables обновите значение DATABASE_URL

Шаг 5: Деплой и настройка
Запустите деплой:

Нажмите "Create Web Service"

Render начнет процесс сборки и деплоя

Проверьте логи:

После деплоя проверьте логи на вкладке "Logs"

Убедитесь, что нет ошибок

Добавьте пользовательский домен (опционально):

В настройках Web Service перейдите в "Custom Domains"

Добавьте свой домен и настройте DNS

Шаг 6: Проверка работоспособности
После успешного деплоя проверьте:

Главная страница: https://your-app-name.onrender.com

API эндпоинты:

GET /api/courses - список курсов

GET /api/course/midjourney-basics - конкретный курс

Админка: https://your-app-name.onrender.com/admin/courses?token=your-secret-token-here
