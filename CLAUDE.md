# CLAUDE.md

## Project Overview

Supply Chain Dashboard - A web application that tracks supply-chain stress using a composite index built from macroeconomic indicators.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, SQLite
- **Frontend:** Streamlit, Pandas
- **Data Sources:** FRED API, NY Fed (Excel)

## Project Structure

```
backend/app/
├── core/config.py       # Settings via pydantic
├── db/                  # SQLAlchemy session, base, deps
├── models/              # Series and Observation ORM models
├── routers/             # API endpoints (health, series, observations, composite)
├── services/            # Data ingestion (GSCPI, Cass, Retail IR/SA, seed)
└── main.py              # FastAPI app

frontend/app.py          # Streamlit dashboard
```

## Key Commands

```bash
# Run backend
cd backend && uvicorn app.main:app --reload

# Run frontend
cd frontend && streamlit run app.py

# Database migrations
cd backend && alembic upgrade head

# Data ingestion (run from backend/)
python -m app.services.seed           # Initialize series metadata
python -m app.services.ingest_gscpi   # NY Fed GSCPI data
python -m app.services.ingest_cass    # FRED Cass Freight Index
python -m app.services.ingest_retailirsa  # FRED Retail Inventories
```

## Environment Variables

- `DATABASE_URL` - SQLite connection string (default: `sqlite:///./scdash.db`)
- `FRED_API_KEY` - Required for FRED API calls
- `API_BASE` - Backend URL for frontend (default: `http://127.0.0.1:8000`)

## API Endpoints

- `GET /health` - Health check
- `GET /series/{series_id}/latest` - Latest observation for a series
- `GET /observations?series_id=&start=&end=` - Historical observations
- `GET /v1/composite/latest` - Current composite score with z-scores
- `GET /v1/composite/history?window=365` - Historical composite index

## Composite Index Logic

- Combines 3 indicators: GSCPI, Retail IR/SA, Cass Freight Index
- Z-score normalization using 36-month rolling window
- Regime classification: `low` (<-0.5), `normal` (-0.5 to 0.5), `elevated` (0.5 to 1.5), `crisis` (>=1.5)

## Database Models

- **Series:** id (PK), name, frequency, source, url
- **Observation:** id (PK), series_id (FK), date, value
