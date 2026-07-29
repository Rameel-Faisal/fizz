from sqlalchemy.orm import Session
from app.models.sustainability_metric import SustainabilityMetric
from app.schemas.sustainability_metric import SustainabilityMetricCreate, SustainabilityMetricUpdate

def get_sustainability_metric(db: Session, sustainability_id: int):
    return db.query(SustainabilityMetric).filter(SustainabilityMetric.sustainability_id == sustainability_id).first()

def get_sustainability_metrics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SustainabilityMetric).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    return db.query(SustainabilityMetric).filter(SustainabilityMetric.fiber_id == fiber_id).all()

def get_by_year(db: Session, year: int):
    return db.query(SustainabilityMetric).filter(SustainabilityMetric.year == year).all()

def create_sustainability_metric(db: Session, metric: SustainabilityMetricCreate):
    db_metric = SustainabilityMetric(**metric.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

def create_sustainability_metric_bulk(db: Session, metrics: list[SustainabilityMetricCreate]):
    db_objects = [SustainabilityMetric(**m.model_dump()) for m in metrics]
    db.add_all(db_objects)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    for obj in db_objects:
        db.refresh(obj)
    return db_objects

def update_sustainability_metric(db: Session, db_metric: SustainabilityMetric, metric: SustainabilityMetricUpdate):
    data = metric.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_metric, field, value)
    db.commit()
    db.refresh(db_metric)
    return db_metric

def delete_sustainability_metric(db: Session, sustainability_id: int):
    db_metric = db.query(SustainabilityMetric).filter(SustainabilityMetric.sustainability_id == sustainability_id).first()
    db.delete(db_metric)
    db.commit()
    return db_metric