from sqlalchemy import Boolean, Column, DateTime, String, Text, ForeignKey, Float
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Invoice(Base):
    """
    发票模型 - 存储从上传文件中提取的发票数据
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)

    # 发票基本信息
    markt_name = Column(String(255), nullable=True)
    store_address = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True)
    telephone = Column(String(50), nullable=True)
    uid_number = Column(String(50), nullable=True)  # UID-Nr.
    markt_id = Column(String(50), nullable=True)  # 新增：商店ID

    # 发票详情
    receipt_nr = Column(String(100), nullable=True)  # Bon-Nr.
    document_nr = Column(String(100), nullable=True)  # 新增：Beleg-Nr.
    date = Column(DateTime, nullable=True)
    time = Column(String(20), nullable=True)  # 新增：时间
    payment_method = Column(String(50), nullable=True)
    total = Column(Float, nullable=True)

    # 原始OCR文本
    ocr_text = Column(Text, nullable=True)

    # 处理状态
    is_processed = Column(Boolean, default=False, nullable=False)

    # 关系
    file_id = Column(UUID(as_uuid=True), ForeignKey("file.id"), nullable=False)
    file = relationship("File", back_populates="invoice")

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="invoices")

    # 商品项目关系
    items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
