"""Запись в блокчейне - событие смены статуса сделки."""
import time
from dataclasses import dataclass, field, asdict
from enum import IntEnum


class DealStatus(IntEnum):
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


@dataclass
class StatusChange:
    deal_id: str
    status: DealStatus
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        self.status = DealStatus(self.status)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StatusChange":
        return cls(
            deal_id=data["deal_id"],
            status=data["status"],
            timestamp=data["timestamp"],
        )
