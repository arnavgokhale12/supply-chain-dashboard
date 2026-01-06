from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models.observation import Observation

router = APIRouter(prefix="/observations", tags=["observations"])

@router.get("")
def list_observations(
    series_id: str = Query(...),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Observation).filter(Observation.series_id == series_id)
    if start:
        q = q.filter(Observation.date >= start)
    if end:
        q = q.filter(Observation.date <= end)
    q = q.order_by(Observation.date.asc())
    rows = q.all()
    return [{"date": r.date.isoformat(), "value": r.value} for r in rows]
