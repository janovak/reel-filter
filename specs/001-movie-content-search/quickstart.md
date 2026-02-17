# Reel-Filter Quickstart Guide

**Feature**: Movie Content-Aware Search  
**Last Updated**: 2025-01-23  
**Target Audience**: Developers setting up local development environment

---

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher (with npm)
- **PostgreSQL**: 15 or higher
- **Redis**: 7.0 or higher (for Celery task queue)
- **Git**: For version control

### Optional Tools

- **Docker**: For containerized PostgreSQL + Redis (recommended)
- **Postman/Insomnia**: For API testing
- **pgAdmin**: For database management

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for dependencies + database
- **OS**: Windows, macOS, or Linux

---

## Quick Setup (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/reel-filter.git
cd reel-filter
git checkout 001-movie-content-search
```

### 2. Start Infrastructure (Docker)

```bash
# Start PostgreSQL + Redis with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Docker Compose Configuration** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: reelfilter
      POSTGRES_USER: reelfilter
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your OMDb API key
# OMDB_API_KEY=your_api_key_here

# Run database migrations
alembic upgrade head

# Seed test data (optional)
python scripts/seed_test_data.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend should now be running at**: `http://localhost:8000`

**API Documentation**: `http://localhost:8000/docs` (Swagger UI)

### 4. Setup Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env if needed (default points to localhost:8000)
# VITE_API_BASE_URL=http://localhost:8000/api

# Start development server
npm run dev
```

**Frontend should now be running at**: `http://localhost:3000`

### 5. Verify Setup

Open browser to `http://localhost:3000` and:
1. Search for a movie (e.g., "Matrix")
2. Set content thresholds
3. Verify filter results update

---

## Detailed Setup

### Backend Setup

#### Environment Variables

Create `backend/.env` file:

```bash
# OMDb API Configuration
OMDB_API_KEY=your_api_key_here
OMDB_BASE_URL=http://www.omdbapi.com/

# Kids-in-Mind Scraper Configuration
KIM_BASE_URL=https://kids-in-mind.com
KIM_RATE_LIMIT=0.5  # Requests per second (1 req per 2 seconds)

# Database Configuration
DATABASE_URL=postgresql://reelfilter:dev_password@localhost:5432/reelfilter

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Fuzzy Matching Configuration
FUZZY_MATCH_AUTO_THRESHOLD=88
FUZZY_MATCH_REVIEW_THRESHOLD=75

# Weekly Refresh Schedule (Celery Beat)
REFRESH_CRON_DAY=sunday
REFRESH_CRON_HOUR=2
REFRESH_CRON_MINUTE=0
```

#### Dependencies

`backend/requirements.txt`:

```text
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# HTTP Client
httpx==0.26.0

# Web Scraping
beautifulsoup4==4.12.3
lxml==5.1.0

# Fuzzy Matching
rapidfuzz==3.6.1

# Task Queue
celery==5.3.6
redis==5.0.1

# Data Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
responses==0.24.1
openapi-spec-validator==0.7.1

# Development
black==24.1.1
ruff==0.1.13
mypy==1.8.0
```

#### Database Migrations

```bash
# Initialize Alembic (first time only)
cd backend
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# View migration history
alembic history

# Rollback migration
alembic downgrade -1
```

#### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_movie_service.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

#### Starting Celery Workers (Weekly Refresh)

```bash
cd backend

# Start Celery worker
celery -A app.jobs.celery_app worker --loglevel=info

# Start Celery Beat scheduler (separate terminal)
celery -A app.jobs.celery_app beat --loglevel=info

# Run both in single process (development only)
celery -A app.jobs.celery_app worker --beat --loglevel=info

# Trigger manual refresh (test)
celery -A app.jobs.celery_app call app.jobs.weekly_refresh.refresh_movie_data
```

---

### Frontend Setup

#### Environment Variables

