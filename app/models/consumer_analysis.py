from sqlalchemy import Column, DateTime, String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ConsumerAnalysis(Base):
    """
    存储ChatGPT分析的消费数据结果
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)

    # 基本关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="consumer_analyses")

    # 分析结果
    analysis_data = Column(JSON, nullable=False)  # ChatGPT分析的结构化结果
    raw_response = Column(Text, nullable=True)  # ChatGPT的原始响应

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
