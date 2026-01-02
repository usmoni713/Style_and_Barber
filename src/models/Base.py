from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

class BaseMixin:
    """Миксин с общими полями для всех таблиц."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @declared_attr
    def is_active(cls):
        return Column(Boolean, default=True, nullable=False)


class Base(DeclarativeBase):
    pass

