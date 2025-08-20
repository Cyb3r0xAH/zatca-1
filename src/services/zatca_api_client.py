"""
ZATCA API Client
Based on ZATCA Developer Portal Manual Version 3

This module implements the complete ZATCA API integration following
the official specifications for onboarding, reporting, and clearance.
"""

import base64
import hashlib
import json
import ssl
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

import httpx
import structlog
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec

logger = structlog.get_logger(__name__)


class ZATCAAPIClient:
    """
    ZATCA API Client implementing the complete integration workflow:
    
    1. Compliance CSID Generation
    2. Production CSID Generation  
    3. Invoice Reporting (Simplified invoices)
    4. Invoice Clearance (Standard invoices)
    5. Certificate Renewal
    """
    
    def __init__(self, 
                 sandbox_mode: bool = True,
                 private_key_path: Optional[str] = None,
                 certificate_path: Optional[str] = None):
        """
        Initialize ZATCA API Client
        
        Args:
            sandbox_mode: Use sandbox environment for testing
            private_key_path: Path to private key file
            certificate_path: Path to certificate file
        """
        
        self.sandbox_mode = sandbox_mode
        
        if sandbox_mode:
            self.base_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal"
        else:
            self.base_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/core"
        
        self.private_key_path = private_key_path
        self.certificate_path = certificate_path
        self.compliance_csid = None
        self.production_csid = None
        self.request_id = None
        
        # Load certificates if provided
        if private_key_path and certificate_path:
            self._load_certificates()
    
    def _load_certificates(self):
        """Load private key and certificate from files"""
        try:
            if self.private_key_path and os.path.exists(self.private_key_path):
                with open(self.private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(), password=None
                    )
                    
            if self.certificate_path and os.path.exists(self.certificate_path):
                with open(self.certificate_path, 'rb') as f:
                    self.certificate = x509.load_pem_x509_certificate(f.read())
                    
            logger.info("Certificates loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load certificates", error=str(e))
            raise
    
    async def _make_request(self, 
                           method: str, 
                           endpoint: str, 
                           data: Optional[Dict] = None,
                           headers: Optional[Dict] = None,
                           auth_cert: Optional[str] = None) -> httpx.Response:
        """
        Make HTTP request to ZATCA API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            headers: Additional headers
            auth_cert: Authentication certificate
            
        Returns:
            HTTP response
        """
        
        url = f"{self.base_url}{endpoint}"
        
        # Default headers
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en"
        }
        
        if headers:
            request_headers.update(headers)
            
        if auth_cert:
            request_headers["authentication-certificate"] = auth_cert
        
        # Create SSL context if certificates are available
        ssl_context = None
        if hasattr(self, 'private_key') and hasattr(self, 'certificate'):
            ssl_context = self._create_ssl_context()
        
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=ssl_context if ssl_context else True
        ) as client:
            
            if method.upper() == "GET":
                response = await client.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=request_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.info(
                "ZATCA API request",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code
            )
            
            return response
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with client certificate"""
        
        context = ssl.create_default_context()
        
        # Create temporary files for certificate and key
        cert_pem = self.certificate.public_bytes(serialization.Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_file:
            cert_file.write(cert_pem)
            cert_file_path = cert_file.name
            
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as key_file:
            key_file.write(key_pem)
            key_file_path = key_file.name
        
        try:
            context.load_cert_chain(cert_file_path, key_file_path)
        finally:
            # Clean up temporary files
            os.unlink(cert_file_path)
            os.unlink(key_file_path)
        
        return context
    
    async def generate_compliance_csid(self, csr: str, otp: Optional[str] = None) -> Dict:
        """
        Generate Compliance CSID (Step 1 of onboarding)
        
        Args:
            csr: Certificate Signing Request in base64 format
            otp: One-time password (if required)
            
        Returns:
            Response containing compliance CSID and request ID
        """
        
        logger.info("Generating Compliance CSID")
        
        payload = {
            "csr": csr
        }
        
        if otp:
            payload["otp"] = otp
        
        try:
            response = await self._make_request("POST", "/compliance", data=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                self.compliance_csid = result.get("binarySecurityToken")
                self.request_id = result.get("requestID")
                
                logger.info(
                    "Compliance CSID generated successfully",
                    request_id=self.request_id
                )
                
                return {
                    "success": True,
                    "compliance_csid": self.compliance_csid,
                    "request_id": self.request_id,
                    "response": result
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error("Compliance CSID generation failed", error=error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error("Compliance CSID generation exception", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_production_csid(self, otp: str) -> Dict:
        """
        Generate Production CSID (Step 2 of onboarding)
        
        Args:
            otp: One-time password from taxpayer
            
        Returns:
            Response containing production CSID
        """
        
        logger.info("Generating Production CSID")
        
        if not self.request_id:
            return {
                "success": False,
                "error": "Request ID required. Generate compliance CSID first."
            }
        
        payload = {
            "compliance_request_id": self.request_id,
            "otp": otp
        }
        
        try:
            response = await self._make_request(
                "POST", 
                "/production/csids", 
                data=payload,
                auth_cert=self.compliance_csid
            )
            
            if response.status_code == 200:
                result = response.json()
                
                self.production_csid = result.get("binarySecurityToken")
                
                logger.info("Production CSID generated successfully")
                
                return {
                    "success": True,
                    "production_csid": self.production_csid,
                    "response": result
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error("Production CSID generation failed", error=error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error("Production CSID generation exception", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def report_invoice(self, 
                           invoice_xml: str, 
                           invoice_hash: Optional[str] = None) -> Dict:
        """
        Report simplified invoice to ZATCA
        
        Args:
            invoice_xml: UBL 2.1 XML invoice content
            invoice_hash: SHA256 hash of the invoice (calculated if not provided)
            
        Returns:
            Response from reporting API
        """
        
        logger.info("Reporting simplified invoice")
        
        # Calculate hash if not provided
        if not invoice_hash:
            invoice_hash = hashlib.sha256(invoice_xml.encode('utf-8')).hexdigest()
        
        # Encode invoice in base64
        invoice_b64 = base64.b64encode(invoice_xml.encode('utf-8')).decode('utf-8')
        
        payload = {
            "invoiceHash": invoice_hash,
            "invoice": invoice_b64
        }
        
        # Use production CSID if available, otherwise compliance CSID
        auth_cert = self.production_csid or self.compliance_csid
        
        if not auth_cert:
            return {
                "success": False,
                "error": "Authentication certificate required. Complete onboarding first."
            }
        
        try:
            response = await self._make_request(
                "POST", 
                "/invoices/reporting/single", 
                data=payload,
                auth_cert=auth_cert
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                
                logger.info(
                    "Invoice reported successfully",
                    status=result.get("status"),
                    invoice_hash=result.get("invoiceHash")
                )
                
                return {
                    "success": True,
                    "status": result.get("status"),
                    "invoice_hash": result.get("invoiceHash"),
                    "warnings": result.get("warnings"),
                    "errors": result.get("errors"),
                    "response": result
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error("Invoice reporting failed", error=error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error("Invoice reporting exception", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_invoice(self, 
                          invoice_xml: str, 
                          invoice_hash: Optional[str] = None) -> Dict:
        """
        Clear standard invoice with ZATCA
        
        Args:
            invoice_xml: UBL 2.1 XML invoice content
            invoice_hash: SHA256 hash of the invoice (calculated if not provided)
            
        Returns:
            Response from clearance API including cleared invoice
        """
        
        logger.info("Clearing standard invoice")
        
        # Calculate hash if not provided
        if not invoice_hash:
            invoice_hash = hashlib.sha256(invoice_xml.encode('utf-8')).hexdigest()
        
        # Encode invoice in base64
        invoice_b64 = base64.b64encode(invoice_xml.encode('utf-8')).decode('utf-8')
        
        payload = {
            "invoiceHash": invoice_hash,
            "invoice": invoice_b64
        }
        
        # Use production CSID for clearance
        auth_cert = self.production_csid
        
        if not auth_cert:
            return {
                "success": False,
                "error": "Production CSID required for invoice clearance."
            }
        
        try:
            response = await self._make_request(
                "POST", 
                "/invoices/clearance/single", 
                data=payload,
                auth_cert=auth_cert
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                
                logger.info(
                    "Invoice cleared successfully",
                    status=result.get("status"),
                    invoice_hash=result.get("invoiceHash")
                )
                
                return {
                    "success": True,
                    "status": result.get("status"),
                    "invoice_hash": result.get("invoiceHash"),
                    "cleared_invoice": result.get("clearedInvoice"),
                    "qr_code": result.get("qrCode"),
                    "warnings": result.get("warnings"),
                    "errors": result.get("errors"),
                    "response": result
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error("Invoice clearance failed", error=error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error("Invoice clearance exception", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def renew_certificate(self, csr: str, otp: str) -> Dict:
        """
        Renew certificate (similar to initial onboarding)
        
        Args:
            csr: New Certificate Signing Request
            otp: One-time password
            
        Returns:
            Response containing new certificates
        """
        
        logger.info("Renewing certificate")
        
        # Step 1: Generate new compliance CSID
        compliance_result = await self.generate_compliance_csid(csr, otp)
        
        if not compliance_result["success"]:
            return compliance_result
        
        # Step 2: Generate new production CSID
        production_result = await self.generate_production_csid(otp)
        
        return {
            "success": production_result["success"],
            "compliance_csid": compliance_result.get("compliance_csid"),
            "production_csid": production_result.get("production_csid"),
            "compliance_response": compliance_result.get("response"),
            "production_response": production_result.get("response"),
            "error": production_result.get("error")
        }
    
    async def validate_invoice(self, invoice_xml: str) -> Dict:
        """
        Validate invoice XML against ZATCA requirements
        
        Args:
            invoice_xml: UBL 2.1 XML invoice content
            
        Returns:
            Validation results
        """
        
        logger.info("Validating invoice XML")
        
        # Basic XML structure validation
        validation_checks = {
            "has_xml_declaration": invoice_xml.strip().startswith('<?xml'),
            "has_invoice_root": '<Invoice' in invoice_xml,
            "has_customization_id": 'BR-KSA-CB' in invoice_xml,
            "has_profile_id": 'reporting:1.0' in invoice_xml,
            "has_ubl_namespace": 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2' in invoice_xml,
            "has_vat_calculation": '<cbc:Percent>' in invoice_xml,
            "has_currency_sar": 'currencyID="SAR"' in invoice_xml,
            "has_supplier_info": '<cac:AccountingSupplierParty>' in invoice_xml,
            "has_customer_info": '<cac:AccountingCustomerParty>' in invoice_xml,
            "has_tax_total": '<cac:TaxTotal>' in invoice_xml,
            "has_monetary_total": '<cac:LegalMonetaryTotal>' in invoice_xml,
            "has_invoice_lines": '<cac:InvoiceLine>' in invoice_xml,
            "well_formed": invoice_xml.count('<') == invoice_xml.count('>')
        }
        
        passed_checks = sum(1 for check in validation_checks.values() if check)
        total_checks = len(validation_checks)
        
        return {
            "validation_checks": validation_checks,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "compliance_score": f"{passed_checks}/{total_checks}",
            "is_compliant": passed_checks == total_checks,
            "xml_size": len(invoice_xml)
        }
    
    def get_api_status(self) -> Dict:
        """Get current API client status"""
        
        return {
            "sandbox_mode": self.sandbox_mode,
            "base_url": self.base_url,
            "has_compliance_csid": bool(self.compliance_csid),
            "has_production_csid": bool(self.production_csid),
            "has_request_id": bool(self.request_id),
            "has_private_key": hasattr(self, 'private_key'),
            "has_certificate": hasattr(self, 'certificate'),
            "ready_for_reporting": bool(self.compliance_csid or self.production_csid),
            "ready_for_clearance": bool(self.production_csid)
        }


class ZATCAOnboardingHelper:
    """Helper class for ZATCA onboarding process"""
    
    @staticmethod
    def generate_csr_config(
        common_name: str,
        organization_name: str,
        organization_unit: str,
        vat_number: str,
        invoice_type: str = "1100",  # Standard and Simplified
        location: str = "Riyadh",
        industry: str = "Retail"
    ) -> Dict:
        """
        Generate CSR configuration according to ZATCA requirements
        
        Args:
            common_name: EGS unit name or asset tracking number
            organization_name: Taxpayer name
            organization_unit: Branch name or TIN for VAT groups
            vat_number: 15-digit VAT registration number
            invoice_type: 4-digit binary functionality map (TSCZ)
            location: Branch location or address
            industry: Industry sector
            
        Returns:
            CSR configuration dictionary
        """
        
        return {
            "subject": {
                "country_name": "SA",
                "organization_name": organization_name,
                "organizational_unit_name": organization_unit,
                "common_name": common_name,
                "serial_number": f"1-{organization_name}|2-EGS|3-{common_name}"
            },
            "subject_alternative_name": {
                "organization_identifier": vat_number,
                "organizational_unit_name": location,
                "title": invoice_type,  # Functionality map
                "locality_name": location,
                "state_or_province_name": industry
            },
            "key_usage": {
                "digital_signature": True,
                "content_commitment": True,
                "key_encipherment": False,
                "data_encipherment": False,
                "key_agreement": False,
                "key_cert_sign": False,
                "crl_sign": False
            },
            "extended_key_usage": [
                "client_auth"
            ]
        }
    
    @staticmethod
    def validate_invoice_type(invoice_type: str) -> bool:
        """
        Validate invoice type functionality map
        
        Args:
            invoice_type: 4-digit binary string (TSCZ format)
            
        Returns:
            True if valid, False otherwise
        """
        
        if len(invoice_type) != 4:
            return False
        
        if not all(c in '01' for c in invoice_type):
            return False
        
        if invoice_type == "0000":
            return False
        
        return True
    
    @staticmethod
    def decode_invoice_type(invoice_type: str) -> Dict:
        """
        Decode invoice type functionality map
        
        Args:
            invoice_type: 4-digit binary string
            
        Returns:
            Dictionary with supported invoice types
        """
        
        if len(invoice_type) != 4:
            return {"error": "Invalid invoice type format"}
        
        return {
            "standard_invoices": invoice_type[0] == "1",  # T
            "simplified_invoices": invoice_type[1] == "1",  # S
            "buyer_qr_code": invoice_type[2] == "1",  # C
            "seller_qr_code": invoice_type[3] == "1",  # Z
            "description": {
                "1000": "Standard invoices only",
                "0100": "Simplified invoices only", 
                "1100": "Standard and Simplified invoices",
                "0010": "Buyer QR code only",
                "0001": "Seller QR code only",
                "1111": "All invoice types supported"
            }.get(invoice_type, "Custom configuration")
        }