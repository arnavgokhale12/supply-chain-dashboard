"""Market data API endpoints."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.deps import get_db
from backend.app.models.market_price import MarketPrice
from backend.app.models.market_series import MarketSeries
from backend.app.models.regime_return import RegimeReturn
from backend.app.services.composite_calculator import calculate_composite_latest
from backend.app.services.regime_analyzer import get_regime_context

router = APIRouter(prefix="/v1/market", tags=["market"])


@router.get("/series")
def list_series(db: Session = Depends(get_db)):
    """List all market series (stocks, ETFs, indices)."""
    series = db.query(MarketSeries).order_by(MarketSeries.series_type, MarketSeries.symbol).all()
    return [
        {
            "symbol": s.symbol,
            "name": s.name,
            "type": s.series_type,
            "theme": s.theme,
        }
        for s in series
    ]


@router.get("/prices/{symbol}")
def get_prices(
    symbol: str,
    days: int = Query(365, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Get historical prices for a symbol."""
    start_date = date.today() - timedelta(days=days)

    prices = (
        db.query(MarketPrice)
        .filter(MarketPrice.symbol == symbol)
        .filter(MarketPrice.date >= start_date)
        .order_by(MarketPrice.date)
        .all()
    )

    return [
        {
            "date": str(p.date),
            "close": p.close,
            "adjusted_close": p.adjusted_close,
            "volume": p.volume,
        }
        for p in prices
    ]


@router.get("/regime-returns")
def get_regime_returns(
    regime: str | None = None,
    theme: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Get regime-conditional return statistics.

    Optional filters:
    - regime: Filter by regime (low, normal, elevated, crisis)
    - theme: Filter by theme (chips, retail, logistics, etc.)
    """
    query = db.query(RegimeReturn, MarketSeries).join(MarketSeries)

    if regime:
        query = query.filter(RegimeReturn.regime == regime)
    if theme:
        query = query.filter(MarketSeries.theme == theme)

    results = query.all()

    return [
        {
            "symbol": ms.symbol,
            "name": ms.name,
            "theme": ms.theme,
            "regime": rr.regime,
            "avg_monthly_return_pct": round(rr.avg_monthly_return * 100, 2),
            "std_monthly_return_pct": round((rr.std_monthly_return or 0) * 100, 2),
            "sample_count": rr.sample_count,
        }
        for rr, ms in results
    ]


@router.get("/current")
def get_current_market(db: Session = Depends(get_db)):
    """
    Get current market snapshot with regime context.

    Returns:
    - current_regime: Current supply chain regime
    - symbols: Latest prices and returns for all symbols
    - regime_context: Historical performance in current regime
    """
    # Get current composite to determine regime
    composite = calculate_composite_latest(db)
    current_regime = composite.get("composite", {}).get("regime", "normal")

    # Get latest prices for each symbol
    symbols_data = []
    series = db.query(MarketSeries).all()

    for s in series:
        # Get two most recent prices to calculate daily return
        prices = (
            db.query(MarketPrice)
            .filter(MarketPrice.symbol == s.symbol)
            .order_by(MarketPrice.date.desc())
            .limit(2)
            .all()
        )

        if not prices:
            continue

        latest = prices[0]
        daily_return = None
        if len(prices) > 1:
            prev = prices[1]
            if prev.adjusted_close > 0:
                daily_return = (latest.adjusted_close - prev.adjusted_close) / prev.adjusted_close

        # Get regime return for current regime
        regime_return = (
            db.query(RegimeReturn)
            .filter(RegimeReturn.symbol == s.symbol)
            .filter(RegimeReturn.regime == current_regime)
            .first()
        )

        symbols_data.append({
            "symbol": s.symbol,
            "name": s.name,
            "type": s.series_type,
            "theme": s.theme,
            "latest_date": str(latest.date),
            "latest_price": latest.adjusted_close,
            "daily_return_pct": round(daily_return * 100, 2) if daily_return else None,
            "regime_avg_return_pct": round(regime_return.avg_monthly_return * 100, 2) if regime_return else None,
        })

    # Get regime context
    context = get_regime_context(db, current_regime)

    return {
        "current_regime": current_regime,
        "composite_score": composite.get("composite", {}).get("score"),
        "symbols": symbols_data,
        "regime_context": context,
    }
