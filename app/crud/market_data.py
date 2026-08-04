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
 

 # UPSERT for market_data — solves the duplicate-import problem.
def upsert_market_data_bulk(db: Session, items: list[MarketDataCreate]):
    """
    Insert or update rows in market_data, matched on the natural key:
    fiber_id + year + region + industry.
 
    - If a row with the same natural key already exists -> UPDATE it with
      the new values (price, demand, source, etc. all get refreshed)
    - If no matching row exists -> INSERT a new row
    - Whole batch is one transaction: if anything fails, everything rolls
      back together, same as the plain bulk insert
 
    Returns a summary dict: {"inserted": X, "updated": Y}
    """
    inserted_count = 0
    updated_count = 0
 
    try:
        for item in items:
            data = item.model_dump()
 
            # Build the match filter for this row's natural key.
            # region and industry can be NULL, so they need `.is_(None)`
            # instead of `== None` — SQL treats NULL comparisons specially,
            # and `column == None` in SQLAlchemy would silently match nothing.
            filters = [
                MarketData.fiber_id == data["fiber_id"],
                MarketData.year == data["year"],
            ]
 
            if data.get("region") is not None:
                filters.append(MarketData.region == data["region"])
            else:
                filters.append(MarketData.region.is_(None))
 
            if data.get("industry") is not None:
                filters.append(MarketData.industry == data["industry"])
            else:
                filters.append(MarketData.industry.is_(None))
 
            existing = db.query(MarketData).filter(*filters).first()
 
            if existing:
                # UPDATE — refresh every field on the existing row
                for field, value in data.items():
                    setattr(existing, field, value)
                updated_count += 1
            else:
                # INSERT — no matching row, this is genuinely new data
                db.add(MarketData(**data))
                inserted_count += 1
 
        db.commit()
 
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(
            f"Upsert batch rejected — database constraint violation: "
            f"{str(e.orig) if hasattr(e, 'orig') else str(e)}"
        )
 
    return {"inserted": inserted_count, "updated": updated_count, "total": inserted_count + updated_count}
    

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