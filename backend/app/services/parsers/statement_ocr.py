import io
import re
from datetime import UTC, datetime
from typing import Any

from app.schemas.ingestion import SourceType
from app.schemas.statement import ExtractedStatementTransaction, StatementExtractionResult

# Optional PyMuPDF (fitz)
try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Optional Pillow and Tesseract
try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract

    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class StatementOCRParser:
    """Modular parser for PDF and Image bank statement extraction."""

    def __init__(self) -> None:
        self.tx_id_pattern = re.compile(
            r"\b(TX-[A-Za-z0-9_-]+|REF-[A-Za-z0-9_-]+|TRX-[A-Za-z0-9_-]+)\b", re.I
        )
        self.date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")
        self.account_pattern = re.compile(r"\b(ACC-[A-Za-z0-9_-]+|USER-[A-Za-z0-9_-]+)\b", re.I)
        self.amount_pattern = re.compile(r"\$?\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+\.\d{2})\b")
        self.currency_pattern = re.compile(r"\b(USD|EUR|GBP|INR|CAD|AUD)\b", re.I)

    def extract_text_from_bytes(
        self, content: bytes, filename: str
    ) -> tuple[list[tuple[int, str]], str]:
        """Extracts lines of text indexed by page number from PDF or image content."""
        pages_text: list[tuple[int, str]] = []
        fn_lower = filename.lower()
        engine_used = "Fallback_Parser"

        # PDF handling via PyMuPDF
        if fn_lower.endswith(".pdf"):
            if HAS_PYMUPDF:
                try:
                    doc = fitz.open(stream=content, filetype="pdf")
                    engine_used = "PyMuPDF_Text"
                    for page_idx, page in enumerate(doc, start=1):
                        txt = page.get_text()
                        if txt.strip():
                            for line in txt.splitlines():
                                if line.strip():
                                    pages_text.append((page_idx, line.strip()))
                        else:
                            # Scanned page fallback to Tesseract if available
                            if HAS_PYTESSERACT and HAS_PIL:
                                pix = page.get_pixmap()
                                img = Image.open(io.BytesIO(pix.tobytes("png")))
                                ocr_txt = pytesseract.image_to_string(img)
                                engine_used = "PyMuPDF_Tesseract_OCR"
                                for line in ocr_txt.splitlines():
                                    if line.strip():
                                        pages_text.append((page_idx, line.strip()))
                except Exception:
                    pass

        # Image handling via PIL + PyTesseract
        elif any(fn_lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            if HAS_PIL and HAS_PYTESSERACT:
                try:
                    img = Image.open(io.BytesIO(content))
                    ocr_txt = pytesseract.image_to_string(img)
                    engine_used = "Tesseract_OCR"
                    for line in ocr_txt.splitlines():
                        if line.strip():
                            pages_text.append((1, line.strip()))
                except Exception:
                    pass

        # Fallback string decoder if no PDF/Image library matched
        if not pages_text:
            try:
                raw_txt = content.decode("utf-8", errors="ignore")
                for line in raw_txt.splitlines():
                    if line.strip():
                        pages_text.append((1, line.strip()))
            except Exception:
                pass

        return pages_text, engine_used

    def parse_line(
        self, page_num: int, line: str, idx: int, filename: str
    ) -> ExtractedStatementTransaction | None:
        """Parses a single text line into a candidate transaction record."""
        # Find transaction ID
        tx_id_match = self.tx_id_pattern.search(line)
        tx_id = tx_id_match.group(1).upper() if tx_id_match else None

        # Find date
        date_match = self.date_pattern.search(line)
        date_str = date_match.group(1) if date_match else None

        # Find accounts
        acc_matches = self.account_pattern.findall(line)
        account_id = acc_matches[0].upper() if len(acc_matches) > 0 else None
        recipient_id = acc_matches[1].upper() if len(acc_matches) > 1 else None

        # Find currency
        curr_match = self.currency_pattern.search(line)
        currency = curr_match.group(1).upper() if curr_match else "USD"

        # Direction
        inbound_keywords = ("deposit", "credit", "received", "inbound", "cr")
        direction = "INBOUND" if any(w in line.lower() for w in inbound_keywords) else "OUTBOUND"

        # Strip dates, IDs, and account tokens to isolate amount
        clean_text = line
        if date_str:
            clean_text = clean_text.replace(date_str, " ")
        if tx_id:
            clean_text = clean_text.replace(tx_id, " ")
        for acc in acc_matches:
            clean_text = clean_text.replace(acc, " ")

        # Find amounts in remaining clean text
        amount_matches = re.findall(r"\$?\b(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b", clean_text)
        valid_amounts: list[float] = []
        for am_str in amount_matches:
            clean_am = am_str.replace("$", "").replace(",", "")
            try:
                val = float(clean_am)
                if val > 0.0:
                    valid_amounts.append(val)
            except ValueError:
                continue

        if not valid_amounts:
            return None

        amount = valid_amounts[0]

        # Validate required fields
        validation_errors: list[str] = []
        if not account_id:
            validation_errors.append("Missing originating account ID (e.g. ACC-XXXX)")
        if not recipient_id:
            validation_errors.append("Missing beneficiary recipient ID (e.g. ACC-YYYY)")
        if amount <= 0.0:
            validation_errors.append("Transaction amount must be greater than zero")

        # Confidence Scoring
        is_valid = len(validation_errors) == 0
        if is_valid and tx_id:
            confidence_score = 0.95
            confidence_level = "HIGH"
        elif is_valid:
            confidence_score = 0.85
            confidence_level = "MEDIUM"
            tx_id = f"STMT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{idx:03d}"
        elif account_id or recipient_id:
            confidence_score = 0.50
            confidence_level = "LOW"
            if not tx_id:
                tx_id = f"STMT-INVALID-{idx:03d}"
        else:
            confidence_score = 0.20
            confidence_level = "NEEDS_REVIEW"
            if not tx_id:
                tx_id = f"STMT-INVALID-{idx:03d}"

        extracted_fields = {
            "transaction_id": tx_id,
            "date": date_str,
            "account_id": account_id,
            "recipient_id": recipient_id,
            "amount": amount,
            "currency": currency,
            "direction": direction,
            "description": line,
        }

        return ExtractedStatementTransaction(
            page_number=page_num,
            raw_text=line,
            transaction_id=tx_id,
            date=date_str,
            account_id=account_id,
            recipient_id=recipient_id,
            amount=amount,
            currency=currency,
            direction=direction,
            description=line,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            extracted_fields=extracted_fields,
            validation_errors=validation_errors,
            is_valid=is_valid,
        )

    def parse_statement(
        self, content: bytes, filename: str = "statement.pdf"
    ) -> StatementExtractionResult:
        """Parses bank statement content, extracts transactions, and scores confidence."""
        lines_with_page, engine_used = self.extract_text_from_bytes(content, filename)

        extracted_txs: list[ExtractedStatementTransaction] = []
        valid_count = 0
        invalid_count = 0

        for idx, (page_num, line) in enumerate(lines_with_page, start=1):
            parsed = self.parse_line(page_num, line, idx, filename)
            if parsed:
                extracted_txs.append(parsed)
                if parsed.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

        batch_id = f"BATCH-STMT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        return StatementExtractionResult(
            batch_id=batch_id,
            filename=filename,
            total_lines_scanned=len(lines_with_page),
            extracted_count=len(extracted_txs),
            valid_count=valid_count,
            invalid_count=invalid_count,
            extracted_transactions=extracted_txs,
            ocr_engine_used=engine_used,
        )

    def convert_to_raw_records(
        self, extraction_result: StatementExtractionResult
    ) -> list[dict[str, Any]]:
        """Converts valid statement transactions into raw dictionaries for normalization."""
        records: list[dict[str, Any]] = []
        for item in extraction_result.extracted_transactions:
            if item.is_valid and item.account_id and item.recipient_id and item.amount:
                rec = {
                    "transaction_id": item.transaction_id,
                    "source_reference_id": item.transaction_id,
                    "account_id": item.account_id,
                    "recipient_id": item.recipient_id,
                    "amount": item.amount,
                    "currency": item.currency,
                    "channel": "WEB",
                    "payment_method": "WIRE_TRANSFER",
                    "status": "COMPLETED",
                    "timestamp": item.date or datetime.now(UTC).isoformat(),
                    "source_type": SourceType.BANK_STATEMENT.value,
                    "statement_metadata": {
                        "filename": extraction_result.filename,
                        "page_number": item.page_number,
                        "confidence_score": item.confidence_score,
                        "confidence_level": item.confidence_level,
                        "raw_text": item.raw_text,
                        "ocr_engine_used": extraction_result.ocr_engine_used,
                    },
                }
                records.append(rec)
        return records
