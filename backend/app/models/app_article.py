"""App Article data model - matches Flutter Article model structure."""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class AppArticle(Document):
    """
    App article document model that matches the Flutter Article model.
    This is used for articles published to the app database.
    """
    
    # Core fields matching Flutter Article model
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., description="Article category")
    imageUrl: str = Field(..., description="URL to article image")
    medicalConditionTags: List[str] = Field(default_factory=list, description="Medical condition tags")
    content: Optional[str] = Field(None, description="Article content")
    
    # Additional metadata (not in Flutter model but useful for backend)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "educational_content"  # Collection name in app database
        # Remove indexes to avoid conflicts with existing collection
        # indexes = [
        #     [("title", "text"), ("content", "text")],  # Text search
        #     "category",
        #     "created_at"
        # ]
    
    def __str__(self) -> str:
        return f"AppArticle(title='{self.title}', category='{self.category}')"


class AppArticleCreate(BaseModel):
    """Schema for creating app articles."""
    title: str = Field(..., min_length=1, max_length=200)
    category: str
    imageUrl: str
    medicalConditionTags: List[str] = Field(default_factory=list)
    content: Optional[str] = None


class AppArticleResponse(BaseModel):
    """Schema for app article API responses."""
    id: str
    title: str
    category: str
    imageUrl: str
    medicalConditionTags: List[str]
    content: Optional[str]
    created_at: datetime
    updated_at: datetime 