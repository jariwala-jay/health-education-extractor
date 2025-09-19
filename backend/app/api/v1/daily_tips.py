"""Daily Tips API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from datetime import datetime, timezone

from app.models.daily_tip import (
    DailyTip,
    DailyTipCreate,
    DailyTipUpdate,
    DailyTipResponse,
    TipProcessingStatus,
    TipCategory
)
from app.models.health_article import HealthArticle
from pydantic import BaseModel
from app.core.auth_middleware import get_current_active_user
from app.services.app_database_uploader import app_uploader

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


class TipsListResponse(BaseModel):
    tips: List[DailyTipResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/", response_model=TipsListResponse)
async def get_daily_tips(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    processing_status: Optional[TipProcessingStatus] = Query(None, description="Filter by processing status"),
    source_article_id: Optional[str] = Query(None, description="Filter by source article ID")
):
    """Get daily tips with pagination and filtering."""
    
    try:
        # For now, let's use a simple approach without complex filtering
        # TODO: Implement proper filtering later
        
        # Get total count
        total = await DailyTip.count()
        
        # Get paginated results
        skip = (page - 1) * per_page
        tips = await DailyTip.find().sort(-DailyTip.created_at).skip(skip).limit(per_page).to_list()
        
        # Get source article titles for tips that have source_article_id
        source_article_titles = {}
        source_article_ids = [tip.source_article_id for tip in tips if tip.source_article_id]
        
        if source_article_ids:
            try:
                from bson import ObjectId
                # Convert string IDs to ObjectId for MongoDB query
                object_ids = [ObjectId(article_id) for article_id in source_article_ids]
                source_articles = await HealthArticle.find(
                    {"_id": {"$in": object_ids}}
                ).to_list()
                source_article_titles = {
                    str(article.id): article.title 
                    for article in source_articles
                }
                logger.info(f"Fetched {len(source_articles)} source articles for {len(source_article_ids)} tip source IDs")
            except Exception as e:
                logger.warning(f"Error fetching source article titles: {e}")
                import traceback
                traceback.print_exc()
        
        # Convert to response format
        tip_responses = [
            DailyTipResponse(
                id=str(tip.id),
                tip_text=tip.tip_text,
                category=tip.category,
                tags=tip.tags,
                source_article_id=tip.source_article_id,
                source_article_title=source_article_titles.get(tip.source_article_id) if tip.source_article_id else None,
                image_url=tip.image_url,
                processing_status=tip.processing_status,
                app_tip_id=tip.app_tip_id,
                reading_level_score=tip.reading_level_score,
                created_at=tip.created_at,
                updated_at=tip.updated_at,
                reviewed_at=tip.reviewed_at,
                reviewer_notes=tip.reviewer_notes
            )
            for tip in tips
        ]
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return TipsListResponse(
            tips=tip_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error getting daily tips: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily tips")




@router.post("/", response_model=DailyTipResponse)
async def create_daily_tip(tip_data: DailyTipCreate):
    """Create a new daily tip."""
    
    try:
        tip = DailyTip(**tip_data.model_dump())
        await tip.insert()
        
        logger.info(f"Created daily tip: {tip.tip_text[:50]}...")
        
        return DailyTipResponse(
            id=str(tip.id),
            tip_text=tip.tip_text,
            category=tip.category,
            tags=tip.tags,
            source_article_id=tip.source_article_id,
            image_url=tip.image_url,
            processing_status=tip.processing_status,
            app_tip_id=tip.app_tip_id,
            reading_level_score=tip.reading_level_score,
            created_at=tip.created_at,
            updated_at=tip.updated_at,
            reviewed_at=tip.reviewed_at,
            reviewer_notes=tip.reviewer_notes
        )
        
    except Exception as e:
        logger.error(f"Error creating daily tip: {e}")
        raise HTTPException(status_code=500, detail="Failed to create daily tip")


@router.put("/{tip_id}", response_model=DailyTipResponse)
async def update_daily_tip(tip_id: str, tip_update: DailyTipUpdate):
    """Update a daily tip."""
    
    try:
        tip = await DailyTip.get(tip_id)
        if not tip:
            raise HTTPException(status_code=404, detail="Tip not found")
        
        # Update fields
        update_data = tip_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tip, field, value)
        
        # Update reviewed_at if processing status changes
        if 'processing_status' in update_data and update_data['processing_status'] in [TipProcessingStatus.REVIEWED, TipProcessingStatus.APPROVED, TipProcessingStatus.REJECTED]:
            tip.reviewed_at = datetime.now(timezone.utc)
        
        tip.updated_at = datetime.now(timezone.utc)
        await tip.save()
        
        logger.info(f"Updated daily tip: {tip_id}")
        
        return DailyTipResponse(
            id=str(tip.id),
            tip_text=tip.tip_text,
            category=tip.category,
            tags=tip.tags,
            source_article_id=tip.source_article_id,
            image_url=tip.image_url,
            processing_status=tip.processing_status,
            app_tip_id=tip.app_tip_id,
            reading_level_score=tip.reading_level_score,
            created_at=tip.created_at,
            updated_at=tip.updated_at,
            reviewed_at=tip.reviewed_at,
            reviewer_notes=tip.reviewer_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating daily tip {tip_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update daily tip")




@router.delete("/{tip_id}")
async def delete_daily_tip(tip_id: str):
    """Delete a daily tip."""
    
    try:
        tip = await DailyTip.get(tip_id)
        if not tip:
            raise HTTPException(status_code=404, detail="Tip not found")
        
        await tip.delete()
        
        logger.info(f"Deleted daily tip: {tip_id}")
        
        return {"message": "Tip deleted successfully", "tip_id": tip_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting daily tip {tip_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete daily tip")


@router.get("/stats")
async def get_tips_stats():
    """Get statistics about daily tips."""
    
    try:
        total_tips = await DailyTip.find().count()
        
        # Get tips by processing status
        status_counts = {}
        for status in TipProcessingStatus:
            count = await DailyTip.find({"processing_status": status}).count()
            status_counts[status.value] = count
        
        # Get tips by source article
        tips_by_article = await DailyTip.aggregate([
            {"$group": {"_id": "$source_article_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list()
        
        return {
            "total_tips": total_tips,
            "status_counts": status_counts,
            "tips_by_article": tips_by_article
        }
        
    except Exception as e:
        logger.error(f"Error getting tips stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tips stats")


@router.post("/upload-to-app-database")
async def upload_tips_to_app_database(
    category: Optional[TipCategory] = None,
    tags: Optional[List[str]] = Query(None),
    source_pdf_id: Optional[str] = Query(None, description="Filter by source PDF ID")
):
    """Upload approved tips directly to the app database (tips collection)."""
    
    try:
        # Build query filters - only get approved tips that haven't been uploaded
        query_filters = {
            "processing_status": TipProcessingStatus.APPROVED,  # Only approved tips
            "app_tip_id": None  # That haven't been uploaded yet
        }
            
        if category:
            query_filters["category"] = category
            
        if tags:
            query_filters["tags"] = {"$in": tags}
            
        if source_pdf_id:
            query_filters["source_article_id"] = {"$exists": True}  # Tips with source articles
            # We'll filter by source PDF through the source article
        
        # Get the filtered tips
        tips = await DailyTip.find(query_filters).sort(-DailyTip.created_at).to_list()
        
        # If source_pdf_id is specified, filter tips by their source article's PDF
        if source_pdf_id:
            tips = [tip for tip in tips if tip.source_article_id]
            if tips:
                # Get source articles for these tips
                source_article_ids = [tip.source_article_id for tip in tips if tip.source_article_id]
                source_articles = await HealthArticle.find(
                    {"_id": {"$in": source_article_ids}, "source_pdf_id": source_pdf_id}
                ).to_list()
                source_article_id_set = {str(article.id) for article in source_articles}
                tips = [tip for tip in tips if tip.source_article_id in source_article_id_set]
        
        if not tips:
            return {
                "message": "No approved tips to upload",
                "total_tips": 0,
                "uploaded_tips": 0,
                "failed_tips": 0,
                "filters_applied": {
                    "category": category.value if category else None,
                    "tags": tags,
                    "source_pdf_id": source_pdf_id
                }
            }
        
        # Upload tips to app database
        uploaded_count = 0
        failed_count = 0
        failed_tips = []
        
        for tip in tips:
            try:
                # Check if tip has required fields
                if not tip.image_url:
                    logger.warning(f"Skipping tip without image URL: {tip.tip_text[:50]}...")
                    failed_count += 1
                    failed_tips.append({
                        "tip_text": tip.tip_text[:50] + "...",
                        "reason": "Missing image URL"
                    })
                    continue
                
                # Upload to app database
                app_tip_id = await app_uploader.upload_tip(tip)
                
                if app_tip_id:
                    # Update the tip with the app ID
                    tip.app_tip_id = app_tip_id
                    tip.processing_status = TipProcessingStatus.UPLOADED
                    tip.updated_at = datetime.now(timezone.utc)
                    await tip.save()
                    
                    uploaded_count += 1
                    logger.info(f"Uploaded tip to app database: {tip.tip_text[:50]}... (App ID: {app_tip_id})")
                else:
                    failed_count += 1
                    failed_tips.append({
                        "tip_text": tip.tip_text[:50] + "...",
                        "reason": "Failed to upload to app database"
                    })
                
            except Exception as e:
                logger.error(f"Error uploading tip {tip.id}: {e}")
                failed_count += 1
                failed_tips.append({
                    "tip_text": tip.tip_text[:50] + "...",
                    "reason": str(e)
                })
        
        return {
            "message": f"Upload completed: {uploaded_count} tips uploaded, {failed_count} failed",
            "total_tips": len(tips),
            "uploaded_tips": uploaded_count,
            "failed_tips": failed_count,
            "failed_details": failed_tips if failed_tips else None,
            "filters_applied": {
                "category": category.value if category else None,
                "tags": tags,
                "source_pdf_id": source_pdf_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading tips to app database: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload tips to app database")
