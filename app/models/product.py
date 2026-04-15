
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)
    product_category = Column(String(50), nullable=True)
    product_type = Column(String(50), nullable=True)
    quality_required = Column(Integer, ForeignKey("fiber_quality.quality_id"), nullable=True)
    description = Column(Text, nullable=True)

    fiber_type = relationship("FiberType", back_populates="products")
    quality = relationship("FiberQuality", back_populates="products")