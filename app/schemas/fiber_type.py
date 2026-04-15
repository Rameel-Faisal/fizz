from pydantic import BaseModel
from typing import Optional

class FiberTypeBase(BaseModel):
    fiber_type_name: str
    scientific_name: Optional[str] = None
    notes: Optional[str] = None

class FiberTypeCreate(FiberTypeBase):
    # Used when someone sends a POST request to create a new fiber type
    pass

class FiberTypeUpdate(FiberTypeBase):
    # Used for PATCH requests - all fields optional so you can update just one thing
    fiber_type_name: Optional[str] = None

class FiberTypeOut(FiberTypeBase):
    # Used when sending data back - includes the ID from the database
    fiber_id: int

    model_config = {"from_attributes": True}  # lets pydantic read SQLAlchemy objects