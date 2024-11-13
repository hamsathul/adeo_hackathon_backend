# Makefile for FastAPI and PostgreSQL Docker setup

.PHONY: help build up down logs ps shell db-shell clean restart status test lint

# Default target when running just 'make'
help:
	@echo "Available commands:"
	@echo "  make build         - Build all containers"
	@echo "  make up           - Start all containers in detached mode"
	@echo "  make down         - Stop all containers"
	@echo "  make restart      - Restart all containers"
	@echo "  make logs         - View logs of all containers"
	@echo "  make ps           - List running containers"
	@echo "  make shell        - Open shell in API container"
	@echo "  make db-shell     - Open psql shell in database container"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make status       - Show status of containers"
	@echo "  make db-backup    - Backup the database"
	@echo "  make db-restore   - Restore the database from backup"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"

# Build containers
build:
	docker-compose build

# Start containers
up:
	docker-compose up -d

# Build and start containers
up-build:
	docker-compose up -d --build

# Stop containers
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Show running containers
ps:
	docker-compose ps

# Shell into API container
shell:
	docker-compose exec api bash

# Shell into database with psql
db-shell:
	docker-compose exec db psql -U postgres abu_dhabi_services

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Restart all containers
restart:
	docker-compose down
	docker-compose up -d

# Show status of containers
status:
	@echo "=== Container Status ==="
	@docker-compose ps
	@echo "\n=== Container Stats ==="
	@docker stats --no-stream $(docker-compose ps -q)

# Database operations
db-backup:
	@echo "Creating database backup..."
	@docker-compose exec -T db pg_dump -U postgres abu_dhabi_services > backup/$(shell date +%Y%m%d_%H%M%S)_backup.sql
	@echo "Backup created in backup directory"

db-restore:
	@if [ -z "$(file)" ]; then \
		echo "Please specify a backup file: make db-restore file=backup/filename.sql"; \
	else \
		echo "Restoring database from $(file)..."; \
		docker-compose exec -T db psql -U postgres abu_dhabi_services < $(file); \
	fi

# Development commands
test:
	docker-compose exec api pytest

lint:
	docker-compose exec api flake8 .

# Production commands
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Development convenience commands
dev: down build up logs

# Watch logs for specific service
logs-api:
	docker-compose logs -f api

logs-db:
	docker-compose logs -f db

# Maintenance commands
prune:
	docker system prune -a

volumes:
	docker volume ls

networks:
	docker network ls

# Create backup directory if it doesn't exist
backup-dir:
	mkdir -p backup

rebuild: clean
	docker-compose up --build

fix-permissions:
	chmod +x docker/entrypoint.sh
	sed -i 's/\r$$//' docker/entrypoint.sh

# Database migrations
db-init:
	docker-compose exec api alembic init alembic

db-migrate:
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

db-upgrade:
	docker-compose exec api alembic upgrade head

db-downgrade:
	docker-compose exec api alembic downgrade -1

db-history:
	docker-compose exec api alembic history

db-current:
	docker-compose exec api alembic current