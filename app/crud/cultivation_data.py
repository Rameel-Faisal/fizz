from sqlalchemy.orm import Session
from app.models.cultivation_data import CultivationData
from app.schemas.cultivation_data import CultivationCreate, CultivationUpdate
from sqlalchemy.exc import SQLAlchemyError

def get_cultivation(db: Session, cultivation_id: int):
    return db.query(CultivationData).filter(
        CultivationData.cultivation_id == cultivation_id
    ).first()

def get_cultivations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CultivationData).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    return db.query(CultivationData).filter(
        CultivationData.fiber_id == fiber_id
    ).all()

def get_by_region(db: Session, region: str):
    return db.query(CultivationData).filter(
        CultivationData.region == region
    ).all()

def create_cultivation(db: Session, cultivation: CultivationCreate):
    db_cultivation = CultivationData(**cultivation.model_dump())
    db.add(db_cultivation)
    db.commit()
    db.refresh(db_cultivation)
    return db_cultivation

def create_cultivation_bulk(db: Session, items: list[CultivationCreate]):
    db_objects = [CultivationData(**c.model_dump()) for c in items]
    db.add_all(db_objects)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    for obj in db_objects:
        db.refresh(obj)
    return db_objects
 
def upsert_cultivation_bulk(db: Session, items: list[CultivationCreate]):
    inserted_count = 0
    updated_count = 0
    try:
        for item in items:
            data = item.model_dump()
            filters = [CultivationData.fiber_id == data["fiber_id"]]
 
            if data.get("country") is not None:
                filters.append(CultivationData.country == data["country"])
            else:
                filters.append(CultivationData.country.is_(None))
 
            if data.get("region") is not None:
                filters.append(CultivationData.region == data["region"])
            else:
                filters.append(CultivationData.region.is_(None))
 
            if data.get("harvest_date") is not None:
                filters.append(CultivationData.harvest_date == data["harvest_date"])
            else:
                filters.append(CultivationData.harvest_date.is_(None))
 
            existing = db.query(CultivationData).filter(*filters).first()
 
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                updated_count += 1
            else:
                db.add(CultivationData(**data))
                inserted_count += 1
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Upsert batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    return {"inserted": inserted_count, "updated": updated_count, "total": inserted_count + updated_count}

def update_cultivation(db: Session, db_cultivation: CultivationData, cultivation: CultivationUpdate):
    data = cultivation.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_cultivation, field, value)
    db.commit()
    db.refresh(db_cultivation)
    return db_cultivation

def delete_cultivation(db: Session, cultivation_id: int):
    db_cultivation = db.query(CultivationData).filter(
        CultivationData.cultivation_id == cultivation_id
    ).first()
    db.delete(db_cultivation)
    db.commit()
    return db_cultivation