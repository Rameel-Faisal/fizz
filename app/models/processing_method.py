from sqlalchemy import Column, Integer,String, Numeric,Text,ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class ProcessingMethod(Base,TimestampMixin):
    __tablename__="processing_methods"

    processing_id = Column(Integer, primary_key=True, index=True)
    fiber_id = Column(Integer, ForeignKey("fiber_types.fiber_id"), nullable=False, index=True)
    process_type = Column(String(80), nullable=True)
    energy_required = Column(Numeric(12, 2), nullable=True)
    chemicals_used = Column(Text, nullable=True)
    source = Column(Text, nullable=True)

    fiber_type = relationship("FiberType", back_populates="processing_methods")