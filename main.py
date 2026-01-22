from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import engine, Base
import sqlite3
import os

app = FastAPI(title="Каталог курсов по нейросетям")

# Создаем таблицы в БД (если их нет) через SQLAlchemy
Base.metadata.create_all(bind=engine)

# Инициализация БД с тестовыми данными
def init_db():
    # используем тот же файл, что и SQLAlchemy: ./courses.db
    db_path = 'courses.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицы если они не существуют (включая поля для referer/utm)
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
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        referer TEXT,
        utm_source TEXT,
        utm_campaign TEXT
    )
    ''')
    
    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM courses")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Добавляем тестовые данные - каждый кортеж имеет 13 полей соответствующих INSERT
        test_courses = [
            ("midjourney-basics", "Основы Midjourney: генерация изображений", "Нетология", "design", "beginner", "online", 15000, "4 недели", "midjourney,ai,art", "Короткое описание по Midjourney", "https://example.com/aff/midjourney", 1, 0),
            ("chatgpt-pro", "ChatGPT для профессионалов", "Skillbox", "coding", "middle", "online", 25000, "6 недель", "chatgpt,ai,programming", "Короткое описание ChatGPT", "https://example.com/aff/chatgpt", 1, 0),
            ("stable-diffusion", "Stable Diffusion с нуля", "Яндекс Практикум", "design", "beginner", "online", 18000, "5 недель", "stable-diffusion,ai", "Короткое описание Stable Diffusion", "https://example.com/aff/stable", 1, 0),
            ("neural-networks", "Нейронные сети на Python", "Stepik", "coding", "pro", "online", 35000, "8 недель", "python,нейросети,ml", "Короткое описание нейросетей", "https://example.com/aff/neural", 1, 0),
            ("ai-marketing", "AI в маркетинге", "GeekBrains", "marketing", "middle", "mixed", 22000, "4 недели", "маркетинг,ai", "Короткое описание AI в маркетинге", "https://example.com/aff/marketing", 1, 0),
            ("video-ai", "AI для видеомонтажа", "Coursera", "video", "beginner", "online", 12000, "3 недели", "video,ai", "Короткое описание AI для видео", "https://example.com/aff/video", 1, 0),
            ("automation-ai", "Автоматизация с помощью AI", "Otus", "automation", "middle", "online", 20000, "5 недель", "automation,ai", "Короткое описание автоматизации", "https://example.com/aff/automation", 1, 0),
            ("ai-business", "AI для бизнеса: стратегия", "Practicum", "business", "pro", "mixed", 40000, "6 недель", "business,ai,strategy", "Короткое описание AI для бизнеса", "https://example.com/aff/business", 1, 0)
            # можно расширить до 20+ записей по аналогии
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
    cursor.execute("SELECT * FROM courses WHERE is_published = 1 ORDER BY created_at DESC")
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
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    
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

    # собираем referer и utm
    referer = request.headers.get("referer")
    utm_source = request.query_params.get("utm_source")
    utm_campaign = request.query_params.get("utm_campaign")
    
    # Логируем клик с деталями
    cursor.execute("INSERT INTO clicks (course_id, referer, utm_source, utm_campaign) VALUES (?, ?, ?, ?)",
                   (course_id, referer, utm_source, utm_campaign))
    
    # Увеличиваем счетчик кликов у курса
    cursor.execute("UPDATE courses SET clicks = clicks + 1 WHERE id = ?", (course_id,))
    
    conn.commit()
    conn.close()
    
    # Редирект на партнерскую ссылку (fallback на /)
    if not affiliate_url:
        return RedirectResponse("/")
    return RedirectResponse(affiliate_url, status_code=302)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
