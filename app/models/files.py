from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class File(Base):

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # 单位:字节
    file_type = Column(String(100), nullable=False)  # MIME类型

    is_active = Column(Boolean, default=True, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("Users", back_populates="files")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    invoice = relationship(
        "Invoice", back_populates="file", uselist=False, cascade="all, delete-orphan"
    )
