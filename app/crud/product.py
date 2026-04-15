from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

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