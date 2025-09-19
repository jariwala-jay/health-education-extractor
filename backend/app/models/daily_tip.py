"""Daily Tip data model."""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum


class TipProcessingStatus(str, Enum):
    """Processing status for daily tips."""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    UPLOADED = "uploaded"  # Tip has been uploaded to app database
    REJECTED = "rejected"


class TipCategory(str, Enum):
    """Categories for daily tips."""
    HYPERTENSION = "Hypertension"
    OBESITY = "Obesity"
    DIABETES = "Diabetes"
    PREDIABETES = "Prediabetes"
    NUTRITION = "Nutrition"
    GENERAL = "General"


class DailyTip(Document):
    """Daily tip document model."""
    
    # Core content fields
    tip_text: str = Field(..., min_length=10, max_length=200, description="The tip content")
    category: TipCategory = Field(..., description="Category of the tip")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    source_article_id: Optional[str] = Field(None, description="Reference to source health article")
    
    # Image support
    image_url: Optional[str] = Field(None, description="URL to tip image")
    
    # Processing metadata
    processing_status: TipProcessingStatus = Field(default=TipProcessingStatus.DRAFT)
    
    # App database integration
    app_tip_id: Optional[str] = Field(None, description="ID of the tip in the app database after upload")
    
    # Quality metrics
    reading_level_score: Optional[float] = Field(None, ge=1.0, le=12.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    
    # Review metadata
    reviewer_notes: Optional[str] = None
    
    class Settings:
        name = "daily_tips"
        indexes = [
            "tags",
            "source_article_id",
            "processing_status",
            "created_at",
            "app_tip_id"
        ]
    
    def __str__(self) -> str:
        return f"DailyTip(tip_text='{self.tip_text[:50]}...', tags={self.tags})"


class DailyTipCreate(BaseModel):
    """Schema for creating daily tips."""
    tip_text: str = Field(..., min_length=10, max_length=200)
    category: TipCategory
    tags: List[str] = Field(default_factory=list)
    source_article_id: Optional[str] = None
    image_url: Optional[str] = None


class DailyTipUpdate(BaseModel):
    """Schema for updating daily tips."""
    tip_text: Optional[str] = Field(None, min_length=10, max_length=200)
    category: Optional[TipCategory] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    processing_status: Optional[TipProcessingStatus] = None
    reviewer_notes: Optional[str] = None


class DailyTipResponse(BaseModel):
    """Schema for daily tip API responses."""
    id: str
    tip_text: str
    category: TipCategory
    tags: List[str]
    source_article_id: Optional[str]
    source_article_title: Optional[str] = None
    image_url: Optional[str]
    processing_status: TipProcessingStatus
    app_tip_id: Optional[str]
    reading_level_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime]
    reviewer_notes: Optional[str]
