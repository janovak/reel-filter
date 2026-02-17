# reel-filter Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-23

## Active Technologies

**Backend (001-movie-content-search)**:
- Python 3.11+ with FastAPI web framework
- SQLAlchemy 2.0+ ORM
- PostgreSQL 15+ database
- Celery + Redis (async task queue for weekly refresh)
- httpx (async HTTP client)
- BeautifulSoup4 + lxml (web scraping)
- RapidFuzz (fuzzy string matching)
- Pydantic (data validation)

**Frontend (001-movie-content-search)**:
- React 18+ with TypeScript
- Tailwind CSS 3.0+ (utility-first CSS)
- React Router 6+ (client-side routing)
- Axios (HTTP client)
- Vite (build tool)

**Testing**:
- Backend: pytest + responses + openapi-spec-validator
- Frontend: Vitest + React Testing Library + Playwright

## Project Structure

```text
backend/
├── app/
│   ├── models/              # SQLAlchemy ORM models
│   ├── services/            # Business logic
│   ├── api/                 # REST API routes
│   ├── integrations/        # OMDb API + Kids-in-Mind scraper
│   ├── database/            # Database setup + migrations
│   └── jobs/                # Celery scheduled tasks
└── tests/

frontend/
├── src/
│   ├── components/          # React components
│   ├── pages/               # Page components
│   ├── services/            # API client
│   ├── hooks/               # Custom React hooks
│   └── types/               # TypeScript types
└── tests/

specs/
└── 001-movie-content-search/
    ├── spec.md              # Feature specification
    ├── plan.md              # Implementation plan
    ├── research.md          # Technology research
    ├── data-model.md        # Database design
    ├── quickstart.md        # Developer setup guide
    └── contracts/
        └── api.yaml         # OpenAPI specification
```

## Commands

**Backend**:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload  # Start dev server
pytest  # Run tests
alembic upgrade head  # Apply migrations
celery -A app.jobs.celery_app worker --beat --loglevel=info  # Start task queue
```

**Frontend**:
```bash
cd frontend
npm run dev  # Start dev server
npm test  # Run tests
npm run build  # Production build
```

## Code Style

**Python**:
- Use Black formatter (line length: 88)
- Use Ruff linter
- Type hints required (mypy)
- Follow PEP 8 conventions
- Async/await for I/O operations

**TypeScript/React**:
- ESLint + Prettier
- Functional components with hooks
- TypeScript strict mode
- Tailwind CSS for styling (avoid inline styles)

## API Design

- RESTful endpoints following OpenAPI 3.0 spec
- See `specs/001-movie-content-search/contracts/api.yaml`
- Base URL: `/api`
- Error responses follow RFC 7807 (Problem Details)

## Database

- PostgreSQL 15+ with SQLAlchemy ORM
- See `specs/001-movie-content-search/data-model.md` for schema
- Use Alembic for migrations
- Indexes on filtered fields (title FTS, genre GIN, ratings)

## Recent Changes

- 001-movie-content-search: Added Python FastAPI backend + React frontend for movie content-aware search with OMDb API + Kids-in-Mind integration

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
