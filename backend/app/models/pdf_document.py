"""PDF Document data model."""

from beanie import Document
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class PDFProcessingStatus(str, Enum):
    """Processing status for PDF documents."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHUNKING = "chunking"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFDocument(Document):
    """PDF document model for tracking uploaded files."""
    
    # File metadata
    filename: str = Field(..., min_length=1)
    original_filename: str = Field(..., min_length=1)
    file_path: str = Field(..., description="Path to stored PDF file")
    file_size_bytes: int = Field(..., ge=0)
    content_type: str = Field(default="application/pdf")
    
    # Processing status
    processing_status: PDFProcessingStatus = Field(default=PDFProcessingStatus.UPLOADED)
    
    # Extracted content metadata
    total_pages: Optional[int] = Field(None, ge=0)
    total_chunks: Optional[int] = Field(None, ge=0)
    total_articles_generated: Optional[int] = Field(None, ge=0)
    
    # Processing results
    chunk_ids: List[str] = Field(default_factory=list)
    article_ids: List[str] = Field(default_factory=list)
    
    # Error tracking
    error_message: Optional[str] = None
    processing_logs: List[str] = Field(default_factory=list)
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    # Processing statistics
    processing_stats: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Settings:
        name = "pdf_documents"
        indexes = [
            "filename",
            "processing_status",
            "uploaded_at",
            "original_filename"
        ]
    
    def __str__(self) -> str:
        return f"PDFDocument(filename='{self.filename}', status='{self.processing_status}')"


class PDFChunk(BaseModel):
    """Model for PDF content chunks."""
    chunk_id: str
    pdf_document_id: str
    page_number: int
    chunk_index: int
    content: str
    word_count: int
    is_relevant: bool = False
    relevance_score: Optional[float] = None
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PDFUploadResponse(BaseModel):
    """Response schema for PDF upload."""
    id: str
    filename: str
    file_size_bytes: int
    processing_status: PDFProcessingStatus
    uploaded_at: datetime


class PDFProcessingResponse(BaseModel):
    """Response schema for PDF processing status."""
    id: str
    filename: str
    processing_status: PDFProcessingStatus
    total_pages: Optional[int]
    total_chunks: Optional[int]
    total_articles_generated: Optional[int]
    uploaded_at: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]


class PDFListResponse(BaseModel):
    """Response schema for listing PDFs."""
    documents: List[PDFProcessingResponse]
    total: int
    page: int
    per_page: int 