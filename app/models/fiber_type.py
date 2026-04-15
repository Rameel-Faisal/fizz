

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class FiberType(Base, TimestampMixin):
    __tablename__ = "fiber_types"
    __table_args__ = (UniqueConstraint("fiber_type_name"),)

    fiber_id = Column(Integer, primary_key=True, index=True)
    fiber_type_name = Column(String(100), nullable=False)
    scientific_name = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)

    quality_records = relationship("FiberQuality", back_populates="fiber_type")
    products = relationship("Product", back_populates="fiber_type")
    cultivation_records = relationship("CultivationData", back_populates="fiber_type")
    processing_methods = relationship("ProcessingMethod", back_populates="fiber_type")
    sustainability_metrics = relationship("SustainabilityMetric", back_populates="fiber_type")
    market_data = relationship("MarketData", back_populates="fiber_type")