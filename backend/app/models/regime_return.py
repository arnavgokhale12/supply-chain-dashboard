from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.market_series import MarketSeries


class RegimeReturn(Base):
    """Precomputed regime-conditional return statistics."""
    __tablename__ = "regime_returns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        String(20), ForeignKey("market_series.symbol"), index=True, nullable=False
    )
    regime: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    avg_monthly_return: Mapped[float] = mapped_column(Float, nullable=False)
    std_monthly_return: Mapped[float] = mapped_column(Float, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    market_series: Mapped[MarketSeries] = relationship(MarketSeries)
