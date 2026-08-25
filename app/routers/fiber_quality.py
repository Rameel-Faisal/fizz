from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.fiber_quality import FiberQualityCreate, FiberQualityOut, FiberQualityUpdate
from app.crud.fiber_quality import (
    get_fiber_quality, get_fiber_qualities, get_by_fiber,
    get_by_grade, create_fiber_quality, update_fiber_quality, delete_fiber_quality,create_fiber_quality_bulk,upsert_fiber_quality_bulk
)
from app.dependencies.db import get_db
from app.dependencies.auth import verify_api_key


router = APIRouter(prefix="/fiber-quality", tags=["Fiber Quality"])

@router.post("/bulk", response_model=list[FiberQualityOut], status_code=201)
def create_fiber_quality_bulk_route(items: list[FiberQualityCreate], db: Session = Depends(get_db), api_key: str = Depends(verify_api_key) ):
    try:
        return create_fiber_quality_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upsert", status_code=200)
def upsert_fiber_quality_route(items: list[FiberQualityCreate], db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    try:
        return upsert_fiber_quality_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[FiberQualityOut])
def list_qualities(
    skip: int = 0,
    limit: int = 100,
    fiber_id: int = None,   # optional filter by fiber
    grade: str = None,      # optional filter by grade
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    if grade:
        return get_by_grade(db, grade)
    return get_fiber_qualities(db, skip=skip, limit=limit)

@router.post("/", response_model=FiberQualityOut, status_code=201)
def create(payload: FiberQualityCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    return create_fiber_quality(db, payload)

@router.get("/{quality_id}", response_model=FiberQualityOut)
def get_one(quality_id: int, db: Session = Depends(get_db)):
    obj = get_fiber_quality(db, quality_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Quality record not found")
    return obj

@router.patch("/{quality_id}", response_model=FiberQualityOut)
def update(quality_id: int, payload: FiberQualityUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    obj = get_fiber_quality(db, quality_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return update_fiber_quality(db, obj, payload)

@router.delete("/{quality_id}", status_code=204)
def delete(quality_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    delete_fiber_quality(db, quality_id)
# ```

# **New concept here** — optional query parameters in the list endpoint:
# ```
# GET /fiber-quality/              → all records
# GET /fiber-quality/?fiber_id=1   → only records for Cotton
# GET /fiber-quality/?grade=A      → only grade A records