from typing import Optional
import uuid
from pydantic import BaseModel


class InvoiceItemBase(BaseModel):

    name: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: float


class InvoiceItemCreate(InvoiceItemBase):

    invoice_id: uuid.UUID


class InvoiceItemInDBBase(InvoiceItemBase):

    id: uuid.UUID
    invoice_id: uuid.UUID

    model_config = {"from_attributes": True}


class InvoiceItem(InvoiceItemInDBBase):

    pass
