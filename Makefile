# City Guide Smart Assistant Makefile
# Common development commands for the project

.PHONY: help install setup test lint format clean docker-up docker-down docker-reset db-migrate db-upgrade db-downgrade run-dev run-prod

# Default target
help:
	@echo "City Guide Smart Assistant Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install dependencies using Poetry"
	@echo "  setup            Full project setup (install + database setup)"
	@echo ""
	@echo "Development:"
	@echo "  run-dev          Run development server with hot reload"
	@echo "  run-prod         Run production server"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run all linters (ruff, black, mypy)"
	@echo "  format           Format code with black and ruff"
	@echo "  check-types      Run type checking with mypy"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate       Create new migration"
	@echo "  db-upgrade       Apply all migrations"
	@echo "  db-downgrade     Rollback last migration"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up        Start all services with Docker Compose"
	@echo "  docker-down      Stop all services"
	@echo "  docker-reset     Reset all services (stop, remove volumes, start)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean            Clean up temporary files and caches"

# Setup commands
install:
	poetry install

setup: install docker-up
	@echo "Waiting for services to be ready..."
	sleep 10
	poetry run python -m scripts.setup_database
	poetry run python -m scripts.setup_vector_db
	@echo "Setup complete! Run 'make run-dev' to start the application"

# Development server commands
run-dev:
	poetry run chainlit run src/chainlit/app.py --watch

run-prod:
	poetry run chainlit run src/chainlit/app.py --host 0.0.0.0 --port 8000

# Testing commands
test:
	poetry run pytest tests/

test-unit:
	poetry run pytest tests/unit/

test-integration:
	poetry run pytest tests/integration/

test-coverage:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing tests/

# Code quality commands
lint:
	poetry run ruff check src/
	poetry run black --check src/
	poetry run mypy src/

format:
	poetry run black src/
	poetry run ruff --fix src/

check-types:
	poetry run mypy src/

# Database commands
db-migrate:
	@read -p "Enter migration message: " message; \
	poetry run alembic revision --autogenerate -m "$$message"

db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

# Docker commands
docker-up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "- PostgreSQL: localhost:5432"
	@echo "- Milvus: localhost:19530"
	@echo "- Redis: localhost:6379"
	@echo "- Milvus Web UI: localhost:3000"

docker-down:
	docker-compose down

docker-reset:
	docker-compose down -v
	docker-compose up -d
	@echo "All services have been reset"

# Cleanup commands
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "*.egg-info" -delete
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -delete
	find . -type f -name ".coverage" -delete
	@echo "Cleaned up temporary files and caches"

# Health check
health-check:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/api/v1/health || echo "Application not running"
	@docker-compose ps

# Development environment setup
dev-setup: install docker-up
	@echo "Development environment setup complete"
	@echo "Run 'make run-dev' to start the development server"

# Production preparation
build-prod:
	poetry install --only main
	docker build -t cityguide-app .

# Data management
data-load:
	poetry run python -m scripts.load_initial_data

data-reset:
	poetry run python -m scripts.reset_data

# Monitoring
logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

logs-db:
	docker-compose logs -f postgres
