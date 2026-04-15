from sqlalchemy import Column, Integer,String,Text, Date, Numeric,ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class CultivationData(Base,TimestampMixin):
    __tablename__="cultivation_data"

    cultivation_id = Column(Integer, primary_key=True, index=True)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)
    region = Column(String(100), nullable=True)
    soil_type = Column(String(50), nullable=True)
    farming_method = Column(String(50), nullable=True)
    water_required = Column(Numeric(12, 2), nullable=True)
    yield_amount = Column(Numeric(12, 2), nullable=True)
    harvest_date = Column(Date, nullable=True)
    source = Column(Text, nullable=True)
 
    fiber_type=relationship("FiberType",back_populates="cultivation_records")