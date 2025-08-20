# ZATCA Technical Documentation

## Overview

This document provides detailed technical information about the ZATCA Invoice Management System implementation, including XML structure, database schema, API specifications, and integration details.

## ZATCA XML Structure

### UBL 2.1 Invoice Format

The system generates XML invoices compliant with UBL 2.1 standard as required by ZATCA:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    
    <!-- ZATCA Required Fields -->
    <cbc:CustomizationID>BR-KSA-CB</cbc:CustomizationID>
    <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
    <cbc:ID>INV-20250820-0001</cbc:ID>
    <cbc:UUID>550e8400-e29b-41d4-a716-446655440000</cbc:UUID>
    <cbc:IssueDate>2025-08-20</cbc:IssueDate>
    <cbc:IssueTime>10:30:00</cbc:IssueTime>
    <cbc:InvoiceTypeCode name="0200000">388</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>SAR</cbc:DocumentCurrencyCode>
    <cbc:TaxCurrencyCode>SAR</cbc:TaxCurrencyCode>
    
    <!-- Supplier Information -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="CRN">302008893200003</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>شــركــة الـسـلـوم والــغيث لتسويق الـتـمـور</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>المملكة العربية السعودية - الــقــصــيــم - بريدة</cbc:StreetName>
                <cbc:CityName>الرياض</cbc:CityName>
                <cbc:PostalZone>12345</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>SA</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>302008893200003</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <!-- Customer Information -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>عميل رقم 1</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <!-- Tax Information -->
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="SAR">72.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="SAR">480.00</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="SAR">72.00</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>15.00</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    
    <!-- Monetary Totals -->
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="SAR">480.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="SAR">480.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="SAR">552.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="SAR">552.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <!-- Invoice Lines -->
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="PCE">8</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="SAR">60.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>تمور خلاص</cbc:Name>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="SAR">60.00</cbc:PriceAmount>
        </cac:Price>
        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="SAR">72.00</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="SAR">60.00</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="SAR">72.00</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:ID>S</cbc:ID>
                    <cbc:Percent>15.00</cbc:Percent>
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>
    </cac:InvoiceLine>
</Invoice>
```

### XML Validation Rules

The system validates XML against these ZATCA requirements:

1. **Structure Validation**:
   - XML declaration present
   - Root `<Invoice>` element with proper namespaces
   - Required UBL elements present

2. **Content Validation**:
   - CustomizationID = "BR-KSA-CB"
   - ProfileID = "reporting:1.0"
   - InvoiceTypeCode = "388"
   - Currency codes = "SAR"
   - VAT percentage = "15.00"

3. **Business Rules**:
   - Invoice ID uniqueness
   - Valid VAT registration number format
   - Proper tax calculations
   - Required supplier information

## QR Code Implementation

### TLV (Tag-Length-Value) Encoding

ZATCA requires QR codes with specific TLV structure:

```python
def encode_tlv(tag: int, value: str) -> bytes:
    """Encode a single TLV field"""
    value_bytes = value.encode('utf-8')
    return bytes([tag]) + bytes([len(value_bytes)]) + value_bytes

# ZATCA QR Code Fields
tlv_data = b''
tlv_data += encode_tlv(1, seller_name)        # Seller name
tlv_data += encode_tlv(2, vat_number)         # VAT registration number
tlv_data += encode_tlv(3, timestamp)          # Invoice timestamp
tlv_data += encode_tlv(4, total_with_vat)     # Total amount including VAT
tlv_data += encode_tlv(5, vat_amount)         # VAT amount

qr_data = base64.b64encode(tlv_data).decode('utf-8')
```

### QR Code Generation Process

1. **Data Collection**: Gather required invoice fields
2. **TLV Encoding**: Encode each field with tag, length, value
3. **Base64 Encoding**: Convert TLV bytes to base64 string
4. **QR Generation**: Create QR code image from base64 data
5. **PDF Embedding**: Include QR code in invoice PDF

## Database Schema

### Core Tables

#### invoices
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR NOT NULL UNIQUE,
    store_name VARCHAR NOT NULL,
    store_address VARCHAR NOT NULL,
    vat_number VARCHAR NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    total NUMERIC(10,2) NOT NULL,
    taxes NUMERIC(10,2) NOT NULL,
    seller_taxes NUMERIC(10,2) NOT NULL,
    net_total NUMERIC(10,2) NOT NULL,
    user_name VARCHAR NOT NULL,
    account_id VARCHAR NOT NULL,
    status invoice_status_enum NOT NULL DEFAULT 'PENDING',
    zatca_uuid VARCHAR,
    zatca_xml TEXT,
    zatca_xml_hash VARCHAR(128),
    submitted_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_date ON invoices(date);
CREATE INDEX idx_invoices_vat_number ON invoices(vat_number);
```

#### invoice_item
```sql
CREATE TABLE invoice_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    item_name VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    tax NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_invoice_item_invoice_id ON invoice_item(invoice_id);
```