Create `frontend/.env` file:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Feature Flags
VITE_ENABLE_URL_FILTERS=true
VITE_ENABLE_DEBUG_MODE=false

# Analytics (optional)
VITE_GA_TRACKING_ID=
```

#### Dependencies

`frontend/package.json`:

```json
{
  "name": "reel-filter-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,css,md}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "axios": "^1.6.5",
    "@tanstack/react-query": "^5.17.9"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.11",
    "typescript": "^5.3.3",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.33",
    "vitest": "^1.2.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0",
    "@playwright/test": "^1.40.1",
    "eslint": "^8.56.0",
    "prettier": "^3.1.1"
  }
}
```

#### Running Tests

```bash
cd frontend

# Run unit/component tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode
npm run test:e2e -- --headed

# Run specific E2E test
npm run test:e2e -- tests/search-workflow.spec.js
```

#### Building for Production

```bash
cd frontend

# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview

# Output will be in frontend/dist/
```

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Browser                           │
│  ┌──────────────┐                                               │
│  │  React App   │  (Port 3000)                                  │
│  │  - Search UI │                                               │
│  │  - Filters   │                                               │
│  │  - Results   │                                               │
│  └──────┬───────┘                                               │
└─────────┼───────────────────────────────────────────────────────┘
          │ HTTP/JSON
          ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  API Routes  │────→│   Services   │────→│   Database   │    │
│  │  /search     │     │  MovieSvc    │     │  PostgreSQL  │    │
│  │  /movies/:id │     │  SearchSvc   │     │   (Movies)   │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                     │                                 │
│         │                     ↓                                 │
│         │            ┌──────────────┐                           │
│         │            │ Integrations │                           │
│         │            │  - OMDb API  │                           │
│         │            │  - KIM Scrpr │                           │
│         │            └──────────────┘                           │
│         │                                                       │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ Celery Tasks │                                               │
│  │ Weekly Refsh │                                               │
│  └──────┬───────┘                                               │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────┐      ┌──────────────┐      ┌──────────────┐
│  Redis Queue    │      │  OMDb API    │      │Kids-in-Mind  │
│  (Celery)       │      │  (External)  │      │  (Scraping)  │
└─────────────────┘      └──────────────┘      └──────────────┘
```

### Directory Structure

```
reel-filter/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── movie.py
│   │   │   ├── content_score.py
│   │   │   └── data_refresh_log.py
│   │   ├── services/               # Business logic
│   │   │   ├── movie_service.py
│   │   │   ├── search_service.py
│   │   │   └── matching_service.py
│   │   ├── api/                    # API routes
│   │   │   ├── routes/
│   │   │   │   ├── movies.py       # /movies/* endpoints
│   │   │   │   ├── metadata.py     # /genres, etc.
│   │   │   │   └── health.py       # /health
│   │   │   └── middleware/
│   │   │       ├── error_handler.py
│   │   │       └── logging.py
│   │   ├── integrations/           # External API clients
│   │   │   ├── omdb_client.py
│   │   │   └── kim_scraper.py
│   │   ├── database/               # Database setup
│   │   │   ├── session.py          # SQLAlchemy session
│   │   │   └── base.py             # Base model
│   │   └── jobs/                   # Scheduled tasks
│   │       ├── celery_app.py
│   │       └── weekly_refresh.py
│   ├── alembic/                    # Database migrations
│   │   └── versions/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── scripts/
│   │   └── seed_test_data.py
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable components
│   │   │   ├── MovieCard.tsx
│   │   │   ├── ContentBadge.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   └── SearchBar.tsx
│   │   ├── pages/                  # Page components
│   │   │   ├── SearchPage.tsx
│   │   │   └── MovieDetail.tsx
│   │   ├── services/               # API client
│   │   │   └── api.ts
│   │   ├── hooks/                  # Custom React hooks
│   │   │   └── useFilters.ts
│   │   ├── types/                  # TypeScript types
│   │   │   └── api.types.ts
│   │   ├── styles/                 # Global styles
│   │   │   └── index.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   │   ├── components/
│   │   └── e2e/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
│
├── specs/
│   └── 001-movie-content-search/
│       ├── spec.md                 # Feature specification
│       ├── plan.md                 # Implementation plan
│       ├── research.md             # Technology research
│       ├── data-model.md           # Database design
│       ├── quickstart.md           # This file
│       └── contracts/
│           └── api.yaml            # OpenAPI spec
│
├── docker-compose.yml
└── README.md
```

