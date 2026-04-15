from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class MarketData(Base, TimestampMixin):
    __tablename__ = "market_data"

    market_id = Column(Integer, primary_key=True, index=True)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)
    industry = Column(String(80), nullable=True)
    year = Column(Integer, nullable=True)
    region = Column(String(100), nullable=True)
    demand = Column(Numeric(12, 2), nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=True)
    source = Column(Text, nullable=True)

    fiber_type = relationship("FiberType", back_populates="market_data")