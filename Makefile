.PHONY: help build up down logs shell db-shell clean setup migrate init

# Default help command
help:
	@echo Available commands:
	@echo   make build     - Build containers
	@echo   make up        - Start containers
	@echo   make down      - Stop containers
	@echo   make logs      - View logs
	@echo   make shell     - Open API container shell
	@echo   make db-shell  - Open database shell
	@echo   make clean     - Remove containers and volumes
	@echo   make setup     - Complete setup (clean, build, migrate, init)

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec api bash

db-shell:
	docker-compose exec db psql -U postgres adeo_services

clean:
	docker-compose down -v
	docker system prune -f

# Setup using Python script
setup:
	python scripts/setup.py

# Individual database commands
migrate:
	docker-compose exec api alembic upgrade head

init:
	docker-compose exec api python scripts/manage_db.py init --force

