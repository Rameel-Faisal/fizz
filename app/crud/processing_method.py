from sqlalchemy.orm import Session
from app.models.processing_method import ProcessingMethod
from app.schemas.processing_method import ProcessingMethodCreate, ProcessingMethodUpdate
from sqlalchemy.exc import SQLAlchemyError 

def get_processing_method(db: Session, processing_id: int):
    return db.query(ProcessingMethod).filter(ProcessingMethod.processing_id == processing_id).first()

def get_processing_methods(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProcessingMethod).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    return db.query(ProcessingMethod).filter(ProcessingMethod.fiber_id == fiber_id).all()

def get_by_process_type(db: Session, process_type: str):
    return db.query(ProcessingMethod).filter(ProcessingMethod.process_type == process_type).all()

def create_processing_method(db: Session, method: ProcessingMethodCreate):
    db_method = ProcessingMethod(**method.model_dump())
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method

def create_processing_method_bulk(db: Session, methods: list[ProcessingMethodCreate]):
    db_objects = [ProcessingMethod(**m.model_dump()) for m in methods]
    db.add_all(db_objects)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    for obj in db_objects:
        db.refresh(obj)
    return db_objects

 
def upsert_processing_method_bulk(db: Session, items: list[ProcessingMethodCreate]):
    inserted_count = 0
    updated_count = 0
    try:
        for item in items:
            data = item.model_dump()
            filters = [ProcessingMethod.fiber_id == data["fiber_id"]]
 
            if data.get("process_type") is not None:
                filters.append(ProcessingMethod.process_type == data["process_type"])
            else:
                filters.append(ProcessingMethod.process_type.is_(None))
 
            existing = db.query(ProcessingMethod).filter(*filters).first()
 
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                updated_count += 1
            else:
                db.add(ProcessingMethod(**data))
                inserted_count += 1
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Upsert batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    return {"inserted": inserted_count, "updated": updated_count, "total": inserted_count + updated_count}
  

def update_processing_method(db: Session, db_method: ProcessingMethod, method: ProcessingMethodUpdate):
    data = method.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_method, field, value)
    db.commit()
    db.refresh(db_method)
    return db_method

def delete_processing_method(db: Session, processing_id: int):
    db_method = db.query(ProcessingMethod).filter(ProcessingMethod.processing_id == processing_id).first()
    db.delete(db_method)
    db.commit()
    return db_method