from pydantic import BaseModel
from typing import Optional
from datetime import date

class FiberQualityBase(BaseModel):
    fiber_id: int
    tensile_strength: Optional[float] = None
    fiber_length: Optional[float] = None
    purity_level: Optional[float] = None
    moisture_content: Optional[float] = None
    elasticity: Optional[float] = None
    quality_grade: Optional[str] = None
    testing_date: Optional[date] = None   # date type, not string
    source: Optional[str] = None

class FiberQualityCreate(FiberQualityBase):
    pass

class FiberQualityUpdate(FiberQualityBase):
    fiber_id: Optional[int] = None        # optional on update

class FiberQualityOut(FiberQualityBase):
    quality_id: int

    model_config = {"from_attributes": True}