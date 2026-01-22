from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base

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
    tags = Column(Text)  # JSON строка
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
