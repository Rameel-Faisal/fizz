from pydantic import BaseModel
from typing import Optional

class ProcessingMethodBase(BaseModel):
    fiber_id: int
    process_type: Optional[str] = None
    energy_required: Optional[float] = None
    chemicals_used: Optional[str] = None
    source: Optional[str] = None

class ProcessingMethodCreate(ProcessingMethodBase):
    pass

class ProcessingMethodUpdate(ProcessingMethodBase):
    fiber_id: Optional[int] = None

class ProcessingMethodOut(ProcessingMethodBase):
    processing_id: int

    model_config = {"from_attributes": True}