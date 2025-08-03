"""Health articles API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
import json
from fastapi.responses import JSONResponse, StreamingResponse
from io import StringIO
from datetime import datetime, timezone

from app.models.health_article import (
    HealthArticle,
    HealthArticleCreate,
    HealthArticleUpdate,
    HealthArticleResponse,
    CategoryEnum,
    ProcessingStatus
)
from app.services.app_database_uploader import app_uploader
from app.core.auth_middleware import get_current_active_user
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.post("/", response_model=HealthArticleResponse)
async def create_article(article_data: HealthArticleCreate):
    """Create a new health article."""
    
    try:
        # Create new article
        article = HealthArticle(**article_data.dict())
        await article.insert()
        
        logger.info(f"Article created: {article.title}")
        
        return HealthArticleResponse(
            id=str(article.id),
            title=article.title,
            category=article.category,
            image_url=article.image_url,
            medical_condition_tags=article.medical_condition_tags,
            content=article.content,
            source_pdf_id=article.source_pdf_id,
            chunk_id=article.chunk_id,
            processing_status=article.processing_status,
            app_article_id=article.app_article_id,
            reading_level_score=article.reading_level_score,
            similarity_scores=article.similarity_scores,
            created_at=article.created_at,
            updated_at=article.updated_at,
            reviewed_at=article.reviewed_at,
            reviewer_notes=article.reviewer_notes
        )
        
    except Exception as e:
        logger.error(f"Error creating article: {e}")
        raise HTTPException(status_code=500, detail="Failed to create article")


@router.get("/{article_id}", response_model=HealthArticleResponse)
async def get_article(article_id: str):
    """Get a specific health article by ID."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return HealthArticleResponse(
            id=str(article.id),
            title=article.title,
            category=article.category,
            image_url=article.image_url,
            medical_condition_tags=article.medical_condition_tags,
            content=article.content,
            source_pdf_id=article.source_pdf_id,
            chunk_id=article.chunk_id,
            processing_status=article.processing_status,
            app_article_id=article.app_article_id,
            reading_level_score=article.reading_level_score,
            similarity_scores=article.similarity_scores,
            created_at=article.created_at,
            updated_at=article.updated_at,
            reviewed_at=article.reviewed_at,
            reviewer_notes=article.reviewer_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        raise HTTPException(status_code=500, detail="Failed to get article")


@router.put("/{article_id}", response_model=HealthArticleResponse)
async def update_article(article_id: str, article_data: HealthArticleUpdate):
    """Update a health article."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Update fields that are provided
        update_data = article_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)
        
        # Update timestamp
        article.updated_at = datetime.now(timezone.utc)
        
        await article.save()
        
        logger.info(f"Article updated: {article.title}")
        
        return HealthArticleResponse(
            id=str(article.id),
            title=article.title,
            category=article.category,
            image_url=article.image_url,
            medical_condition_tags=article.medical_condition_tags,
            content=article.content,
            source_pdf_id=article.source_pdf_id,
            chunk_id=article.chunk_id,
            processing_status=article.processing_status,
            app_article_id=article.app_article_id,
            reading_level_score=article.reading_level_score,
            similarity_scores=article.similarity_scores,
            created_at=article.created_at,
            updated_at=article.updated_at,
            reviewed_at=article.reviewed_at,
            reviewer_notes=article.reviewer_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        raise HTTPException(status_code=500, detail="Failed to update article")


@router.delete("/{article_id}")
async def delete_article(article_id: str):
    """Delete a health article."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await article.delete()
        
        logger.info(f"Article deleted: {article.title}")
        return {"message": "Article deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete article")


@router.get("/", response_model=List[HealthArticleResponse])
async def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    category: Optional[CategoryEnum] = None,
    status: Optional[ProcessingStatus] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None)
):
    """List health articles with filtering and pagination."""
    
    try:
        # Build query
        query_filters = {}
        
        if category:
            query_filters["category"] = category
        
        if status:
            query_filters["processing_status"] = status
        
        if tags:
            query_filters["medical_condition_tags"] = {"$in": tags}
        
        # Start query
        query = HealthArticle.find(query_filters)
        
        # Add text search if provided
        if search:
            query = query.find({"$text": {"$search": search}})
        
        # Apply pagination
        skip = (page - 1) * per_page
        articles = await query.sort(-HealthArticle.created_at).skip(skip).limit(per_page).to_list()
        
        # Convert to response format
        responses = [
            HealthArticleResponse(
                id=str(article.id),
                title=article.title,
                category=article.category,
                image_url=article.image_url,
                medical_condition_tags=article.medical_condition_tags,
                content=article.content,
                source_pdf_id=article.source_pdf_id,
                chunk_id=article.chunk_id,
                processing_status=article.processing_status,
                app_article_id=article.app_article_id,
                reading_level_score=article.reading_level_score,
                similarity_scores=article.similarity_scores,
                created_at=article.created_at,
                updated_at=article.updated_at,
                reviewed_at=article.reviewed_at,
                reviewer_notes=article.reviewer_notes
            )
            for article in articles
        ]
        
        return responses
        
    except Exception as e:
        logger.error(f"Error listing articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list articles")


