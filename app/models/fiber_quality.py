
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class FiberQuality(Base, TimestampMixin):
    __tablename__ = "fiber_quality"

    quality_id = Column(Integer, primary_key=True, index=True)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)

    tensile_strength = Column(Numeric(12, 2), nullable=True)
    fiber_length = Column(Numeric(12, 2), nullable=True)
    purity_level = Column(Numeric(5, 2), nullable=True)
    moisture_content = Column(Numeric(5, 2), nullable=True)
    elasticity = Column(Numeric(5, 2), nullable=True)
    quality_grade = Column(String(10), nullable=True)
    testing_date = Column(Date, nullable=True)
    source = Column(Text, nullable=True)

    fiber_type = relationship("FiberType", back_populates="quality_records")
    products = relationship("Product", back_populates="quality")