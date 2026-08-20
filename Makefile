# AegisGraph Makefile
# Common development and deployment tasks

.PHONY: help seed run-api run-web test eval verify-audit diagrams clean

# Default target
help:
	@echo "AegisGraph - Decision Intelligence Demo"
	@echo ""
	@echo "Available targets:"
	@echo "  seed           - Generate synthetic data (100 entities, ~15k observations)"
	@echo "  run-api        - Start FastAPI backend on port 8000"
	@echo "  run-web        - Start Next.js frontend on port 3000"
	@echo "  dev            - Run both API and frontend (background)"
	@echo "  test           - Run pytest test suite"
	@echo "  eval           - Run evaluation and print metrics"
	@echo "  verify-audit   - Verify audit chain integrity"
	@echo "  diagrams       - Export Mermaid diagrams to SVG"
	@echo "  clean          - Remove generated files and database"
	@echo ""

# Seed the database with synthetic data
seed:
	@echo "Seeding database..."
	python scripts/seed_demo.py --seed 42

# Start the API server
run-api:
	@echo "Starting FastAPI backend..."
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start the web frontend
run-web:
	@echo "Starting Next.js frontend..."
	cd frontend && npm run dev

# Run both in background
dev:
	@echo "Starting development environment..."
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Press Ctrl+C to stop all services"

# Run tests
test:
	@echo "Running tests..."
	cd backend && python -m pytest tests/ -v --tb=short

# Run tests with coverage
coverage:
	@echo "Running tests with coverage..."
	cd backend && python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Run evaluation
eval:
	@echo "Running evaluation..."
	python scripts/eval_demo.py --format markdown

# Save evaluation results
eval-save:
	python scripts/eval_demo.py --format markdown --output docs/EVALUATION_RESULTS.md

# Verify audit chain
verify-audit:
	@echo "Verifying audit chain..."
	python scripts/verify_audit.py

# Export diagrams
diagrams:
	@echo "Exporting diagrams..."
	python scripts/export_diagrams.py

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r backend/requirements.txt
	@echo "Installing Node.js dependencies..."
	cd frontend && npm install

# Create database directory
db-dir:
	@mkdir -p db

# Clean generated files
clean:
	@echo "Cleaning..."
	rm -rf __pycache__ */__pycache__ .pytest_cache
	rm -rf backend/.coverage backend/htmlcov
	rm -f aegisgraph.db aegisgraph*.db
	rm -f db/*.db
	rm -rf frontend/.next frontend/node_modules
	@echo "Clean complete."

# Lint code
lint:
	@echo "Linting Python code..."
	flake8 backend/ --max-line-length=100 --ignore=E501,W503
	@echo "Linting TypeScript code..."
	cd frontend && npm run lint

# Format code
format:
	@echo "Formatting Python code..."
	black backend/ --line-length 100
	isort backend/
	@echo "Formatting TypeScript code..."
	cd frontend && npm run format

# Security check
security:
	@echo "Running security check..."
	bandit -r backend/ -ll

# Build for production
build:
	@echo "Building frontend..."
	cd frontend && npm run build

# Docker targets (TODO)
docker-build:
	@echo "Building Docker image..."
	docker build -t aegisgraph:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 -p 3000:3000 aegisgraph:latest

docker-compose:
	@echo "Starting with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker Compose..."
	docker-compose down

# Show this help
.DEFAULT_GOAL := help
