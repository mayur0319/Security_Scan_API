# SSDLC Scanning API

A FastAPI-based microservice for performing security scans on source code and container images as part of SSDLC (Secure Software Development Life Cycle). The service integrates with various tools like:

- **SonarQube** – for static code analysis
- **Nexus IQ** – for SCA (Software Composition Analysis)
- **Wiz** – for Dockerfile & Container image scanning
- **Git** – to pull and scan repositories
- **Bitbucket** – as the Git source

---

## 🚀 Features

- Clone source code from Bitbucket/Git using credentials
- Perform Static Code Analysis (SonarQube)
- Perform SCA (Software Composition Analysis) using Nexus IQ
- Perform Dockerfile and IaC scanning with Wiz
- Scan container images using supported tools (`wiz`, `nexus`)
- Centralized logging and exception handling
- Results sent to a Signature Store endpoint

---

## 📁 Directory Structure

.
├── app.py # FastAPI main entrypoint
├── utils/
│ ├── config.py # Configuration variables loaded from environment
│ ├── git_helper.py # Git cloning logic
│ ├── log_manager.py # Singleton logger utility
│ ├── nexus_helper.py # Nexus IQ CLI integration
│ ├── sonar_helper.py # SonarQube CLI + API integration
│ ├── wiz_helper.py # Wiz scanning logic
├── requirements.txt
└── README.md # This file


---

## 🔧 Environment Variables (`.env`)

| Variable | Description |
|---------|-------------|
| `BITBUCKET_USER` | Bitbucket username |
| `BITBUCKET_TOKEN` | Bitbucket access token |
| `GIT_PYTHON_REFRESH` | Used by GitPython for repo refresh |
| `GIT_SSL_CAINFO` | Git SSL config |
| `REQUESTS_CA_BUNDLE` | Path to SSL cert bundle |
| `SSL_CERT_FILE` | Custom SSL cert file |
| `HTTPLIB2_CA_CERTS` | For SSL trust chain (optional) |
| `WIZ_CLIENT_ID` | Wiz client ID |
| `WIZ_SECRET` | Wiz client secret |
| `AMS_ACCOUNTS` | AWS account list (comma separated) |
| `AMS_DEFAULT_REGION` | Default AWS region (default: `us-east-1`) |
| `SIGNATURE_STORE_ENDPOINT` | Endpoint where scan result is submitted |
| `SUPPORTED_TOOLS` | Supported container tools (e.g., `['wiz', 'nexus']`) |
| `NEXUS_IQ_URL` | Nexus IQ API base URL |
| `NEXUS_SECRET` | Nexus IQ token |
| `SONAR_HOST_URL` | SonarQube base URL |
| `SONAR_TOKEN` | SonarQube token for API and CLI |

---

## 🔌 API Endpoints

### Root & Health

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/` | GET | Redirects to `/docs` |
| `/health` | GET | Health check |
| `/v1` | GET | Basic info |
| `/v1/health` | GET | Health check v1 |

### Scanning APIs

| Endpoint | Method | Tool Used | Description |
|----------|--------|-----------|-------------|
| `/v1/DockerFileScan` | GET | Wiz | Dockerfile scan from Git |
| `/v1/LacScan` | GET | Wiz | Infrastructure-as-Code scan |
| `/v1/ConImgScan` | GET | Wiz/Nexus | Container Image scan |
| `/v1/SCAScan` | GET | Nexus IQ | SCA dependency scan |
| `/v1/staticCodeScan` | GET | SonarQube | Static code analysis |

> All scanning endpoints support optional query parameter: `Metadata` (JSON string)

---

## ✅ Sample API Request

```bash
curl -X GET "http://localhost:8000/v1/staticCodeScan?bitbucketRepo=https://repo.git&branch=main&pathToScan=src&commit_id=abc123" \
-H "accept: application/json"
```

