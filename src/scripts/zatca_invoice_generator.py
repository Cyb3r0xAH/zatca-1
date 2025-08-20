#!/usr/bin/env python3
"""
ZATCA-compliant invoice generation script
Generates invoices with proper XML structure, encryption, and QR codes
"""

import os
import sys
import asyncio
import base64
import hashlib
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_session
from src.db.models.invoices import Invoice, InvoiceItem, InvoiceStatus
from src.scripts.invoice_creator import InvoiceCreator


class ZATCAInvoiceGenerator:
    """Enhanced invoice generator with full ZATCA compliance"""
    
    def __init__(self):
        self.invoice_creator = InvoiceCreator()
        
    def calculate_tax(self, amount: Decimal, tax_rate: Decimal = Decimal('0.15')) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate tax amounts with proper rounding
        Returns: (tax_amount, seller_tax, net_total)
        """
        # Round to 2 decimal places
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calculate VAT (15%)
        tax_amount = (amount * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # For simplified invoices, seller tax is usually the same as VAT
        seller_tax = tax_amount
        
        # Net total includes tax
        net_total = (amount + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return tax_amount, seller_tax, net_total
    
    def generate_zatca_xml(self, invoice_data: Dict) -> str:
        """Generate ZATCA-compliant UBL 2.1 XML"""
        
        # Generate UUID for this invoice
        invoice_uuid = str(uuid.uuid4())
        
        # Format date properly
        issue_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        issue_time = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        # Build invoice lines XML
        invoice_lines = []
        for idx, item in enumerate(invoice_data.get('items', []), 1):
            line_xml = f"""
    <cac:InvoiceLine>
        <cbc:ID>{idx}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="PCE">{item['quantity']}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="SAR">{item['price']}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>{item['name']}</cbc:Name>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="SAR">{item['price']}</cbc:PriceAmount>
        </cac:Price>
        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="SAR">{item.get('tax', 0)}</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="SAR">{item['price']}</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="SAR">{item.get('tax', 0)}</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:ID>S</cbc:ID>
                    <cbc:Percent>15.00</cbc:Percent>
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>
    </cac:InvoiceLine>"""
            invoice_lines.append(line_xml)
        
        # Build complete XML
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>BR-KSA-CB</cbc:CustomizationID>
    <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
    <cbc:ID>{invoice_data['invoice']['number']}</cbc:ID>
    <cbc:UUID>{invoice_uuid}</cbc:UUID>
    <cbc:IssueDate>{issue_date}</cbc:IssueDate>
    <cbc:IssueTime>{issue_time}</cbc:IssueTime>
    <cbc:InvoiceTypeCode name="0200000">388</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>SAR</cbc:DocumentCurrencyCode>
    <cbc:TaxCurrencyCode>SAR</cbc:TaxCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="CRN">{invoice_data['store']['vat_number']}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>{invoice_data['store']['name']}</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>{invoice_data['store']['address']}</cbc:StreetName>
                <cbc:CityName>الرياض</cbc:CityName>
                <cbc:PostalZone>12345</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>SA</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{invoice_data['store']['vat_number']}</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>{invoice_data['customer']['name']}</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="SAR">{invoice_data['price']['taxes']}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="SAR">{invoice_data['price']['subtotal']}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="SAR">{invoice_data['price']['taxes']}</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>15.00</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="SAR">{invoice_data['price']['subtotal']}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="SAR">{invoice_data['price']['subtotal']}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="SAR">{invoice_data['price']['net_total']}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="SAR">{invoice_data['price']['net_total']}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    {''.join(invoice_lines)}
</Invoice>"""
        
        return xml.strip()
    
    def encrypt_xml(self, xml: str) -> Tuple[str, str]:
        """Encrypt XML with base64 encoding and generate hash"""
        xml_bytes = xml.encode('utf-8')
        xml_hash = hashlib.sha256(xml_bytes).hexdigest()
        enc_xml = base64.b64encode(xml_bytes).decode('ascii')
        return enc_xml, xml_hash
    
    def generate_zatca_qr_data(self, invoice_data: Dict) -> str:
        """Generate ZATCA-compliant QR code data with TLV encoding"""
        
        # TLV fields for ZATCA QR code
        # 1: Seller name
        # 2: VAT registration number  
        # 3: Timestamp
        # 4: Invoice total (with VAT)
        # 5: VAT amount
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        tlv_data = b''
        tlv_data += self.encode_tlv(1, invoice_data['store']['name'])
        tlv_data += self.encode_tlv(2, invoice_data['store']['vat_number'])
        tlv_data += self.encode_tlv(3, timestamp)
        tlv_data += self.encode_tlv(4, str(invoice_data['price']['net_total']))
        tlv_data += self.encode_tlv(5, str(invoice_data['price']['taxes']))
        
        return base64.b64encode(tlv_data).decode('utf-8')
    
    def encode_tlv(self, tag: int, value: str) -> bytes:
        """Encode a single TLV field"""
        value_bytes = value.encode('utf-8')
        return bytes([tag]) + bytes([len(value_bytes)]) + value_bytes
    
    async def create_invoice_in_db(self, session: AsyncSession, invoice_data: Dict, xml: str, enc_xml: str, xml_hash: str) -> Invoice:
        """Create invoice record in PostgreSQL database"""
        
        # Create main invoice record
        invoice = Invoice(
            store_name=invoice_data['store']['name'],
            store_address=invoice_data['store']['address'],
            vat_number=invoice_data['store']['vat_number'],
            account_id=invoice_data['customer'].get('account_id', 'N/A'),
            user_name=invoice_data['customer']['name'],
            invoice_number=invoice_data['invoice']['number'],
            date=datetime.now(timezone.utc),
            total=Decimal(str(invoice_data['price']['subtotal'])),
            taxes=Decimal(str(invoice_data['price']['taxes'])),
            seller_taxes=Decimal(str(invoice_data['price']['taxes'])),
            net_total=Decimal(str(invoice_data['price']['net_total'])),
            status=InvoiceStatus.PENDING,
            zatca_xml=enc_xml,
            zatca_xml_hash=xml_hash
        )
        
        session.add(invoice)
        await session.flush()  # Get the ID
        
        # Create invoice items
        for item_data in invoice_data.get('items', []):
            item = InvoiceItem(
                invoice_id=invoice.id,
                item_name=item_data['name'],
                quantity=int(item_data['quantity']),
                price=Decimal(str(item_data['price'])),
                tax=Decimal(str(item_data.get('tax', 0)))
            )
            session.add(item)
        
        await session.commit()
        return invoice
    
    async def generate_sample_invoices(self, count: int = 10) -> List[str]:
        """Generate sample invoices for testing"""
        
        sample_items = [
            {"name": "تمور مجدول", "quantity": 10, "price": 50.00},
            {"name": "تمور صقعي", "quantity": 5, "price": 75.00},
            {"name": "تمور خلاص", "quantity": 8, "price": 60.00},
            {"name": "تمور زهدي", "quantity": 12, "price": 40.00},
            {"name": "تمور برحي", "quantity": 6, "price": 80.00},
        ]
        
        generated_invoices = []
        
        async for session in get_session():
            for i in range(count):
                # Select random items
                import random
                selected_items = random.sample(sample_items, random.randint(1, 3))
                
                # Calculate totals
                subtotal = sum(item['price'] * item['quantity'] for item in selected_items)
                tax_amount, seller_tax, net_total = self.calculate_tax(Decimal(str(subtotal)))
                
                # Update items with tax info
                for item in selected_items:
                    item_subtotal = item['price'] * item['quantity']
                    item_tax, _, item_total = self.calculate_tax(Decimal(str(item_subtotal)))
                    item['tax'] = float(item_tax)
                    item['total'] = float(item_total)
                
                # Create invoice data
                invoice_data = {
                    "store": {
                        "name": "شــركــة الـسـلـوم والــغيث لتسويق الـتـمـور",
                        "address": "المملكة العربية السعودية - الــقــصــيــم - بريدة",
                        "vat_number": "302008893200003"
                    },
                    "invoice": {
                        "number": f"INV-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}",
                        "tax_number": f"302008893200003"
                    },
                    "customer": {
                        "name": f"عميل رقم {i+1}",
                        "address": "الرياض، المملكة العربية السعودية",
                        "account_id": f"ACC{2010000 + i}"
                    },
                    "items": selected_items,
                    "price": {
                        "subtotal": float(subtotal),
                        "taxes": float(tax_amount),
                        "net_total": float(net_total)
                    }
                }
                
                # Generate XML and encryption
                xml = self.generate_zatca_xml(invoice_data)
                enc_xml, xml_hash = self.encrypt_xml(xml)
                
                # Generate QR code
                qr_data = self.generate_zatca_qr_data(invoice_data)
                qr_base64 = self.invoice_creator.generate_qr_base64(qr_data)
                invoice_data['qr_base64'] = qr_base64
                
                # Save to database
                invoice = await self.create_invoice_in_db(session, invoice_data, xml, enc_xml, xml_hash)
                
                # Generate PDF
                html = self.invoice_creator.render_invoice_html(invoice_data)
                pdf_path = f"invoice_{invoice.invoice_number}.pdf"
                
                try:
                    self.invoice_creator.html_to_pdf_auto(html, pdf_path)
                    generated_invoices.append(f"Generated: {invoice.invoice_number} -> {pdf_path}")
                except Exception as e:
                    generated_invoices.append(f"Generated: {invoice.invoice_number} (PDF failed: {e})")
                
                print(f"✅ Generated invoice {invoice.invoice_number} with ID {invoice.id}")
        
        return generated_invoices


async def main():
    """Main function to generate sample invoices"""
    generator = ZATCAInvoiceGenerator()
    
    print("🚀 Starting ZATCA invoice generation...")
    results = await generator.generate_sample_invoices(count=5)
    
    print("\n📊 Generation Results:")
    for result in results:
        print(f"  {result}")
    
    print(f"\n✅ Successfully generated {len(results)} invoices!")


if __name__ == "__main__":
    asyncio.run(main())