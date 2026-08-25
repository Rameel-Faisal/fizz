from pydantic import BaseModel
from typing import Optional

class MarketDataBase(BaseModel):
    fiber_id: int
    industry: Optional[str] = None
    year: Optional[int] = None
    country: Optional[str] = None        # ADD
    region: Optional[str] = None
    demand: Optional[float] = None
    demand_unit: Optional[str] = None    # ADD
    price: Optional[float] = None
    price_unit: Optional[str] = None     # ADD
    currency: Optional[str] = None
    source: Optional[str] = None

class MarketDataCreate(MarketDataBase):
    pass

class MarketDataUpdate(MarketDataBase):
    fiber_id: Optional[int] = None

class MarketDataOut(MarketDataBase):
    market_id: int

    model_config = {"from_attributes": True}