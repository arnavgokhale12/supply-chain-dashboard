from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models.observation import Observation

router = APIRouter(prefix="/series", tags=["series"])


@router.get("/{series_id}/latest")
def latest(series_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(Observation)
        .filter(Observation.series_id == series_id)
        .order_by(Observation.date.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")

    return {
        "series_id": series_id,
        "date": row.date.isoformat(),
        "value": float(row.value),
    }
