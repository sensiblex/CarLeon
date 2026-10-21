import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrackingPoint(Base):
    __tablename__ = "tracking_points"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    deal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deals.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True, index=True)
    block_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    deal = relationship("Deal", back_populates="tracking_points")