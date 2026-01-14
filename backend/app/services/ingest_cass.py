from __future__ import annotations

from backend.app.db.session import SessionLocal
from backend.app.models.observation import Observation
from backend.app.services.fred import fetch_fred_series
from datetime import datetime

# Cass Freight Index via FRED
FRED_SERIES_ID = "FRGSHPUSM649NCIS"  # Shipments
# FRED_SERIES_ID = "FRGEXPUSM649NCIS"  # Expenditures


def main() -> None:
    db = SessionLocal()
    try:
        series_id = "cass"
        rows = fetch_fred_series(FRED_SERIES_ID)  # list[tuple[str, float]]

        inserted = 0
        for (date, value) in rows:
            exists = (
                db.query(Observation)
                .filter(Observation.series_id == series_id, Observation.date == date)
                .first()
            )
            if exists:
                continue

            db.add(Observation(series_id=series_id, date=datetime.strptime(date, '%Y-%m-%d').date(), value=float(value)))
            inserted += 1

        db.commit()

        total = db.query(Observation).filter(Observation.series_id == series_id).count()
        print(f"Ingested {inserted} new observations. Total now: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()