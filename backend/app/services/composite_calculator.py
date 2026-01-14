"""Dynamic composite index calculator supporting N indicators."""
from __future__ import annotations

from datetime import date, datetime
from statistics import mean, pstdev
from typing import NamedTuple

from sqlalchemy.orm import Session

from backend.app.models.indicator_config import IndicatorConfig
from backend.app.models.observation import Observation

WINDOW = 36  # months


class IndicatorResult(NamedTuple):
    series_id: str
    date: date
    value: float
    z_score: float
    regime: str
    weight: float


def zscore(xs: list[float], x: float) -> float:
    """Calculate z-score of x given a list of values."""
    if len(xs) < 2:
        return 0.0
    mu = mean(xs)
    sd = pstdev(xs)
    if sd < 1e-6:
        return 0.0
    return (x - mu) / sd


def regime(z: float) -> str:
    """Classify z-score into regime."""
    if z < -0.5:
        return "low"
    if z < 0.5:
        return "normal"
    if z < 1.5:
        return "elevated"
    return "crisis"


def to_month(d: date | datetime) -> str:
    """Convert date to YYYY-MM string."""
    if isinstance(d, datetime):
        d = d.date()
    return f"{d.year:04d}-{d.month:02d}"


def get_series(db: Session, series_id: str) -> list[Observation]:
    """Get all observations for a series, ordered by date."""
    return (
        db.query(Observation)
        .filter(Observation.series_id == series_id)
        .order_by(Observation.date.asc())
        .all()
    )


def series_month_map(obs: list[Observation]) -> dict[str, Observation]:
    """Map YYYY-MM -> Observation. Keep latest date if multiple per month."""
    m: dict[str, Observation] = {}
    for o in obs:
        k = to_month(o.date)
        if (k not in m) or (o.date > m[k].date):
            m[k] = o
    return m


def get_active_indicators(db: Session) -> list[IndicatorConfig]:
    """Get all indicators configured to be in the composite."""
    return (
        db.query(IndicatorConfig)
        .filter(IndicatorConfig.include_in_composite == True)
        .order_by(IndicatorConfig.display_order)
        .all()
    )


def calculate_composite_latest(db: Session, window: int = WINDOW) -> dict:
    """
    Calculate latest composite score using dynamic indicators.

    Returns dict with:
    - month: current month
    - indicators: dict of series_id -> {date, value, z_score, regime}
    - composite: {score, regime}
    - meta: {window, aligned_months, indicator_count}
    """
    configs = get_active_indicators(db)
    if not configs:
        return {"error": "no indicators configured"}

    # Build month maps for each indicator
    indicator_maps: dict[str, dict[str, Observation]] = {}
    for config in configs:
        obs = get_series(db, config.series_id)
        if obs:
            indicator_maps[config.series_id] = series_month_map(obs)

    if not indicator_maps:
        return {"error": "no indicator data found"}

    # Find common months across all indicators
    all_month_sets = [set(m.keys()) for m in indicator_maps.values()]
    common_months = sorted(set.intersection(*all_month_sets))

    if len(common_months) < window:
        return {
            "error": "not enough aligned data",
            "aligned_months": len(common_months),
            "required": window,
        }

    window_months = common_months[-window:]
    current_month = window_months[-1]

    # Calculate z-scores for each indicator
    indicator_results: dict[str, dict] = {}
    weighted_z_sum = 0.0
    weight_sum = 0.0

    for config in configs:
        if config.series_id not in indicator_maps:
            continue

        obs_map = indicator_maps[config.series_id]
        values = [float(obs_map[m].value) for m in window_months]
        latest_value = values[-1]
        z = zscore(values, latest_value)

        # Apply sign inversion if configured
        if config.invert_sign:
            z = -z

        indicator_results[config.series_id] = {
            "date": str(obs_map[current_month].date),
            "value": latest_value,
            "z_score": round(z, 3),
            "regime": regime(z),
        }

        weighted_z_sum += z * config.weight
        weight_sum += config.weight

    # Calculate weighted composite
    composite_score = weighted_z_sum / weight_sum if weight_sum > 0 else 0.0

    return {
        "month": current_month,
        **indicator_results,
        "composite": {
            "score": round(composite_score, 3),
            "regime": regime(composite_score),
        },
        "meta": {
            "window": window,
            "aligned_months": len(common_months),
            "indicator_count": len(indicator_results),
        },
    }


def calculate_composite_history(db: Session, window: int = WINDOW) -> list[dict]:
    """
    Calculate composite history with z-scores for each month.

    Returns list of dicts with:
    - month
    - {series_id}_z for each indicator
    - composite
    - regime
    """
    configs = get_active_indicators(db)
    if not configs:
        return []

    # Build month maps for each indicator
    indicator_maps: dict[str, dict[str, Observation]] = {}
    config_map: dict[str, IndicatorConfig] = {}
    for config in configs:
        obs = get_series(db, config.series_id)
        if obs:
            indicator_maps[config.series_id] = series_month_map(obs)
            config_map[config.series_id] = config

    if not indicator_maps:
        return []

    # Find common months
    all_month_sets = [set(m.keys()) for m in indicator_maps.values()]
    common_months = sorted(set.intersection(*all_month_sets))

    if len(common_months) < window:
        return []

    results = []
    for i in range(window - 1, len(common_months)):
        window_months = common_months[i - (window - 1) : i + 1]
        current_month = common_months[i]

        row: dict = {"month": current_month}
        weighted_z_sum = 0.0
        weight_sum = 0.0

        for series_id, obs_map in indicator_maps.items():
            config = config_map[series_id]
            values = [float(obs_map[m].value) for m in window_months]
            latest_value = values[-1]
            z = zscore(values, latest_value)

            if config.invert_sign:
                z = -z

            row[f"{series_id}_z"] = round(z, 3)
            weighted_z_sum += z * config.weight
            weight_sum += config.weight

        composite_score = weighted_z_sum / weight_sum if weight_sum > 0 else 0.0
        row["composite"] = round(composite_score, 3)
        row["regime"] = regime(composite_score)
        results.append(row)

    return results
