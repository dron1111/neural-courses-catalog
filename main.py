from fastapi import FastAPI, Request, Depends, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
from pydantic import Field
from typing import Union
from typing import Optional
import urllib.parse

# ================== НАСТРОЙКА БАЗЫ ДАННЫХ ==================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./courses.db")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ДЛЯ SQLite: добавляем параметры для работы в многопоточном режиме
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},  # Важно для SQLite + FastAPI
        poolclass=StaticPool  # Для SQLite в многопоточном режиме
    )
else:
    # Для PostgreSQL оставляем как было
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================== МОДЕЛИ ==================
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    provider = Column(String)
    category_slug = Column(String)
    level = Column(String)  # beginner|middle|pro
    format = Column(String)  # online|offline|mixed
    price_from = Column(Integer)
    duration = Column(String)
    tags = Column(Text)
    short_desc = Column(Text)
    affiliate_url = Column(String)
    is_published = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Click(Base):
    __tablename__ = "clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, index=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    referer = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)

# ================== ИНИЦИАЛИЗАЦИЯ FASTAPI ==================
app = FastAPI(title="Каталог курсов по нейросетям")

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Настройка статики и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def add_test_data():
    """Добавление тестовых данных (минимум 20 курсов)"""
    db = SessionLocal()
    
    # Проверяем, есть ли уже данные
    count = db.query(Course).count()
    if count > 0:
        db.close()
        return
    
    test_courses = [
        # design (4 курса)
        ("midjourney-basics", "Основы Midjourney: генерация изображений", "Нетология", "design", "beginner", "online", 15000, "4 недели", "midjourney,ai,art,design", "Научитесь создавать креативные изображения с помощью нейросетей", "https://example.com/aff/midjourney", True, 42),
        ("stable-diffusion", "Stable Diffusion с нуля", "Яндекс Практикум", "design", "beginner", "online", 18000, "5 недель", "stable-diffusion,ai,art", "Создавайте уникальные изображения и арты", "https://example.com/aff/stable", True, 28),
        ("figma-ai", "Дизайн интерфейсов с AI в Figma", "Contented", "design", "middle", "online", 28000, "6 недель", "figma,ui/ux,ai,design", "Автоматизируйте дизайн-процесс с помощью AI", "https://example.com/aff/figma-ai", True, 15),
        ("ai-photo", "AI-обработка фотографий", "Photoshop", "design", "pro", "offline", 35000, "8 недель", "photoshop,ai,photo,editing", "Профессиональная ретушь с нейросетями", "https://example.com/aff/ai-photo", True, 8),
        
        # video (3 курса)
        ("video-ai", "AI для видеомонтажа", "Coursera", "video", "beginner", "online", 12000, "3 недели", "video,ai,editing", "Автоматизируйте монтаж видео", "https://example.com/aff/video", True, 24),
        ("ai-video-pro", "AI-инструменты для продвинутого монтажа", "Skillbox", "video", "pro", "mixed", 45000, "8 недель", "premiere pro,ai,video,editing", "Продвинутые техники монтажа с AI", "https://example.com/aff/video-pro", True, 12),
        ("youtube-ai", "Создание контента для YouTube с AI", "Нетология", "video", "middle", "online", 22000, "4 недели", "youtube,ai,video,content", "Генерация идей и автоматизация производства", "https://example.com/aff/youtube", True, 19),
        
        # marketing (3 курса)
        ("ai-marketing", "AI в маркетинге", "GeekBrains", "marketing", "middle", "mixed", 22000, "4 недели", "маркетинг,ai,analytics", "Используйте нейросети для маркетинга", "https://example.com/aff/marketing", True, 31),
        ("smm-ai", "AI для SMM-специалистов", "Skillfactory", "marketing", "beginner", "online", 15000, "5 недель", "smm,ai,social media", "Автоматизация постинга и анализ аудитории", "https://example.com/aff/smm", True, 22),
        ("seo-ai", "SEO и контент с искусственным интеллектом", "Яндекс Практикум", "marketing", "pro", "online", 32000, "6 недель", "seo,ai,content,marketing", "Оптимизация сайтов с помощью AI", "https://example.com/aff/seo", True, 14),
        
        # automation (3 курса)
        ("automation-ai", "Автоматизация с помощью AI", "Otus", "automation", "middle", "online", 20000, "5 недель", "automation,ai,scripts", "Создание автоматических скриптов", "https://example.com/aff/automation", True, 17),
        ("ai-zapier", "Автоматизация бизнеса: AI + Zapier", "Нетология", "automation", "beginner", "online", 18000, "4 недели", "zapier,automation,no-code", "Настройка автоматических workflow", "https://example.com/aff/zapier", True, 26),
        ("rpa-ai", "RPA и AI для автоматизации процессов", "Stepik", "automation", "pro", "mixed", 38000, "7 недель", "rpa,ai,automation,business", "Роботизация бизнес-процессов", "https://example.com/aff/rpa", True, 9),
        
        # coding (4 курса)
        ("chatgpt-pro", "ChatGPT для профессионалов", "Skillbox", "coding", "middle", "online", 25000, "6 недель", "chatgpt,ai,programming", "Используйте ChatGPT для автоматизации задач", "https://example.com/aff/chatgpt", True, 37),
        ("neural-networks", "Нейронные сети на Python", "Stepik", "coding", "pro", "online", 35000, "8 недель", "python,нейросети,ml,ai", "Погружение в глубокое обучение", "https://example.com/aff/neural", True, 45),
        ("python-ml-basics", "Машинное обучение на Python с нуля", "Coursera", "coding", "beginner", "online", 5000, "6 недель", "python,ml,data science", "Введение в машинное обучение", "https://example.com/aff/python-ml", True, 33),
        ("ai-api", "Разработка AI-приложений и API", "Яндекс Практикум", "coding", "pro", "mixed", 42000, "9 недель", "python,api,ai,development", "Создание микросервисов с AI", "https://example.com/aff/ai-api", True, 11),
        
        # business (3 курса)
        ("ai-business", "AI для бизнеса: стратегия", "Practicum", "business", "pro", "mixed", 40000, "6 недель", "business,ai,strategy", "Внедрение AI в бизнес-процессы", "https://example.com/aff/business", True, 18),
        ("ai-startup", "Запуск AI-стартапа", "Нетология", "business", "middle", "online", 28000, "5 недель", "startup,ai,business,entrepreneurship", "От идеи к MVP с использованием AI", "https://example.com/aff/startup", True, 23),
        ("ai-analytics", "Аналитика данных для бизнеса с AI", "GeekBrains", "business", "beginner", "online", 19000, "4 недели", "analytics,ai,business,data", "Принятие решений на основе данных", "https://example.com/aff/analytics", True, 16)
    ]
    
    for course_data in test_courses:
        course = Course(
            slug=course_data[0],
            title=course_data[1],
            provider=course_data[2],
            category_slug=course_data[3],
            level=course_data[4],
            format=course_data[5],
            price_from=course_data[6],
            duration=course_data[7],
            tags=course_data[8],
            short_desc=course_data[9],
            affiliate_url=course_data[10],
            is_published=course_data[11],
            clicks=course_data[12]
        )
        db.add(course)
    
    db.commit()
    db.close()

