"""PDF processing API endpoints."""

import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
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
from app.core.auth_middleware import get_current_active_user
from app.models.daily_tip import TipCategory
from app.services.gemini_summarizer import SummarizedContent

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


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


@router.delete("/delete-all")
async def delete_all_pdfs():
    """Delete all PDF documents and their files (for cleanup purposes)."""
    try:
        # Get all PDFs
        pdfs = await PDFDocument.find().to_list()
        count_before = len(pdfs)
        
        logger.info(f"Deleting {count_before} PDF documents and their files")
        
        deleted_files = 0
        failed_files = []
        
        # Delete files from file system
        for pdf in pdfs:
            if pdf.file_path and os.path.exists(pdf.file_path):
                try:
                    os.remove(pdf.file_path)
                    deleted_files += 1
                    logger.info(f"Deleted file: {pdf.file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {pdf.file_path}: {e}")
                    failed_files.append(pdf.file_path)
        
        # Delete database records
        result = await PDFDocument.delete_all()
        
        logger.info(f"Successfully deleted {result.deleted_count} PDF documents from database")
        logger.info(f"Deleted {deleted_files} files from file system")
        
        return {
            "message": "All PDF documents deleted successfully",
            "deleted_count": result.deleted_count,
            "count_before": count_before,
            "files_deleted": deleted_files,
            "failed_files": failed_files
        }
        
    except Exception as e:
        logger.error(f"Error deleting all PDFs: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete all PDFs")


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


