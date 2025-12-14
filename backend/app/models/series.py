from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Series(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)   # e.g. "gscpi"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # monthly / weekly / daily
    source: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)
