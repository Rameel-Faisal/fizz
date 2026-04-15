from sqlalchemy.orm import Session
from app.models.processing_method import ProcessingMethod
from app.schemas.processing_method import ProcessingMethodCreate, ProcessingMethodUpdate

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