@router.get("/{pdf_id}/download")
async def download_pdf(pdf_id: str):
    """Download a PDF file."""
    
    try:
        pdf_doc = await PDFDocument.get(pdf_id)
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Check if file exists
        if not os.path.exists(pdf_doc.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        
        # Return the file for download
        return FileResponse(
            path=pdf_doc.file_path,
            filename=pdf_doc.original_filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF {pdf_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download PDF")


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
        from app.models.daily_tip import DailyTip, DailyTipCreate, TipCategory
        
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
        
        # Use new summarization approach based on configuration
        if settings.summarization_mode == "map_reduce":
            # Use map-reduce for better quality, but process chunks in groups to get multiple articles
            logger.info(f"Using map_reduce mode for document summarization")
            
            # Process chunks in groups to generate multiple articles
            chunk_groups = []
            group_size = max(3, len(chunks) // 5)  # Aim for 5 groups, minimum 3 chunks per group
            
            for i in range(0, len(chunks), group_size):
                group = chunks[i:i + group_size]
                if group:  # Only add non-empty groups
                    chunk_groups.append(group)
            
            logger.info(f"Processing {len(chunk_groups)} chunk groups for map_reduce")
            
            summarized_contents = []
            for i, group in enumerate(chunk_groups):
                logger.info(f"Processing group {i+1}/{len(chunk_groups)} with {len(group)} chunks")
                summarized_content = await summarizer.summarize_document(group)
                if summarized_content:
                    summarized_contents.append(summarized_content)
            
            logger.info(f"Map_reduce generated {len(summarized_contents)} articles from {len(chunk_groups)} groups")
            
        elif settings.summarization_mode == "full":
            # Use full document summarization (single article)
            logger.info(f"Using full mode for document summarization")
            summarized_content = await summarizer.summarize_document(chunks)
            summarized_contents = [summarized_content] if summarized_content else []
            logger.info(f"Full document summarization result: {len(summarized_contents)} articles")
        else:
            # Use chunk-level summarization with diversity filtering
            logger.info(f"Using chunk mode for document summarization")
            all_summarized_contents = await summarizer.batch_summarize_chunks(chunks)
            logger.info(f"Batch summarization generated {len(all_summarized_contents)} articles")
            
            # Apply diversity filtering to reduce similar articles
            summarized_contents = await _filter_diverse_articles(all_summarized_contents)
            logger.info(f"After diversity filtering: {len(summarized_contents)} articles")
        
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
                    official_sources=summarized_content.official_sources,
                    learn_more_url=summarized_content.learn_more_url,
                    source_pdf_id=pdf_id,
                    chunk_id=summarized_content.source_chunk_id
                )
                
                # Create and save article
                article = HealthArticle(**article_data.dict())
                article.reading_level_score = summarized_content.reading_level_score
                await article.insert()
                
                # Generate tips for this article
                try:
                    tips = await summarizer.generate_tips(
                        summarized_content.content, 
                        summarized_content.medical_condition_tags
                    )
                    
                    # Save tips to database with images
                    for tip_text in tips:
                        # Find matching image for the tip
                        tip_image_result = await image_matcher.find_image_for_article(
                            tip_text,  # Use tip text as search query
                            summarized_content.category,
                            summarized_content.medical_condition_tags
                        )
                        
                        tip_image_url = tip_image_result.url if tip_image_result else None
                        
                        # Calculate reading level for tip
                        tip_reading_level = summarizer._estimate_reading_level(tip_text)
                        
                        tip_data = DailyTipCreate(
                            tip_text=tip_text,
                            category=_map_article_category_to_tip_category(summarized_content.category),
                            tags=summarized_content.medical_condition_tags,
                            source_article_id=str(article.id),
                            image_url=tip_image_url
                        )
                        tip = DailyTip(**tip_data.model_dump())
                        tip.reading_level_score = tip_reading_level
                        await tip.insert()
                        logger.info(f"Created tip with image: {tip_text[:50]}...")
                    
                    # Store tips in summarized content for potential future use
                    summarized_content.tips = tips
                    
                except Exception as e:
                    logger.error(f"Error generating tips for article {article.id}: {e}")
                
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


async def _filter_diverse_articles(summarized_contents: List[SummarizedContent]) -> List[SummarizedContent]:
    """Filter articles to ensure diversity and limit quantity."""
    if not summarized_contents:
        return []
    
    # If we have fewer articles than the limit, return all
    if len(summarized_contents) <= settings.max_articles_per_pdf:
        return summarized_contents
    
    # Sort by confidence score and content length (prefer comprehensive articles)
    sorted_contents = sorted(
        summarized_contents, 
        key=lambda x: (x.confidence_score or 0.5) * len(x.content), 
        reverse=True
    )
    
    # Select diverse articles
    selected = []
    used_titles = set()
    
    for content in sorted_contents:
        if len(selected) >= settings.max_articles_per_pdf:
            break
        
        # Check if this article is too similar to already selected ones
        is_similar = False
        for selected_content in selected:
            if _are_articles_similar(content, selected_content):
                is_similar = True
                break
        
        # Check for title similarity
        title_lower = content.title.lower()
        if any(title_lower in used_title or used_title in title_lower 
               for used_title in used_titles):
            is_similar = True
        
        if not is_similar:
            selected.append(content)
            used_titles.add(title_lower)
    
    logger.info(f"Filtered {len(summarized_contents)} articles down to {len(selected)} diverse articles")
    return selected


def _map_article_category_to_tip_category(article_category: str) -> TipCategory:
    """Map article category to appropriate tip category."""
    category_mapping = {
        "Hypertension": TipCategory.HYPERTENSION,
        "Diabetes": TipCategory.DIABETES,
        "Nutrition": TipCategory.NUTRITION,
        "Physical Activity": TipCategory.GENERAL,
        "Obesity": TipCategory.OBESITY,
        "General Health": TipCategory.GENERAL
    }
    
    return category_mapping.get(article_category, TipCategory.GENERAL)


def _are_articles_similar(article1: SummarizedContent, article2: SummarizedContent) -> bool:
    """Check if two articles are similar based on content and tags."""
    # Check tag overlap
    tags1 = set(tag.lower() for tag in article1.medical_condition_tags)
    tags2 = set(tag.lower() for tag in article2.medical_condition_tags)
    common_tags = tags1.intersection(tags2)
    
    if len(common_tags) > 0 and len(common_tags) / max(len(tags1), len(tags2)) > 0.8:
        return True
    
    # Check content similarity (simple word overlap)
    content1 = set(article1.content.lower().split())
    content2 = set(article2.content.lower().split())
    common_words = content1.intersection(content2)
    
    if len(common_words) > 0 and len(common_words) / max(len(content1), len(content2)) > 0.5:
        return True
    
    return False 