from sqlalchemy.orm import Session
from app.models.cultivation_data import CultivationData
from app.schemas.cultivation_data import CultivationCreate, CultivationUpdate

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