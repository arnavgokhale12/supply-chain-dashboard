"""Regime-conditional return analysis."""
from __future__ import annotations

from datetime import datetime
from statistics import mean, pstdev

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.market_price import MarketPrice
from backend.app.models.market_series import MarketSeries
from backend.app.models.regime_return import RegimeReturn
from backend.app.services.composite_calculator import calculate_composite_history


def compute_monthly_returns(prices: list[dict]) -> dict[str, float]:
    """
    Compute monthly returns from daily prices.

    Args:
        prices: List of {date, adjusted_close} sorted by date

    Returns:
        Dict of YYYY-MM -> monthly return (as decimal, e.g., 0.05 for 5%)
    """
    if not prices:
        return {}

    # Group by month, take last price of each month
    month_prices: dict[str, float] = {}
    for p in prices:
        month = f"{p['date'].year:04d}-{p['date'].month:02d}"
        month_prices[month] = p["adjusted_close"]

    # Calculate month-over-month returns
    months = sorted(month_prices.keys())
    returns: dict[str, float] = {}

    for i in range(1, len(months)):
        prev_month = months[i - 1]
        curr_month = months[i]
        prev_price = month_prices[prev_month]
        curr_price = month_prices[curr_month]

        if prev_price > 0:
            returns[curr_month] = (curr_price - prev_price) / prev_price

    return returns


def compute_regime_returns(db: Session) -> int:
    """
    Compute regime-conditional returns for all market symbols.

    1. Get composite history with regime labels
    2. For each symbol, compute monthly returns
    3. Group returns by regime
    4. Calculate statistics and store

    Returns count of records inserted.
    """
    # Get composite history with regimes
    composite_history = calculate_composite_history(db)
    if not composite_history:
        print("No composite history available")
        return 0

    # Build month -> regime map
    month_regime: dict[str, str] = {}
    for row in composite_history:
        month_regime[row["month"]] = row["regime"]

    # Get all market symbols
    symbols = db.query(MarketSeries.symbol).all()
    if not symbols:
        print("No market series found")
        return 0

    # Clear existing regime returns
    db.execute(delete(RegimeReturn))
    db.commit()

    records_inserted = 0

    for (symbol,) in symbols:
        # Get prices for this symbol
        prices = (
            db.query(MarketPrice)
            .filter(MarketPrice.symbol == symbol)
            .order_by(MarketPrice.date)
            .all()
        )

        if not prices:
            continue

        # Convert to dict format
        price_data = [
            {"date": p.date, "adjusted_close": p.adjusted_close}
            for p in prices
        ]

        # Compute monthly returns
        returns = compute_monthly_returns(price_data)

        # Group returns by regime
        regime_returns: dict[str, list[float]] = {
            "low": [],
            "normal": [],
            "elevated": [],
            "crisis": [],
        }

        for month, ret in returns.items():
            if month in month_regime:
                regime_returns[month_regime[month]].append(ret)

        # Calculate and store statistics for each regime
        for regime, rets in regime_returns.items():
            if not rets:
                continue

            avg_return = mean(rets)
            std_return = pstdev(rets) if len(rets) > 1 else 0.0

            db.add(RegimeReturn(
                symbol=symbol,
                regime=regime,
                avg_monthly_return=avg_return,
                std_monthly_return=std_return,
                sample_count=len(rets),
                computed_at=datetime.utcnow(),
            ))
            records_inserted += 1

    db.commit()
    return records_inserted


def get_regime_context(db: Session, current_regime: str) -> dict:
    """
    Get market performance context for the current regime.

    Returns dict with:
    - regime: Current regime
    - sector_performance: Dict of theme -> avg historical return
    - top_performers: List of symbols that historically perform well
    - bottom_performers: List of symbols that historically underperform
    """
    # Get all regime returns for current regime
    regime_data = (
        db.query(RegimeReturn, MarketSeries)
        .join(MarketSeries)
        .filter(RegimeReturn.regime == current_regime)
        .all()
    )

    if not regime_data:
        return {"regime": current_regime, "message": "No historical data for this regime"}

    # Group by theme
    theme_returns: dict[str, list[float]] = {}
    symbol_returns: list[tuple[str, str, float, int]] = []

    for rr, ms in regime_data:
        theme = ms.theme or "other"
        if theme not in theme_returns:
            theme_returns[theme] = []
        theme_returns[theme].append(rr.avg_monthly_return)

        symbol_returns.append((
            ms.symbol,
            ms.name,
            rr.avg_monthly_return,
            rr.sample_count,
        ))

    # Calculate theme averages
    sector_performance = {
        theme: {
            "avg_monthly_return": round(mean(rets) * 100, 2),  # As percentage
            "symbol_count": len(rets),
        }
        for theme, rets in theme_returns.items()
    }

    # Sort symbols by performance
    symbol_returns.sort(key=lambda x: x[2], reverse=True)

    top_performers = [
        {"symbol": s[0], "name": s[1], "avg_return_pct": round(s[2] * 100, 2)}
        for s in symbol_returns[:5]
    ]

    bottom_performers = [
        {"symbol": s[0], "name": s[1], "avg_return_pct": round(s[2] * 100, 2)}
        for s in symbol_returns[-5:]
    ]

    return {
        "regime": current_regime,
        "sector_performance": sector_performance,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
    }


def main() -> None:
    """Compute regime returns for all symbols."""
    db = SessionLocal()
    try:
        print("Computing regime-conditional returns...")
        n = compute_regime_returns(db)
        print(f"Inserted {n} regime return records")
    finally:
        db.close()


if __name__ == "__main__":
    main()
