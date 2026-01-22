from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import engine, Base
import sqlite3
import os

app = FastAPI(title="Каталог курсов по нейросетям")

# Создаем таблицы в БД (если их нет)
Base.metadata.create_all(bind=engine)

# Инициализация БД с тестовыми данными
def init_db():
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    
    # Создаем таблицы если они не существуют
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        title TEXT NOT NULL,
        provider TEXT,
        category_slug TEXT,
        level TEXT,
        format TEXT,
        price_from INTEGER,
        duration TEXT,
        tags TEXT,
        short_desc TEXT,
        affiliate_url TEXT,
        is_published BOOLEAN DEFAULT 1,
        clicks INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM courses")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Добавляем тестовые данные
        test_courses = [
            ("midjourney-basics", "Основы Midjourney: генерация изображений", "Нетология", "design", "beginner", "online", 15000, "4 недели", "midjourney,ai,дизайн", "Научитесь создавать изображения с помощью нейросетей", "https://netology.ru/courses/midjourney", 1, 42),
            ("chatgpt-pro", "ChatGPT для профессионалов", "Skillbox", "coding", "middle", "online", 25000, "6 недель", "chatgpt,программирование", "Используйте ChatGPT для автоматизации задач", "https://skillbox.ru/course/chatgpt", 1, 28),
            ("stable-diffusion", "Stable Diffusion с нуля", "Яндекс Практикум", "design", "beginner", "online", 18000, "5 недель", "stable-diffusion,ai", "Создавайте уникальные изображения", "https://practicum.yandex.ru/stable-diffusion", 1, 15),
            ("neural-networks", "Нейронные сети на Python", "Stepik", "coding", "pro", "online", 35000, "8 недель", "python,нейросети,ml", "Погружение в глубокое обучение", "https://stepik.org/course/neural-networks", 1, 37),
            ("ai-marketing", "AI в маркетинге", "GeekBrains", "marketing", "middle", "mixed", 22000, "4 недели", "маркетинг,ai", "Используйте нейросети для маркетинга", "https://gb.ru/courses/ai-marketing", 1, 19),
            ("video-ai", "AI для видеомонтажа", "Coursera", "video", "beginner", "online", 12000, "3 недели", "video,ai", "Автоматизируйте монтаж видео", "https://coursera.org/ai-video", 1, 24)
        ]
        
        cursor.executemany('''
        INSERT INTO courses (slug, title, provider, category_slug, level, format, price_from, duration, tags, short_desc, affiliate_url, is_published, clicks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_courses)
    
    conn.commit()
    conn.close()

# Инициализируем БД при старте
init_db()

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE is_published = 1 ORDER BY clicks DESC LIMIT 6")
    columns = [column[0] for column in cursor.description]
    courses = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "courses": courses})

@app.get("/courses", response_class=HTMLResponse)
async def courses_list(request: Request):
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE is_published = 1")
    columns = [column[0] for column in cursor.description]
    courses = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse("courses.html", {"request": request, "courses": courses})

@app.get("/course/{slug}", response_class=HTMLResponse)
async def course_detail(slug: str, request: Request):
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE slug = ?", (slug,))
    columns = [column[0] for column in cursor.description]
    course_row = cursor.fetchone()
    
    if not course_row:
        conn.close()
        return templates.TemplateResponse("404.html", {"request": request})
    
    course = dict(zip(columns, course_row))
    conn.close()
    return templates.TemplateResponse("course.html", {"request": request, "course": course})

@app.get("/out/{slug}")
async def redirect_out(slug: str, request: Request):
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    
    # Находим курс
    cursor.execute("SELECT id, affiliate_url FROM courses WHERE slug = ?", (slug,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return RedirectResponse("/")
    
    course_id, affiliate_url = result
    
    # Логируем клик
    cursor.execute("INSERT INTO clicks (course_id) VALUES (?)", (course_id,))
    
    # Увеличиваем счетчик кликов у курса
    cursor.execute("UPDATE courses SET clicks = clicks + 1 WHERE id = ?", (course_id,))
    
    conn.commit()
    conn.close()
    
    # Редирект на партнерскую ссылку
    return RedirectResponse(affiliate_url)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
