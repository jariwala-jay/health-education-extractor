"""Main FastAPI application for Health Education Extractor."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import pdf_processing, health_articles
from app.core.database import init_database, close_database
from app.services.app_database_uploader import app_uploader


# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Health Education Extractor API...")
    await init_database()
    await app_uploader.init_app_database()
    yield
    # Shutdown
    logger.info("Shutting down Health Education Extractor API...")
    await close_database()
    await app_uploader.close_app_database()


# Create FastAPI app
app = FastAPI(
    title="Health Education Extractor API",
    description="Extract and process health education content from PDFs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Health Education Extractor API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "health-education-extractor"}
    )


# Include routers
app.include_router(
    pdf_processing.router,
    prefix="/api/v1/pdf",
    tags=["PDF Processing"]
)

app.include_router(
    health_articles.router,
    prefix="/api/v1/articles",
    tags=["Health Articles"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 