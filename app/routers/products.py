from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.crud.product import (
    get_product, get_products, get_by_fiber,
    create_product, update_product, delete_product,create_product_bulk,
)
from app.dependencies.db import get_db

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/bulk", response_model=list[ProductOut], status_code=201)
def create_products_bulk(items: list[ProductCreate], db: Session = Depends(get_db)):
    return create_product_bulk(db, items)

@router.get("/", response_model=List[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 100,
    fiber_id: int = None,
    db: Session = Depends(get_db)
):
    if fiber_id:
        return get_by_fiber(db, fiber_id)
    return get_products(db, skip=skip, limit=limit)

@router.post("/", response_model=ProductOut, status_code=201)
def create(payload: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, payload)

@router.get("/{product_id}", response_model=ProductOut)
def get_one(product_id: int, db: Session = Depends(get_db)):
    obj = get_product(db, product_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@router.patch("/{product_id}", response_model=ProductOut)
def update(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    obj = get_product(db, product_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return update_product(db, obj, payload)

@router.delete("/{product_id}", status_code=204)
def delete(product_id: int, db: Session = Depends(get_db)):
    obj = get_product(db, product_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    delete_product(db, product_id)