#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Initialize alembic if migrations directory doesn't exist
if [ ! -d "/app/migrations" ]; then
    echo "Initializing Alembic..."
    alembic init migrations
fi

# Create initial migration if no migrations exist
if [ ! -d "/app/migrations/versions" ] || [ -z "$(ls -A /app/migrations/versions)" ]; then
    echo "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Apply migrations
echo "Applying migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload