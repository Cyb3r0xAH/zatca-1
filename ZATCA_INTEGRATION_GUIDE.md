# ZATCA API Integration Guide

This guide explains how to obtain ZATCA credentials and configure the system for production use with the real ZATCA API.

## 🏢 ZATCA Registration Process

### Step 1: Business Registration
1. **Visit ZATCA Portal**: https://zatca.gov.sa
2. **Register Your Business**: Complete the e-invoicing registration
3. **Compliance Assessment**: Pass the technical compliance test
4. **Documentation**: Submit required business documents

### Step 2: Technical Onboarding
1. **Developer Portal Access**: Get access to ZATCA developer portal
2. **API Documentation**: Review ZATCA API specifications
3. **Testing Environment**: Access sandbox environment for testing

## 🔐 Certificate Generation

### Generate CSR (Certificate Signing Request)

Run the CSR generation script:

```bash
cd /workspace/project/zatca-1
pip install cryptography  # If not already installed
python src/scripts/generate_zatca_csr.py
```

This will generate:
- `zatca_certs/zatca_private_key.pem` - Your private key
- `zatca_certs/zatca_csr.pem` - Certificate Signing Request to submit to ZATCA

### Company Information Required

Update the script with your actual company information:

```python
company_info = {
    "organization_name": "Your Company Name (Arabic)",
    "organization_unit": "IT Department", 
    "common_name": "Your VAT Number",
    "vat_number": "Your 15-digit VAT Number",
    "serial_number": "Your Commercial Registration Number",
}
```

### Submit CSR to ZATCA

1. **Login to ZATCA Portal**: Use your business credentials
2. **Navigate to Certificates**: Find the certificate management section
3. **Upload CSR**: Submit the generated `zatca_csr.pem` file
4. **Wait for Approval**: ZATCA will review and issue your certificate
5. **Download Certificate**: Save the issued certificate file

## 🔑 API Credentials Setup

### 1. Environment Variables

After receiving your certificate from ZATCA, update your `.env` file:

```env
# ZATCA API Configuration
ZATCA_ENDPOINT=https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal
ZATCA_CLIENT_ID=your_client_id_from_zatca
ZATCA_CLIENT_SECRET=your_client_secret_from_zatca

# Certificates (Base64 encoded)
ZATCA_CERT_B64=LS0tLS1CRUdJTi... # Your certificate from ZATCA (base64)
ZATCA_PRIVATE_KEY_B64=LS0tLS1CRUdJTi... # Your private key (base64)
```

### 2. Convert Certificate to Base64

```bash
# Convert certificate to base64
base64 -w 0 your_zatca_certificate.pem > zatca_cert_b64.txt

# Convert private key to base64 (if needed)
base64 -w 0 zatca_certs/zatca_private_key.pem > zatca_key_b64.txt
```

### 3. Client Credentials

ZATCA will provide:
- **Client ID**: Unique identifier for your application
- **Client Secret**: Secret key for authentication
- **API Endpoint**: Production API URL

## 🚀 Production Configuration

### Update ZATCA Service

The system needs to be updated to use real ZATCA API. Here's the enhanced service:

