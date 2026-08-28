# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Local SSL Certificate & Root CA Generator
# =============================================================================
# Description:
#   Generates a dedicated local Root CA and an end-entity SSL server certificate
#   with full ExtendedKeyUsage (SERVER_AUTH) and SAN for localhost and local IPs.
#
# File: generate_ssl_certs.py
# Project: ai-breadboard
# Package: scripts.maintenance
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import ipaddress
import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def generate_certificates(certs_dir: Path | None = None, extra_ips: list[str] | None = None) -> tuple[Path, Path, Path]:
    """Generate Root CA and server leaf certificate for localhost.

    Args:
        certs_dir: Destination directory for certificates (~/.certs by default).
        extra_ips: List of additional IP addresses to add to SAN.

    Returns:
        tuple[Path, Path, Path]: (cert_path, key_path, root_ca_path)
    """
    if not certs_dir:
        certs_dir = Path(os.path.expanduser('~')) / '.certs'
    certs_dir.mkdir(parents=True, exist_ok=True)

    ca_cert_path = certs_dir / 'rootCA.pem'
    ca_key_path = certs_dir / 'rootCA-key.pem'
    cert_path = certs_dir / 'localhost+2.pem'
    key_path = certs_dir / 'localhost+2-key.pem'

    # 1. Generate or load Root CA
    ca_cert = None
    ca_key = None
    if ca_cert_path.exists() and ca_key_path.exists():
        try:
            ca_cert = x509.load_pem_x509_certificate(ca_cert_path.read_bytes())
            ca_key = serialization.load_pem_private_key(ca_key_path.read_bytes(), password=None)
            ca_name = ca_cert.subject
        except Exception:
            ca_cert = None
            ca_key = None

    if not ca_cert or not ca_key:
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'aibreadboard Local Root CA'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'aibreadboard Development'),
        ])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=True, encipher_only=False, decipher_only=False
            ), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        ca_cert_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
        ca_key_path.write_bytes(ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # 2. Build SAN list for Server Certificate
    san_list: list[x509.GeneralName] = [
        x509.DNSName('localhost'),
        x509.DNSName(socket.gethostname()),
        x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
        x509.IPAddress(ipaddress.IPv6Address('::1')),
    ]

    all_ips = extra_ips or []
    try:
        host_ips = socket.gethostbyname_ex(socket.gethostname())[2]
        for hip in host_ips:
            if hip not in all_ips:
                all_ips.append(hip)
    except Exception:
        pass

    for ip_str in all_ips:
        try:
            ip_obj = ipaddress.ip_address(ip_str.strip())
            if ip_obj not in [x.value for x in san_list if isinstance(x, x509.IPAddress)]:
                san_list.append(x509.IPAddress(ip_obj))
        except Exception:
            pass

    # 3. Generate End-Entity Server Certificate signed by Root CA
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'aibreadboard Local Server'),
    ])

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1825))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=True,
            data_encipherment=False, key_agreement=False, key_cert_sign=False,
            crl_sign=False, encipher_only=False, decipher_only=False
        ), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    cert_path.write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

    # 4. Install Root CA into Windows Trusted Root Store
    if sys.platform == 'win32':
        try:
            subprocess.run(['certutil', '-user', '-addstore', '-f', 'Root', str(ca_cert_path)], capture_output=True)
        except Exception:
            pass

    return cert_path, key_path, ca_cert_path


if __name__ == '__main__':
    extra = sys.argv[1:]
    c_path, k_path, ca_path = generate_certificates(extra_ips=extra)
    print(f'SUCCESS: cert={c_path} key={k_path} ca={ca_path}')
