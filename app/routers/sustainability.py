from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.sustainability_metric import SustainabilityMetricCreate, SustainabilityMetricOut, SustainabilityMetricUpdate
from app.crud.sustainability_metric import (
    get_sustainability_metric, get_sustainability_metrics, get_by_fiber,
    get_by_year, create_sustainability_metric,
    update_sustainability_metric, delete_sustainability_metric
)
from app.dependencies.db import get_db

router = APIRouter(prefix="/sustainability", tags=["Sustainability"])

@router.get("/", response_model=List[SustainabilityMetricOut])
def list_metrics(
    skip: int = 0,
    limit: int = 100,
    fiber_id: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    if year:
        return get_by_year(db, year)
    return get_sustainability_metrics(db, skip=skip, limit=limit)

@router.post("/", response_model=SustainabilityMetricOut, status_code=201)
def create(payload: SustainabilityMetricCreate, db: Session = Depends(get_db)):
    return create_sustainability_metric(db, payload)

@router.get("/{sustainability_id}", response_model=SustainabilityMetricOut)
def get_one(sustainability_id: int, db: Session = Depends(get_db)):
    obj = get_sustainability_metric(db, sustainability_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Sustainability metric not found")
    return obj

@router.patch("/{sustainability_id}", response_model=SustainabilityMetricOut)
def update(sustainability_id: int, payload: SustainabilityMetricUpdate, db: Session = Depends(get_db)):
    obj = get_sustainability_metric(db, sustainability_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Sustainability metric not found")
    return update_sustainability_metric(db, obj, payload)

@router.delete("/{sustainability_id}", status_code=204)
def delete(sustainability_id: int, db: Session = Depends(get_db)):
    obj = get_sustainability_metric(db, sustainability_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Sustainability metric not found")
    delete_sustainability_metric(db, sustainability_id)