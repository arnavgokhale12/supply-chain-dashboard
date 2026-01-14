"""Composite index API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models.indicator_config import IndicatorConfig
from backend.app.services.composite_calculator import (
    WINDOW,
    calculate_composite_history,
    calculate_composite_latest,
)

router = APIRouter(prefix="/v1/composite", tags=["composite"])


@router.get("/latest")
def latest(db: Session = Depends(get_db)):
    """
    Get the latest composite index value with all indicator details.

    Returns:
    - month: Current month (YYYY-MM)
    - {indicator_id}: For each indicator, contains date, value, z_score, regime
    - composite: Overall score and regime
    - meta: Window size, aligned months count, indicator count
    """
    return calculate_composite_latest(db)


@router.get("/history")
def history(db: Session = Depends(get_db)):
    """
    Get historical composite index values.

    Returns list of monthly records with:
    - month: Month (YYYY-MM)
    - {indicator_id}_z: Z-score for each indicator
    - composite: Composite score
    - regime: Composite regime classification
    """
    return calculate_composite_history(db)


@router.get("/indicators")
def list_indicators(db: Session = Depends(get_db)):
    """
    List all configured indicators and their composite participation status.

    Returns list of indicators with:
    - series_id: Indicator identifier
    - include_in_composite: Whether it's included in composite calculation
    - weight: Weight in composite calculation
    - invert_sign: Whether z-score sign is inverted
    - display_order: Display order in UI
    """
    configs = db.query(IndicatorConfig).order_by(IndicatorConfig.display_order).all()
    return [
        {
            "series_id": c.series_id,
            "include_in_composite": c.include_in_composite,
            "weight": c.weight,
            "invert_sign": c.invert_sign,
            "display_order": c.display_order,
        }
        for c in configs
    ]
