from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.consumer_analysis import ConsumerAnalysis
from app.schemas.consumer_analysis import ConsumerAnalysisCreate


def create_consumer_analysis(
    db: Session, analysis_in: ConsumerAnalysisCreate
) -> ConsumerAnalysis:
    """创建新的分析记录"""
    db_analysis = ConsumerAnalysis(
        user_id=analysis_in.user_id,
        analysis_data=analysis_in.analysis_data,
        raw_response=analysis_in.raw_response,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_latest_user_analysis(
    db: Session, user_id: uuid.UUID
) -> Optional[ConsumerAnalysis]:
    """获取用户最新的分析记录"""
    return (
        db.query(ConsumerAnalysis)
        .filter(ConsumerAnalysis.user_id == user_id)
        .order_by(desc(ConsumerAnalysis.created_at))
        .first()
    )


def get_user_analyses(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 10
) -> List[ConsumerAnalysis]:
    """获取用户的所有分析记录"""
    return (
        db.query(ConsumerAnalysis)
        .filter(ConsumerAnalysis.user_id == user_id)
        .order_by(desc(ConsumerAnalysis.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_analysis(db: Session, analysis_id: uuid.UUID) -> Optional[ConsumerAnalysis]:
    """获取指定ID的分析记录"""
    return db.query(ConsumerAnalysis).filter(ConsumerAnalysis.id == analysis_id).first()
