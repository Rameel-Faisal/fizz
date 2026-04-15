from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.cultivation_data import CultivationCreate, CultivationOut, CultivationUpdate
from app.crud.cultivation_data import (
    get_cultivation, get_cultivations, get_by_fiber,
    get_by_region, create_cultivation, update_cultivation, delete_cultivation
)
from app.dependencies.db import get_db

router = APIRouter(prefix="/cultivation-data", tags=["Cultivation Data"])

@router.get("/", response_model=List[CultivationOut])
def list_cultivations(
    skip: int = 0,
    limit: int = 100,
    fiber_id: Optional[int] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    if region:
        return get_by_region(db, region)
    return get_cultivations(db, skip=skip, limit=limit)

@router.post("/", response_model=CultivationOut, status_code=201)
def create(payload: CultivationCreate, db: Session = Depends(get_db)):
    return create_cultivation(db, payload)

@router.get("/{cultivation_id}", response_model=CultivationOut)
def get_one(cultivation_id: int, db: Session = Depends(get_db)):
    obj = get_cultivation(db, cultivation_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cultivation record not found")
    return obj

@router.patch("/{cultivation_id}", response_model=CultivationOut)
def update(cultivation_id: int, payload: CultivationUpdate, db: Session = Depends(get_db)):
    obj = get_cultivation(db, cultivation_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cultivation record not found")
    return update_cultivation(db, obj, payload)

@router.delete("/{cultivation_id}", status_code=204)
def delete(cultivation_id: int, db: Session = Depends(get_db)):
    obj = get_cultivation(db, cultivation_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cultivation record not found")
    delete_cultivation(db, cultivation_id)