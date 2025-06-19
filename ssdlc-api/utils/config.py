import os
import json

# Bitbucket
BITBUCKET_USER = os.getenv('BITBUCKET_USER')
BITBUCKET_TOKEN = os.getenv('BITBUCKET_TOKEN')
GIT_PYTHON_REFRESH = os.getenv('GIT_PYTHON_REFRESH')
GIT_SSL_CAINFO = os.getenv('GIT_SSL_CAINFO')

# SSL-related environment variables
REQUESTS_CA_BUNDLE = os.getenv('REQUESTS_CA_BUNDLE')
SSL_CERT_FILE = os.getenv('SSL_CERT_FILE')
HTTPLIB2_CA_CERTS = os.getenv('HTTPLIB2_CA_CERTS')

# Wiz Credentials
WIZ_CLIENT_ID = os.getenv('WIZ_CLIENT_ID')
WIZ_SECRET = os.getenv('WIZ_SECRET')

# AMS Related
AMS_ACCOUNTS = os.getenv('AMS_ACCOUNTS', '').split(',')
AMS_DEFAULT_REGION = os.getenv('AMS_DEFAULT_REGION', 'us-east-1')

# Signature Store
SIGNATURE_STORE_ENDPOINT = os.getenv('SIGNATURE_STORE_ENDPOINT')

# Container Image Tools Supported
SUPPORTED_TOOLS = ['wiz', 'nexus']

# Nexus IQ
NEXUS_IQ_URL = os.getenv('NEXUS_IQ_URL')
NEXUS_SECRET = os.getenv('NEXUS_SECRET')

# SonarQube
SONAR_HOST_URL = os.getenv('SONAR_HOST_URL')
SONAR_TOKEN = os.getenv('SONAR_TOKEN')
