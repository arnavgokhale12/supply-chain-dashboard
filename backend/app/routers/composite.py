from __future__ import annotations

from datetime import date, datetime
CASS_SERIES_ID = "cass"
from statistics import mean, pstdev

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models.observation import Observation

router = APIRouter(prefix="/v1/composite", tags=["composite"])

WINDOW = 36  # months


def zscore(xs: list[float], x: float) -> float:
    mu = mean(xs)
    sd = pstdev(xs)
    if sd < 1e-6:
        return 0.0
    return (x - mu) / sd


def regime(z: float) -> str:
    if z < -0.5:
        return "low"
    if z < 0.5:
        return "normal"
    if z < 1.5:
        return "elevated"
    return "crisis"


def to_month(d: date | datetime) -> str:
    if isinstance(d, datetime):
        d = d.date()
    return f"{d.year:04d}-{d.month:02d}"


def get_series(db: Session, series_id: str) -> list[Observation]:
    return (
        db.query(Observation)
        .filter(Observation.series_id == series_id)
        .order_by(Observation.date.asc())
        .all()
    )


def series_month_map(obs: list[Observation]) -> dict[str, Observation]:
    """
    Map YYYY-MM -> Observation.
    If multiple observations exist in a month, keep the latest date in that month.
    """
    m: dict[str, Observation] = {}
    for o in obs:
        k = to_month(o.date)
        if (k not in m) or (o.date > m[k].date):
            m[k] = o
    return m


@router.get("/latest")
def latest(db: Session = Depends(get_db)):
    g_obs = get_series(db, "gscpi")
    r_obs = get_series(db, "retailirsa")
    c_obs = get_series(db, "cass")

    g_map = series_month_map(g_obs)
    r_map = series_month_map(r_obs)
    c_map = series_month_map(c_obs)

    common_months = sorted(set(g_map.keys()) & set(r_map.keys()) & set(c_map.keys()))
    if len(common_months) < WINDOW:
        return {"error": "not enough aligned data", "aligned_months": len(common_months)}

    window_months = common_months[-WINDOW:]
    m = window_months[-1]

    g_vals = [float(g_map[k].value) for k in window_months]
    r_vals = [float(r_map[k].value) for k in window_months]
    c_vals = [float(c_map[k].value) for k in window_months]

    g_latest = float(g_map[m].value)
    r_latest = float(r_map[m].value)

    c_latest = float(c_map[m].value)
    g_z = zscore(g_vals, g_latest)
    r_z = zscore(r_vals, r_latest)

    c_z = zscore(c_vals, c_latest)
    comp = (g_z + r_z + c_z) / 3

    return {
        "month": m,
        "gscpi": {
            "date": str(g_map[m].date),
            "value": g_latest,
            "z_score": round(g_z, 3),
            "regime": regime(g_z),
        },
        "retailirsa": {
            "date": str(r_map[m].date),
            "value": r_latest,
            "z_score": round(r_z, 3),
            "regime": regime(r_z),
        },
        "cass": {
            "date": str(c_map[m].date),
            "value": c_latest,
            "z_score": round(c_z, 3),
            "regime": regime(c_z),
        },
        "composite": {"score": round(comp, 3), "regime": regime(comp)},
        "meta": {"window": WINDOW, "aligned_months": len(common_months)},
    }


@router.get("/history")
def history(db: Session = Depends(get_db)):
    g_map = series_month_map(get_series(db, "gscpi"))
    r_map = series_month_map(get_series(db, "retailirsa"))
    c_map = series_month_map(get_series(db, "cass"))

    common_months = sorted(set(g_map.keys()) & set(r_map.keys()) & set(c_map.keys()))
    if len(common_months) < WINDOW:
        return {"error": "not enough aligned data", "aligned_months": len(common_months)}

    out = []
    for i in range(WINDOW - 1, len(common_months)):
        window = common_months[i - (WINDOW - 1) : i + 1]
        m = common_months[i]

        g_vals = [float(g_map[k].value) for k in window]
        r_vals = [float(r_map[k].value) for k in window]
        c_vals = [float(c_map[k].value) for k in window]

        g_z = zscore(g_vals, float(g_map[m].value))
        r_z = zscore(r_vals, float(r_map[m].value))
        c_z = zscore(c_vals, float(c_map[m].value))
        comp = (g_z + r_z + c_z) / 3

        out.append(
            {
                "month": m,
                "gscpi_z": round(g_z, 3),
                "retailirsa_z": round(r_z, 3),
        "cass_z": round(c_z, 3),
                "composite": round(comp, 3),
                "regime": regime(comp),
            }
        )

    return out