#### Status Enum
```sql
CREATE TYPE invoice_status_enum AS ENUM (
    'PENDING',
    'IN_PROGRESS', 
    'DONE',
    'FAILED'
);
```

### DBISAM Legacy Tables

#### dbisam_accounts
```sql
CREATE TABLE dbisam_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number INTEGER NOT NULL,
    account_name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### dbisam_items
```sql
CREATE TABLE dbisam_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_number REAL NOT NULL,
    item_name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### dbisam_entries
```sql
CREATE TABLE dbisam_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number INTEGER,
    total_amount REAL NOT NULL,
    item_number REAL NOT NULL,
    item_price REAL NOT NULL,
    item_quantity REAL NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### dbisam_index_entries
```sql
CREATE TABLE dbisam_index_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_number INTEGER NOT NULL,
    document_kind INTEGER NOT NULL,
    account_number INTEGER,
    date VARCHAR NOT NULL,
    ratio REAL NOT NULL,
    user_name VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Specifications

### Authentication
Currently, the API uses basic authentication. For production, implement:
- JWT tokens
- API key authentication
- OAuth 2.0 integration

### Rate Limiting
Implement rate limiting for production:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/invoices/process-zakat")
@limiter.limit("10/minute")
async def process_zakat(request: Request, ...):
    # Implementation
```

### Error Handling
Standard error response format:
```json
{
    "error": {
        "code": "ZATCA_001",
        "message": "XML validation failed",
        "details": {
            "field": "cbc:UUID",
            "reason": "Invalid UUID format"
        }
    },
    "timestamp": "2025-08-20T10:30:00Z",
    "request_id": "req_123456789"
}
```

### Response Schemas

#### Invoice Response
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "invoice_number": "INV-20250820-0001",
    "store_name": "شــركــة الـسـلـوم والــغيث لتسويق الـتـمـور",
    "customer_name": "عميل رقم 1",
    "date": "2025-08-20T10:30:00Z",
    "total": 480.00,
    "taxes": 72.00,
    "net_total": 552.00,
    "status": "DONE",
    "zatca_uuid": "zatca_550e8400-e29b-41d4-a716-446655440000",
    "submitted_at": "2025-08-20T10:35:00Z",
    "items": [
        {
            "name": "تمور خلاص",
            "quantity": 8,
            "price": 60.00,
            "tax": 72.00
        }
    ]
}
```

## Tax Calculations

### VAT Calculation Formula
```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_vat(amount: Decimal, vat_rate: Decimal = Decimal('0.15')) -> tuple:
    """
    Calculate VAT with proper rounding
    Returns: (vat_amount, total_with_vat)
    """
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    vat_amount = (amount * vat_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_with_vat = (amount + vat_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return vat_amount, total_with_vat
```

### Tax Categories
- **Standard Rate (S)**: 15% VAT
- **Zero Rate (Z)**: 0% VAT (exports, certain goods)
- **Exempt (E)**: VAT exempt items
- **Out of Scope (O)**: Non-VAT applicable

## Security Implementation

### XML Encryption
```python
import base64
import hashlib

def encrypt_xml(xml: str) -> tuple[str, str]:
    """Encrypt XML with base64 and generate hash"""
    xml_bytes = xml.encode('utf-8')
    xml_hash = hashlib.sha256(xml_bytes).hexdigest()
    encrypted_xml = base64.b64encode(xml_bytes).decode('ascii')
    return encrypted_xml, xml_hash
```

### Data Validation
```python
from pydantic import BaseModel, validator

class InvoiceCreate(BaseModel):
    invoice_number: str
    vat_number: str
    total: Decimal
    
    @validator('vat_number')
    def validate_vat_number(cls, v):
        if not v.isdigit() or len(v) != 15:
            raise ValueError('VAT number must be 15 digits')
        return v
    
    @validator('total')
    def validate_total(cls, v):
        if v <= 0:
            raise ValueError('Total must be positive')
        return v
```

## Performance Optimization

### Database Optimization
1. **Indexing Strategy**:
   ```sql
   CREATE INDEX CONCURRENTLY idx_invoices_status_date ON invoices(status, date);
   CREATE INDEX CONCURRENTLY idx_invoices_vat_number_status ON invoices(vat_number, status);
   ```

2. **Query Optimization**:
   ```python
   # Use selectinload for related data
   stmt = (
       select(Invoice)
       .options(selectinload(Invoice.items))
       .where(Invoice.status == InvoiceStatus.PENDING)
       .limit(100)
   )
   ```

3. **Connection Pooling**:
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True,
       pool_recycle=3600
   )
   ```

### Caching Strategy
```python
from functools import lru_cache
import redis

# In-memory caching
@lru_cache(maxsize=1000)
def get_vat_rate(country_code: str) -> Decimal:
    return Decimal('0.15')  # Saudi Arabia VAT rate

