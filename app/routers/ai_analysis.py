from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timezone

from app.core.db import get_db
from app.auth import get_current_active_user
from app.models.user import User as UserModel

from app.utils.consumer_data_extractor import ConsumerDataExtractor
from app.utils.chatgpt_client import ChatGPTClient
from app.crud.consumer_analysis import (
    create_consumer_analysis,
    get_latest_user_analysis,
    get_user_analyses,
    get_analysis,
)
from app.schemas.consumer_analysis import (
    ConsumerAnalysis as ConsumerAnalysisSchema,
    ConsumerAnalysisCreate,
)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/analyze-consumer-data", response_model=Dict[str, Any])
async def analyze_consumer_data(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    data_extractor = ConsumerDataExtractor(current_user.id, db)
    consumer_data = data_extractor.extract_data()

    if "error" in consumer_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=consumer_data["error"]
        )

    chatgpt_client = ChatGPTClient()
    analysis_result = await chatgpt_client.analyze_consumer_data(consumer_data)

    if "error" in analysis_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result["error"],
        )

    analysis_create = ConsumerAnalysisCreate(
        user_id=current_user.id,
        analysis_data=analysis_result["analysis"],
        raw_response=analysis_result.get("raw_response"),
    )

    db_analysis = create_consumer_analysis(db, analysis_create)

    return {
        "analysis_id": str(db_analysis.id),
        "created_at": db_analysis.created_at.isoformat(),
        "analysis": db_analysis.analysis_data,
        "from_cache": False,
    }


@router.get("/consumer-analyses", response_model=List[ConsumerAnalysisSchema])
async def get_analysis_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    analyses = get_user_analyses(db, current_user.id, skip=skip, limit=limit)
    return analyses


@router.get("/consumer-analyses/{analysis_id}", response_model=ConsumerAnalysisSchema)
async def get_analysis_by_id(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """get analysis by id"""
    analysis = get_analysis(db, analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"analysis record {analysis_id} not exists",
        )

    # check if the analysis belongs to the current user or if the user is a superuser
    if analysis.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you have no permission to access this analysis",
        )

    return analysis
