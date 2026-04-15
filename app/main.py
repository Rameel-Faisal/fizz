from fastapi import FastAPI
from app.routers import fiber_types,fiber_quality,products,cultivation_data,processing_methods,sustainability,market_data


app = FastAPI(
    title="Fizz API",
    description="Fiber plant data management platform",
    version="1.0.0"
)

app.include_router(fiber_types.router)
app.include_router(fiber_quality.router)
app.include_router(products.router)
app.include_router(cultivation_data.router)
app.include_router(processing_methods.router)
app.include_router(sustainability.router)
app.include_router(market_data.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Fizz API 🌿"}