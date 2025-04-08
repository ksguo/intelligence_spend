from sqlalchemy.orm import Session

from app.models.invoice_item import InvoiceItem
from app.schemas.invoice_item import InvoiceItemCreate


def create_invoice_item(db: Session, item_in: InvoiceItemCreate):
    """创建新的发票项目"""
    db_item = InvoiceItem(
        name=item_in.name,
        quantity=item_in.quantity,
        unit_price=item_in.unit_price,
        total_price=item_in.total_price,
        invoice_id=item_in.invoice_id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
