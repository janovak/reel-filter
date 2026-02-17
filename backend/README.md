# Reel-Filter Backend

FastAPI backend for the Reel-Filter movie content-aware search application.

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your OMDb API key
   ```

4. Setup database:
   ```bash
   docker-compose up -d db redis
   alembic upgrade head
   python scripts/seed_test_data.py
   ```

5. Run development server:
   ```bash
   python src/main.py
   ```

API will be available at http://localhost:8000
API docs at http://localhost:8000/docs
