from app.database import engine
from app.models.base import Base
from app.models.fiber_type import FiberType
from app.models.fiber_quality import FiberQuality
from app.models.product import Product
from app.models.cultivation_data import CultivationData
from app.models.processing_method import ProcessingMethod
from app.models.sustainability_metric import SustainabilityMetric
from app.models.market_data import MarketData


Base.metadata.create_all(bind=engine)
print("Tables created!")