---

## Common Development Tasks

### Database Operations

```bash
# Connect to PostgreSQL
psql -h localhost -U reelfilter -d reelfilter

# View tables
\dt

# Describe table
\d movies

# Query movies
SELECT title, year, imdb_rating FROM movies LIMIT 10;

# Check content scores
SELECT m.title, cs.sex_nudity, cs.violence_gore, cs.language_profanity
FROM movies m
JOIN content_scores cs ON m.id = cs.movie_id
LIMIT 10;

# Reset database
alembic downgrade base
alembic upgrade head
```

### Manual Data Refresh

```bash
cd backend

# Fetch movies from OMDb
python scripts/fetch_omdb_movies.py

# Scrape content scores from Kids-in-Mind
python scripts/scrape_kim_scores.py

# Run fuzzy matching
python scripts/match_content_scores.py

# Full refresh (all steps)
python scripts/full_refresh.py
```

### API Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Get genres
curl http://localhost:8000/api/genres

# Search movies
curl "http://localhost:8000/api/movies/search?q=matrix&sex_max=5&violence_max=6"

# Get movie details
curl http://localhost:8000/api/movies/{movie_id}
```

### Logs and Monitoring

```bash
# Backend logs (if running with uvicorn)
tail -f backend/logs/app.log

# Celery worker logs
tail -f backend/logs/celery.log

# PostgreSQL logs
docker logs reel-filter-postgres-1 -f

# Redis logs
docker logs reel-filter-redis-1 -f
```

---

## Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### Database connection error

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**: Verify PostgreSQL is running:
```bash
docker-compose ps
# If not running:
docker-compose up -d postgres
```

---

### OMDb API rate limit

**Problem**: `429 Too Many Requests` from OMDb API

**Solution**: 
1. Check API key tier limits
2. Reduce scraping frequency in `.env`:
   ```
   OMDB_RATE_LIMIT=0.1  # 1 request per 10 seconds
   ```

---

### Kids-in-Mind scraping fails

**Problem**: Content scores not being scraped

**Solution**:
1. Verify Kids-in-Mind is accessible: `curl https://kids-in-mind.com`
2. Check HTML structure hasn't changed (may need to update scraper selectors)
3. Reduce rate limit:
   ```
   KIM_RATE_LIMIT=0.25  # 1 request per 4 seconds
   ```

---

### Frontend can't reach API

**Problem**: Network error in browser console

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS origins in `backend/.env`:
   ```
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```
3. Verify frontend API URL in `frontend/.env`:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

---

## Next Steps

1. **Read Feature Spec**: Review `specs/001-movie-content-search/spec.md` for requirements
2. **Explore API**: Open `http://localhost:8000/docs` for interactive API documentation
3. **Run Tests**: Execute `pytest` (backend) and `npm test` (frontend) to verify setup
4. **Seed Data**: Run `python scripts/seed_test_data.py` for sample movies
5. **Review Code**: Start with `backend/app/api/routes/movies.py` and `frontend/src/pages/SearchPage.tsx`

---

## Support

- **Documentation**: See `specs/001-movie-content-search/` directory
- **API Reference**: `http://localhost:8000/docs` (Swagger UI)
- **Issues**: Check project issue tracker
- **Contributing**: See CONTRIBUTING.md (if available)

---

**Happy Coding!** 🎬
