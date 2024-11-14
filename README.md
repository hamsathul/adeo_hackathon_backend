Here is the updated README file considering the provided Makefile:

# Abu Dhabi Government Services API

A FastAPI backend service for streamlining Abu Dhabi government services.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- PostgreSQL (if using database features)
- Docker and Docker Compose (for running the application in containers)

## Project Setup

1. Clone the repository
```bash
git clone https://github.com/hamsathul/adeo_hackathon_backend.git
cd adeo_hackathon_backend
```

2. (Optional) Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file
```bash
# Copy the example environment file
cp .env.example .env

# Edit `.env` with your settings
nano .env
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```plaintext
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running the Application

### Using Docker Compose

Complete Setup

```bash
make setup
```

Step by step build

1. Build the Docker containers:
```bash
make build
```

2. Start the containers:
```bash
make up
```

3. The API will be available at:
- Main API: http://localhost:8000
- Interactive documentation (Swagger): http://localhost:8000/docs
- Alternative documentation (ReDoc): http://localhost:8000/redoc

### Using Python Directly

1. Make sure your virtual environment is activated (if using one)

2. Start the server:
```bash
uvicorn app.main:app --reload
```

3. The API will be available at:
- Main API: http://localhost:8000
- Interactive documentation (Swagger): http://localhost:8000/docs
- Alternative documentation (ReDoc): http://localhost:8000/redoc

## Common Make Commands

```
make help           # Show available commands
make build          # Build containers
make up             # Start containers
make down           # Stop containers
make logs           # View logs
make shell          # Open API container shell
make db-shell       # Open database shell
make clean          # Remove containers and volumes
make setup          # Complete setup (clean, build, migrate, init)
make migrate        # Run database migrations
make init           # Initialize the database
```

## Project Structure

```
adeo_hackathon_backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   ├── dependencies/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── request.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── request.py
├── tests/
├── alembic/
├── requirements.txt
├── .env
├── README.md
├── Makefile
├── docker-compose.yml
├── scripts/
│   ├── setup.py
│   ├── manage_db.py
```

## API Endpoints

- `GET /`: Welcome message and API status
- `GET /hello/{name}`: Test endpoint with path parameter
- Additional endpoints documented in Swagger UI

## Development

### Adding New Dependencies

When adding new packages:
```bash
pip install package-name
pip freeze > requirements.txt
```

### Database Migrations

If using database:
```bash
# Initialize migrations
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

### Running Tests

```bash
pytest
```

## Common Issues and Solutions

1. **Port already in use**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

2. **Module not found errors**
- Ensure virtual environment is activated
- Reinstall dependencies:
```bash
pip install -r requirements.txt
```

3. **Environment variables not loading**
- Check if `.env` file exists
- Verify file permissions
- Ensure variables are correctly formatted

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request