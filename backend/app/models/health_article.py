"""Health Article data model."""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum


class CategoryEnum(str, Enum):
    """Health article categories."""
    HYPERTENSION = "Hypertension"
    DIABETES = "Diabetes"
    NUTRITION = "Nutrition"
    PHYSICAL_ACTIVITY = "Physical Activity"
    OBESITY = "Obesity"
    GENERAL_HEALTH = "General Health"


class ProcessingStatus(str, Enum):
    """Processing status for articles."""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    UPLOADED = "uploaded"  # Article has been uploaded to app database
    REJECTED = "rejected"


class HealthArticle(Document):
    """Health article document model."""
    
    # Core content fields (from JSON schema)
    title: str = Field(..., min_length=1, max_length=200)
    category: CategoryEnum
    image_url: Optional[str] = Field(None, description="URL to article image")
    medical_condition_tags: List[str] = Field(default_factory=list)
    content: str = Field(..., min_length=10)
    
    # Processing metadata
    source_pdf_id: Optional[str] = Field(None, description="Reference to source PDF document")
    chunk_id: Optional[str] = Field(None, description="Reference to source chunk")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.DRAFT)
    
    # App database integration
    app_article_id: Optional[str] = Field(None, description="ID of the article in the app database after upload")
    
    # Quality metrics
    reading_level_score: Optional[float] = Field(None, ge=1.0, le=12.0)
    similarity_scores: Optional[List[float]] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    
    # Review metadata
    reviewer_notes: Optional[str] = None
    
    class Settings:
        name = "health_articles"
        indexes = [
            [("title", "text"), ("content", "text")],  # Text search
            "category",
            "medical_condition_tags",
            "processing_status",
            "created_at",
            "source_pdf_id",
            "app_article_id"  # Add index for app article ID
        ]
    
    def __str__(self) -> str:
        return f"HealthArticle(title='{self.title}', category='{self.category}')"


class HealthArticleCreate(BaseModel):
    """Schema for creating health articles."""
    title: str = Field(..., min_length=1, max_length=200)
    category: CategoryEnum
    image_url: Optional[str] = None
    medical_condition_tags: List[str] = Field(default_factory=list)
    content: str = Field(..., min_length=10)
    source_pdf_id: Optional[str] = None
    chunk_id: Optional[str] = None


class HealthArticleUpdate(BaseModel):
    """Schema for updating health articles."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[CategoryEnum] = None
    image_url: Optional[str] = None
    medical_condition_tags: Optional[List[str]] = None
    content: Optional[str] = Field(None, min_length=10)
    processing_status: Optional[ProcessingStatus] = None
    reviewer_notes: Optional[str] = None


class HealthArticleResponse(BaseModel):
    """Schema for health article API responses."""
    id: str
    title: str
    category: CategoryEnum
    image_url: Optional[str]
    medical_condition_tags: List[str]
    content: str
    source_pdf_id: Optional[str]
    chunk_id: Optional[str]
    processing_status: ProcessingStatus
    app_article_id: Optional[str]
    reading_level_score: Optional[float]
    similarity_scores: Optional[List[float]]
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime]
    reviewer_notes: Optional[str] 