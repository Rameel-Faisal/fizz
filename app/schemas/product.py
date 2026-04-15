from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    product_name: str
    fiber_id: int
    product_category: Optional[str] = None
    product_type: Optional[str] = None
    quality_required: Optional[int] = None
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    product_name: Optional[str] = None
    fiber_id: Optional[int] = None

class ProductOut(ProductBase):
    product_id: int

    model_config = {"from_attributes": True}