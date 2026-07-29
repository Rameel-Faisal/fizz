from sqlalchemy.orm import Session
from app.models.fiber_type import FiberType
from app.schemas.fiber_type import FiberTypeCreate, FiberTypeUpdate

def get_fiber_type(db: Session, fiber_id: int):
    # READ one - find by ID
    return db.query(FiberType).filter(FiberType.fiber_id == fiber_id).first()

def get_fiber_types(db: Session, skip: int = 0, limit: int = 100):
    # READ many - get a list
    return db.query(FiberType).offset(skip).limit(limit).all()

def create_fiber_type(db: Session, fiber: FiberTypeCreate):
    # CREATE - add new row to database
    db_fiber = FiberType(**fiber.model_dump())  # unpack schema into model
    db.add(db_fiber)
    db.commit()       # save to database
    db.refresh(db_fiber)  # reload to get the generated ID
    return db_fiber

def create_fiber_type_bulk(db: Session, fibers: list[FiberTypeCreate]):
    db_objects = [FiberType(**f.model_dump()) for f in fibers]
    db.add_all(db_objects)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    for obj in db_objects:
        db.refresh(obj)
    return db_objects

def update_fiber_type(db: Session, db_fiber: FiberType, fiber: FiberTypeUpdate):
    # UPDATE - change existing row
    data = fiber.model_dump(exclude_unset=True)  # only update fields that were sent
    for field, value in data.items():
        setattr(db_fiber, field, value)
    db.commit()
    db.refresh(db_fiber)
    return db_fiber

def delete_fiber_type(db: Session, fiber_id: int):
    # DELETE - remove a row
    db_fiber = db.query(FiberType).filter(FiberType.fiber_id == fiber_id).first()
    db.delete(db_fiber)
    db.commit()
    return db_fiber