# Redis caching for invoice stats
redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_invoice_stats() -> dict:
    cached = redis_client.get('invoice_stats')
    if cached:
        return json.loads(cached)
    
    # Calculate stats from database
    stats = await calculate_stats()
    redis_client.setex('invoice_stats', 300, json.dumps(stats))  # 5 min cache
    return stats
```

## Monitoring and Logging

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

async def process_invoice(invoice_id: str):
    logger.info(
        "Processing invoice",
        invoice_id=invoice_id,
        action="process_start"
    )
    
    try:
        # Process invoice
        result = await process_zatca_invoice(invoice_id)
        
        logger.info(
            "Invoice processed successfully",
            invoice_id=invoice_id,
            zatca_uuid=result.zatca_uuid,
            action="process_success"
        )
        
    except Exception as e:
        logger.error(
            "Invoice processing failed",
            invoice_id=invoice_id,
            error=str(e),
            action="process_error"
        )
        raise
```

### Health Checks
```python
@app.get("/api/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "zatca_api": await check_zatca_api_connectivity(),
        "redis": await check_redis_connection(),
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
```

## Deployment Configuration

### Docker Setup
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 12000

CMD ["uvicorn", "src:app", "--host", "0.0.0.0", "--port", "12000"]
```

### Environment Variables
```env
# Production settings
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/zatca
ZATCA_ENDPOINT=https://api.zatca.gov.sa/invoices
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=production-secret-key
JWT_SECRET=jwt-secret-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# ZATCA Configuration
ZATCA_CERT_PATH=/app/certs/zatca.crt
ZATCA_KEY_PATH=/app/certs/zatca.key
```

### Production Checklist
- [ ] SSL/TLS certificates configured
- [ ] Database connection pooling enabled
- [ ] Redis caching implemented
- [ ] Rate limiting configured
- [ ] Monitoring and alerting setup
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] ZATCA API credentials configured
- [ ] Load balancing configured
- [ ] Health checks implemented

## Testing Strategy

### Unit Tests
```python
import pytest
from src.services.zakat import ZakatService

@pytest.mark.asyncio
async def test_xml_generation():
    service = ZakatService()
    invoice = create_test_invoice()
    
    xml = service.build_xml(invoice)
    
    assert '<?xml version="1.0"' in xml
    assert '<cbc:CustomizationID>BR-KSA-CB</cbc:CustomizationID>' in xml
    assert invoice.invoice_number in xml
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_invoice_processing_flow():
    # Create test invoice
    invoice_data = create_test_invoice_data()
    
    # Import invoice
    response = await client.post("/api/invoices/import", files={"file": invoice_data})
    assert response.status_code == 200
    
    # Process invoice
    response = await client.post("/api/invoices/process-zakat?simulate=true")
    assert response.status_code == 200
    
    # Verify processing
    stats = await client.get("/api/invoices/stats")
    assert stats.json()["done"] > 0
```

### Load Testing
```python
import asyncio
import aiohttp

async def load_test_invoice_processing():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post(
                "http://localhost:12000/api/invoices/process-zakat",
                params={"limit": 1, "simulate": True}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        success_count = sum(1 for r in responses if r.status == 200)
        
        print(f"Success rate: {success_count}/100")
```

## Troubleshooting Guide

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U zatca_user -d zatca_db -c "SELECT 1;"

# Check connection pool
SELECT count(*) FROM pg_stat_activity WHERE datname = 'zatca_db';
```

#### XML Validation Failures
```python
# Debug XML structure
def debug_xml_validation(xml: str):
    checks = {
        "has_declaration": xml.startswith('<?xml'),
        "has_invoice_root": '<Invoice' in xml,
        "has_customization_id": 'BR-KSA-CB' in xml,
        "has_profile_id": 'reporting:1.0' in xml,
        "well_formed": xml.count('<') == xml.count('>')
    }
    
    for check, passed in checks.items():
        print(f"{check}: {'✅' if passed else '❌'}")
```

#### Performance Issues
```python
# Monitor query performance
import time

async def monitor_query_performance():
    start_time = time.time()
    
    # Execute query
    result = await session.execute(query)
    
    execution_time = time.time() - start_time
    
    if execution_time > 1.0:  # Log slow queries
        logger.warning(
            "Slow query detected",
            execution_time=execution_time,
            query=str(query)
        )
```

### Debug Commands
```bash
# Check invoice processing status
curl -X GET "http://localhost:12000/api/invoices/stats"

# Test XML generation
python -c "
from src.scripts.zakat_api_integration import ZATCAAPIIntegration
import asyncio
asyncio.run(ZATCAAPIIntegration().test_xml_generation())
"

# Validate database schema
python -c "
from src.db.models.invoices import Invoice
print(Invoice.__table__.columns.keys())
"
```

This technical documentation provides comprehensive details for developers working with the ZATCA Invoice Management System. For additional information, refer to the main README.md file and the inline code documentation.