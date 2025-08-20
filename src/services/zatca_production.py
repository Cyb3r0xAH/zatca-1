"""
ZATCA Production API Integration Service
Handles real ZATCA API communication with client certificates and OAuth2 authentication
"""

import base64
import ssl
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import tempfile
import os

import httpx
import structlog
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from src.core.config import Config

logger = structlog.get_logger(__name__)


class ZATCAProductionService:
    """Production ZATCA API integration with client certificate authentication"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.client_cert_path: Optional[str] = None
        self.private_key_path: Optional[str] = None
        self._setup_certificates()
    
    def _setup_certificates(self):
        """Setup client certificates from environment variables"""
        try:
            if not Config.ZATCA_CERT_B64 or not Config.ZATCA_PRIVATE_KEY_B64:
                logger.warning("ZATCA certificates not configured - using simulation mode")
                return
            
            # Decode certificates from base64
            cert_pem = base64.b64decode(Config.ZATCA_CERT_B64)
            key_pem = base64.b64decode(Config.ZATCA_PRIVATE_KEY_B64)
            
            # Create temporary files for certificates
            cert_temp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
            key_temp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
            
            cert_temp.write(cert_pem)
            key_temp.write(key_pem)
            
            cert_temp.close()
            key_temp.close()
            
            self.client_cert_path = cert_temp.name
            self.private_key_path = key_temp.name
            
            logger.info("ZATCA certificates loaded successfully")
            
        except Exception as e:
            logger.error("Failed to setup ZATCA certificates", error=str(e))
            raise
    
    def _cleanup_certificates(self):
        """Clean up temporary certificate files"""
        try:
            if self.client_cert_path and os.path.exists(self.client_cert_path):
                os.unlink(self.client_cert_path)
            if self.private_key_path and os.path.exists(self.private_key_path):
                os.unlink(self.private_key_path)
        except Exception as e:
            logger.warning("Failed to cleanup certificate files", error=str(e))
    
    def __del__(self):
        """Cleanup certificates on object destruction"""
        self._cleanup_certificates()
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Create HTTP client with SSL configuration"""
        if not self.client_cert_path or not self.private_key_path:
            # No certificates - use regular client for simulation
            return httpx.AsyncClient(timeout=30.0)
        
        # Create SSL context with client certificate
        ssl_context = ssl.create_default_context()
        ssl_context.load_cert_chain(self.client_cert_path, self.private_key_path)
        
        return httpx.AsyncClient(
            verify=ssl_context,
            timeout=30.0
        )
    
    async def authenticate(self) -> str:
        """Authenticate with ZATCA OAuth2 and get access token"""
        
        # Check if we have a valid token
        if (self.access_token and self.token_expires_at and 
            datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)):
            return self.access_token
        
        if not Config.ZATCA_ENDPOINT:
            raise ValueError("ZATCA_ENDPOINT not configured")
        
        if not Config.ZATCA_CLIENT_ID or not Config.ZATCA_CLIENT_SECRET:
            raise ValueError("ZATCA client credentials not configured")
        
        auth_url = f"{Config.ZATCA_ENDPOINT}/oauth2/token"
        
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": Config.ZATCA_CLIENT_ID,
            "client_secret": Config.ZATCA_CLIENT_SECRET,
            "scope": "InvoiceSubmission"
        }
        
        logger.info("Authenticating with ZATCA", endpoint=auth_url)
        
        async with await self._get_http_client() as client:
            try:
                response = await client.post(
                    auth_url,
                    data=auth_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data["access_token"]
                    
                    # Calculate token expiry (default to 1 hour if not provided)
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    logger.info(
                        "ZATCA authentication successful",
                        expires_in=expires_in,
                        expires_at=self.token_expires_at.isoformat()
                    )
                    
                    return self.access_token
                else:
                    error_msg = f"Authentication failed: HTTP {response.status_code} - {response.text}"
                    logger.error("ZATCA authentication failed", 
                               status_code=response.status_code,
                               response=response.text)
                    raise Exception(error_msg)
                    
            except httpx.TimeoutException:
                error_msg = "ZATCA authentication timeout"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                logger.error("ZATCA authentication error", error=str(e))
                raise
    
    async def submit_invoice(self, invoice_xml: str, invoice_hash: str, invoice_uuid: str) -> Dict:
        """
        Submit invoice to ZATCA API
        
        Args:
            invoice_xml: UBL 2.1 XML invoice content
            invoice_hash: SHA256 hash of the XML
            invoice_uuid: Unique invoice identifier
            
        Returns:
            Dict with submission result
        """
        
        if not Config.ZATCA_ENDPOINT:
            # Simulation mode
            logger.info("ZATCA simulation mode - invoice not actually submitted",
                       invoice_uuid=invoice_uuid)
            return {
                "success": True,
                "zatca_uuid": f"sim_{invoice_uuid}",
                "status": "ACCEPTED",
                "message": "Invoice submitted successfully (simulation)",
                "simulation": True
            }
        
        try:
            # Get access token
            access_token = await self.authenticate()
            
            # Prepare submission URL
            submission_url = f"{Config.ZATCA_ENDPOINT}/invoices"
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Invoice-UUID": invoice_uuid
            }
            
            # Prepare payload
            payload = {
                "invoiceXml": base64.b64encode(invoice_xml.encode('utf-8')).decode('utf-8'),
                "invoiceHash": invoice_hash,
                "invoiceUuid": invoice_uuid,
                "submissionType": "production"
            }
            
            logger.info(
                "Submitting invoice to ZATCA",
                invoice_uuid=invoice_uuid,
                endpoint=submission_url,
                xml_length=len(invoice_xml)
            )
            
            async with await self._get_http_client() as client:
                response = await client.post(
                    submission_url,
                    json=payload,
                    headers=headers
                )
                
                response_data = {}
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text}
                
                if response.status_code in [200, 201, 202]:
                    logger.info(
                        "Invoice submitted successfully to ZATCA",
                        invoice_uuid=invoice_uuid,
                        status_code=response.status_code,
                        zatca_response=response_data
                    )
                    
                    return {
                        "success": True,
                        "zatca_uuid": response_data.get("invoiceUuid", invoice_uuid),
                        "status": response_data.get("status", "ACCEPTED"),
                        "message": response_data.get("message", "Invoice submitted successfully"),
                        "response_data": response_data,
                        "simulation": False
                    }
                else:
                    error_msg = f"ZATCA submission failed: HTTP {response.status_code}"
                    logger.error(
                        "Invoice submission failed",
                        invoice_uuid=invoice_uuid,
                        status_code=response.status_code,
                        response=response_data
                    )
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code,
                        "response_data": response_data,
                        "zatca_errors": response_data.get("errors", []),
                        "simulation": False
                    }
                    
        except Exception as e:
            logger.error(
                "Invoice submission exception",
                invoice_uuid=invoice_uuid,
                error=str(e),
                exc_info=True
            )
            
            return {
                "success": False,
                "error": str(e),
                "simulation": False
            }
    
    async def get_invoice_status(self, zatca_uuid: str) -> Dict:
        """
        Get invoice status from ZATCA
        
        Args:
            zatca_uuid: ZATCA invoice UUID
            
        Returns:
            Dict with invoice status
        """
        
        if not Config.ZATCA_ENDPOINT:
            return {
                "success": True,
                "status": "ACCEPTED",
                "message": "Simulation mode",
                "simulation": True
            }
        
        try:
            access_token = await self.authenticate()
            
            status_url = f"{Config.ZATCA_ENDPOINT}/invoices/{zatca_uuid}/status"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            async with await self._get_http_client() as client:
                response = await client.get(status_url, headers=headers)
                
                if response.status_code == 200:
                    status_data = response.json()
                    return {
                        "success": True,
                        "status": status_data.get("status"),
                        "message": status_data.get("message"),
                        "data": status_data,
                        "simulation": False
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Status check failed: HTTP {response.status_code}",
                        "simulation": False
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "simulation": False
            }
    
    async def health_check(self) -> Dict:
        """
        Check ZATCA API health and connectivity
        
        Returns:
            Dict with health status
        """
        
        if not Config.ZATCA_ENDPOINT:
            return {
                "status": "simulation",
                "message": "ZATCA endpoint not configured - running in simulation mode",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Try to authenticate
            await self.authenticate()
            
            return {
                "status": "healthy",
                "message": "ZATCA API is accessible and authentication successful",
                "endpoint": Config.ZATCA_ENDPOINT,
                "authenticated": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"ZATCA API health check failed: {str(e)}",
                "endpoint": Config.ZATCA_ENDPOINT,
                "authenticated": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance for reuse
_zatca_service_instance: Optional[ZATCAProductionService] = None


def get_zatca_service() -> ZATCAProductionService:
    """Get singleton ZATCA service instance"""
    global _zatca_service_instance
    
    if _zatca_service_instance is None:
        _zatca_service_instance = ZATCAProductionService()
    
    return _zatca_service_instance