# Инициализируем данные при старте
add_test_data()

# ================== ПУБЛИЧНЫЕ РОУТЫ ==================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Главная страница с популярными курсами"""
    courses = db.query(Course).filter(
        Course.is_published == True
    ).order_by(Course.clicks.desc()).limit(8).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "courses": courses
    })

@app.get("/courses", response_class=HTMLResponse)
async def courses_list(
    request: Request,
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    price_min: Optional[str] = Query(None), 
    price_max: Optional[str] = Query(None),
    sort: str = Query("popular"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Каталог курсов с фильтрами, поиском и сортировкой"""
    # Базовый запрос
    db_query = db.query(Course).filter(Course.is_published == True)
    
    # ПРИМЕНЕНИЕ ФИЛЬТРОВ
    if query:
        search_term = f"%{query}%"
        db_query = db_query.filter(
            (Course.title.ilike(search_term)) | 
            (Course.tags.ilike(search_term)) |
            (Course.short_desc.ilike(search_term))
        )
    
    if category and category != "all":
        db_query = db_query.filter(Course.category_slug == category)
    
    if level and level != "all":
        db_query = db_query.filter(Course.level == level)
    
    if format and format != "all":
        db_query = db_query.filter(Course.format == format)
    
    if price_min is not None:
        db_query = db_query.filter(Course.price_from >= price_min)
    
    if price_max is not None:
        db_query = db_query.filter(Course.price_from <= price_max)
    
    # ПРИМЕНЕНИЕ СОРТИРОВКИ
    if sort == "new":
        db_query = db_query.order_by(Course.created_at.desc())
    elif sort == "price_asc":
        db_query = db_query.order_by(Course.price_from.asc())
    elif sort == "price_desc":
        db_query = db_query.order_by(Course.price_from.desc())
    else:  # "popular" по умолчанию
        db_query = db_query.order_by(Course.clicks.desc())
    
    # ПАГИНАЦИЯ
    per_page = 9  # Курсов на странице
    total_courses = db_query.count()
    total_pages = (total_courses + per_page - 1) // per_page if total_courses > 0 else 1
    page = max(1, min(page, total_pages))
    
    # Получаем курсы для текущей страницы
    offset = (page - 1) * per_page
    courses = db_query.offset(offset).limit(per_page).all()
    
    # Получаем уникальные категории для фильтра
    categories = db.query(Course.category_slug).filter(Course.is_published == True).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "courses": courses,
        "current_query": query,
        "current_category": category,
        "current_level": level,
        "current_format": format,
        "current_price_min": price_min,
        "current_price_max": price_max,
        "current_sort": sort,
        "current_page": page,
        "total_pages": total_pages,
        "total_courses": total_courses,
        "available_categories": categories,
        "price_range": {
            "min": db.query(func.min(Course.price_from)).filter(Course.is_published == True).scalar() or 0,
            "max": db.query(func.max(Course.price_from)).filter(Course.is_published == True).scalar() or 100000
        }
    })

@app.get("/category/{category_slug}", response_class=HTMLResponse)
async def category_list(
    request: Request,
    category_slug: str,
    query: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    sort: str = Query("popular"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Страница категории с фильтрами"""
    # Базовый запрос с фильтром по категории
    db_query = db.query(Course).filter(
        Course.is_published == True,
        Course.category_slug == category_slug
    )
    
    # Дополнительные фильтры
    if query:
        search_term = f"%{query}%"
        db_query = db_query.filter(
            (Course.title.ilike(search_term)) | 
            (Course.tags.ilike(search_term))
        )
    
    if level and level != "all":
        db_query = db_query.filter(Course.level == level)
    
    if format and format != "all":
        db_query = db_query.filter(Course.format == format)
    
    if price_min is not None:
        db_query = db_query.filter(Course.price_from >= price_min)
    
    if price_max is not None:
        db_query = db_query.filter(Course.price_from <= price_max)
    
    # Сортировка
    if sort == "new":
        db_query = db_query.order_by(Course.created_at.desc())
    elif sort == "price_asc":
        db_query = db_query.order_by(Course.price_from.asc())
    elif sort == "price_desc":
        db_query = db_query.order_by(Course.price_from.desc())
    else:
        db_query = db_query.order_by(Course.clicks.desc())
    
    # Пагинация
    per_page = 9
    total_courses = db_query.count()
    total_pages = (total_courses + per_page - 1) // per_page if total_courses > 0 else 1
    page = max(1, min(page, total_pages))
    
    courses = db_query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Название категории для отображения
    category_names = {
        "design": "Дизайн",
        "video": "Видео",
        "marketing": "Маркетинг",
        "automation": "Автоматизация",
        "coding": "Программирование",
        "business": "Бизнес"
    }
    
    category_name = category_names.get(category_slug, category_slug)
    
    return templates.TemplateResponse("category.html", {
        "request": request,
        "courses": courses,
        "category_slug": category_slug,
        "category_name": category_name,
        "current_query": query,
        "current_level": level,
        "current_format": format,
        "current_price_min": price_min,
        "current_price_max": price_max,
        "current_sort": sort,
        "current_page": page,
        "total_pages": total_pages,
        "total_courses": total_courses
    })

@app.get("/course/{slug}", response_class=HTMLResponse)
async def course_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    """Карточка курса"""
    course = db.query(Course).filter(Course.slug == slug).first()
    
    if not course:
        return templates.TemplateResponse("404.html", {
            "request": request
        }, status_code=404)
    
    # Разделяем теги для отображения
    tags_list = course.tags.split(",") if course.tags else []
    
    return templates.TemplateResponse("course.html", {
        "request": request,
        "course": course,
        "tags_list": tags_list
    })

@app.get("/out/{slug}")
async def redirect_out(
    slug: str, 
    request: Request,
    utm_source: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Редирект на партнерку с логированием клика"""
    course = db.query(Course).filter(Course.slug == slug).first()
    
    if not course:
        return RedirectResponse("/")
    
    # Логируем клик
    referer = request.headers.get("referer")
    click = Click(
        course_id=course.id,
        referer=referer,
        utm_source=utm_source,
        utm_campaign=utm_campaign
    )
    db.add(click)
    
    # Увеличиваем счетчик кликов
    course.clicks += 1
    db.commit()
    
    # Редирект на партнерскую ссылку
    if not course.affiliate_url:
        return RedirectResponse("/")
    
    return RedirectResponse(course.affiliate_url, status_code=302)



# ================== API ЭНДПОИНТЫ ==================

@app.get("/api/courses")
async def api_courses_list(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    sort: str = Query("popular"),
    query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """API для получения списка курсов"""
    db_query = db.query(Course).filter(Course.is_published == True)
    
    if category and category != "all":
        db_query = db_query.filter(Course.category_slug == category)
    
    if level and level != "all":
        db_query = db_query.filter(Course.level == level)
    
    if format and format != "all":
        db_query = db_query.filter(Course.format == format)
    
    if price_min is not None:
        db_query = db_query.filter(Course.price_from >= price_min)
    
    if price_max is not None:
        db_query = db_query.filter(Course.price_from <= price_max)
    
    if query:
        search = f"%{query}%"
        db_query = db_query.filter(
            (Course.title.ilike(search)) | 
            (Course.tags.ilike(search))
        )
    
    if sort == "new":
        db_query = db_query.order_by(Course.created_at.desc())
    elif sort == "price_asc":
        db_query = db_query.order_by(Course.price_from.asc())
    elif sort == "price_desc":
        db_query = db_query.order_by(Course.price_from.desc())
    else:
        db_query = db_query.order_by(Course.clicks.desc())
    
    total = db_query.count()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = max(1, min(page, total_pages))
    
    courses = db_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "courses": [
            {
                "id": c.id,
                "slug": c.slug,
                "title": c.title,
                "provider": c.provider,
                "price_from": c.price_from,
                "duration": c.duration,
                "level": c.level,
                "format": c.format,
                "category_slug": c.category_slug,
                "clicks": c.clicks,
                "short_desc": c.short_desc,
                "tags": c.tags.split(",") if c.tags else []
            }
            for c in courses
        ]
    }

@app.get("/api/course/{slug}")
async def api_course_detail(slug: str, db: Session = Depends(get_db)):
    """API для получения курса по slug"""
    course = db.query(Course).filter(Course.slug == slug).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {
        "id": course.id,
        "slug": course.slug,
        "title": course.title,
        "provider": course.provider,
        "category_slug": course.category_slug,
        "level": course.level,
        "format": course.format,
        "price_from": course.price_from,
        "duration": course.duration,
        "tags": course.tags.split(",") if course.tags else [],
        "short_desc": course.short_desc,
        "affiliate_url": course.affiliate_url,
        "is_published": course.is_published,
        "clicks": course.clicks,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None
    }

# ================== АДМИНКА ==================

def check_admin_token(token: str):
    """Проверка токена админки"""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")

@app.get("/admin/courses", response_class=HTMLResponse)
async def admin_courses_list(
    request: Request,
    token: str = Query(...),
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Список всех курсов в админке"""
    check_admin_token(token)
    
    # Получаем курсы с пагинацией
    per_page = 20
    db_query = db.query(Course).order_by(Course.created_at.desc())
    total = db_query.count()
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    
    courses = db_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse("admin/courses.html", {
        "request": request,
        "courses": courses,
        "token": token,
        "current_page": page,
        "total_pages": total_pages,
        "total_courses": total
    })

@app.get("/admin/course/new", response_class=HTMLResponse)
async def admin_course_new_form(request: Request, token: str = Query(...)):
    """Форма создания нового курса"""
    check_admin_token(token)
    
    return templates.TemplateResponse("admin/course_form.html", {
        "request": request,
        "course": None,
        "token": token,
        "is_new": True
    })

@app.post("/admin/course/new")
async def admin_course_create(
    request: Request,
    token: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    provider: str = Form(...),
    category_slug: str = Form(...),
    level: str = Form(...),
    format: str = Form(...),
    price_from: int = Form(...),
    duration: str = Form(...),
    tags: str = Form(...),
    short_desc: str = Form(...),
    affiliate_url: str = Form(...),
    is_published: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Создание нового курса"""
    check_admin_token(token)
    
    # Проверяем, существует ли уже такой slug
    existing = db.query(Course).filter(Course.slug == slug).first()
    if existing:
        return templates.TemplateResponse("admin/course_form.html", {
            "request": request,
            "course": None,
            "token": token,
            "is_new": True,
            "error": "Курс с таким slug уже существует"
        })
    
    # Создаем новый курс
    course = Course(
        slug=slug,
        title=title,
        provider=provider,
        category_slug=category_slug,
        level=level,
        format=format,
        price_from=price_from,
        duration=duration,
        tags=tags,
        short_desc=short_desc,
        affiliate_url=affiliate_url,
        is_published=is_published
    )
    
    db.add(course)
    db.commit()
    
    return RedirectResponse(f"/admin/courses?token={token}", status_code=303)

@app.get("/admin/course/{course_id}", response_class=HTMLResponse)
async def admin_course_edit_form(
    request: Request,
    course_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Форма редактирования курса"""
    check_admin_token(token)
    
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return templates.TemplateResponse("admin/course_form.html", {
        "request": request,
        "course": course,
        "token": token,
        "is_new": False
    })

@app.post("/admin/course/{course_id}")
async def admin_course_update(
    request: Request,
    course_id: int,
    token: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    provider: str = Form(...),
    category_slug: str = Form(...),
    level: str = Form(...),
    format: str = Form(...),
    price_from: int = Form(...),
    duration: str = Form(...),
    tags: str = Form(...),
    short_desc: str = Form(...),
    affiliate_url: str = Form(...),
    is_published: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Обновление курса"""
    check_admin_token(token)
    
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Проверяем slug на уникальность (кроме текущего курса)
    existing = db.query(Course).filter(Course.slug == slug, Course.id != course_id).first()
    if existing:
        return templates.TemplateResponse("admin/course_form.html", {
            "request": request,
            "course": course,
            "token": token,
            "is_new": False,
            "error": "Курс с таким slug уже существует"
        })
    
    # Обновляем поля
    course.slug = slug
    course.title = title
    course.provider = provider
    course.category_slug = category_slug
    course.level = level
    course.format = format
    course.price_from = price_from
    course.duration = duration
    course.tags = tags
    course.short_desc = short_desc
    course.affiliate_url = affiliate_url
    course.is_published = is_published
    
    db.commit()
    
    return RedirectResponse(f"/admin/courses?token={token}", status_code=303)

@app.get("/api/admin/courses")
async def api_admin_courses_list(
    token: str = Query(...),
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """API для админки: список всех курсов"""
    check_admin_token(token)
    
    db_query = db.query(Course).order_by(Course.created_at.desc())
    total = db_query.count()
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    
    courses = db_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "courses": [
            {
                "id": c.id,
                "slug": c.slug,
                "title": c.title,
                "provider": c.provider,
                "category_slug": c.category_slug,
                "level": c.level,
                "format": c.format,
                "price_from": c.price_from,
                "duration": c.duration,
                "tags": c.tags,
                "short_desc": c.short_desc,
                "affiliate_url": c.affiliate_url,
                "is_published": c.is_published,
                "clicks": c.clicks,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            }
            for c in courses
        ]
    }
# ================== АДМИНКА ==================

def check_admin_token(token: str):
    """Проверка токена админки (самая простая защита)"""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Неверный токен админки")

@app.get("/admin/courses", response_class=HTMLResponse)
async def admin_courses_list(
    request: Request,
    token: str = Query(...),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Список всех курсов в админке"""
    check_admin_token(token)
    
    # Пагинация
    per_page = 20
    db_query = db.query(Course).order_by(Course.created_at.desc())
    total = db_query.count()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = max(1, min(page, total_pages))
    
    courses = db_query.offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse("admin/courses.html", {
        "request": request,
        "courses": courses,
        "token": token,
        "current_page": page,
        "total_pages": total_pages,
        "total_courses": total
    })

@app.get("/admin/course/new", response_class=HTMLResponse)
async def admin_course_new_form(request: Request, token: str = Query(...)):
    """Форма создания нового курса"""
    check_admin_token(token)
    
    return templates.TemplateResponse("admin/course_form.html", {
        "request": request,
        "course": None,
        "token": token,
        "is_new": True
    })

@app.post("/admin/course/new")
async def admin_course_create(
    request: Request,
    token: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    provider: str = Form(...),
    category_slug: str = Form(...),
    level: str = Form(...),
    format: str = Form(...),
    price_from: int = Form(...),
    duration: str = Form(...),
    tags: str = Form(...),
    short_desc: str = Form(...),
    affiliate_url: str = Form(...),
    is_published: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Создание нового курса"""
    check_admin_token(token)
    
    # Проверяем уникальность slug
    existing = db.query(Course).filter(Course.slug == slug).first()
    if existing:
        return templates.TemplateResponse("admin/course_form.html", {
            "request": request,
            "course": None,
            "token": token,
            "is_new": True,
            "error": "Курс с таким URL-адресом (slug) уже существует"
        })
    
    # Создаем курс
    course = Course(
        slug=slug,
        title=title,
        provider=provider,
        category_slug=category_slug,
        level=level,
        format=format,
        price_from=price_from,
        duration=duration,
        tags=tags,
        short_desc=short_desc,
        affiliate_url=affiliate_url,
        is_published=is_published
    )
    
    db.add(course)
    db.commit()
    
    # Редирект на список курсов
    return RedirectResponse(f"/admin/courses?token={token}", status_code=303)

@app.get("/admin/course/{course_id}", response_class=HTMLResponse)
async def admin_course_edit_form(
    request: Request,
    course_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Форма редактирования курса"""
    check_admin_token(token)
    
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    return templates.TemplateResponse("admin/course_form.html", {
        "request": request,
        "course": course,
        "token": token,
        "is_new": False
    })

@app.post("/admin/course/{course_id}")
async def admin_course_update(
    request: Request,
    course_id: int,
    token: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    provider: str = Form(...),
    category_slug: str = Form(...),
    level: str = Form(...),
    format: str = Form(...),
    price_from: int = Form(...),
    duration: str = Form(...),
    tags: str = Form(...),
    short_desc: str = Form(...),
    affiliate_url: str = Form(...),
    is_published: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Обновление курса"""
    check_admin_token(token)
    
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Проверяем slug на уникальность (кроме текущего курса)
    existing = db.query(Course).filter(Course.slug == slug, Course.id != course_id).first()
    if existing:
        return templates.TemplateResponse("admin/course_form.html", {
            "request": request,
            "course": course,
            "token": token,
            "is_new": False,
            "error": "Курс с таким URL-адресом (slug) уже существует"
        })
    
    # Обновляем поля
    course.slug = slug
    course.title = title
    course.provider = provider
    course.category_slug = category_slug
    course.level = level
    course.format = format
    course.price_from = price_from
    course.duration = duration
    course.tags = tags
    course.short_desc = short_desc
    course.affiliate_url = affiliate_url
    course.is_published = is_published
    
    db.commit()
    
    return RedirectResponse(f"/admin/courses?token={token}", status_code=303)

@app.get("/admin/delete/{course_id}")
async def admin_course_delete(
    course_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Удаление курса (опционально)"""
    check_admin_token(token)
    
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if course:
        db.delete(course)
        db.commit()
    
    return RedirectResponse(f"/admin/courses?token={token}")
# ================== ЗАПУСК ==================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
