from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from typing import Tuple
from uuid import uuid4

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.config import Config
from src.db.models.invoices import Invoice, InvoiceStatus


class ZakatService:
    async def process_pending(self, session: AsyncSession, limit: int = 50, simulate: bool = True) -> dict[str, int]:
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.status == InvoiceStatus.PENDING)
            .limit(limit)
        )
        res = await session.execute(stmt)
        invoices = list(res.scalars().all())

        processed = 0
        success = 0
        failed = 0

        for inv in invoices:
            processed += 1
            try:
                xml = self.build_xml(inv)
                enc_xml, xml_hash = self.encrypt_xml(xml)

                inv.zatca_xml = enc_xml
                inv.zatca_xml_hash = xml_hash
                inv.status = InvoiceStatus.IN_PROGRESS
                await session.flush()

                if simulate or not Config.ZATCA_ENDPOINT:
                    inv.zatca_uuid = str(uuid4())
                    inv.status = InvoiceStatus.DONE
                    inv.submitted_at = datetime.utcnow()
                    await session.flush()
                    success += 1
                else:
                    ok, msg, remote_id = await self.upload_xml(enc_xml, xml_hash, str(inv.id))
                    if ok:
                        inv.zatca_uuid = remote_id or str(uuid4())
                        inv.status = InvoiceStatus.DONE
                        inv.submitted_at = datetime.utcnow()
                        success += 1
                    else:
                        inv.status = InvoiceStatus.FAILED
                        inv.last_error = msg[:1000]
                        failed += 1
            except Exception as e:
                inv.status = InvoiceStatus.FAILED
                inv.last_error = str(e)[:1000]
                failed += 1

        await session.commit()
        return {"processed": processed, "success": success, "failed": failed}

    def build_xml(self, inv: Invoice) -> str:
        items_xml = "".join(
            [
                f"<cac:InvoiceLine><cbc:ID>{i.id}</cbc:ID><cbc:InvoicedQuantity>{i.quantity}</cbc:InvoicedQuantity><cbc:LineExtensionAmount>{i.price}</cbc:LineExtensionAmount></cac:InvoiceLine>"
                for i in (inv.items or [])
            ]
        )
        return (
            """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>{invoice_number}</cbc:ID>
  <cbc:UUID>{uuid}</cbc:UUID>
  <cbc:IssueDate>{date}</cbc:IssueDate>
  <cbc:TaxTotal>{taxes}</cbc:TaxTotal>
  <cbc:LegalMonetaryTotal>{net_total}</cbc:LegalMonetaryTotal>
  <cac:AccountingSupplierParty>
    <cbc:Name>{store_name}</cbc:Name>
    <cbc:CompanyID>{vat_number}</cbc:CompanyID>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cbc:Name>{account_id}</cbc:Name>
  </cac:AccountingCustomerParty>
  {items}
</Invoice>"""
        ).format(
            invoice_number=inv.invoice_number,
            uuid=str(inv.id),
            date=inv.date.date().isoformat() if isinstance(inv.date, datetime) else str(inv.date),
            taxes=inv.taxes,
            net_total=inv.net_total,
            store_name=inv.store_name,
            vat_number=inv.vat_number,
            account_id=inv.account_id,
            items=items_xml,
        )

    def encrypt_xml(self, xml: str) -> Tuple[str, str]:
        xml_bytes = xml.encode("utf-8")
        xml_hash = hashlib.sha256(xml_bytes).hexdigest()
        enc_xml = base64.b64encode(xml_bytes).decode("ascii")
        return enc_xml, xml_hash

    async def upload_xml(self, enc_xml: str, xml_hash: str, invoice_uuid: str) -> Tuple[bool, str, str | None]:
        """Upload XML to ZATCA using production service"""
        try:
            # Import here to avoid circular imports
            from src.services.zatca_production import get_zatca_service
            
            zatca_service = get_zatca_service()
            
            # Decode the base64 XML
            xml_bytes = base64.b64decode(enc_xml)
            xml_str = xml_bytes.decode('utf-8')
            
            # Submit to ZATCA
            result = await zatca_service.submit_invoice(xml_str, xml_hash, invoice_uuid)
            
            if result["success"]:
                return True, result["message"], result["zatca_uuid"]
            else:
                error_msg = result.get("error", "Unknown error")
                if "zatca_errors" in result and result["zatca_errors"]:
                    error_msg += f" - ZATCA Errors: {result['zatca_errors']}"
                return False, error_msg, None
                
        except Exception as e:
            return False, str(e), None
