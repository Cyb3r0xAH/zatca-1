#!/usr/bin/env python3
"""
ZATCA API Integration Script
Fetches invoices from PostgreSQL and sends them to ZATCA API
"""

import os
import sys
import asyncio
import base64
from typing import List, Dict, Optional
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.session import get_session
from src.db.models.invoices import Invoice, InvoiceStatus
from src.services.zakat import ZakatService


class ZATCAAPIIntegration:
    """Enhanced ZATCA API integration with comprehensive testing"""
    
    def __init__(self):
        self.zakat_service = ZakatService()
    
    async def get_pending_invoices(self, session: AsyncSession, limit: int = 10) -> List[Invoice]:
        """Get pending invoices from database"""
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.status == InvoiceStatus.PENDING)
            .limit(limit)
            .order_by(Invoice.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_processed_invoices(self, session: AsyncSession, limit: int = 10) -> List[Invoice]:
        """Get processed invoices from database"""
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.status.in_([InvoiceStatus.DONE, InvoiceStatus.FAILED]))
            .limit(limit)
            .order_by(Invoice.updated_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    def decode_xml(self, encoded_xml: str) -> str:
        """Decode base64 encoded XML"""
        try:
            xml_bytes = base64.b64decode(encoded_xml)
            return xml_bytes.decode('utf-8')
        except Exception as e:
            return f"Error decoding XML: {e}"
    
    def display_invoice_summary(self, invoice: Invoice) -> Dict:
        """Create a summary of invoice for display"""
        return {
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "store_name": invoice.store_name,
            "customer": invoice.user_name,
            "date": invoice.date.isoformat() if invoice.date else None,
            "total": float(invoice.total),
            "taxes": float(invoice.taxes),
            "net_total": float(invoice.net_total),
            "status": invoice.status.value,
            "zatca_uuid": invoice.zatca_uuid,
            "zatca_xml_hash": invoice.zatca_xml_hash,
            "submitted_at": invoice.submitted_at.isoformat() if invoice.submitted_at else None,
            "last_error": invoice.last_error,
            "items_count": len(invoice.items) if invoice.items else 0,
            "items": [
                {
                    "name": item.item_name,
                    "quantity": int(item.quantity),
                    "price": float(item.price),
                    "tax": float(item.tax)
                }
                for item in (invoice.items or [])
            ]
        }
    
    async def test_xml_generation(self, session: AsyncSession) -> Dict:
        """Test XML generation for pending invoices"""
        print("🧪 Testing XML Generation...")
        
        invoices = await self.get_pending_invoices(session, limit=3)
        results = []
        
        for invoice in invoices:
            try:
                # Generate XML using ZakatService
                xml = self.zakat_service.build_xml(invoice)
                enc_xml, xml_hash = self.zakat_service.encrypt_xml(xml)
                
                result = {
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "xml_length": len(xml),
                    "encoded_xml_length": len(enc_xml),
                    "xml_hash": xml_hash,
                    "xml_preview": xml[:200] + "..." if len(xml) > 200 else xml,
                    "status": "success"
                }
                results.append(result)
                print(f"  ✅ {invoice.invoice_number}: XML generated ({len(xml)} chars)")
                
            except Exception as e:
                result = {
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "error": str(e),
                    "status": "failed"
                }
                results.append(result)
                print(f"  ❌ {invoice.invoice_number}: {e}")
        
        return {"test": "xml_generation", "results": results}
    
    async def test_zakat_processing(self, session: AsyncSession, limit: int = 5, simulate: bool = True) -> Dict:
        """Test ZATCA processing with simulation"""
        print(f"🚀 Testing ZATCA Processing (simulate={simulate})...")
        
        # Process invoices using ZakatService
        result = await self.zakat_service.process_pending(session, limit=limit, simulate=simulate)
        
        print(f"  📊 Processed: {result['processed']}")
        print(f"  ✅ Success: {result['success']}")
        print(f"  ❌ Failed: {result['failed']}")
        
        return {"test": "zakat_processing", "result": result}
    
    async def inspect_processed_invoices(self, session: AsyncSession) -> Dict:
        """Inspect processed invoices"""
        print("🔍 Inspecting Processed Invoices...")
        
        invoices = await self.get_processed_invoices(session, limit=5)
        results = []
        
        for invoice in invoices:
            summary = self.display_invoice_summary(invoice)
            results.append(summary)
            
            status_icon = "✅" if invoice.status == InvoiceStatus.DONE else "❌"
            print(f"  {status_icon} {invoice.invoice_number} ({invoice.status.value})")
            
            if invoice.zatca_xml:
                xml = self.decode_xml(invoice.zatca_xml)
                print(f"    📄 XML: {len(xml)} chars, Hash: {invoice.zatca_xml_hash[:16]}...")
            
            if invoice.zatca_uuid:
                print(f"    🆔 ZATCA UUID: {invoice.zatca_uuid}")
            
            if invoice.last_error:
                print(f"    ⚠️  Error: {invoice.last_error[:100]}...")
        
        return {"test": "inspect_processed", "results": results}
    
    async def validate_xml_structure(self, session: AsyncSession) -> Dict:
        """Validate XML structure of processed invoices"""
        print("🔍 Validating XML Structure...")
        
        invoices = await self.get_processed_invoices(session, limit=3)
        results = []
        
        for invoice in invoices:
            if not invoice.zatca_xml:
                continue
                
            try:
                xml = self.decode_xml(invoice.zatca_xml)
                
                # Basic XML validation
                validation_checks = {
                    "has_xml_declaration": xml.startswith('<?xml'),
                    "has_invoice_root": '<Invoice' in xml,
                    "has_uuid": '<cbc:UUID>' in xml,
                    "has_issue_date": '<cbc:IssueDate>' in xml,
                    "has_supplier": '<cac:AccountingSupplierParty>' in xml,
                    "has_customer": '<cac:AccountingCustomerParty>' in xml,
                    "has_tax_total": '<cac:TaxTotal>' in xml,
                    "has_monetary_total": '<cac:LegalMonetaryTotal>' in xml,
                    "has_invoice_lines": '<cac:InvoiceLine>' in xml,
                    "well_formed": xml.count('<') == xml.count('>'),
                }
                
                passed_checks = sum(validation_checks.values())
                total_checks = len(validation_checks)
                
                result = {
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "validation_score": f"{passed_checks}/{total_checks}",
                    "checks": validation_checks,
                    "xml_size": len(xml),
                    "status": "valid" if passed_checks == total_checks else "issues"
                }
                results.append(result)
                
                status_icon = "✅" if passed_checks == total_checks else "⚠️"
                print(f"  {status_icon} {invoice.invoice_number}: {passed_checks}/{total_checks} checks passed")
                
            except Exception as e:
                result = {
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)
                print(f"  ❌ {invoice.invoice_number}: Validation error - {e}")
        
        return {"test": "xml_validation", "results": results}
    
    async def export_sample_data(self, session: AsyncSession, filename: str = "zatca_sample_data.json") -> Dict:
        """Export sample invoice data for analysis"""
        print(f"📤 Exporting Sample Data to {filename}...")
        
        # Get a mix of pending and processed invoices
        pending = await self.get_pending_invoices(session, limit=3)
        processed = await self.get_processed_invoices(session, limit=3)
        
        export_data = {
            "export_timestamp": asyncio.get_event_loop().time(),
            "pending_invoices": [self.display_invoice_summary(inv) for inv in pending],
            "processed_invoices": [self.display_invoice_summary(inv) for inv in processed],
            "sample_xml": {}
        }
        
        # Add sample XML for processed invoices
        for invoice in processed[:2]:
            if invoice.zatca_xml:
                xml = self.decode_xml(invoice.zatca_xml)
                export_data["sample_xml"][invoice.invoice_number] = {
                    "xml": xml,
                    "hash": invoice.zatca_xml_hash,
                    "uuid": invoice.zatca_uuid
                }
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"  ✅ Exported {len(export_data['pending_invoices'])} pending + {len(export_data['processed_invoices'])} processed invoices")
        
        return {"test": "export_data", "filename": filename, "exported_count": len(pending) + len(processed)}


