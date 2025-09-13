# Ghostworks Docker Compose Management
.PHONY: help build up down logs clean restart status health

# Default target
help: ## Show this help message
	@echo "Ghostworks Docker Compose Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
build: ## Build all services
	docker-compose build

up: ## Start all services in development mode
	docker-compose up -d

up-logs: ## Start all services and show logs
	docker-compose up

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

restart: ## Restart all services
	docker-compose restart

status: ## Show status of all services
	docker-compose ps

# Production commands
prod-build: ## Build all services for production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Start all services in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Individual service commands
api: ## Start only API service and dependencies
	docker-compose up -d postgres redis api

web: ## Start only web service and dependencies
	docker-compose up -d api web

worker: ## Start only worker service and dependencies
	docker-compose up -d postgres redis worker

observability: ## Start only observability stack
	docker-compose up -d prometheus grafana otelcol

# Health and monitoring
health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "API Health:"
	@curl -s http://localhost:8000/api/v1/health || echo "API not responding"
	@echo ""
	@echo "Web Health:"
	@curl -s http://localhost:3000/health || echo "Web not responding"
	@echo ""
	@echo "Prometheus Health:"
	@curl -s http://localhost:9090/-/healthy || echo "Prometheus not responding"
	@echo ""
	@echo "Grafana Health:"
	@curl -s http://localhost:3001/api/health || echo "Grafana not responding"

# Database commands
db-migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	docker-compose exec api alembic upgrade head

# Demo data commands
seed-demo: ## Seed demo data to existing database
	docker-compose exec api python scripts/seed_only.py

reset-demo: ## Reset database and seed fresh demo data (WARNING: destroys all data)
	docker-compose exec api python scripts/reset_demo_environment.py --force

reset-demo-interactive: ## Reset database with confirmation prompt
	docker-compose exec api python scripts/reset_demo_environment.py

init-demo: ## Initialize database and seed demo data (for first setup)
	docker-compose exec api python scripts/init_db.py
	docker-compose exec api python scripts/seed_only.py

validate-demo: ## Check if demo data exists in database
	docker-compose exec api python scripts/validate_demo_data.py

test-demo-scripts: ## Test demo data scripts functionality
	docker-compose exec api python scripts/test_demo_scripts.py

# Cleanup commands
clean: ## Remove all containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Remove everything including images
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af

# Development helpers
shell-api: ## Open shell in API container
	docker-compose exec api bash

shell-worker: ## Open shell in worker container
	docker-compose exec worker bash

shell-web: ## Open shell in web container
	docker-compose exec web sh

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d ghostworks

# Monitoring shortcuts
metrics: ## Open Prometheus metrics
	@echo "Opening Prometheus at http://localhost:9090"
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "Please open http://localhost:9090"

dashboards: ## Open Grafana dashboards
	@echo "Opening Grafana at http://localhost:3001 (admin/admin)"
	@open http://localhost:3001 2>/dev/null || xdg-open http://localhost:3001 2>/dev/null || echo "Please open http://localhost:3001"

flower: ## Open Celery Flower monitoring
	@echo "Opening Flower at http://localhost:5555"
	@open http://localhost:5555 2>/dev/null || xdg-open http://localhost:5555 2>/dev/null || echo "Please open http://localhost:5555"