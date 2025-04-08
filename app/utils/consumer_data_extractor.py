import logging
from typing import Dict, Any, List
import json
from sqlalchemy.orm import Session
import uuid

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem

logger = logging.getLogger(__name__)


class ConsumerDataExtractor:

    def __init__(self, user_id, db: Session):
        self.user_id = user_id
        self.db = db

    def extract_data(self) -> Dict[str, Any]:

        try:

            invoices = (
                self.db.query(Invoice)
                .filter(Invoice.user_id == self.user_id)
                .order_by(Invoice.date.desc())
                .all()
            )

            if not invoices:
                logger.warning(f"用户 {self.user_id} 没有发票记录")
                return {"error": "没有找到发票数据"}

            invoice_ids = [invoice.id for invoice in invoices]

            items = (
                self.db.query(InvoiceItem)
                .filter(InvoiceItem.invoice_id.in_(invoice_ids))
                .all()
            )

            items_by_invoice = {}
            for item in items:
                if item.invoice_id not in items_by_invoice:
                    items_by_invoice[item.invoice_id] = []
                items_by_invoice[item.invoice_id].append(
                    {
                        "name": item.name,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                    }
                )

            formatted_invoices = []
            for invoice in invoices:
                invoice_data = {
                    "id": str(invoice.id),
                    "date": invoice.date.strftime("%Y-%m-%d") if invoice.date else None,
                    "time": invoice.time,
                    "store": invoice.markt_name or invoice.brand,
                    "store_address": invoice.store_address,
                    "total": invoice.total,
                    "payment_method": invoice.payment_method,
                    "items": items_by_invoice.get(invoice.id, []),
                }
                formatted_invoices.append(invoice_data)

            total_spent = sum(i.total for i in invoices if i.total is not None)
            total_items = len(items)

            consumer_data = {
                "user_id": str(self.user_id),
                "invoices": formatted_invoices,
                "summary": {
                    "total_invoices": len(invoices),
                    "total_items": total_items,
                    "total_spent": round(total_spent, 2),
                },
            }

            logger.info(
                f"已提取用户 {self.user_id} 的 {len(invoices)} 份发票和 {total_items} 个商品项"
            )
            return consumer_data

        except Exception as e:
            logger.error(f"提取用户 {self.user_id} 的数据时出错: {str(e)}")
            return {"error": f"数据提取错误: {str(e)}"}