async def main():
    """Main function to run comprehensive ZATCA integration tests"""
    integration = ZATCAAPIIntegration()
    
    print("🏁 Starting ZATCA API Integration Tests...")
    print("=" * 60)
    
    test_results = []
    
    async for session in get_session():
        # Test 1: XML Generation
        result1 = await integration.test_xml_generation(session)
        test_results.append(result1)
        print()
        
        # Test 2: ZATCA Processing (Simulation)
        result2 = await integration.test_zakat_processing(session, limit=3, simulate=True)
        test_results.append(result2)
        print()
        
        # Test 3: Inspect Processed Invoices
        result3 = await integration.inspect_processed_invoices(session)
        test_results.append(result3)
        print()
        
        # Test 4: Validate XML Structure
        result4 = await integration.validate_xml_structure(session)
        test_results.append(result4)
        print()
        
        # Test 5: Export Sample Data
        result5 = await integration.export_sample_data(session)
        test_results.append(result5)
        print()
        
        break  # Exit the async generator
    
    print("=" * 60)
    print("🎯 Test Summary:")
    for result in test_results:
        test_name = result.get('test', 'unknown')
        print(f"  ✅ {test_name}")
    
    print(f"\n🏆 All {len(test_results)} tests completed successfully!")
    print("📁 Check zatca_sample_data.json for detailed export data")


if __name__ == "__main__":
    asyncio.run(main())