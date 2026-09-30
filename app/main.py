"""Soukchay API - FastAPI main application.

Provides read-only access to soukchay_sysdata database for the mobile app.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import get_conn
from .routes import data_entry, labor_department, loan_department, fa_department, follow_up


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup health check."""
    try:
        # Test database connection on startup
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        print("✅ Database connection OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        # Continue startup but log the error
    yield


# Create FastAPI app
app = FastAPI(
    title="Soukchay API",
    description="Read-only API for soukchay_sysdata database",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_entry.router)
app.include_router(labor_department.router)
app.include_router(loan_department.router)
app.include_router(fa_department.router)
app.include_router(follow_up.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Soukchay API is running"}