@router.get("/search/similar/{article_id}")
async def find_similar_articles(
    article_id: str,
    limit: int = Query(5, ge=1, le=20)
):
    """Find articles similar to the given article (placeholder for now)."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # TODO: Implement similarity search using embeddings
        # For now, return articles with same category or overlapping tags
        similar_articles = await HealthArticle.find({
            "$or": [
                {"category": article.category},
                {"medical_condition_tags": {"$in": article.medical_condition_tags}}
            ],
            "_id": {"$ne": article.id}
        }).limit(limit).to_list()
        
        responses = [
            HealthArticleResponse(
                id=str(similar.id),
                title=similar.title,
                category=similar.category,
                image_url=similar.image_url,
                medical_condition_tags=similar.medical_condition_tags,
                content=similar.content,
                source_pdf_id=similar.source_pdf_id,
                chunk_id=similar.chunk_id,
                processing_status=similar.processing_status,
                app_article_id=similar.app_article_id,
                reading_level_score=similar.reading_level_score,
                similarity_scores=similar.similarity_scores,
                created_at=similar.created_at,
                updated_at=similar.updated_at,
                reviewed_at=similar.reviewed_at,
                reviewer_notes=similar.reviewer_notes
            )
            for similar in similar_articles
        ]
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar articles")


@router.post("/{article_id}/approve")
async def approve_article(article_id: str):
    """Approve an article for publication and upload to app database."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check if article has required fields for upload
        if not article.image_url:
            raise HTTPException(
                status_code=400, 
                detail="Article must have an image URL before approval"
            )
        
        # Upload to app database
        app_article_id = await app_uploader.upload_article(article)
        if not app_article_id:
            raise HTTPException(
                status_code=500, 
                detail="Failed to upload article to app database"
            )
        
        # Update article status and app database reference
        article.processing_status = ProcessingStatus.UPLOADED  # Changed from APPROVED to UPLOADED
        article.app_article_id = app_article_id
        article.reviewed_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)
        
        await article.save()
        
        logger.info(f"Article approved and uploaded to app database: {article.title} (App ID: {app_article_id})")
        return {
            "message": "Article approved and uploaded successfully",
            "app_article_id": app_article_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving article: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve article")


@router.post("/{article_id}/reject")
async def reject_article(article_id: str, reason: str = ""):
    """Reject an article."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article.processing_status = ProcessingStatus.REJECTED
        if reason:
            article.reviewer_notes = reason
        
        article.reviewed_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)
        
        await article.save()
        
        logger.info(f"Article rejected: {article.title}")
        return {"message": "Article rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting article: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject article") 


@router.post("/upload-to-app-database")
async def upload_articles_to_app_database(
    category: Optional[CategoryEnum] = None,
    tags: Optional[List[str]] = Query(None),
    source_pdf_id: Optional[str] = Query(None, description="Filter by source PDF ID")
):
    """Upload approved articles directly to the app database (educational_content collection)."""
    
    try:
        # Build query filters - only get approved articles that haven't been uploaded
        query_filters = {
            "processing_status": ProcessingStatus.APPROVED,  # Only approved articles
            "app_article_id": None  # That haven't been uploaded yet
        }
        
        if category:
            query_filters["category"] = category
            
        if tags:
            query_filters["medical_condition_tags"] = {"$in": tags}
            
        if source_pdf_id:
            query_filters["source_pdf_id"] = source_pdf_id
        
        # Get the filtered articles
        articles = await HealthArticle.find(query_filters).sort(-HealthArticle.created_at).to_list()
        
        if not articles:
            return {
                "message": "No approved articles to upload",
                "total_articles": 0,
                "uploaded_articles": 0,
                "failed_articles": 0,
                "filters_applied": {
                    "category": category.value if category else None,
                    "tags": tags,
                    "source_pdf_id": source_pdf_id
                }
            }
        
        # Upload articles to app database
        uploaded_count = 0
        failed_count = 0
        failed_articles = []
        
        for article in articles:
            try:
                # Check if article has required fields
                if not article.image_url:
                    logger.warning(f"Skipping article without image URL: {article.title}")
                    failed_count += 1
                    failed_articles.append({
                        "title": article.title,
                        "reason": "Missing image URL"
                    })
                    continue
                
                # Upload to app database
                app_article_id = await app_uploader.upload_article(article)
                
                if app_article_id:
                    # Update the health article with app database reference and status
                    article.app_article_id = app_article_id
                    article.processing_status = ProcessingStatus.UPLOADED  # Mark as uploaded
                    article.updated_at = datetime.now(timezone.utc)
                    await article.save()
                    
                    uploaded_count += 1
                    logger.info(f"Exported article to app database: {article.title} (App ID: {app_article_id})")
                else:
                    failed_count += 1
                    failed_articles.append({
                        "title": article.title,
                        "reason": "Upload failed"
                    })
                    
            except Exception as e:
                failed_count += 1
                failed_articles.append({
                    "title": article.title,
                    "reason": str(e)
                })
                logger.error(f"Failed to export article {article.title}: {e}")
        
        # Return summary
        result = {
            "message": f"Upload completed: {uploaded_count} articles uploaded, {failed_count} failed",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "total_articles": len(articles),
            "uploaded_articles": uploaded_count,
            "failed_articles": failed_count,
            "filters_applied": {
                "category": category.value if category else None,
                "tags": tags,
                "source_pdf_id": source_pdf_id
            }
        }
        
        if failed_articles:
            result["failed_details"] = failed_articles
            
        return result
        
    except Exception as e:
        logger.error(f"Error uploading articles to app database: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload articles to app database")



@router.get("/by-pdf/{pdf_id}")
async def get_articles_by_pdf(
    pdf_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page")
):
    """Get articles from a specific PDF document."""
    
    try:
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build query
        query_filters = {"source_pdf_id": pdf_id}
        
        # Get articles and count
        articles = await HealthArticle.find(query_filters).sort(-HealthArticle.created_at).skip(skip).limit(per_page).to_list()
        total_count = await HealthArticle.find(query_filters).count()
        
        # Convert to response format
        article_responses = []
        for article in articles:
            article_response = HealthArticleResponse(
                id=str(article.id),
                title=article.title,
                category=article.category,
                image_url=article.image_url,
                medical_condition_tags=article.medical_condition_tags,
                content=article.content,
                source_pdf_id=article.source_pdf_id,
                chunk_id=article.chunk_id,
                processing_status=article.processing_status,
                app_article_id=article.app_article_id,
                reading_level_score=article.reading_level_score,
                similarity_scores=article.similarity_scores,
                created_at=article.created_at,
                updated_at=article.updated_at,
                reviewed_at=article.reviewed_at,
                reviewer_notes=article.reviewer_notes
            )
            article_responses.append(article_response)
        
        return {
            "articles": article_responses,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "pdf_id": pdf_id
        }
        
    except Exception as e:
        logger.error(f"Error getting articles by PDF {pdf_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get articles")


@router.get("/export/summary")
async def get_export_summary(
    source_pdf_id: Optional[str] = Query(None, description="Filter summary by source PDF ID")
):
    """Get summary statistics for export."""
    
    try:
        # Base query filter
        base_filter = {}
        if source_pdf_id:
            base_filter["source_pdf_id"] = source_pdf_id
        
        # Get counts by status
        status_counts = {}
        for status in ProcessingStatus:
            query_filter = {**base_filter, "processing_status": status}
            count = await HealthArticle.find(query_filter).count()
            status_counts[status.value] = count
        
        # Get counts by category
        category_counts = {}
        for category in CategoryEnum:
            query_filter = {**base_filter, "category": category}
            count = await HealthArticle.find(query_filter).count()
            category_counts[category.value] = count
        
        # Get total articles
        total_articles = await HealthArticle.find(base_filter).count()
        
        # Get count of articles ready to upload (approved but not uploaded)
        ready_to_upload = await HealthArticle.find({
            **base_filter,
            "processing_status": ProcessingStatus.APPROVED,
            "app_article_id": None
        }).count()
        
        # Get recent articles
        recent_articles = await HealthArticle.find(base_filter).sort(-HealthArticle.created_at).limit(5).to_list()
        
        summary = {
            "total_articles": total_articles,
            "ready_to_upload": ready_to_upload,
            "status_breakdown": status_counts,
            "category_breakdown": category_counts,
            "source_pdf_id": source_pdf_id,
            "recent_articles": [
                {
                    "id": str(article.id),
                    "title": article.title,
                    "category": article.category,
                    "status": article.processing_status,
                    "source_pdf_id": article.source_pdf_id,
                    "created_at": article.created_at.isoformat()
                }
                for article in recent_articles
            ]
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting export summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export summary") 