import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DealStatus(enum.IntEnum):
    PUBLISHED = 0
    ORDER_CREATED = 1
    DEPOSIT_PAID = 2
    PURCHASED = 3
    IN_TRANSIT_ORIGIN = 4
    CUSTOMS = 5
    IN_TRANSIT_RF = 6
    DELIVERED_CITY = 7
    READY_FOR_PICKUP = 8
    COMPLETED = 9


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    track_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    supplier: Mapped[str] = mapped_column(String(128))
    buyer: Mapped[str] = mapped_column(String(128))
    status: Mapped[DealStatus] = mapped_column(
        Enum(DealStatus, name="deal_status"), default=DealStatus.PUBLISHED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tracking_points = relationship(
        "TrackingPoint", back_populates="deal", cascade="all, delete-orphan"
    )