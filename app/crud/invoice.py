from typing import List, Optional
import uuid
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


def get_invoice(db: Session, invoice_id: uuid.UUID) -> Optional[Invoice]:
    """获取单个发票"""
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def get_invoice_by_file(db: Session, file_id: uuid.UUID) -> Optional[Invoice]:
    """通过文件ID获取发票"""
    return db.query(Invoice).filter(Invoice.file_id == file_id).first()


def get_user_invoices(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Invoice]:
    """获取用户的所有发票"""
    return (
        db.query(Invoice)
        .filter(Invoice.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_invoice(db: Session, invoice_in: InvoiceCreate) -> Invoice:
    """创建新发票"""
    db_invoice = Invoice(
        file_id=invoice_in.file_id,
        user_id=invoice_in.user_id,
        markt_name=invoice_in.markt_name,
        store_address=invoice_in.store_address,
        telephone=invoice_in.telephone,
        uid_number=invoice_in.uid_number,
        brand=invoice_in.brand,
        markt_id=invoice_in.markt_id,
        receipt_nr=invoice_in.receipt_nr,
        document_nr=invoice_in.document_nr,
        date=invoice_in.date,
        time=invoice_in.time,
        payment_method=invoice_in.payment_method,
        total=invoice_in.total,
        items=invoice_in.items,
        ocr_text=invoice_in.ocr_text,
        is_processed=invoice_in.is_processed,
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


def update_invoice(
    db: Session, invoice_id: uuid.UUID, invoice_in: InvoiceUpdate
) -> Optional[Invoice]:
    """更新发票"""
    db_invoice = get_invoice(db, invoice_id)
    if not db_invoice:
        return None

    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_invoice, field, value)

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


def delete_invoice(db: Session, invoice_id: uuid.UUID) -> Optional[Invoice]:
    """删除发票"""
    db_invoice = get_invoice(db, invoice_id)
    if not db_invoice:
        return None

    db.delete(db_invoice)
    db.commit()
    return db_invoice
