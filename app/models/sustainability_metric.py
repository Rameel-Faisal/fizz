from sqlalchemy import Column, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class SustainabilityMetric(Base, TimestampMixin):
    __tablename__ = "sustainability_metrics"

    sustainability_id = Column(Integer, primary_key=True, index=True)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)
    year = Column(Integer, nullable=True)
    co2_emissions = Column(Numeric(12, 2), nullable=True)
    water_usage = Column(Numeric(12, 2), nullable=True)
    energy_consumption = Column(Numeric(12, 2), nullable=True)
    source = Column(Text, nullable=True)

    fiber_type = relationship("FiberType", back_populates="sustainability_metrics")