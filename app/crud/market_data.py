from sqlalchemy.orm import Session
from app.models.market_data import MarketData
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate
from sqlalchemy.exc import SQLAlchemyError 

def get_market_data(db: Session, market_id: int):
    return db.query(MarketData).filter(MarketData.market_id == market_id).first()

def get_market_data_list(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MarketData).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    return db.query(MarketData).filter(MarketData.fiber_id == fiber_id).all()

def get_by_industry(db: Session, industry: str):
    return db.query(MarketData).filter(MarketData.industry == industry).all()

def get_by_region(db: Session, region: str):
    return db.query(MarketData).filter(MarketData.region == region).all()

def create_market_data(db: Session, market: MarketDataCreate):
    db_market = MarketData(**market.model_dump())
    db.add(db_market)
    db.commit()
    db.refresh(db_market)
    return db_market

 
def create_market_data_bulk(db: Session, items: list[MarketDataCreate]):
    db_objects = [MarketData(**i.model_dump()) for i in items]
    db.add_all(db_objects)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    for obj in db_objects:
        db.refresh(obj)
    return db_objects
 

def update_market_data(db: Session, db_market: MarketData, market: MarketDataUpdate):
    data = market.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_market, field, value)
    db.commit()
    db.refresh(db_market)
    return db_market

def delete_market_data(db: Session, market_id: int):
    db_market = db.query(MarketData).filter(MarketData.market_id == market_id).first()
    db.delete(db_market)
    db.commit()
    return db_market