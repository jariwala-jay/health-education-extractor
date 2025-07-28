"""PDF processing API endpoints."""

import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime, timezone

from app.config import settings
from app.models.pdf_document import (
    PDFDocument, 
    PDFUploadResponse, 
    PDFProcessingResponse,
    PDFListResponse,
    PDFProcessingStatus
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a PDF file for processing."""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        file_path = os.path.join("data/uploads", filename)
        
        # Ensure upload directory exists
        os.makedirs("data/uploads", exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create database record
        pdf_doc = PDFDocument(
            filename=filename,
            original_filename=file.filename or "unknown.pdf",
            file_path=file_path,
            file_size_bytes=file_size,
            content_type=file.content_type or "application/pdf"
        )
        
        await pdf_doc.insert()
        
        # Queue background processing
        background_tasks.add_task(process_pdf_background, str(pdf_doc.id))
        
        logger.info(f"PDF uploaded successfully: {filename}")
        
        return PDFUploadResponse(
            id=str(pdf_doc.id),
            filename=pdf_doc.original_filename,
            file_size_bytes=pdf_doc.file_size_bytes,
            processing_status=pdf_doc.processing_status,
            uploaded_at=pdf_doc.uploaded_at
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload PDF")


@router.get("/status/{pdf_id}", response_model=PDFProcessingResponse)
async def get_pdf_status(pdf_id: str):
    """Get processing status of a PDF document."""
    
    try:
        pdf_doc = await PDFDocument.get(pdf_id)
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return PDFProcessingResponse(
            id=str(pdf_doc.id),
            filename=pdf_doc.original_filename,
            processing_status=pdf_doc.processing_status,
            total_pages=pdf_doc.total_pages,
            total_chunks=pdf_doc.total_chunks,
            total_articles_generated=pdf_doc.total_articles_generated,
            uploaded_at=pdf_doc.uploaded_at,
            processing_started_at=pdf_doc.processing_started_at,
            processing_completed_at=pdf_doc.processing_completed_at,
            error_message=pdf_doc.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get PDF status")


@router.get("/list", response_model=PDFListResponse)
async def list_pdfs(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[PDFProcessingStatus] = None
):
    """List all PDF documents with pagination."""
    
    try:
        # Build query
        query = {}
        if status:
            query["processing_status"] = status
        
        # Get total count
        total = await PDFDocument.find(query).count()
        
        # Get paginated results
        skip = (page - 1) * per_page
        documents = await PDFDocument.find(query).sort(-PDFDocument.uploaded_at).skip(skip).limit(per_page).to_list()
        
        # Convert to response format
        doc_responses = [
            PDFProcessingResponse(
                id=str(doc.id),
                filename=doc.original_filename,
                processing_status=doc.processing_status,
                total_pages=doc.total_pages,
                total_chunks=doc.total_chunks,
                total_articles_generated=doc.total_articles_generated,
                uploaded_at=doc.uploaded_at,
                processing_started_at=doc.processing_started_at,
                processing_completed_at=doc.processing_completed_at,
                error_message=doc.error_message
            )
            for doc in documents
        ]
        
        return PDFListResponse(
            documents=doc_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing PDFs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list PDFs")


@router.delete("/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete a PDF document and its associated data."""
    
    try:
        pdf_doc = await PDFDocument.get(pdf_id)
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Delete associated articles (will be implemented later)
        # TODO: Delete health articles associated with this PDF
        
        # Delete file from disk
        if os.path.exists(pdf_doc.file_path):
            os.remove(pdf_doc.file_path)
        
        # Delete database record
        await pdf_doc.delete()
        
        logger.info(f"PDF deleted: {pdf_doc.filename}")
        return JSONResponse(content={"message": "PDF deleted successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete PDF")


async def process_pdf_background(pdf_id: str):
    """Background task to process PDF and generate articles."""
    
    logger.info(f"Starting background processing for PDF: {pdf_id}")
    
    try:
        pdf_doc = await PDFDocument.get(pdf_id)
        if not pdf_doc:
            logger.error(f"PDF not found: {pdf_id}")
            return
        
        # Initialize processing services
        from app.services.pdf_parser import PDFParser
        from app.services.content_chunker import ContentChunker
        from app.services.gemini_summarizer import GeminiSummarizer
        from app.services.image_matcher import UnsplashImageMatcher
        from app.services.duplicate_detector import DuplicateDetector
        from app.models.health_article import HealthArticle, HealthArticleCreate
        
        pdf_parser = PDFParser()
        chunker = ContentChunker()
        summarizer = GeminiSummarizer()
        image_matcher = UnsplashImageMatcher()
        duplicate_detector = DuplicateDetector()
        
        # Update status to parsing
        pdf_doc.processing_status = PDFProcessingStatus.PARSING
        pdf_doc.processing_started_at = datetime.now(timezone.utc)
        await pdf_doc.save()
        
        # Step 1: Parse PDF content
        logger.info(f"Step 1: Parsing PDF content for {pdf_id}")
        pdf_content = await pdf_parser.parse_pdf(pdf_doc.file_path)
        pdf_doc.total_pages = pdf_content.total_pages
        await pdf_doc.save()
        
        # Step 2: Chunk content
        logger.info(f"Step 2: Chunking content for {pdf_id}")
        pdf_doc.processing_status = PDFProcessingStatus.CHUNKING
        await pdf_doc.save()
        
        chunks = chunker.chunk_content(pdf_content, pdf_id)
        pdf_doc.total_chunks = len(chunks)
        pdf_doc.chunk_ids = [chunk.chunk_id for chunk in chunks]
        await pdf_doc.save()
        
        if not chunks:
            logger.warning(f"No relevant chunks found for PDF {pdf_id}")
            pdf_doc.processing_status = PDFProcessingStatus.COMPLETED
            pdf_doc.processing_completed_at = datetime.now(timezone.utc)
            await pdf_doc.save()
            return
        
        # Step 3: Generate articles with LLM
        logger.info(f"Step 3: Generating articles for {pdf_id} ({len(chunks)} chunks)")
        pdf_doc.processing_status = PDFProcessingStatus.PROCESSING
        await pdf_doc.save()
        
        summarized_contents = await summarizer.batch_summarize_chunks(chunks)
        
        if not summarized_contents:
            logger.warning(f"No articles generated for PDF {pdf_id}")
            pdf_doc.processing_status = PDFProcessingStatus.COMPLETED
            pdf_doc.processing_completed_at = datetime.now(timezone.utc)
            await pdf_doc.save()
            return
        
        # Step 4: Process each summarized content
        created_articles = []
        
        for i, summarized_content in enumerate(summarized_contents):
            try:
                logger.info(f"Processing article {i+1}/{len(summarized_contents)}: {summarized_content.title}")
                
                # Check for duplicates
                duplicates = await duplicate_detector.check_for_duplicates(summarized_content)
                if duplicates:
                    logger.warning(f"Skipping duplicate article: {summarized_content.title}")
                    continue
                
                # Find matching image
                image_result = await image_matcher.find_image_for_article(
                    summarized_content.title,
                    summarized_content.category,
                    summarized_content.medical_condition_tags
                )
                
                image_url = image_result.url if image_result else None
                
                # Create health article
                article_data = HealthArticleCreate(
                    title=summarized_content.title,
                    category=summarized_content.category,
                    image_url=image_url,
                    medical_condition_tags=summarized_content.medical_condition_tags,
                    content=summarized_content.content,
                    source_pdf_id=pdf_id,
                    chunk_id=summarized_content.source_chunk_id
                )
                
                # Create and save article
                article = HealthArticle(**article_data.dict())
                article.reading_level_score = summarized_content.reading_level_score
                await article.insert()
                
                created_articles.append(str(article.id))
                logger.info(f"Created article: {article.title} (ID: {article.id})")
                
            except Exception as e:
                logger.error(f"Error processing article {i+1}: {e}")
                continue
        
        # Update PDF document with results
        pdf_doc.article_ids = created_articles
        pdf_doc.total_articles_generated = len(created_articles)
        pdf_doc.processing_status = PDFProcessingStatus.COMPLETED
        pdf_doc.processing_completed_at = datetime.now(timezone.utc)
        
        # Add processing statistics
        processing_time_seconds = 0
        if pdf_doc.processing_started_at:
            # Ensure both datetimes are timezone-aware for subtraction
            started_at = pdf_doc.processing_started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            processing_time_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
        
        pdf_doc.processing_stats = {
            "total_chunks": len(chunks),
            "articles_generated": len(created_articles),
            "articles_skipped_duplicates": len(summarized_contents) - len(created_articles),
            "processing_time_seconds": processing_time_seconds
        }
        
        await pdf_doc.save()
        
        logger.info(f"PDF processing completed: {pdf_id} - Generated {len(created_articles)} articles")
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_id}: {e}")
        
        # Update PDF status to failed
        try:
            pdf_doc = await PDFDocument.get(pdf_id)
            if pdf_doc:
                pdf_doc.processing_status = PDFProcessingStatus.FAILED
                pdf_doc.error_message = str(e)
                pdf_doc.processing_completed_at = datetime.now(timezone.utc)
                await pdf_doc.save()
        except Exception as save_error:
            logger.error(f"Error updating PDF status: {save_error}")


# Import datetime for background task
from datetime import datetime 