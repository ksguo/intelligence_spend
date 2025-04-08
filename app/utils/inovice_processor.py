import os
import subprocess
import re
import json
from datetime import datetime
import pdfplumber
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvoiceProcessor:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_extension = os.path.splitext(file_path)[1].lower()
        self.ocr_output_path = None
        self.extracted_text = ""
        self.extracted_data = {
            "markt_name": None,
            "store_address": None,
            "telephone": None,
            "uid_number": None,
            "items": [],
            "total": None,
            "date": None,
            "time": None,
            "payment_method": None,
            "receipt_nr": None,
            "document_nr": None,
            "brand": None,
            "markt_id": None,
        }

    def process(self) -> Dict[str, Any]:

        try:

            if self.file_extension == ".pdf":
                self._process_pdf()
            elif self.file_extension in [".jpg", ".jpeg", ".png"]:
                self._process_image()
            else:
                logger.error(f"not support file type: {self.file_extension}")
                return self.extracted_data

            if self.extracted_text:
                self._extract_invoice_data()

            return self.extracted_data

        except Exception as e:
            logger.error(f"error processing invoice: {str(e)}")
            return self.extracted_data

    def _process_pdf(self):

        base_path = os.path.splitext(self.file_path)[0]
        self.ocr_output_path = f"{base_path}_ocr.pdf"

        try:

            result = subprocess.run(
                [
                    "ocrmypdf",
                    "--skip-text",
                    "--deskew",
                    "--clean",
                    "--language",
                    "deu+eng",
                    self.file_path,
                    self.ocr_output_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"ocr process successful: {result.stdout}")

            self._extract_text_from_pdf(self.ocr_output_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"ocr process failed: {e.stderr}")

            self._extract_text_from_pdf(self.file_path)

    def _process_image(self):

        base_path = os.path.splitext(self.file_path)[0]
        temp_pdf_path = f"{base_path}_temp.pdf"
        self.ocr_output_path = f"{base_path}_ocr.pdf"

        try:

            result = subprocess.run(
                ["convert", self.file_path, temp_pdf_path],
                capture_output=True,
                text=True,
                check=True,
            )

            result = subprocess.run(
                [
                    "ocrmypdf",
                    "--deskew",
                    "--clean",
                    "--language",
                    "deu+eng",
                    temp_pdf_path,
                    self.ocr_output_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self._extract_text_from_pdf(self.ocr_output_path)

            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"image process failed: {e.stderr}")

    def _extract_text_from_pdf(self, pdf_path):

        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    text_parts.append(text)

            self.extracted_text = "\n".join(text_parts)
            logger.info(
                f"text extracted successful,total {len(self.extracted_text)} characters"
            )
        except Exception as e:
            logger.error(f"text extracted failed: {str(e)}")

    def _extract_invoice_data(self):

        if not self.extracted_text:
            logger.warning("no text extracted from the invoice")
            return

        text = self.extracted_text

        if re.search(r"REWE", text, re.IGNORECASE):
            self.extracted_data["brand"] = "REWE"
        elif re.search(r"Kaufland", text, re.IGNORECASE):
            self.extracted_data["brand"] = "Kaufland"
        elif re.search(r"ALDI", text, re.IGNORECASE):
            self.extracted_data["brand"] = "ALDI"
        elif re.search(r"LIDL", text, re.IGNORECASE):
            self.extracted_data["brand"] = "LIDL"
        elif re.search(r"Edeka", text, re.IGNORECASE):
            self.extracted_data["brand"] = "Edeka"

        markt_match = re.search(r"REWE\s+([A-Za-z0-9\s.\-]+)(?=\n|$)", text)
        if markt_match:
            self.extracted_data["markt_name"] = markt_match.group(1).strip()

        address_match = re.search(
            r"(?<=\n)([A-Za-zäöüÄÖÜß\s.\-]+\s\d+[\s,]*\n\d{5}\s+[A-Za-zäöüÄÖÜß\s.\-]+)",
            text,
        )
        if address_match:
            self.extracted_data["store_address"] = address_match.group(1).strip()

        phone_match = re.search(
            r"(?:Tel|Telefon|Tel\.)[:\s]+([0-9\s/\-+]+)", text, re.IGNORECASE
        )
        if phone_match:
            self.extracted_data["telephone"] = phone_match.group(1).strip()

        uid_match = re.search(
            r"(?:UID-Nr|USt-IdNr|Steuernummer)[:\s.]+([A-Z0-9\s]+)", text, re.IGNORECASE
        )
        if uid_match:
            self.extracted_data["uid_number"] = uid_match.group(1).strip()

        markt_id_match = re.search(
            r"(?:Markt-ID|Filial-ID|Markt)[:\s]+(\d+)", text, re.IGNORECASE
        )
        if markt_id_match:
            self.extracted_data["markt_id"] = markt_id_match.group(1).strip()

        receipt_match = re.search(
            r"(?:Bon-Nr|Bon|Beleg)[:\s.]+([A-Z0-9\-]+)", text, re.IGNORECASE
        )
        if receipt_match:
            self.extracted_data["receipt_nr"] = receipt_match.group(1).strip()

        doc_match = re.search(
            r"(?:Beleg-Nr|Belegnummer)[:\s.]+([A-Z0-9\-]+)", text, re.IGNORECASE
        )
        if doc_match and not self.extracted_data["receipt_nr"]:
            self.extracted_data["document_nr"] = doc_match.group(1).strip()

        date_match = re.search(r"(\d{1,2})[\.-](\d{1,2})[\.-](\d{2,4})", text)
        if date_match:
            day, month, year = date_match.groups()
            if len(year) == 2:
                year = "20" + year
            try:
                self.extracted_data["date"] = datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        time_match = re.search(r"(\d{1,2}):(\d{2})(?:\s*Uhr)?", text)
        if time_match:
            self.extracted_data["time"] = f"{time_match.group(1)}:{time_match.group(2)}"

        payment_methods = [
            "EC-Cash",
            "Girocard",
            "Kreditkarte",
            "Mastercard",
            "Visa",
            "American Express",
            "BAR",
            "Bar",
            "Bargeld",
        ]
        for method in payment_methods:
            if re.search(rf"\b{method}\b", text, re.IGNORECASE):
                self.extracted_data["payment_method"] = method
                break

        total_match = re.search(
            r"(?:SUMME|Summe|Gesamtbetrag|Gesamt|Total)[:\s]*(\d+[,.]\d{2})",
            text,
            re.IGNORECASE,
        )
        if total_match:
            try:
                self.extracted_data["total"] = float(
                    total_match.group(1).replace(",", ".")
                )
            except ValueError:
                pass

        self._extract_items_rewe()

    def _extract_items_rewe(self):

        lines = self.extracted_text.split("\n")
        items = []

        start_markers = [
            r"^\s*\d+\s+Artikel",
            r"Ihre\s+Einkäufe",
            r"^Pos\.\s+Artikel",
            r"Artikelbezeichnung",
            r"mit Pick & Go",
            r"UID Nr\.",
            r"EUR$",
        ]

        end_markers = [
            r"^\s*SUMME\s+EUR",
            r"^\s*Gesamtbetrag",
            r"^\s*Summe\s+EUR",
            r"^\s*zu zahlen",
            r"^-{6,}",
        ]

        start_index = -1
        end_index = -1

        for i, line in enumerate(lines):
            for pattern in start_markers:
                if re.search(pattern, line, re.IGNORECASE):
                    start_index = i
                    logger.info(f"找到商品区域开始标记: '{line}' at line {i}")
                    break
            if start_index != -1:
                break

        if start_index != -1:
            start_index += 1

        if start_index != -1:
            for i in range(start_index + 1, len(lines)):
                for pattern in end_markers:
                    if re.search(pattern, lines[i], re.IGNORECASE):
                        end_index = i
                        logger.info(f"找到商品区域结束标记: '{lines[i]}' at line {i}")
                        break
                if end_index != -1:
                    break

        if start_index == -1:
            logger.warning("未找到商品区域开始标记")
        if end_index == -1:
            logger.warning("未找到商品区域结束标记")

        if start_index != -1 and end_index != -1:
            logger.info(f"商品区域范围: {start_index} 到 {end_index-1}")

            logger.debug("商品区域内容:")
            for i in range(start_index, end_index):
                logger.debug(f"  行 {i}: {lines[i]}")

            for i in range(start_index, end_index):
                line = lines[i].strip()
                if not line or re.search(r"www\.|http|^EUR$", line, re.IGNORECASE):
                    continue

                rewe_item_match = re.search(
                    r"(.+?)\s+(\d+[,.]\d{1,2})\s*([A-Z])$", line
                )
                if rewe_item_match:
                    name, price, tax_category = rewe_item_match.groups()
                    items.append(
                        {
                            "name": name.strip(),
                            "total_price": float(price.replace(",", ".")),
                        }
                    )
                    logger.info(f"匹配到REWE商品: {name.strip()}, 价格: {price}")
                    continue

                item_match = re.search(
                    r"(.+?)\s+(\d+(?:[,.]\d+)?)\s*[xX]\s*(\d+[,.]\d{2})\s+(\d+[,.]\d{2})",
                    line,
                )
                if item_match:
                    name, quantity, unit_price, total_price = item_match.groups()
                    items.append(
                        {
                            "name": name.strip(),
                            "quantity": float(quantity.replace(",", ".")),
                            "unit_price": float(unit_price.replace(",", ".")),
                            "total_price": float(total_price.replace(",", ".")),
                        }
                    )
                    continue

                price_match = re.search(r"(.+?)\s+(\d+[,.]\d{2})$", line)
                if price_match:
                    name, price = price_match.groups()

                    if not re.search(
                        r"MwSt\.|Rabatt|Pfand|Steuer|Netto|Brutto", name, re.IGNORECASE
                    ):
                        items.append(
                            {
                                "name": name.strip(),
                                "total_price": float(price.replace(",", ".")),
                            }
                        )
                        continue

        logger.info(f"共提取到 {len(items)} 个商品项目")
        self.extracted_data["items"] = items
