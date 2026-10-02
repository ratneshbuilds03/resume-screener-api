# Resume Screener API

A production-ready FastAPI application for AI-assisted resume screening, applicant fit analysis, and analytics for placement and hiring workflows.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-S3-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/s3/)
[![JWT](https://img.shields.io/badge/JWT-Authentication-000000?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Pytest](https://img.shields.io/badge/Pytest-8.3-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)

## Project Overview

This project helps recruiters and hiring teams evaluate a resume against a job description by combining:

- PDF validation and text extraction
- keyword and skill matching
- experience and education scoring
- AI-assisted reasoning with OpenAI
- secure user authentication and ownership checks
- MongoDB analytics and Redis caching
- AWS S3 storage for uploaded resumes

## Features

- Resume upload with PDF validation and text extraction
- Role-based JWT authentication
- Background processing for analysis requests
- AI fallback logic when the OpenAI service is unavailable
- Score grading and summary generation
- Redis caching to reduce repeat AI calls
- MongoDB analytics for overview, comparisons, and skill gaps
- MySQL persistence for user and analysis records
- AWS S3 upload and presigned download links
- Dockerized local setup and GitHub Actions CI

## Architecture

```text
Client
  -> FastAPI API
      -> Authentication (JWT)
      -> PDF validation & extraction
      -> Keyword matching + scoring
      -> OpenAI AI analysis (with fallback)
      -> AWS S3 upload
      -> MySQL persistence
      -> MongoDB analytics payload
      -> Redis cache
```

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy + MySQL
- MongoDB
- Redis
- OpenAI API
- AWS S3
- JWT / OAuth2
- PyPDF2
- Docker + Docker Compose
- Pytest + GitHub Actions

## API Endpoints

### Authentication

- POST /auth/signup
- POST /auth/login

### Resume Analysis

- POST /analysis/upload
- GET /analysis/history
- GET /analysis/{analysis_id}
- GET /analysis/{analysis_id}/status
- DELETE /analysis/{analysis_id}

### Analytics

- GET /analytics/overview
- GET /analytics/skill-gaps
- GET /analytics/recent
- GET /analytics/compare/{analysis_id_1}/{analysis_id_2}

### Health

- GET /health

## Authentication and Security

- JWT-based access tokens with expiration handling
- user ownership enforcement for every analysis and analytics request
- inactive users are denied access
- password hashes are never returned in API responses
- environment-driven secrets and AWS credentials
- configurable CORS origins
- PDF-only upload validation with size limits
- no sensitive credentials exposed through health checks

## AI Analysis Flow

1. User uploads a resume PDF and a job description.
2. The PDF is validated and converted to text.
3. The system extracts skill and keyword matches.
4. Experience and education scoring are computed locally.
5. OpenAI generates a structured evaluation when configured.
6. If the model fails or a key is missing, the app falls back to the local scoring flow without crashing the request.

## Scoring System

The scoring model combines:

- keyword match percentage
- experience score
- education score
- skills alignment score

These are weighted into a final score and mapped to a letter grade such as A, B, C, D, or F.

## Redis Caching

Redis is used to reduce repeated work for identical PDF and job description pairs.

- Cache hit: returns the cached result quickly
- Cache miss: performs scoring and stores the result
- Redis outage: the app degrades gracefully without failing the whole request pipeline

## MongoDB Analytics

MongoDB stores detailed analysis documents for:

- score trends
- skill gaps
- keyword match history
- comparison views
- recommendation summaries

Analytics endpoints are guarded by authenticated user ownership checks.

## AWS S3

Uploaded resume files are stored in S3 with a safe generated object name and a PDF content type. Presigned URLs can be used for download access without exposing AWS credentials.

## Docker

```bash
docker compose up --build
```

This starts the API, MySQL, MongoDB, and Redis services together.

## Testing

```bash
python -m pytest tests/ -v
```

The project uses mocked external integrations so tests remain fast and do not call the real OpenAI or AWS services.

## Environment Variables

Use a local `.env` file or a deployment platform secret manager.

Example variables:

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/resume_db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=resume_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BUCKET_NAME=
AWS_REGION=ap-south-1
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## GitHub Actions

The repository includes CI checks to install dependencies, start MySQL, MongoDB, and Redis, run the test suite, and build the Docker image.

## Project Structure

```text
resume-scanner/
├── app/
│   ├── config.py
│   ├── database.py
│   ├── limiter.py
│   ├── main.py
│   ├── mongodb.py
│   ├── redis_client.py
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
├── .env.example
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── run.py
├── README.MD
└── .gitignore
```

## Security Notes

- `.env` is never committed
- `.env.example` is included as a safe template
- no hardcoded API or AWS credentials
- secrets are supplied via runtime environment configuration
- all analysis endpoints verify ownership before returning data

## Backend Concepts Demonstrated

- REST API design with FastAPI
- JWT auth and protected routing
- SQLAlchemy ORM with relational persistence
- async MongoDB access for analytics documents
- Redis cache integration
- S3 object storage management
- background worker pattern
- test-driven validation with mocks
- CI pipeline automation

## Author

Ratnesh Makwana

GitHub: https://github.com/ratneshbuilds03
