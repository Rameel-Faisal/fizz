from pydantic import BaseModel
from typing import Optional

class MarketDataBase(BaseModel):
    fiber_id: int
    industry: Optional[str] = None
    year: Optional[int] = None
    region: Optional[str] = None
    demand: Optional[float] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    source: Optional[str] = None

class MarketDataCreate(MarketDataBase):
    pass

class MarketDataUpdate(MarketDataBase):
    fiber_id: Optional[int] = None

class MarketDataOut(MarketDataBase):
    market_id: int

    model_config = {"from_attributes": True}