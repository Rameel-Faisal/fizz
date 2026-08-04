from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.market_data import MarketDataCreate, MarketDataOut, MarketDataUpdate
from app.crud.market_data import (
    get_market_data, get_market_data_list, get_by_fiber,
    get_by_industry, get_by_region,
    create_market_data, update_market_data, delete_market_data,create_market_data_bulk,upsert_market_data_bulk
)
from app.dependencies.db import get_db

router = APIRouter(prefix="/market-data", tags=["Market Data"])

@router.post("/bulk", response_model=list[MarketDataOut], status_code=201)
def create_market_data_bulk_route(items: list[MarketDataCreate], db: Session = Depends(get_db)):
    try:
        return create_market_data_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 
@router.post("/upsert", status_code=200)
def upsert_market_data_route(items: list[MarketDataCreate], db: Session = Depends(get_db)):
    try:
        return upsert_market_data_bulk(db, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 

@router.get("/", response_model=List[MarketDataOut])
def list_market_data(
    skip: int = 0,
    limit: int = 100,
    fiber_id: int = None,
    industry: str = None,
    region: str = None,
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    if industry:
        return get_by_industry(db, industry)
    if region:
        return get_by_region(db, region)
    return get_market_data_list(db, skip=skip, limit=limit)

@router.post("/", response_model=MarketDataOut, status_code=201)
def create(payload: MarketDataCreate, db: Session = Depends(get_db)):
    return create_market_data(db, payload)

@router.get("/{market_id}", response_model=MarketDataOut)
def get_one(market_id: int, db: Session = Depends(get_db)):
    obj = get_market_data(db, market_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Market data not found")
    return obj

@router.patch("/{market_id}", response_model=MarketDataOut)
def update(market_id: int, payload: MarketDataUpdate, db: Session = Depends(get_db)):
    obj = get_market_data(db, market_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Market data not found")
    return update_market_data(db, obj, payload)

@router.delete("/{market_id}", status_code=204)
def delete(market_id: int, db: Session = Depends(get_db)):
    obj = get_market_data(db, market_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Market data not found")
    delete_market_data(db, market_id)