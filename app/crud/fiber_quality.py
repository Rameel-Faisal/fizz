from sqlalchemy.orm import Session
from app.models.fiber_quality import FiberQuality
from app.schemas.fiber_quality import FiberQualityCreate, FiberQualityUpdate

def get_fiber_quality(db: Session, quality_id: int):
    return db.query(FiberQuality).filter(FiberQuality.quality_id == quality_id).first()

def get_fiber_qualities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(FiberQuality).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    # extra filter — get all quality records for a specific fiber
    return db.query(FiberQuality).filter(FiberQuality.fiber_id == fiber_id).all()

def get_by_grade(db: Session, grade: str):
    # extra filter — get all records with a specific grade
    return db.query(FiberQuality).filter(FiberQuality.quality_grade == grade).all()

def create_fiber_quality(db: Session, quality: FiberQualityCreate):
    db_quality = FiberQuality(**quality.model_dump())
    db.add(db_quality)
    db.commit()
    db.refresh(db_quality)
    return db_quality

def update_fiber_quality(db: Session, db_quality: FiberQuality, quality: FiberQualityUpdate):
    data = quality.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_quality, field, value)
    db.commit()
    db.refresh(db_quality)
    return db_quality

def delete_fiber_quality(db: Session, quality_id: int):
    db_quality = db.query(FiberQuality).filter(FiberQuality.quality_id == quality_id).first()
    db.delete(db_quality)
    db.commit()
    return db_quality