# scripts/init_db.py
import os
import sys
from pathlib import Path
import alembic.config

def main():
    # Get the directory containing this script
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Change to the project root directory
    os.chdir(project_root)

    # Initialize Alembic if not already initialized
    if not os.path.exists("alembic"):
        os.system("alembic init alembic")

    # Run Alembic migrations
    alembicArgs = [
        '--raiseerr',
        'upgrade', 'head',
    ]
    alembic.config.main(argv=alembicArgs)

if __name__ == "__main__":
    main()