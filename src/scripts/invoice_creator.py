import os
import io
import base64
import datetime
import logging
from typing import Dict, Optional

import qrcode
from jinja2 import Template

class InvoiceCreator:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    @staticmethod
    def encode_tlv(tag: int, value: str) -> bytes:
        """Encode a single TLV field"""
        value_bytes = value.encode("utf-8")
        return bytes([tag]) + bytes([len(value_bytes)]) + value_bytes

    @staticmethod
    def generate_qr_base64(data: str, box_size: int = 6, border: int = 2) -> str:
        """Generate QR PNG from raw data and return base64 (for HTML embedding)."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    @classmethod
    def generate_zatca_qr_base64(cls, seller_name: str, vat_number: str,
                                    issue_datetime: str, total_with_vat: str, vat_total: str) -> str:
        """Generate ZATCA-compliant QR code (Base64 TLV encoding)."""
        tlv_bytes = b"".join([
            cls.encode_tlv(1, seller_name),
            cls.encode_tlv(2, vat_number),
            cls.encode_tlv(3, issue_datetime),
            cls.encode_tlv(4, total_with_vat),
            cls.encode_tlv(5, vat_total),
        ])

        base64_str = base64.b64encode(tlv_bytes).decode("utf-8")
        return cls.generate_qr_base64(base64_str)

    # Read template once, as a class variable
    with open(os.path.join(os.getcwd(), 'src/scripts/template/invoice.html'), mode='r', encoding='utf-8') as f:
        INVOICE_TEMPLATE = f.read()

    @classmethod
    def render_invoice_html(cls, context: Dict) -> str:
        tpl = Template(cls.INVOICE_TEMPLATE)
        return tpl.render(**context, enumerate=enumerate)

    @staticmethod
    def html_to_pdf_weasy(html_str: str, output_path: str) -> None:
        try:
            from weasyprint import HTML
        except Exception as e:
            raise RuntimeError("WeasyPrint not available: " + str(e))
        HTML(string=html_str).write_pdf(output_path)
        InvoiceCreator.logger.info("PDF written with WeasyPrint: %s", output_path)

    @staticmethod
    def html_to_pdf_pdfkit(html_str: str, output_path: str, wkhtmltopdf_path: Optional[str] = None) -> None:
        import pdfkit
        config = None
        if wkhtmltopdf_path:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        pdfkit.from_string(html_str, output_path, configuration=config)
        InvoiceCreator.logger.info("PDF written with pdfkit/wkhtmltopdf: %s", output_path)

    @staticmethod
    def html_to_pdf_auto(html_str: str, output_path: str,
                            prefer: str = "weasyprint", wkhtmltopdf_path: Optional[str] = None) -> None:
        errors = []
        if prefer == "weasyprint":
            try:
                InvoiceCreator.html_to_pdf_weasy(html_str, output_path)
                return
            except Exception as e:
                errors.append(("weasyprint", str(e)))
                InvoiceCreator.logger.warning("WeasyPrint failed: %s", e)
                try:
                    InvoiceCreator.html_to_pdf_pdfkit(html_str, output_path, wkhtmltopdf_path=wkhtmltopdf_path)
                    return
                except Exception as e2:
                    errors.append(("pdfkit", str(e2)))
        else:
            try:
                InvoiceCreator.html_to_pdf_pdfkit(html_str, output_path, wkhtmltopdf_path=wkhtmltopdf_path)
                return
            except Exception as e:
                errors.append(("pdfkit", str(e)))
                InvoiceCreator.logger.warning("pdfkit failed: %s", e)
                try:
                    InvoiceCreator.html_to_pdf_weasy(html_str, output_path)
                    return
                except Exception as e2:
                    errors.append(("weasyprint", str(e2)))

        raise RuntimeError("All converters failed: " + str(errors))

    def main(self, data: object, issue_datetime: datetime.datetime):
        """
            Main function: expects `data` dict with the following pattern:

            {
                "store": {
                    "seller_name": str,
                    "address": str,
                    "vat_number": str
                },
                "invoice": {
                    "number": str,
                    "tax_number": str,
                    "issue_datetime": str  # will be overwritten if issue_datetime arg is provided
                },
                "customer": {
                    "name": str,
                    "address": str
                },
                "items": [
                    {"name": str, "quantity": int, "price": float, "total": float},
                    ...
                ],
                "price": {
                    "subtotal": float,
                    "taxes": float,
                    "net_total": float
                }
            }
        """
        qr_b64 = self.generate_zatca_qr_base64(
            seller_name=data["store"]["name"],
            vat_number=data["invoice"]["tax_number"],
            issue_datetime=issue_datetime,
            total_with_vat=str(data["price"]["net_total"]),
            vat_total=str(data["price"]["taxes"])
        )

        data["qr_base64"] = qr_b64
        data["invoice"]["issue_datetime"] = issue_datetime

        html = self.render_invoice_html(data)
        out_pdf = "invoice_example.pdf"

        try:
            self.html_to_pdf_auto(html, out_pdf, prefer="weasyprint", wkhtmltopdf_path=None)
            self.logger.info("Done. PDF saved to %s", out_pdf)
        except Exception as e:
            self.logger.exception("Failed to create PDF: %s", e)
            with open("debug_invoice.html", "w", encoding="utf-8") as f:
                f.write(html)
            self.logger.info("Saved debug_invoice.html for inspection.")