# CHS Backend - FastAPI Project

A FastAPI backend application with PostgreSQL database, containerized with Docker.

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)

### Environment Variables
1. Copy `.env.example` to `.env`
2. Fill in your actual values:
   ```bash
   cp .env.example .env
   ```

### Running with Docker
```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

### Local Development
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn main:app --reload
```

## Project Structure
```
chs-backend/
├── app/                 # Application modules
├── alembic/            # Database migrations
├── .env.example        # Environment variables template
├── docker-compose.yml  # Docker services configuration
├── Dockerfile         # Container build instructions
├── main.py           # FastAPI application entry point
└── requirements.txt  # Python dependencies
```

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
