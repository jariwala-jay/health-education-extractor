"""Health articles API endpoints."""

from fastapi import APIRouter, HTTPException, Query
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

logger = logging.getLogger(__name__)

router = APIRouter()


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
                processing_status=similar.processing_status,
                reading_level_score=similar.reading_level_score,
                created_at=similar.created_at,
                updated_at=similar.updated_at
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
    """Approve an article for publication."""
    
    try:
        article = await HealthArticle.get(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article.processing_status = ProcessingStatus.APPROVED
        article.reviewed_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)
        
        await article.save()
        
        logger.info(f"Article approved: {article.title}")
        return {"message": "Article approved successfully"}
        
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


@router.get("/export/json")
async def export_articles_json(
    category: Optional[CategoryEnum] = None,
    status: Optional[ProcessingStatus] = None,
    tags: Optional[List[str]] = Query(None),
    approved_only: bool = Query(True, description="Only export approved articles"),
    source_pdf_id: Optional[str] = Query(None, description="Filter by source PDF ID")
):
    """Export health articles as JSON file."""
    
    try:
        # Build query filters
        query_filters = {}
        
        if approved_only:
            query_filters["processing_status"] = ProcessingStatus.APPROVED
        elif status:
            query_filters["processing_status"] = status
            
        if category:
            query_filters["category"] = category
            
        if tags:
            query_filters["medical_condition_tags"] = {"$in": tags}
            
        if source_pdf_id:
            query_filters["source_pdf_id"] = source_pdf_id
        
        # Get articles
        articles = await HealthArticle.find(query_filters).sort(-HealthArticle.created_at).to_list()
        
        # Convert to export format
        export_data = {
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(articles),
                "filters_applied": {
                    "category": category.value if category else None,
                    "status": status.value if status else None,
                    "tags": tags,
                    "approved_only": approved_only,
                    "source_pdf_id": source_pdf_id
                }
            },
            "articles": []
        }
        
        for article in articles:
            export_article = {
                "id": str(article.id),
                "title": article.title,
                "category": article.category,
                "imageUrl": article.image_url,
                "medicalConditionTags": article.medical_condition_tags,
                "content": article.content,
                "readingLevelScore": article.reading_level_score,
                "sourcePdfId": article.source_pdf_id,
                "createdAt": article.created_at.isoformat(),
                "updatedAt": article.updated_at.isoformat()
            }
            export_data["articles"].append(export_article)
        
        # Create JSON content
        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Create filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pdf_suffix = f"_pdf_{source_pdf_id[:8]}" if source_pdf_id else ""
        filename = f"health_articles_export{pdf_suffix}_{timestamp}.json"
        
        # Return as downloadable file
        return StreamingResponse(
            StringIO(json_content),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to export articles")


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
        
        # Get recent articles
        recent_articles = await HealthArticle.find(base_filter).sort(-HealthArticle.created_at).limit(5).to_list()
        
        summary = {
            "total_articles": total_articles,
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