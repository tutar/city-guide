# Quick Start: City Guide Smart Assistant

**Date**: 2025-11-07
**Feature**: City Guide Smart Assistant

## Overview

The City Guide Smart Assistant is an AI-powered conversational interface that provides accurate, step-by-step guidance for Shenzhen government services through natural language interaction.

## Prerequisites

### Development Environment
- Docker and Docker Compose
- Python 3.12+ for application 、

### Infrastructure Services
- PostgreSQL 15+ for database
- Milvus 2.3+ for vector search
- Redis 7+ for caching

### API Keys
- Deepseek API key for AI conversation
- (Optional) External government API credentials

## Getting Started

### 1. Infrastructure Setup

```bash
# Start all infrastructure services using Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected services:
- PostgreSQL (port 5432)
- Milvus (port 19530)
- Redis (port 6379)

### 2. Application Setup

```bash
# Clone and setup application
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using Poetry
poetry install

# Environment configuration
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL
# - REDIS_URL
# - DEEPSEEK_API_KEY
# - MILVUS_URL
# - MILVUS_TOKEN
# - SECRET_KEY

# Database setup
python -m scripts.setup_database

# Vector database setup
python -m scripts.setup_vector_db

# Run Chainlit application
chainlit run src/chainlit/app.py --host 0.0.0.0 --port 8001
```

### 3. Verify Setup

1. **Infrastructure Health Check**:
   ```bash
   # Check all services are running
   docker-compose ps
   ```

2. **Application Health Check**:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Should return: {"status": "healthy", "dependencies": {"postgresql": "connected", "milvus": "connected", "redis": "connected"}}
   ```

3. **Chainlit Interface Access**:
   - Open http://localhost:8000 in your browser
   - You should see the City Guide Smart Assistant interface

4. **API Documentation**:
   - Access Swagger UI: http://localhost:8000/docs
   - Access Milvus Web UI: http://localhost:9091/webui/

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

### Application Development

1. **Run Tests**:
   ```bash
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

4. **Chainlit Development**:
   ```bash
   # Run in development mode with hot reload
   chainlit run src/chainlit/app.py --watch
   ```

## Configuration

### Application Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/cityguide

# Redis
REDIS_URL=redis://localhost:6379

# AI & Vector Database
DEEPSEEK_API_KEY=your_deepseek_key
MILVUS_URL=http://localhost:19530
MILVUS_TOKEN=your_milvus_token
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B

# Security
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# External APIs
GOVERNMENT_API_BASE_URL=https://api.shenzhen.gov.cn
GOVERNMENT_API_KEY=your_government_key

# Chainlit Configuration
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8001
```

## Testing

### Application Testing Strategy

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests
pytest tests/contract/

# Performance tests
pytest tests/performance/

# Chainlit UI tests
pytest tests/chainlit/

# All tests with coverage
pytest --cov=src --cov-report=html
```

## Deployment

### Application Deployment

1. **Build Docker Image**:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app

   # Install Poetry using the official installer
   RUN pip install poetry

   # Copy dependency files
   COPY pyproject.toml poetry.lock ./

   # Configure Poetry to not create virtual environment (use system Python)
   RUN poetry config virtualenvs.create false

   # Install dependencies using Poetry
   RUN poetry install --no-dev

   COPY . .
   CMD ["chainlit", "run", "src/chainlit/app.py", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Deploy to Production**:
   ```bash
   docker build -t cityguide-app .
   docker run -p 8000:8000 --env-file .env cityguide-app
   ```

## Monitoring & Observability

### Application Metrics

- Response time metrics
- Error rate monitoring
- Database connection pool status
- External API health checks
- Chainlit conversation analytics
- User interaction patterns
- Search performance metrics

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
   - Verify MILVUS_URL and MILVUS_TOKEN are set
   - Check Milvus server is running
   - Test vector database connection
   - Ensure Qwen3-Embedding-0.6B model is accessible

### Debug Mode

Enable debug logging:

```bash
# Backend
LOG_LEVEL=DEBUG

# Frontend
REACT_APP_DEBUG=true
```

## Support

- **Application Issues**: Check application logs at `/var/log/cityguide/app.log`
- **Chainlit Issues**: Check browser developer console
- **API Issues**: Review API documentation at `/docs` endpoint
- **Database Issues**: Check PostgreSQL logs

## Next Steps

1. **Add More Services**: Extend service categories with additional government services
2. **Multi-language Support**: Add support for more languages
3. **Mobile App**: Develop native mobile applications
4. **Advanced Analytics**: Implement detailed usage analytics
5. **Integration**: Connect with more external government APIs
