from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.series import Series


class IndicatorConfig(Base):
    """Configuration for indicators in the composite calculation."""
    __tablename__ = "indicator_configs"

    series_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("series.id"), primary_key=True
    )
    include_in_composite: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    invert_sign: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    series: Mapped[Series] = relationship(Series)
