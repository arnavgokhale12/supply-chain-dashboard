from __future__ import annotations
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.observation import Observation
from app.services.fred import fetch_fred_series

FRED_SERIES_ID = "RETAILIRSA"
LOCAL_SERIES_ID = "retailirsa"

def upsert_observations(db: Session, series_id: str, rows: list[tuple[str, float]]) -> int:
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
    rows = fetch_fred_series(FRED_SERIES_ID)
    db = SessionLocal()
    try:
        n = upsert_observations(db, LOCAL_SERIES_ID, rows)
        total = db.query(Observation).filter(Observation.series_id == LOCAL_SERIES_ID).count()
        print(f"Ingested {n} new observations. Total now: {total}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
