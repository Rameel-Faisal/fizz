from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func

# All models will inherit from this Base
class Base(DeclarativeBase):
    pass

# This Mixin adds created_at and updated_at to any model that uses it
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())