from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel


from app.schemas.invoice_item import InvoiceItem


class InvoiceBase(BaseModel):
    """发票基础Schema"""

    markt_name: Optional[str] = None
    store_address: Optional[str] = None
    brand: Optional[str] = None
    telephone: Optional[str] = None  # 添加电话字段
    receipt_nr: Optional[str] = None
    date: Optional[datetime] = None
    payment_method: Optional[str] = None
    total: Optional[float] = None


class InvoiceBase(BaseModel):

    markt_name: Optional[str] = None
    store_address: Optional[str] = None
    telephone: Optional[str] = None
    uid_number: Optional[str] = None
    brand: Optional[str] = None
    time: Optional[str] = None
    document_nr: Optional[str] = None
    markt_id: Optional[str] = None

    receipt_nr: Optional[str] = None
    document_nr: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    payment_method: Optional[str] = None
    total: Optional[float] = None

    items: List[Dict[str, Any]] = []


class InvoiceCreate(InvoiceBase):

    file_id: uuid.UUID
    user_id: uuid.UUID
    ocr_text: Optional[str] = None
    is_processed: bool = False


class InvoiceUpdate(BaseModel):

    markt_name: Optional[str] = None
    store_address: Optional[str] = None
    telephone: Optional[str] = None
    uid_number: Optional[str] = None
    brand: Optional[str] = None
    markt_id: Optional[str] = None

    receipt_nr: Optional[str] = None
    document_nr: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    payment_method: Optional[str] = None
    total: Optional[float] = None

    items: Optional[List[Dict[str, Any]]] = None
    ocr_text: Optional[str] = None
    is_processed: Optional[bool] = None
    processing_errors: Optional[str] = None


class InvoiceInDBBase(InvoiceBase):

    id: uuid.UUID
    file_id: uuid.UUID
    user_id: uuid.UUID
    ocr_text: Optional[str] = None
    is_processed: bool
    processing_errors: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Invoice(InvoiceInDBBase):

    pass