```python
# src/services/zatca_production.py
import httpx
import base64
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from src.core.config import Config

class ZATCAProductionService:
    """Production ZATCA API integration"""
    
    def __init__(self):
        self.client_cert = self._load_certificate()
        self.private_key = self._load_private_key()
        self.ssl_context = self._create_ssl_context()
    
    def _load_certificate(self):
        """Load certificate from base64 environment variable"""
        cert_b64 = Config.ZATCA_CERT_B64
        if not cert_b64:
            raise ValueError("ZATCA_CERT_B64 not configured")
        
        cert_pem = base64.b64decode(cert_b64)
        return x509.load_pem_x509_certificate(cert_pem)
    
    def _load_private_key(self):
        """Load private key from base64 environment variable"""
        key_b64 = Config.ZATCA_PRIVATE_KEY_B64
        if not key_b64:
            raise ValueError("ZATCA_PRIVATE_KEY_B64 not configured")
        
        key_pem = base64.b64decode(key_b64)
        return serialization.load_pem_private_key(key_pem, password=None)
    
    def _create_ssl_context(self):
        """Create SSL context with client certificate"""
        context = ssl.create_default_context()
        
        # Convert certificate and key to PEM format
        cert_pem = self.client_cert.public_bytes(serialization.Encoding.PEM)
        key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Load client certificate
        context.load_cert_chain(
            certfile=cert_pem,
            keyfile=key_pem
        )
        
        return context
    
    async def authenticate(self) -> str:
        """Authenticate with ZATCA and get access token"""
        auth_url = f"{Config.ZATCA_ENDPOINT}/oauth2/token"
        
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": Config.ZATCA_CLIENT_ID,
            "client_secret": Config.ZATCA_CLIENT_SECRET,
            "scope": "InvoiceSubmission"
        }
        
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            response = await client.post(auth_url, data=auth_data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data["access_token"]
            else:
                raise Exception(f"Authentication failed: {response.text}")
    
    async def submit_invoice(self, invoice_xml: str, invoice_hash: str) -> dict:
        """Submit invoice to ZATCA"""
        
        # Get access token
        access_token = await self.authenticate()
        
        # Prepare invoice submission
        submission_url = f"{Config.ZATCA_ENDPOINT}/invoices"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "invoiceXml": invoice_xml,
            "invoiceHash": invoice_hash,
            "submissionType": "production"  # or "compliance" for testing
        }
        
        async with httpx.AsyncClient(
            verify=self.ssl_context,
            timeout=30.0
        ) as client:
            response = await client.post(
                submission_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    "success": True,
                    "zatca_uuid": response.json().get("invoiceUuid"),
                    "status": response.json().get("status"),
                    "message": "Invoice submitted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
```

### Update Main Zakat Service

Modify `src/services/zakat.py` to use production service:

```python
from src.services.zatca_production import ZATCAProductionService

class ZakatService:
    def __init__(self):
        self.zatca_service = ZATCAProductionService() if Config.ZATCA_ENDPOINT else None
    
    async def upload_xml(self, enc_xml: str, xml_hash: str) -> Tuple[bool, str, str | None]:
        """Upload XML to ZATCA using production service"""
        if not self.zatca_service:
            return False, "ZATCA service not configured", None
        
        try:
            # Decode the base64 XML
            xml_bytes = base64.b64decode(enc_xml)
            xml_str = xml_bytes.decode('utf-8')
            
            # Submit to ZATCA
            result = await self.zatca_service.submit_invoice(xml_str, xml_hash)
            
            if result["success"]:
                return True, result["message"], result["zatca_uuid"]
            else:
                return False, result["error"], None
                
        except Exception as e:
            return False, str(e), None
```

## 🧪 Testing with ZATCA Sandbox

### Sandbox Configuration

For testing, use ZATCA sandbox environment:

```env
# Sandbox Configuration
ZATCA_ENDPOINT=https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/sandbox
ZATCA_CLIENT_ID=sandbox_client_id
ZATCA_CLIENT_SECRET=sandbox_client_secret
```

### Test Invoice Submission

```bash
# Test with sandbox
python src/scripts/zakat_api_integration.py

# Process invoices with real API (sandbox)
curl -X POST "http://localhost:12000/api/invoices/process-zakat?limit=1&simulate=false"
```

## 📊 Invoice Submission Workflow

### 1. Prepare Invoice
```python
# Generate ZATCA-compliant XML
xml = zakat_service.build_xml(invoice)
enc_xml, xml_hash = zakat_service.encrypt_xml(xml)
```

### 2. Submit to ZATCA
```python
# Submit to ZATCA API
success, message, zatca_uuid = await zakat_service.upload_xml(enc_xml, xml_hash)

if success:
    invoice.zatca_uuid = zatca_uuid
    invoice.status = InvoiceStatus.DONE
    invoice.submitted_at = datetime.utcnow()
else:
    invoice.status = InvoiceStatus.FAILED
    invoice.last_error = message
```

### 3. Handle Response
```python
# Process ZATCA response
if zatca_response["status"] == "ACCEPTED":
    # Invoice accepted by ZATCA
    print(f"✅ Invoice {invoice.invoice_number} accepted")
elif zatca_response["status"] == "REJECTED":
    # Invoice rejected - fix issues
    print(f"❌ Invoice {invoice.invoice_number} rejected: {zatca_response['errors']}")
elif zatca_response["status"] == "PENDING":
    # Invoice under review
    print(f"⏳ Invoice {invoice.invoice_number} pending review")
```

## 🔍 Monitoring and Logging

