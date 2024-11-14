# scripts/setup.py
import time
import sys
import subprocess
from pathlib import Path

def run_command(command, ignore_errors=False):
    """Run a command and return its success status"""
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error output: {e.stderr}")
            return False
        return True

def ensure_migrations_directory():
    """Ensure migrations directory exists with __init__.py"""
    migrations_path = Path("migrations")
    versions_path = migrations_path / "versions"
    
    migrations_path.mkdir(exist_ok=True)
    versions_path.mkdir(exist_ok=True)
    
    # Create __init__.py files
    (migrations_path / "__init__.py").touch()
    (versions_path / "__init__.py").touch()

def main():
    """Run the complete setup process"""
    print("Starting setup process...")
    
    # Clean and build
    print("\nCleaning and building containers...")
    commands = [
        "docker-compose down -v",
        "docker system prune -f",
        "docker-compose build",
        "docker-compose up -d",
    ]
    
    for cmd in commands:
        print(f"\nExecuting: {cmd}")
        if not run_command(cmd):
            print(f"Error executing: {cmd}")
            sys.exit(1)
    
    print("\nWaiting for services to be ready...")
    time.sleep(5)
    
    # Set up migrations
    print("\nSetting up database migrations...")
    ensure_migrations_directory()
    
    # Create and run migrations
    migration_commands = [
        'docker-compose exec -T api alembic revision --autogenerate -m "Initial_migration"',
        "docker-compose exec -T api alembic upgrade head"
    ]
    
    for cmd in migration_commands:
        print(f"\nExecuting: {cmd}")
        if not run_command(cmd):
            print(f"Error executing: {cmd}")
            sys.exit(1)
    
    # Initialize data
    print("\nInitializing database data...")
    if not run_command("docker-compose exec -T api python scripts/manage_db.py init --force"):
        print("Error initializing database data")
        sys.exit(1)
    
    print("\nSetup completed successfully!")

if __name__ == "__main__":
    main()