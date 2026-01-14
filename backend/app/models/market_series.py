from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class MarketSeries(Base):
    """Metadata for stocks, ETFs, and indices."""
    __tablename__ = "market_series"

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    series_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "index", "etf", "stock"
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "chips", "retail", "logistics"
