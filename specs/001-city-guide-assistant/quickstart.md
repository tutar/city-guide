# Quick Start: City Guide Smart Assistant

**Date**: 2025-11-06
**Feature**: City Guide Smart Assistant

## Overview

The City Guide Smart Assistant is an AI-powered conversational interface that provides accurate, step-by-step guidance for Shenzhen government services through natural language interaction.

## Prerequisites

### Development Environment
- Python 3.11+ for backend
- Node.js 18+ for frontend
- PostgreSQL 14+ for database
- Redis 6+ for caching

### API Keys
- Deepseek API key for AI conversation
- (Optional) External government API credentials

## Getting Started

### 1. Backend Setup

```bash
# Clone and setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Environment configuration
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL
# - REDIS_URL
# - DEEPSEEK_API_KEY
# - QDRANT_URL
# - QDRANT_API_KEY
# - SECRET_KEY

# Database setup
python -m scripts.setup_database

# Vector database setup
python -m scripts.setup_vector_db

# Run development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
# Clone and setup frontend
cd frontend

# Install dependencies
npm install

# Environment configuration
cp .env.example .env.local
# Edit .env.local with your settings:
# - REACT_APP_API_BASE_URL=http://localhost:8000/v1

# Run development server
npm start
```

### 3. Verify Setup

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/v1/health
   # Should return: {"status": "healthy", "version": "1.0.0"}
   ```

2. **Frontend Access**:
   - Open http://localhost:3000 in your browser
   - You should see the City Guide Smart Assistant interface

## Core Features

### 1. Conversation Flow

```python
# Example: Starting a conversation
import requests

# Start conversation
response = requests.post(
    "http://localhost:8000/v1/conversation/start",
    json={
        "user_preferences": {
            "language": "zh-CN",
            "location": "Shenzhen"
        }
    }
)

session_id = response.json()["session_id"]

# Send message
response = requests.post(
    f"http://localhost:8000/v1/conversation/{session_id}/message",
    json={
        "message": "How do I get a Hong Kong passport?"
    }
)

print(response.json()["ai_response"])
print(response.json()["navigation_options"])
```

### 2. Service Categories

```python
# List all services
response = requests.get("http://localhost:8000/v1/services")
services = response.json()["services"]

# Search services
response = requests.get(
    "http://localhost:8000/v1/services/search",
    params={"query": "passport"}
)
results = response.json()["results"]
```

## Development Workflow

### Backend Development

1. **Run Tests**:
   ```bash
   cd backend
   pytest tests/unit/
   pytest tests/integration/
   pytest tests/contract/
   ```

2. **API Documentation**:
   - Access Swagger UI: http://localhost:8000/docs
   - Access ReDoc: http://localhost:8000/redoc

3. **Database Migrations**:
   ```bash
   python -m alembic revision --autogenerate -m "description"
   python -m alembic upgrade head
   ```

### Frontend Development

1. **Run Tests**:
   ```bash
   cd frontend
   npm test
   npm run test:e2e
   ```

2. **Build for Production**:
   ```bash
   npm run build
   ```

## Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/cityguide

# Redis
REDIS_URL=redis://localhost:6379

# AI & Vector Database
DEEPSEEK_API_KEY=your_deepseek_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Security
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# External APIs
GOVERNMENT_API_BASE_URL=https://api.shenzhen.gov.cn
GOVERNMENT_API_KEY=your_government_key
```

### Frontend Environment Variables

```bash
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000/v1

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_OFFLINE_MODE=true
```

## Testing

### Backend Testing Strategy

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests
pytest tests/contract/

# Performance tests
pytest tests/performance/

# All tests with coverage
pytest --cov=src --cov-report=html
```

### Frontend Testing Strategy

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Accessibility tests
npm run test:a11y
```

## Deployment

### Backend Deployment

1. **Build Docker Image**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Deploy to Production**:
   ```bash
   docker build -t cityguide-backend .
   docker run -p 8000:8000 --env-file .env cityguide-backend
   ```

### Frontend Deployment

1. **Build for Production**:
   ```bash
   npm run build
   ```

2. **Serve with Nginx**:
   ```nginx
   server {
       listen 80;
       server_name cityguide.example.com;
       root /var/www/cityguide-frontend/build;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

## Monitoring & Observability

### Backend Metrics

- Response time metrics
- Error rate monitoring
- Database connection pool status
- External API health checks

### Frontend Metrics

- Page load performance
- User interaction analytics
- Error tracking
- Accessibility compliance

## Troubleshooting

### Common Issues

1. **Database Connection**:
   - Verify DATABASE_URL format
   - Check PostgreSQL is running
   - Ensure database user has correct permissions

2. **Redis Connection**:
   - Verify REDIS_URL format
   - Check Redis server is running
   - Test connection with redis-cli

3. **Deepseek API**:
   - Verify DEEPSEEK_API_KEY is set
   - Check API quota and billing
   - Test with simple API call

4. **Vector Database**:
   - Verify QDRANT_URL and QDRANT_API_KEY are set
   - Check Qdrant server is running
   - Test vector database connection
   - Ensure embedding model is accessible

### Debug Mode

Enable debug logging:

```bash
# Backend
LOG_LEVEL=DEBUG

# Frontend
REACT_APP_DEBUG=true
```

## Support

- **Backend Issues**: Check backend logs at `/var/log/cityguide/backend.log`
- **Frontend Issues**: Check browser developer console
- **API Issues**: Review API documentation at `/docs` endpoint
- **Database Issues**: Check PostgreSQL logs

## Next Steps

1. **Add More Services**: Extend service categories with additional government services
2. **Multi-language Support**: Add support for more languages
3. **Mobile App**: Develop native mobile applications
4. **Advanced Analytics**: Implement detailed usage analytics
5. **Integration**: Connect with more external government APIs