"""Ingest multiple supply chain indicators from FRED."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.observation import Observation
from backend.app.services.fred import fetch_fred_series

# FRED indicators to ingest
FRED_INDICATORS = [
    {"local_id": "ism_supplier", "fred_id": "MANEMP", "name": "Manufacturing Employment (ISM proxy)"},
    {"local_id": "mfg_new_orders", "fred_id": "NEWORDER", "name": "Manufacturing New Orders"},
    {"local_id": "wholesale_ratio", "fred_id": "ISRATIO", "name": "Wholesale Inventories/Sales Ratio"},
]


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


def ingest_indicator(db: Session, local_id: str, fred_id: str) -> int:
    """Ingest a single FRED indicator."""
    try:
        rows = fetch_fred_series(fred_id)
        return upsert_observations(db, local_id, rows)
    except Exception as e:
        print(f"Error ingesting {local_id} ({fred_id}): {e}")
        return 0


def main() -> None:
    """Ingest all FRED indicators."""
    db = SessionLocal()
    try:
        total_new = 0
        for indicator in FRED_INDICATORS:
            local_id = indicator["local_id"]
            fred_id = indicator["fred_id"]
            name = indicator["name"]

            n = ingest_indicator(db, local_id, fred_id)
            count = db.query(Observation).filter(Observation.series_id == local_id).count()
            print(f"{name}: +{n} new, {count} total")
            total_new += n

        print(f"\nTotal new observations: {total_new}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
