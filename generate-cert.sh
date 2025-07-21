#!/bin/bash
set -e

CERT_SUBJECT="/CN=GtkSignage"
KEY_FILE="key.pem"
CERT_FILE="cert.pem"
DAYS_VALID=365

echo "Generating self-signed certificate for $CERT_SUBJECT"

openssl req -x509 \
  -newkey rsa:2048 \
  -nodes \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -days "$DAYS_VALID" \
  -subj "$CERT_SUBJECT"

echo "Generated:"
echo "  $CERT_FILE"
echo "  $KEY_FILE"
