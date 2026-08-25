from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError        
from typing import List
from app.schemas.fiber_type import FiberTypeCreate, FiberTypeOut, FiberTypeUpdate
from app.crud.fiber_type import get_fiber_type, get_fiber_types, create_fiber_type, update_fiber_type, delete_fiber_type,create_fiber_type_bulk,upsert_fiber_type_bulk
from app.dependencies.db import get_db
from app.dependencies.auth import verify_api_key

router = APIRouter(prefix="/fiber-types", tags=["Fiber Types"])
# --- bulk ---

@router.post("/bulk", response_model=list[FiberTypeOut], status_code=201)
def create_fiber_types_bulk_route(items: list[FiberTypeCreate], db: Session = Depends(get_db), api_key:str=Depends(verify_api_key)):
    try:
        return create_fiber_type_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
# --- upsert ---
@router.post("/upsert", status_code=200)
def upsert_fiber_types_route(items: list[FiberTypeCreate], db: Session = Depends(get_db), api_key:str=Depends(verify_api_key)):
    try:
        return upsert_fiber_type_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[FiberTypeOut])
def list_fiber_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_fiber_types(db, skip=skip, limit=limit)

# --- single create ---
@router.post("/", response_model=FiberTypeOut, status_code=201)
def create(payload: FiberTypeCreate, db: Session = Depends(get_db), api_key:str =Depends(verify_api_key)):
    try:                                            # ← wrap in try/except
        return create_fiber_type(db, payload)
    except IntegrityError:
        db.rollback()                              # ← undo the failed insert
        raise HTTPException(
            status_code=400,
            detail=f"Fiber type '{payload.fiber_type_name}' already exists"
        )

@router.get("/{fiber_id}", response_model=FiberTypeOut)
def get_one(fiber_id: int, db: Session = Depends(get_db)):
    obj = get_fiber_type(db, fiber_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Fiber type not found")
    return obj

# --- patch ---
@router.patch("/{fiber_id}", response_model=FiberTypeOut)
def update(fiber_id: int, payload: FiberTypeUpdate, db: Session = Depends(get_db),api_key:str=Depends(verify_api_key)):
    obj = get_fiber_type(db, fiber_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return update_fiber_type(db, obj, payload)

# --- delete ---
@router.delete("/{fiber_id}", status_code=204)
def delete(fiber_id: int, db: Session = Depends(get_db), api_key:str=Depends(verify_api_key)):
    delete_fiber_type(db, fiber_id)