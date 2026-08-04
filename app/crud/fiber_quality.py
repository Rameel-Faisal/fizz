from sqlalchemy.orm import Session
from app.models.fiber_quality import FiberQuality
from app.schemas.fiber_quality import FiberQualityCreate, FiberQualityUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError


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

from sqlalchemy.exc import SQLAlchemyError

def create_fiber_quality_bulk(db: Session, items: list[FiberQualityCreate]):
    db_objects = [FiberQuality(**i.model_dump()) for i in items]
    db.add_all(db_objects)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    for obj in db_objects:
        db.refresh(obj)
    return db_objects

 
def upsert_fiber_quality_bulk(db: Session, items: list[FiberQualityCreate]):
    inserted_count = 0
    updated_count = 0
    try:
        for item in items:
            data = item.model_dump()
            filters = [FiberQuality.fiber_id == data["fiber_id"]]
 
            if data.get("testing_date") is not None:
                filters.append(FiberQuality.testing_date == data["testing_date"])
            else:
                filters.append(FiberQuality.testing_date.is_(None))
 
            if data.get("source") is not None:
                filters.append(FiberQuality.source == data["source"])
            else:
                filters.append(FiberQuality.source.is_(None))
 
            existing = db.query(FiberQuality).filter(*filters).first()
 
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                updated_count += 1
            else:
                db.add(FiberQuality(**data))
                inserted_count += 1
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Upsert batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    return {"inserted": inserted_count, "updated": updated_count, "total": inserted_count + updated_count}
 

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