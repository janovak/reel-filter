# Reel-Filter — Movie Content-Aware Search

A web application for searching and filtering movies based on **content tolerance thresholds** (sex/nudity, violence/gore, language/profanity on a 0-10 scale) alongside traditional criteria (genre, ratings, year, awards).

## ✅ Features

- **Content filtering**: Set personal tolerance levels (0-10) for sex, violence, and language — only see movies within your limits
- **Traditional search**: Filter by title, genre, year range, MPAA rating, and minimum quality ratings (IMDb, Rotten Tomatoes, Metacritic)
- **Awards filtering**: Filter by minimum number of awards won
- **Movie detail pages**: Full metadata, plot, cast, all rating sources, awards, and visual content score bars
- **Color-coded badges**: Green (within threshold), red (exceeds), gray (no limit set)
- **Mobile responsive**: Collapsible filter drawer, touch-friendly controls (44px targets), responsive grid
- **Session persistence**: Filters persist during your browser session
- **Health monitoring**: `/api/health` endpoint with database and refresh status
- **Performance logging**: Slow query warnings (>500ms), request timing headers
- **Data integration**: OMDb API client, Kids-in-Mind scraper, exact title/year matching, Celery weekly refresh

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ and Node.js 18+ for local development

### Using Docker Compose (recommended)

```bash
git clone <repository-url>
cd reel-filter

# Create environment file
cp backend/.env.example backend/.env
# Edit backend/.env and set your OMDB_API_KEY

# Start all services
docker-compose up -d

# Seed sample data
docker-compose exec backend python scripts/manual_refresh.py --seed
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL and Redis via Docker
docker-compose up -d db redis
python src/main.py
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

**Seed test data:**
```bash
cd backend
python scripts/manual_refresh.py --seed
```

## 📁 Project Structure

```
reel-filter/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/         # movies, metadata, health endpoints
│   │   │   ├── schemas/        # Pydantic request/response models
│   │   │   └── middleware/     # error handling, logging, performance
│   │   ├── database/           # SQLAlchemy engine, session, base
│   │   ├── models/             # Movie, ContentScore, DataRefreshLog
│   │   ├── services/           # SearchService, MovieService
│   │   ├── integrations/       # OMDb client, KIM scraper
│   │   ├── jobs/               # Celery app, weekly refresh tasks
│   │   └── main.py
│   ├── scripts/                # seed_test_data, manual_refresh
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # SearchBar, FilterPanel, MovieCard, ContentBadge,
│   │   │                       # LoadingSpinner, ErrorBoundary, ScoreLegend
│   │   ├── pages/              # SearchPage, MovieDetail
│   │   ├── services/           # API client with error handling
│   │   ├── hooks/              # useFilters (session storage)
│   │   └── types/              # TypeScript interfaces
│   └── package.json
├── specs/                      # Feature specifications and contracts
├── docker-compose.yml
└── README.md
```

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic |
| Database | PostgreSQL 15 (GIN indexes, ARRAY, JSONB, full-text search) |
| Task Queue | Celery + Redis 7 |
| Frontend | React 18, TypeScript, Tailwind CSS 3, Vite 5 |
| HTTP | Axios (frontend), httpx (backend) |
| Scraping | BeautifulSoup4 + lxml |
| Matching | Exact title + year match (SQL) |
| Retry | tenacity (exponential backoff) |

## 📊 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/movies/search` | Search with filters (content, genre, year, ratings, awards) |
| GET | `/api/movies/{id}` | Full movie details with content scores |
| GET | `/api/genres` | List available genres |
| GET | `/api/health` | Health check (DB status, last refresh) |

**Search parameters:** `q`, `genres[]`, `year_min`, `year_max`, `mpaa_ratings[]`, `imdb_min`, `rt_min`, `metacritic_min`, `awards_min`, `sex_max`, `violence_max`, `language_max`, `page`, `per_page`

## 🔐 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...@localhost:5432/reel_filter` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery |
| `OMDB_API_KEY` | — | OMDb API key (required for data refresh) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed origins |
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Frontend API URL |

## 📝 Content Score Scale

| Score | Label | Color |
|-------|-------|-------|
| 0 | None | Gray |
| 1–2 | Mild | Green |
| 3–4 | Moderate | Yellow |
| 5–6 | Strong | Orange |
| 7–8 | Intense | Red |
| 9–10 | Extreme | Dark Red |

## 📄 License

[Your License Here]
