from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import engine, Base
import database.models  # ensure models are loaded
from api import upload, analytics, insights

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trade Intelligence Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(insights.router, prefix="/api/insights")

@app.get("/")
def read_root():
    return {"message": "Welcome to Trade Intelligence Platform API"}
