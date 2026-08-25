from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.processing_method import ProcessingMethodCreate, ProcessingMethodOut, ProcessingMethodUpdate
from app.crud.processing_method import (
    get_processing_method, get_processing_methods, get_by_fiber,
    get_by_process_type, create_processing_method,
    update_processing_method, delete_processing_method,create_processing_method_bulk,upsert_processing_method_bulk
)
from app.dependencies.db import get_db
from app.dependencies.auth import verify_api_key
router = APIRouter(prefix="/processing-methods", tags=["Processing Methods"])

@router.post("/bulk", response_model=list[ProcessingMethodOut], status_code=201)
def create_processing_methods_bulk_route(items: list[ProcessingMethodCreate], db: Session = Depends(get_db) , api_key: str = Depends(verify_api_key) ):
    try:
        return create_processing_method_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upsert", status_code=200)
def upsert_processing_methods_route(items: list[ProcessingMethodCreate], db: Session = Depends(get_db) , api_key: str = Depends(verify_api_key)):
    try:
        return upsert_processing_method_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProcessingMethodOut])
def list_methods(
    skip: int = 0,
    limit: int = 100,
    fiber_id: int = None,
    process_type: str = None,
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    if process_type:
        return get_by_process_type(db, process_type)
    return get_processing_methods(db, skip=skip, limit=limit)

@router.post("/", response_model=ProcessingMethodOut, status_code=201)
def create(payload: ProcessingMethodCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key) ):
    return create_processing_method(db, payload)

@router.get("/{processing_id}", response_model=ProcessingMethodOut)
def get_one(processing_id: int, db: Session = Depends(get_db)):
    obj = get_processing_method(db, processing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Processing method not found")
    return obj

@router.patch("/{processing_id}", response_model=ProcessingMethodOut)
def update(processing_id: int, payload: ProcessingMethodUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    obj = get_processing_method(db, processing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Processing method not found")
    return update_processing_method(db, obj, payload)

@router.delete("/{processing_id}", status_code=204)
def delete(processing_id: int, db: Session = Depends(get_db) , api_key: str = Depends(verify_api_key)):
    obj = get_processing_method(db, processing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Processing method not found")
    delete_processing_method(db, processing_id)