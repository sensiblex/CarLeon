from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealStatus


class TrackingPointCreate(BaseModel):
    status: DealStatus
    comment: str | None = Field(default=None, max_length=255)


class TrackingPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    deal_id: str
    status: int
    comment: str | None
    tx_hash: str | None
    block_index: int | None
    created_at: datetime