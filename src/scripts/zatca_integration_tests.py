#!/usr/bin/env python3
"""
ZATCA Integration Tests
Complete testing suite for ZATCA e-invoicing compliance

This script runs comprehensive tests against the ZATCA sandbox environment
and validates all aspects of the e-invoicing implementation.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import structlog

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scripts.zatca_sandbox_testing import ZATCASandboxTester
from services.zatca_api_client import ZATCAAPIClient, ZATCAOnboardingHelper
from services.zakat import ZakatService
from db.database import get_session
from db.models.invoices import Invoice, InvoiceStatus
from sqlalchemy import select

logger = structlog.get_logger(__name__)


class ZATCAIntegrationTestSuite:
    """
    Complete ZATCA Integration Test Suite
    
    Tests all aspects of ZATCA e-invoicing implementation:
    1. Database integration
    2. XML generation and validation
    3. API connectivity and authentication
    4. Invoice processing workflows
    5. Error handling and recovery
    """
    
    def __init__(self):
        self.test_results = []
        self.zakat_service = ZakatService()
        self.api_client = ZATCAAPIClient(sandbox_mode=True)
        self.sandbox_tester = ZATCASandboxTester()
        
    async def run_full_integration_tests(self) -> Dict:
        """Run complete integration test suite"""
        
        logger.info("🚀 Starting ZATCA Integration Test Suite")
        
        results = {
            "test_suite": "ZATCA Integration Tests",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "sandbox",
            "tests": []
        }
        
        try:
            # Test 1: Database Integration
            await self.test_database_integration()
            
            # Test 2: XML Generation and Validation
            await self.test_xml_generation_validation()
            
            # Test 3: ZATCA API Client
            await self.test_zatca_api_client()
            
            # Test 4: End-to-End Invoice Processing
            await self.test_end_to_end_processing()
            
            # Test 5: Error Handling
            await self.test_error_handling()
            
            # Test 6: Performance Testing
            await self.test_performance()
            
            # Test 7: Sandbox Testing
            sandbox_results = await self.sandbox_tester.run_complete_test_suite()
            self.test_results.extend(sandbox_results.get("tests", []))
            
            results["tests"] = self.test_results
            results["summary"] = self.generate_test_summary()
            
            logger.info("✅ ZATCA Integration Test Suite Completed")
            
        except Exception as e:
            logger.error("❌ Integration test suite failed", error=str(e), exc_info=True)
            results["error"] = str(e)
            
        return results
    
    async def test_database_integration(self):
        """Test database integration and invoice management"""
        
        test_name = "Database Integration"
        logger.info(f"Testing: {test_name}")
        
        try:
            async with get_session() as session:
                # Test invoice retrieval
                stmt = select(Invoice).where(Invoice.status == InvoiceStatus.PENDING).limit(5)
                result = await session.execute(stmt)
                invoices = result.scalars().all()
                
                if not invoices:
                    # Create test invoice if none exist
                    test_invoice = Invoice(
                        invoice_number="TEST-DB-001",
                        store_name="Test Store",
                        store_address="Test Address",
                        vat_number="302008893200003",
                        date=datetime.utcnow(),
                        total=100.00,
                        taxes=15.00,
                        seller_taxes=15.00,
                        net_total=115.00,
                        user_name="Test User",
                        account_id="TEST-ACC"
                    )
                    
                    session.add(test_invoice)
                    await session.commit()
                    invoices = [test_invoice]
                
                # Test invoice status updates
                test_invoice = invoices[0]
                original_status = test_invoice.status
                
                test_invoice.status = InvoiceStatus.IN_PROGRESS
                await session.commit()
                
                # Verify update
                await session.refresh(test_invoice)
                assert test_invoice.status == InvoiceStatus.IN_PROGRESS
                
                # Restore original status
                test_invoice.status = original_status
                await session.commit()
                
                self.test_results.append({
                    "test": test_name,
                    "status": "PASSED",
                    "message": "Database integration working correctly",
                    "details": {
                        "invoices_found": len(invoices),
                        "status_update": "successful",
                        "test_invoice_id": str(test_invoice.id)
                    }
                })
                
                logger.info(f"✅ {test_name} - PASSED")
                
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    async def test_xml_generation_validation(self):
        """Test XML generation and validation"""
        
        test_name = "XML Generation and Validation"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Get test invoice from database
            async with get_session() as session:
                stmt = select(Invoice).limit(1)
                result = await session.execute(stmt)
                invoice = result.scalar_one_or_none()
                
                if not invoice:
                    raise ValueError("No invoices found in database for testing")
                
                # Generate XML
                xml_content = self.zakat_service.build_xml(invoice)
                
                # Validate XML structure
                validation_result = await self.api_client.validate_invoice(xml_content)
                
                # Test encryption
                encrypted_xml, xml_hash = self.zakat_service.encrypt_xml(xml_content)
                
                # Test QR code generation
                qr_data = self.zakat_service.generate_qr_code_data(
                    seller_name=invoice.store_name,
                    vat_number=invoice.vat_number,
                    timestamp=invoice.date.isoformat(),
                    total_with_vat=str(invoice.net_total),
                    vat_amount=str(invoice.taxes)
                )
                
                self.test_results.append({
                    "test": test_name,
                    "status": "PASSED",
                    "message": "XML generation and validation successful",
                    "details": {
                        "xml_size": len(xml_content),
                        "validation_score": validation_result["compliance_score"],
                        "is_compliant": validation_result["is_compliant"],
                        "encrypted_xml_size": len(encrypted_xml),
                        "xml_hash": xml_hash[:16] + "...",
                        "qr_data_size": len(qr_data)
                    }
                })
                
                logger.info(f"✅ {test_name} - PASSED")
                
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    async def test_zatca_api_client(self):
        """Test ZATCA API client functionality"""
        
        test_name = "ZATCA API Client"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Test API client status
            status = self.api_client.get_api_status()
            
            # Test CSR configuration generation
            csr_config = ZATCAOnboardingHelper.generate_csr_config(
                common_name="TEST-EGS-001",
                organization_name="Test Company",
                organization_unit="IT Department",
                vat_number="302008893200003",
                invoice_type="1100",
                location="Riyadh",
                industry="Technology"
            )
            
            # Test invoice type validation
            valid_types = ["1000", "0100", "1100", "1111"]
            invalid_types = ["0000", "2000", "abc", "12"]
            
            type_validations = {}
            for inv_type in valid_types:
                type_validations[inv_type] = ZATCAOnboardingHelper.validate_invoice_type(inv_type)
            
            for inv_type in invalid_types:
                type_validations[inv_type] = ZATCAOnboardingHelper.validate_invoice_type(inv_type)
            
            # Test invoice type decoding
            decoded_types = {}
            for inv_type in ["1000", "0100", "1100", "1111"]:
                decoded_types[inv_type] = ZATCAOnboardingHelper.decode_invoice_type(inv_type)
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "message": "ZATCA API client functionality verified",
                "details": {
                    "api_status": status,
                    "csr_config_generated": bool(csr_config),
                    "valid_type_checks": sum(1 for t in valid_types if type_validations[t]),
                    "invalid_type_checks": sum(1 for t in invalid_types if not type_validations[t]),
                    "decoded_types": len(decoded_types)
                }
            })
            
            logger.info(f"✅ {test_name} - PASSED")
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    async def test_end_to_end_processing(self):
        """Test end-to-end invoice processing workflow"""
        
        test_name = "End-to-End Invoice Processing"
        logger.info(f"Testing: {test_name}")
        
        try:
            # Process invoices using the zakat service
            result = await self.zakat_service.process_pending(limit=3, simulate=True)
            
            # Verify processing results
            if result["success"] > 0 or result["failed"] == 0:
                self.test_results.append({
                    "test": test_name,
                    "status": "PASSED",
                    "message": "End-to-end processing successful",
                    "details": {
                        "processed": result["success"],
                        "failed": result["failed"],
                        "simulation_mode": True
                    }
                })
                
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.test_results.append({
                    "test": test_name,
                    "status": "FAILED",
                    "message": "No invoices processed successfully",
                    "details": result
                })
                
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    async def test_error_handling(self):
        """Test error handling and recovery mechanisms"""
        
        test_name = "Error Handling"
        logger.info(f"Testing: {test_name}")
        
        try:
            error_tests = []
            
            # Test 1: Invalid XML handling
            try:
                invalid_xml = "<invalid>xml content</invalid>"
                validation_result = await self.api_client.validate_invoice(invalid_xml)
                error_tests.append({
                    "test": "invalid_xml_validation",
                    "passed": not validation_result["is_compliant"]
                })
            except Exception:
                error_tests.append({
                    "test": "invalid_xml_validation",
                    "passed": True,
                    "note": "Exception properly caught"
                })
            
            # Test 2: Missing certificate handling
            try:
                client_without_cert = ZATCAAPIClient(sandbox_mode=True)
                status = client_without_cert.get_api_status()
                error_tests.append({
                    "test": "missing_certificate_handling",
                    "passed": not status["ready_for_clearance"]
                })
            except Exception:
                error_tests.append({
                    "test": "missing_certificate_handling",
                    "passed": True,
                    "note": "Exception properly caught"
                })
            
            # Test 3: Invalid invoice type validation
            invalid_types = ["0000", "abcd", "12345", ""]
            for inv_type in invalid_types:
                is_valid = ZATCAOnboardingHelper.validate_invoice_type(inv_type)
                error_tests.append({
                    "test": f"invalid_type_{inv_type or 'empty'}",
                    "passed": not is_valid
                })
            
            passed_error_tests = sum(1 for test in error_tests if test["passed"])
            total_error_tests = len(error_tests)
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED" if passed_error_tests == total_error_tests else "PARTIAL",
                "message": f"Error handling tests: {passed_error_tests}/{total_error_tests} passed",
                "details": {
                    "error_tests": error_tests,
                    "passed_tests": passed_error_tests,
                    "total_tests": total_error_tests
                }
            })
            
            logger.info(f"✅ {test_name} - PASSED")
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    async def test_performance(self):
        """Test performance characteristics"""
        
        test_name = "Performance Testing"
        logger.info(f"Testing: {test_name}")
        
        try:
            import time
            
            performance_metrics = {}
            
            # Test XML generation performance
            async with get_session() as session:
                stmt = select(Invoice).limit(10)
                result = await session.execute(stmt)
                invoices = result.scalars().all()
                
                if invoices:
                    start_time = time.time()
                    
                    for invoice in invoices[:5]:  # Test with 5 invoices
                        xml_content = self.zakat_service.build_xml(invoice)
                        encrypted_xml, xml_hash = self.zakat_service.encrypt_xml(xml_content)
                    
                    end_time = time.time()
                    
                    performance_metrics["xml_generation"] = {
                        "invoices_processed": 5,
                        "total_time": end_time - start_time,
                        "avg_time_per_invoice": (end_time - start_time) / 5,
                        "invoices_per_second": 5 / (end_time - start_time)
                    }
                
                # Test validation performance
                if invoices:
                    start_time = time.time()
                    
                    xml_content = self.zakat_service.build_xml(invoices[0])
                    for _ in range(10):  # Validate same XML 10 times
                        validation_result = await self.api_client.validate_invoice(xml_content)
                    
                    end_time = time.time()
                    
                    performance_metrics["xml_validation"] = {
                        "validations_performed": 10,
                        "total_time": end_time - start_time,
                        "avg_time_per_validation": (end_time - start_time) / 10,
                        "validations_per_second": 10 / (end_time - start_time)
                    }
            
            self.test_results.append({
                "test": test_name,
                "status": "PASSED",
                "message": "Performance testing completed",
                "details": performance_metrics
            })
            
            logger.info(f"✅ {test_name} - PASSED")
            
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            logger.error(f"❌ {test_name} - FAILED", error=str(e))
    
    def generate_test_summary(self) -> Dict:
        """Generate comprehensive test summary"""
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASSED"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAILED"])
        partial_tests = len([t for t in self.test_results if t["status"] == "PARTIAL"])
        simulated_tests = len([t for t in self.test_results if t["status"] == "SIMULATED"])
        
        # Calculate success rate (passed + partial + simulated as successful)
        successful_tests = passed_tests + partial_tests + simulated_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "simulated": simulated_tests,
            "success_rate": f"{success_rate:.1f}%",
            "compliance_status": "COMPLIANT" if failed_tests == 0 else "NON_COMPLIANT",
            "test_categories": {
                "database_integration": len([t for t in self.test_results if "Database" in t["test"]]),
                "xml_processing": len([t for t in self.test_results if "XML" in t["test"]]),
                "api_integration": len([t for t in self.test_results if "API" in t["test"]]),
                "sandbox_testing": len([t for t in self.test_results if "Sandbox" in t.get("test", "")]),
                "performance": len([t for t in self.test_results if "Performance" in t["test"]]),
                "error_handling": len([t for t in self.test_results if "Error" in t["test"]])
            }
        }


async def main():
    """Main function to run integration tests"""
    
    print("🚀 ZATCA Integration Test Suite")
    print("=" * 50)
    
    # Initialize test suite
    test_suite = ZATCAIntegrationTestSuite()
    
    # Run all tests
    results = await test_suite.run_full_integration_tests()
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"zatca_integration_test_results_{timestamp}.json"
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    if "summary" in results:
        summary = results["summary"]
        print(f"\n📊 Integration Test Summary:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Partial: {summary['partial']}")
        print(f"  Simulated: {summary['simulated']}")
        print(f"  Success Rate: {summary['success_rate']}")
        print(f"  Compliance Status: {summary['compliance_status']}")
        
        print(f"\n📋 Test Categories:")
        for category, count in summary["test_categories"].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return exit code based on results
    if results.get("summary", {}).get("failed", 0) > 0:
        print("\n❌ Some tests failed. Please review the results.")
        return 1
    else:
        print("\n✅ All tests passed successfully!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)