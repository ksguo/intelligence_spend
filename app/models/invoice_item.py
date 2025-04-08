from sqlalchemy import Column, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class InvoiceItem(Base):

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)

    name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=False)

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoice.id"), nullable=False)
    invoice = relationship("Invoice", back_populates="items")