### Enhanced Logging
```python
import structlog

logger = structlog.get_logger()

async def submit_invoice_with_logging(invoice):
    logger.info(
        "Submitting invoice to ZATCA",
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        total=float(invoice.net_total)
    )
    
    try:
        result = await zatca_service.submit_invoice(invoice)
        
        logger.info(
            "Invoice submission result",
            invoice_id=str(invoice.id),
            success=result["success"],
            zatca_uuid=result.get("zatca_uuid"),
            status=result.get("status")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Invoice submission failed",
            invoice_id=str(invoice.id),
            error=str(e),
            exc_info=True
        )
        raise
```

### Health Check for ZATCA API
```python
@app.get("/api/health/zatca")
async def zatca_health_check():
    """Check ZATCA API connectivity"""
    try:
        zatca_service = ZATCAProductionService()
        token = await zatca_service.authenticate()
        
        return {
            "status": "healthy",
            "zatca_api": "connected",
            "authenticated": bool(token),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "zatca_api": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## 🚨 Error Handling

### Common ZATCA Errors

1. **Authentication Errors**
   - Invalid client credentials
   - Expired certificates
   - SSL/TLS issues

2. **Invoice Validation Errors**
   - Invalid XML structure
   - Missing required fields
   - Incorrect tax calculations

3. **Business Rule Violations**
   - Duplicate invoice numbers
   - Invalid VAT numbers
   - Incorrect invoice dates

### Error Recovery
```python
async def submit_with_retry(invoice, max_retries=3):
    """Submit invoice with retry logic"""
    
    for attempt in range(max_retries):
        try:
            result = await zatca_service.submit_invoice(invoice)
            return result
            
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
            
        except Exception as e:
            if "authentication" in str(e).lower() and attempt < max_retries - 1:
                # Retry authentication errors
                await asyncio.sleep(1)
                continue
            raise
```

## 📋 Production Checklist

### Before Going Live
- [ ] ZATCA business registration completed
- [ ] Certificates generated and approved by ZATCA
- [ ] Client credentials obtained from ZATCA
- [ ] Sandbox testing completed successfully
- [ ] Production environment configured
- [ ] SSL/TLS certificates properly configured
- [ ] Monitoring and alerting setup
- [ ] Error handling and retry logic implemented
- [ ] Backup and recovery procedures in place
- [ ] Staff training completed

### Environment Variables Checklist
```env
# Required for production
ZATCA_ENDPOINT=https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal
ZATCA_CLIENT_ID=your_production_client_id
ZATCA_CLIENT_SECRET=your_production_client_secret
ZATCA_CERT_B64=your_base64_encoded_certificate
ZATCA_PRIVATE_KEY_B64=your_base64_encoded_private_key

# Optional but recommended
ZATCA_TIMEOUT=30
ZATCA_MAX_RETRIES=3
ZATCA_RETRY_DELAY=2
```

## 🔧 Troubleshooting

### Certificate Issues
```bash
# Verify certificate
openssl x509 -in zatca_certificate.pem -text -noout

# Check certificate expiry
openssl x509 -in zatca_certificate.pem -enddate -noout

# Verify private key matches certificate
openssl x509 -noout -modulus -in zatca_certificate.pem | openssl md5
openssl rsa -noout -modulus -in zatca_private_key.pem | openssl md5
```

### API Connectivity
```bash
# Test ZATCA API connectivity
curl -v https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/health

# Test with client certificate
curl --cert zatca_certificate.pem --key zatca_private_key.pem \
     https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/oauth2/token
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test invoice submission
python -c "
import asyncio
from src.services.zatca_production import ZATCAProductionService

async def test():
    service = ZATCAProductionService()
    token = await service.authenticate()
    print(f'Token: {token[:20]}...')

asyncio.run(test())
"
```

## 📞 Support

### ZATCA Support Channels
- **Technical Support**: support@zatca.gov.sa
- **Developer Portal**: https://zatca.gov.sa/developer
- **Documentation**: Official ZATCA API documentation
- **Helpdesk**: ZATCA technical helpdesk

### System Support
- Check logs in `/var/log/zatca/`
- Monitor API response times
- Verify certificate validity
- Test connectivity regularly

---

**⚠️ Important**: Always test thoroughly in the sandbox environment before switching to production. Keep your certificates and credentials secure and never commit them to version control.