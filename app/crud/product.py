from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from sqlalchemy.exc import SQLAlchemyError 

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.product_id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Product).offset(skip).limit(limit).all()

def get_by_fiber(db: Session, fiber_id: int):
    return db.query(Product).filter(Product.fiber_id == fiber_id).all()

def create_product(db: Session, product: ProductCreate):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_product_bulk(db: Session, items: list[ProductCreate]):
    db_objects = [Product(**i.model_dump()) for i in items]
    db.add_all(db_objects)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    for obj in db_objects:
        db.refresh(obj)
    return db_objects

 
def upsert_product_bulk(db: Session, items: list[ProductCreate]):
    inserted_count = 0
    updated_count = 0
    try:
        for item in items:
            data = item.model_dump()
            existing = db.query(Product).filter(
                Product.product_name == data["product_name"]
            ).first()
 
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                updated_count += 1
            else:
                db.add(Product(**data))
                inserted_count += 1
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Upsert batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    return {"inserted": inserted_count, "updated": updated_count, "total": inserted_count + updated_count}
 

def create_product_bulk(db: Session, items: list[ProductCreate]):
    db_objects = [Product(**i.model_dump()) for i in items]
    db.add_all(db_objects)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Batch rejected — database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}")
    for obj in db_objects:
        db.refresh(obj)
    return db_objects
 

def update_product(db: Session, db_product: Product, product: ProductUpdate):
    data = product.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(Product).filter(Product.product_id == product_id).first()
    db.delete(db_product)
    db.commit()
    return db_product