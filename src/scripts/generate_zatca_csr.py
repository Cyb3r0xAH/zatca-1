#!/usr/bin/env python3
"""
ZATCA Certificate Signing Request (CSR) Generator
Generates CSR and private key for ZATCA API authentication
"""

import os
import base64
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta


class ZATCACSRGenerator:
    """Generate CSR and private key for ZATCA authentication"""
    
    def __init__(self):
        self.private_key = None
        self.csr = None
    
    def generate_private_key(self, key_size: int = 2048) -> rsa.RSAPrivateKey:
        """Generate RSA private key"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        return self.private_key
    
    def generate_csr(self, 
                     organization_name: str,
                     organization_unit: str,
                     common_name: str,
                     country: str = "SA",
                     vat_number: str = None,
                     serial_number: str = None) -> x509.CertificateSigningRequest:
        """
        Generate Certificate Signing Request for ZATCA
        
        Args:
            organization_name: Your company name (Arabic and English)
            organization_unit: Department/Unit name
            common_name: Usually your VAT number or company identifier
            country: Country code (SA for Saudi Arabia)
            vat_number: Your VAT registration number
            serial_number: Your commercial registration number
        """
        
        if not self.private_key:
            self.generate_private_key()
        
        # Build subject name
        subject_components = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organization_unit),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
        
        # Add VAT number if provided
        if vat_number:
            subject_components.append(
                x509.NameAttribute(NameOID.SERIAL_NUMBER, vat_number)
            )
        
        subject = x509.Name(subject_components)
        
        # Create CSR builder
        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(subject)
        
        # Add Subject Alternative Name (SAN) extension
        san_list = []
        if vat_number:
            san_list.append(x509.DirectoryName(x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, vat_number)
            ])))
        
        if san_list:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False
            )
        
        # Add Key Usage extension
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=True,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        
        # Add Extended Key Usage
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH
            ]),
            critical=True
        )
        
        # Sign the CSR
        self.csr = builder.sign(self.private_key, hashes.SHA256())
        return self.csr
    
    def save_files(self, output_dir: str = "zatca_certs"):
        """Save private key and CSR to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save private key
        private_key_path = os.path.join(output_dir, "zatca_private_key.pem")
        with open(private_key_path, "wb") as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save CSR
        csr_path = os.path.join(output_dir, "zatca_csr.pem")
        with open(csr_path, "wb") as f:
            f.write(self.csr.public_bytes(serialization.Encoding.PEM))
        
        return private_key_path, csr_path
    
    def get_base64_encoded(self) -> tuple[str, str]:
        """Get base64 encoded private key and CSR for environment variables"""
        
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        csr_pem = self.csr.public_bytes(serialization.Encoding.PEM)
        
        private_key_b64 = base64.b64encode(private_key_pem).decode('utf-8')
        csr_b64 = base64.b64encode(csr_pem).decode('utf-8')
        
        return private_key_b64, csr_b64


def main():
    """Generate ZATCA CSR with sample company data"""
    
    print("🔐 ZATCA Certificate Signing Request Generator")
    print("=" * 50)
    
    # Company information (replace with your actual data)
    company_info = {
        "organization_name": "شــركــة الـسـلـوم والــغيث لتسويق الـتـمـور",  # Your company name
        "organization_unit": "IT Department",  # Your department
        "common_name": "302008893200003",  # Usually your VAT number
        "vat_number": "302008893200003",  # Your VAT registration number
        "serial_number": "1010123456",  # Your commercial registration number
    }
    
    print("Company Information:")
    for key, value in company_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Generate CSR
    generator = ZATCACSRGenerator()
    
    print("🔑 Generating private key...")
    generator.generate_private_key()
    
    print("📄 Generating Certificate Signing Request...")
    generator.generate_csr(**company_info)
    
    print("💾 Saving files...")
    private_key_path, csr_path = generator.save_files()
    
    print("📋 Getting base64 encoded values...")
    private_key_b64, csr_b64 = generator.get_base64_encoded()
    
    print("\n✅ Files generated successfully!")
    print(f"  Private Key: {private_key_path}")
    print(f"  CSR: {csr_path}")
    
    print("\n📋 Environment Variables (for .env file):")
    print("# Add these to your .env file after getting certificate from ZATCA")
    print(f"ZATCA_PRIVATE_KEY_B64={private_key_b64}")
    print("ZATCA_CERT_B64=<base64_encoded_certificate_from_zatca>")
    print("ZATCA_CLIENT_ID=<your_client_id_from_zatca>")
    print("ZATCA_CLIENT_SECRET=<your_client_secret_from_zatca>")
    print("ZATCA_ENDPOINT=https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal")
    
    print("\n📤 Next Steps:")
    print("1. Submit the CSR file to ZATCA through their portal")
    print("2. Wait for ZATCA to issue your certificate")
    print("3. Download the certificate and convert to base64")
    print("4. Get your Client ID and Client Secret from ZATCA portal")
    print("5. Update your .env file with the credentials")
    
    print(f"\n📄 CSR Content (submit this to ZATCA):")
    print("-" * 50)
    with open(csr_path, 'r') as f:
        print(f.read())


if __name__ == "__main__":
    main()