from pydantic import BaseModel
from typing import Optional

class SustainabilityMetricBase(BaseModel):
    fiber_id: int
    year: Optional[int] = None
    co2_emissions: Optional[float] = None
    water_usage: Optional[float] = None
    energy_consumption: Optional[float] = None
    source: Optional[str] = None

class SustainabilityMetricCreate(SustainabilityMetricBase):
    pass

class SustainabilityMetricUpdate(SustainabilityMetricBase):
    fiber_id: Optional[int] = None

class SustainabilityMetricOut(SustainabilityMetricBase):
    sustainability_id: int

    model_config = {"from_attributes": True}