from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.market_series import MarketSeries


class MarketPrice(Base):
    """Daily price data for stocks, ETFs, and indices."""
    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_market_prices_symbol_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        String(20), ForeignKey("market_series.symbol"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)

    market_series: Mapped[MarketSeries] = relationship(MarketSeries)
