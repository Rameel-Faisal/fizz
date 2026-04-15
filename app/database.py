from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# The engine is the actual connection to PostgreSQL
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory that creates database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)