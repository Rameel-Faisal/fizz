from pydantic import BaseModel
from typing import Optional
from datetime import date

class CultivationBase(BaseModel):
    fiber_id:int
    region:Optional[str]=None
    soil_type:Optional[str]=None
    farming_method:Optional[str]=None
    water_required:Optional[float]=None
    yield_amount:Optional[float]=None
    harvest_date:Optional[date]=None
    source:Optional[str]=None

class CultivationCreate(CultivationBase):
    pass

class CultivationUpdate(CultivationBase):
    fiber_id:Optional[int]=None # optional on update

class CultivationOut(CultivationBase):
    cultivation_id:int

    
    model_config={"from_attributes":True}

