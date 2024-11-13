
# Abu Dhabi Government Services API

A FastAPI backend service for streamlining Abu Dhabi government services.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- PostgreSQL (if using database features)

## Project Setup

1. Clone the repository
```bash
git clone https://github.com/hamsathul/adeo_hackathon_backend.git
cd adeo_hackathon_backend
```

2. Create a virtual environment
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

3. Activate the virtual environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Create .env file
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
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

1. Make sure your virtual environment is activated

2. Start the server:
```bash
uvicorn app.main:app --reload
```

3. The API will be available at:
- Main API: http://localhost:8000
- Interactive documentation (Swagger): http://localhost:8000/docs
- Alternative documentation (ReDoc): http://localhost:8000/redoc

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
- Check if .env file exists
- Verify file permissions
- Ensure variables are correctly formatted

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request

