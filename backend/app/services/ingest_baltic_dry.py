"""Ingest Baltic Dry Index from Nasdaq Data Link (Quandl)."""
from __future__ import annotations

from datetime import date

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.observation import Observation

QUANDL_DATASET = "LLOYDS/BDI"
LOCAL_SERIES_ID = "baltic_dry"


def fetch_quandl_series(dataset: str) -> list[tuple[str, float]]:
    """Fetch time series data from Nasdaq Data Link (Quandl)."""
    if not settings.quandl_api_key:
        raise RuntimeError("QUANDL_API_KEY missing in .env")

    url = f"https://data.nasdaq.com/api/v3/datasets/{dataset}/data.json"
    params = {
        "api_key": settings.quandl_api_key,
        "order": "asc",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    dataset_data = data.get("dataset_data", {})
    column_names = dataset_data.get("column_names", [])
    rows = dataset_data.get("data", [])

    # Find date and value column indices
    date_idx = 0  # Usually first column
    value_idx = 1  # Usually second column (or look for "Value" or "Index")

    for i, col in enumerate(column_names):
        if col.lower() == "date":
            date_idx = i
        elif col.lower() in ("value", "index", "close"):
            value_idx = i

    out: list[tuple[str, float]] = []
    for row in rows:
        date_str = row[date_idx]
        value = row[value_idx]
        if value is not None:
            out.append((date_str, float(value)))

    return out


def upsert_observations(db: Session, series_id: str, rows: list[tuple[str, float]]) -> int:
    """Insert new observations, skip existing ones."""
    existing_dates = {
        d for (d,) in db.execute(
            select(Observation.date).where(Observation.series_id == series_id)
        ).all()
    }

    to_add: list[Observation] = []
    for d_str, v in rows:
        d = date.fromisoformat(d_str)
        if d in existing_dates:
            continue
        to_add.append(Observation(series_id=series_id, date=d, value=v))

    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def main() -> None:
    """Ingest Baltic Dry Index data."""
    print(f"Fetching {QUANDL_DATASET}...")
    try:
        rows = fetch_quandl_series(QUANDL_DATASET)
        print(f"Fetched {len(rows)} observations")
    except Exception as e:
        print(f"Error fetching Baltic Dry Index: {e}")
        print("Note: Requires QUANDL_API_KEY in .env")
        return

    db = SessionLocal()
    try:
        n = upsert_observations(db, LOCAL_SERIES_ID, rows)
        total = db.query(Observation).filter(Observation.series_id == LOCAL_SERIES_ID).count()
        print(f"Ingested {n} new observations. Total now: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
