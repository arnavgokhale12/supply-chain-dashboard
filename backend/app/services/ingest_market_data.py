"""Ingest market data (stocks, ETFs, indices) using yfinance."""
from __future__ import annotations

from datetime import date, timedelta

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.market_price import MarketPrice
from backend.app.models.market_series import MarketSeries

# Market symbols to ingest
MARKET_SYMBOLS = {
    "indices": [
        ("SPY", "S&P 500 ETF", None),
    ],
    "sector_etfs": [
        ("XLI", "Industrial Select Sector SPDR", "industrials"),
        ("XLY", "Consumer Discretionary Select SPDR", "consumer"),
        ("XLK", "Technology Select Sector SPDR", "technology"),
        ("SMH", "VanEck Semiconductor ETF", "chips"),
    ],
    "stocks": [
        ("NVDA", "NVIDIA Corporation", "chips"),
        ("TSM", "Taiwan Semiconductor", "chips"),
        ("AVGO", "Broadcom Inc", "chips"),
        ("AMZN", "Amazon.com Inc", "logistics"),
        ("COST", "Costco Wholesale", "retail"),
        ("WMT", "Walmart Inc", "retail"),
    ],
}


def ensure_market_series(db: Session) -> None:
    """Ensure all market series exist in the database."""
    existing = {s.symbol for s in db.query(MarketSeries).all()}

    to_add = []
    for series_type, symbols in MARKET_SYMBOLS.items():
        type_map = {"indices": "index", "sector_etfs": "etf", "stocks": "stock"}
        stype = type_map.get(series_type, series_type)

        for symbol, name, theme in symbols:
            if symbol not in existing:
                to_add.append(MarketSeries(
                    symbol=symbol,
                    name=name,
                    series_type=stype,
                    theme=theme,
                ))

    if to_add:
        db.add_all(to_add)
        db.commit()
        print(f"Added {len(to_add)} new market series")


def fetch_yfinance_prices(symbol: str, years: int = 5) -> list[dict]:
    """Fetch historical prices using yfinance."""
    ticker = yf.Ticker(symbol)
    end_date = date.today()
    start_date = end_date - timedelta(days=years * 365)

    df = ticker.history(start=start_date.isoformat(), end=end_date.isoformat())

    if df.empty:
        return []

    results = []
    for idx, row in df.iterrows():
        results.append({
            "date": idx.date(),
            "close": float(row["Close"]),
            "adjusted_close": float(row["Close"]),  # yfinance returns adjusted prices by default
            "volume": int(row["Volume"]) if row["Volume"] else None,
        })

    return results


def upsert_prices(db: Session, symbol: str, prices: list[dict]) -> int:
    """Insert new prices, skip existing ones."""
    existing_dates = {
        d for (d,) in db.execute(
            select(MarketPrice.date).where(MarketPrice.symbol == symbol)
        ).all()
    }

    to_add: list[MarketPrice] = []
    for p in prices:
        if p["date"] in existing_dates:
            continue
        to_add.append(MarketPrice(
            symbol=symbol,
            date=p["date"],
            close=p["close"],
            adjusted_close=p["adjusted_close"],
            volume=p.get("volume"),
        ))

    if to_add:
        db.add_all(to_add)
        db.commit()
    return len(to_add)


def ingest_symbol(db: Session, symbol: str) -> int:
    """Ingest price data for a single symbol."""
    try:
        prices = fetch_yfinance_prices(symbol)
        if not prices:
            print(f"  No data returned for {symbol}")
            return 0
        return upsert_prices(db, symbol, prices)
    except Exception as e:
        print(f"  Error ingesting {symbol}: {e}")
        return 0


def main() -> None:
    """Ingest all market data."""
    db = SessionLocal()
    try:
        # Ensure series metadata exists
        ensure_market_series(db)

        total_new = 0
        all_symbols = []
        for symbols in MARKET_SYMBOLS.values():
            all_symbols.extend([s[0] for s in symbols])

        print(f"Ingesting {len(all_symbols)} symbols using yfinance...")

        for symbol in all_symbols:
            n = ingest_symbol(db, symbol)
            count = db.query(MarketPrice).filter(MarketPrice.symbol == symbol).count()
            print(f"{symbol}: +{n} new, {count} total")
            total_new += n

        print(f"\nTotal new prices: {total_new}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
